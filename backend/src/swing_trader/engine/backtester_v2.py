"""Walk-forward backtester for the v2 verdict strategies (S1-S5).

The v1 `backtester.py` drives `BaseStrategy.generate()`. The v2 strategies use a
different interface (`V2Strategy.evaluate() -> StrategyResult`) and only fire LONG
swing setups with an entry/stop/target trade plan. This module:

1. **Adapts** each `V2Strategy` so the existing, well-tested `simulate_trade()` can
   run it bar-by-bar (when `fired=True` we synthesize a `Signal` from the result's
   entry/stop/target/max_hold).
2. **Walk-forward (out-of-sample only).** History is sliced into rolling
   train/test folds (`train_days` / `test_days`, default 126/21 ≈ 6mo/1mo). Only
   trades whose *entry bar* falls inside a test window are kept, so the reported
   stats are genuinely out-of-sample. (The strategies are rule-based with fixed
   params, so "train" here is the war-up/embargo region, not a fit step — but the
   structure is WFA-correct and ready for any future parameter fitting.)
3. **Deflated Sharpe Ratio** (Bailey & López de Prado 2014) using the number of
   strategies tested as the trial count, plus the realized skew/kurtosis of the
   per-trade return stream. A strategy must clear `deflated_sharpe >= DSR_GATE`
   (default 1.0) before it's considered deployable.

Pooling: trades are pooled across the whole universe per strategy (each ticker is
just another sample of the same rule), which is what the `/strategies` cards show.

KNOWN LIMITATION: S2 (Clenow) needs a cross-sectional ``basket_data["clenow_scores"]``
map and S5 (PEAD) needs ``basket_data["earnings_dates"]``; the per-bar walk-forward
loop evaluates one ticker in isolation without that basket context, so those two
strategies currently report 0 OOS trades here. Wiring point-in-time basket context
into the WFA loop is a follow-up (needs historical earnings dates + a rolling
cross-sectional rank); until then their cards correctly show "no qualifying
out-of-sample trades" rather than a fabricated edge.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import UTC, date, datetime

import numpy as np
import pandas as pd
from scipy import stats as _scipy_stats
from sqlalchemy import delete, select

from ..config import settings
from ..data.db import BacktestV2Row, session_scope
from ..data.price_fetcher import load_ohlcv
from ..strategies.base_strategy import Signal
from ..strategies.v2.base import StrategyResult, V2Strategy
from .backtester import Trade, _as_date, simulate_trade
from .indicators import enrich
from .signal_generator import default_v2_strategies

log = logging.getLogger(__name__)


# Deploy gate: a strategy is "live-eligible" only at/above this deflated Sharpe.
DSR_GATE = 1.0
# Walk-forward fold sizing (trading days). 126 ≈ 6 months, 21 ≈ 1 month.
DEFAULT_TRAIN_DAYS = 126
DEFAULT_TEST_DAYS = 21
_MIN_TRAIN_DAYS = 21  # floor when shrinking folds for short histories
_MIN_WARMUP_BARS = 210  # need sma200 + a small buffer before the first test fold


# --- v2 -> Signal adapter ----------------------------------------------------


def _result_to_signal(res: StrategyResult, ticker: str) -> Signal | None:
    """Turn a fired StrategyResult into a Signal the simulator understands.

    Returns None when the result didn't fire or lacks a complete trade plan.
    All v2 strategies are long-only swing setups.
    """
    if not res.fired:
        return None
    if res.entry_price is None or res.stop_price is None or res.target_price is None:
        return None
    entry = float(res.entry_price)
    stop = float(res.stop_price)
    target = float(res.target_price)
    if not (math.isfinite(entry) and math.isfinite(stop) and math.isfinite(target)):
        return None
    # Long-only: stop must sit below entry and target above it.
    if not (stop < entry < target):
        return None
    return Signal(
        ticker=ticker,
        strategy=res.strategy_name,
        direction="LONG",
        entry=entry,
        target=target,
        stop=stop,
        confidence=float(res.score),
    )


# --- Deflated Sharpe ---------------------------------------------------------


def _annualized_sharpe_from_trades(rs: np.ndarray, holds: np.ndarray) -> float:
    """Annualized Sharpe by spreading each trade's R over its hold (bars≈days)."""
    if rs.size < 2:
        return 0.0
    chunks = [np.full(int(max(1, h)), r / max(1, h)) for r, h in zip(rs, holds, strict=True)]
    daily = np.concatenate(chunks) if chunks else np.array([])
    if daily.size < 2:
        return 0.0
    std = float(daily.std(ddof=1))
    if std == 0:
        return 0.0
    return float(daily.mean() / std * math.sqrt(252))


def deflated_sharpe_ratio(
    trade_returns: np.ndarray,
    observed_sharpe_annual: float,
    n_trials: int,
) -> float:
    """Bailey & López de Prado (2014) Deflated Sharpe Ratio.

    Returns a probability in [0, 1]: P(true SR > 0) after correcting the observed
    SR for (a) the number of independent strategy trials and (b) the non-normality
    (skew / kurtosis) of the return stream.

    `observed_sharpe_annual` is the annualized SR; we de-annualize to per-trade.
    """
    n = trade_returns.size
    if n < 8 or n_trials < 1:
        return 0.0

    # Per-trade Sharpe (de-annualize: SR_annual = SR_pertrade * sqrt(trades/yr)).
    # Estimate trades-per-year from the realized cadence isn't available here, so
    # we work directly in per-trade space using the trade-return moments.
    mu = float(trade_returns.mean())
    sigma = float(trade_returns.std(ddof=1))
    if sigma == 0:
        return 0.0
    sr_hat = mu / sigma  # per-trade observed Sharpe

    skew = float(_scipy_stats.skew(trade_returns, bias=False))
    # Fisher kurtosis (excess); DSR formula wants non-excess (Pearson) kurtosis.
    kurt = float(_scipy_stats.kurtosis(trade_returns, fisher=False, bias=False))

    # Expected maximum Sharpe across N independent trials (variance of trial SRs
    # approximated as 1/n — the standard BLdP simplification when the cross-trial
    # SR variance is unknown). E[max] via the Gaussian extreme-value approximation.
    euler_mascheroni = 0.5772156649
    e = math.e
    if n_trials > 1:
        z1 = _scipy_stats.norm.ppf(1.0 - 1.0 / n_trials)
        z2 = _scipy_stats.norm.ppf(1.0 - 1.0 / (n_trials * e))
        expected_max_sr = (1.0 - euler_mascheroni) * z1 + euler_mascheroni * z2
    else:
        expected_max_sr = 0.0
    # Scale the threshold by the cross-trial SR dispersion (~1/sqrt(n) per BLdP).
    sr_star = expected_max_sr / math.sqrt(n)

    # DSR: probability the deflated SR exceeds the trial-adjusted benchmark.
    denom = 1.0 - skew * sr_hat + ((kurt - 1.0) / 4.0) * sr_hat**2
    if denom <= 0:
        return 0.0
    dsr_stat = (sr_hat - sr_star) * math.sqrt(n - 1) / math.sqrt(denom)
    return float(_scipy_stats.norm.cdf(dsr_stat))


# --- Result dataclass --------------------------------------------------------


@dataclass
class V2BacktestResult:
    strategy: str
    period_start: date
    period_end: date
    n_trades: int
    win_rate: float
    avg_r: float
    profit_factor: float
    max_dd_r: float
    sharpe: float
    deflated_sharpe: float
    passes_gate: bool
    avg_hold_bars: float
    n_tickers: int
    trades: list[Trade] = field(default_factory=list)

    def to_card(self) -> dict:
        """The compact shape the `/strategies` frontend card consumes."""
        return {
            "sharpe": round(self.sharpe, 3),
            "deflated_sharpe": round(self.deflated_sharpe, 3),
            "win_rate": round(self.win_rate, 4),
            "avg_r": round(self.avg_r, 3),
            "max_dd_r": round(self.max_dd_r, 3),
            "n_trades": self.n_trades,
            "profit_factor": (
                round(self.profit_factor, 3)
                if math.isfinite(self.profit_factor)
                else 9999.0
            ),
            "passes_gate": self.passes_gate,
            "n_tickers": self.n_tickers,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
        }


# --- Walk-forward driver -----------------------------------------------------


def _test_window_mask(
    n: int,
    train_days: int,
    test_days: int,
    warmup: int,
) -> np.ndarray:
    """Boolean mask over bar indices that are inside an out-of-sample test window.

    Layout (repeating): [warmup ... ][train][test][train][test]...
    Only `test` bars are eligible for entries. The first `warmup + train_days`
    bars are reserved so every test fold has full indicator history behind it.
    """
    mask = np.zeros(n, dtype=bool)
    fold = train_days + test_days
    start = warmup
    while start + train_days < n:
        test_lo = start + train_days
        test_hi = min(test_lo + test_days, n)
        mask[test_lo:test_hi] = True
        start += fold
    return mask


def backtest_v2_strategy_on_ticker(
    strategy: V2Strategy,
    ticker: str,
    df_enriched: pd.DataFrame,
    *,
    train_days: int = DEFAULT_TRAIN_DAYS,
    test_days: int = DEFAULT_TEST_DAYS,
) -> list[Trade]:
    """Out-of-sample trades for one strategy on one ticker (walk-forward).

    Folds are adaptive: if the fixed train window won't leave at least one test
    window after warmup, we shrink ``train_days`` (down to a floor) so short
    histories still yield some out-of-sample evaluation instead of zero trades.
    """
    n = len(df_enriched)
    # Need warmup + at least one (train + test) fold.
    if n < _MIN_WARMUP_BARS + test_days + 5:
        return []

    # Shrink train window if the default leaves no room for a test fold.
    avail = n - _MIN_WARMUP_BARS - test_days
    eff_train = train_days
    if avail < train_days:
        eff_train = max(_MIN_TRAIN_DAYS, avail)
    if eff_train < _MIN_TRAIN_DAYS or n < _MIN_WARMUP_BARS + eff_train + test_days:
        return []

    eligible = _test_window_mask(n, eff_train, test_days, _MIN_WARMUP_BARS)
    if not eligible.any():
        return []
    trades: list[Trade] = []
    open_until_idx = -1  # no overlapping positions per (strategy, ticker)

    for i in range(_MIN_WARMUP_BARS, n - 1):
        if not eligible[i] or i <= open_until_idx:
            continue
        view = df_enriched.iloc[: i + 1]
        try:
            res = strategy.evaluate(view, ticker)
        except Exception as e:
            log.debug("v2 %s failed on %s @ bar %d: %s", strategy.name, ticker, i, e)
            continue
        sig = _result_to_signal(res, ticker)
        if sig is None:
            continue
        max_hold = int(res.max_hold_days or 20)
        trade = simulate_trade(df_enriched, i, sig, max_hold=max_hold)
        if trade is None:
            continue
        trades.append(trade)
        open_until_idx = i + trade.hold_bars

    return trades


def _aggregate_v2(
    strategy: str,
    trades: list[Trade],
    n_tickers: int,
    n_trials: int,
    period_start: date,
    period_end: date,
) -> V2BacktestResult:
    n = len(trades)
    if n == 0:
        return V2BacktestResult(
            strategy=strategy,
            period_start=period_start,
            period_end=period_end,
            n_trades=0,
            win_rate=0.0,
            avg_r=0.0,
            profit_factor=0.0,
            max_dd_r=0.0,
            sharpe=0.0,
            deflated_sharpe=0.0,
            passes_gate=False,
            avg_hold_bars=0.0,
            n_tickers=n_tickers,
            trades=[],
        )

    # Order pooled trades by exit date so the equity curve / DD is chronological.
    trades_sorted = sorted(trades, key=lambda t: t.exit_date)
    rs = np.array([t.return_R for t in trades_sorted], dtype=float)
    holds = np.array([max(1, t.hold_bars) for t in trades_sorted], dtype=float)

    win_rate = float((rs > 0).mean())
    avg_r = float(rs.mean())
    avg_hold_bars = float(holds.mean())

    pos = float(rs[rs > 0].sum())
    neg = float(-rs[rs < 0].sum())
    profit_factor = (float("inf") if pos > 0 else 0.0) if neg == 0 else pos / neg

    cum = np.cumsum(rs)
    dd = np.maximum.accumulate(cum) - cum
    max_dd_r = float(dd.max()) if dd.size else 0.0

    sharpe = _annualized_sharpe_from_trades(rs, holds)
    dsr = deflated_sharpe_ratio(rs, sharpe, n_trials)
    passes = dsr >= DSR_GATE and n >= 20

    return V2BacktestResult(
        strategy=strategy,
        period_start=period_start,
        period_end=period_end,
        n_trades=n,
        win_rate=win_rate,
        avg_r=avg_r,
        profit_factor=profit_factor,
        max_dd_r=max_dd_r,
        sharpe=sharpe,
        deflated_sharpe=dsr,
        passes_gate=passes,
        avg_hold_bars=avg_hold_bars,
        n_tickers=n_tickers,
        trades=trades_sorted,
    )


def backtest_all_v2(
    *,
    lookback_days: int = 1460,  # ~6y so WFA has many folds
    train_days: int = DEFAULT_TRAIN_DAYS,
    test_days: int = DEFAULT_TEST_DAYS,
    persist: bool = True,
) -> dict[str, V2BacktestResult]:
    """Walk-forward backtest all v2 strategies across the universe.

    Returns {strategy_name: V2BacktestResult}. The DSR trial count is the number
    of strategies evaluated (each strategy is one independent trial of "find an
    edge in this universe").
    """
    strategies = default_v2_strategies()
    n_trials = len(strategies)

    # Pre-load + enrich every ticker once; reuse across all strategies.
    enriched: dict[str, pd.DataFrame] = {}
    for t in settings.tickers:
        try:
            raw = load_ohlcv(t, lookback_days=lookback_days)
            if raw.empty:
                continue
            enriched[t] = enrich(raw)
        except Exception as e:
            log.warning("v2 backtest enrich failed for %s: %s", t, e)

    if not enriched:
        log.warning("v2 backtest: no ticker data available")
        return {}

    period_start = min(_as_date(df.index[0]) for df in enriched.values())
    period_end = max(_as_date(df.index[-1]) for df in enriched.values())

    results: dict[str, V2BacktestResult] = {}
    for strat in strategies:
        pooled: list[Trade] = []
        for ticker, df in enriched.items():
            try:
                pooled.extend(
                    backtest_v2_strategy_on_ticker(
                        strat, ticker, df, train_days=train_days, test_days=test_days
                    )
                )
            except Exception as e:
                log.exception("v2 backtest %s/%s failed: %s", strat.name, ticker, e)
        res = _aggregate_v2(
            strat.name, pooled, len(enriched), n_trials, period_start, period_end
        )
        results[strat.name] = res
        log.info(
            "v2 backtest %s: n=%d win=%.1f%% avgR=%+.2f sharpe=%.2f DSR=%.3f gate=%s",
            strat.name,
            res.n_trades,
            res.win_rate * 100,
            res.avg_r,
            res.sharpe,
            res.deflated_sharpe,
            res.passes_gate,
        )

    if persist:
        try:
            _persist_v2(results)
        except Exception as e:
            log.exception("v2 backtest persist failed: %s", e)

    return results


# --- Persistence -------------------------------------------------------------


def _persist_v2(results: dict[str, V2BacktestResult]) -> None:
    """Upsert one summary row per strategy into the `backtests_v2` table."""
    ran_at = datetime.now(UTC).replace(tzinfo=None)
    with session_scope() as s:
        for name, r in results.items():
            s.execute(delete(BacktestV2Row).where(BacktestV2Row.strategy == name))
            s.add(
                BacktestV2Row(
                    strategy=name,
                    period_start=r.period_start,
                    period_end=r.period_end,
                    n_trades=r.n_trades,
                    n_tickers=r.n_tickers,
                    win_rate=r.win_rate,
                    avg_r=r.avg_r,
                    profit_factor=(
                        r.profit_factor if math.isfinite(r.profit_factor) else 9999.0
                    ),
                    max_dd_r=r.max_dd_r,
                    sharpe=r.sharpe,
                    deflated_sharpe=r.deflated_sharpe,
                    passes_gate=r.passes_gate,
                    avg_hold_bars=r.avg_hold_bars,
                    ran_at=ran_at,
                )
            )


def latest_v2_cards() -> dict[str, dict]:
    """{strategy_name: card-dict} from the `backtests_v2` table (for /strategies)."""
    out: dict[str, dict] = {}
    try:
        with session_scope() as s:
            rows = s.execute(select(BacktestV2Row)).scalars().all()
        for r in rows:
            out[r.strategy] = {
                "sharpe": round(r.sharpe, 3),
                "deflated_sharpe": round(r.deflated_sharpe, 3),
                "win_rate": round(r.win_rate, 4),
                "avg_r": round(r.avg_r, 3),
                "max_dd_r": round(r.max_dd_r, 3),
                "n_trades": r.n_trades,
                "profit_factor": round(r.profit_factor, 3),
                "passes_gate": bool(r.passes_gate),
                "n_tickers": r.n_tickers,
                "period_start": r.period_start.isoformat() if r.period_start else None,
                "period_end": r.period_end.isoformat() if r.period_end else None,
                "ran_at": r.ran_at.isoformat() if r.ran_at else None,
            }
    except Exception as e:
        log.debug("latest_v2_cards read failed: %s", e)
    return out
