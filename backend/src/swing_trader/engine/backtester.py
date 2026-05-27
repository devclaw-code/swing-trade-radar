"""Walk-forward backtester.

For each historical bar, slice the enriched df up to that bar and ask the strategy
to generate signals (strategies inspect only the last bar). When a signal fires,
simulate the trade forward bar-by-bar to determine target / stop / timeout exit.
"""
# ruff: noqa: N806, N815  -- `*_R` names are part of the public dataclass / spec.

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import UTC, date, datetime

import numpy as np
import pandas as pd
from sqlalchemy import delete, select

from ..config import settings
from ..data.db import Backtest as BacktestRow
from ..data.db import session_scope
from ..data.price_fetcher import load_ohlcv
from ..strategies.base_strategy import BaseStrategy, Signal
from .indicators import enrich
from .signal_generator import default_strategies

log = logging.getLogger(__name__)


# --- Dataclasses -------------------------------------------------------------


@dataclass
class Trade:
    ticker: str
    strategy: str
    direction: str
    entry_date: date
    entry_price: float
    exit_date: date
    exit_price: float
    exit_reason: str  # "target" | "stop" | "timeout"
    return_R: float
    return_pct: float
    hold_bars: int
    max_adverse_R: float  # MAE
    max_favorable_R: float  # MFE


@dataclass
class BacktestResult:
    strategy: str
    ticker: str
    period_start: date
    period_end: date
    n_trades: int
    win_rate: float
    avg_r: float
    profit_factor: float
    max_dd_r: float
    sharpe: float
    avg_hold_bars: float
    trades: list[Trade] = field(default_factory=list)


# --- Simulation --------------------------------------------------------------


def _as_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if hasattr(value, "date"):
        return value.date()
    return pd.Timestamp(value).date()


def simulate_trade(
    df: pd.DataFrame,
    entry_idx: int,
    signal: Signal,
    max_hold: int = 20,
    slippage_bps: float = 5.0,
) -> Trade | None:
    """Simulate a single trade starting at the bar AFTER entry_idx.

    Entry fills at next bar's open with slippage. Walks forward up to max_hold
    bars looking for target/stop hits. If both hit in the same bar, conservatively
    assume the stop fired first. Times out at close of bar entry_idx+max_hold.
    Returns None if entry_idx+1 is out of bounds.
    """
    n = len(df)
    if entry_idx + 1 >= n:
        return None

    direction = signal.direction
    slip = slippage_bps / 10_000.0

    next_bar = df.iloc[entry_idx + 1]
    raw_open = float(next_bar["open"])
    entry_price = (
        raw_open * (1.0 + slip) if direction == "LONG" else raw_open * (1.0 - slip)
    )

    stop = float(signal.stop)
    target = float(signal.target)
    risk = abs(entry_price - stop)
    if risk <= 0 or not math.isfinite(risk):
        return None

    entry_date = _as_date(next_bar.name)

    last_idx = min(entry_idx + max_hold, n - 1)
    mae = 0.0  # max adverse (negative R)
    mfe = 0.0  # max favorable (positive R)

    exit_price: float | None = None
    exit_date: date | None = None
    exit_reason: str | None = None
    hold_bars = 0

    for j in range(entry_idx + 1, last_idx + 1):
        bar = df.iloc[j]
        high = float(bar["high"])
        low = float(bar["low"])
        close = float(bar["close"])
        hold_bars = j - entry_idx

        # Update MAE/MFE in R units (intra-bar excursion).
        if direction == "LONG":
            adverse_R = (low - entry_price) / risk  # negative when low < entry
            favorable_R = (high - entry_price) / risk
        else:
            adverse_R = (entry_price - high) / risk
            favorable_R = (entry_price - low) / risk
        if adverse_R < mae:
            mae = adverse_R
        if favorable_R > mfe:
            mfe = favorable_R

        # Check exits.
        hit_stop = False
        hit_target = False
        if direction == "LONG":
            if low <= stop:
                hit_stop = True
            if high >= target:
                hit_target = True
        else:  # SHORT
            if high >= stop:
                hit_stop = True
            if low <= target:
                hit_target = True

        if hit_stop and hit_target:
            # Conservative: stop fires first.
            exit_price = stop
            exit_reason = "stop"
            exit_date = _as_date(bar.name)
            break
        if hit_stop:
            exit_price = stop
            exit_reason = "stop"
            exit_date = _as_date(bar.name)
            break
        if hit_target:
            exit_price = target
            exit_reason = "target"
            exit_date = _as_date(bar.name)
            break

        if j == last_idx:
            exit_price = close
            exit_reason = "timeout"
            exit_date = _as_date(bar.name)
            break

    if exit_price is None or exit_date is None or exit_reason is None:
        return None

    pnl = (
        exit_price - entry_price if direction == "LONG" else entry_price - exit_price
    )
    return_R = pnl / risk
    return_pct = pnl / entry_price

    return Trade(
        ticker=signal.ticker,
        strategy=signal.strategy,
        direction=direction,
        entry_date=entry_date,
        entry_price=entry_price,
        exit_date=exit_date,
        exit_price=exit_price,
        exit_reason=exit_reason,
        return_R=float(return_R),
        return_pct=float(return_pct),
        hold_bars=int(hold_bars),
        max_adverse_R=float(mae),
        max_favorable_R=float(mfe),
    )


# --- Aggregation -------------------------------------------------------------


def _aggregate(
    trades: list[Trade],
    strategy: str,
    ticker: str,
    period_start: date,
    period_end: date,
) -> BacktestResult:
    """Compute summary stats over a list of trades."""
    n = len(trades)
    if n == 0:
        return BacktestResult(
            strategy=strategy,
            ticker=ticker,
            period_start=period_start,
            period_end=period_end,
            n_trades=0,
            win_rate=0.0,
            avg_r=0.0,
            profit_factor=0.0,
            max_dd_r=0.0,
            sharpe=0.0,
            avg_hold_bars=0.0,
            trades=[],
        )

    rs = np.array([t.return_R for t in trades], dtype=float)
    holds = np.array([max(1, t.hold_bars) for t in trades], dtype=float)

    wins = int((rs > 0).sum())
    win_rate = wins / n
    avg_r = float(rs.mean())
    avg_hold_bars = float(holds.mean())

    pos_sum = float(rs[rs > 0].sum())
    neg_sum = float(-rs[rs < 0].sum())  # positive magnitude
    if neg_sum == 0 and pos_sum == 0:
        profit_factor = 0.0
    elif neg_sum == 0:
        profit_factor = float("inf")
    elif pos_sum == 0:
        profit_factor = 0.0
    else:
        profit_factor = pos_sum / neg_sum

    # Max drawdown of cumulative R curve (positive number).
    cum = np.cumsum(rs)
    running_max = np.maximum.accumulate(cum)
    dd = running_max - cum  # >= 0
    max_dd_r = float(dd.max()) if len(dd) else 0.0

    # Sharpe: spread each trade's R over its hold_bars as per-day returns.
    if n < 2:
        sharpe = 0.0
    else:
        daily_chunks = [np.full(int(h), r / h) for r, h in zip(rs, holds, strict=True)]
        daily = np.concatenate(daily_chunks) if daily_chunks else np.array([])
        if daily.size < 2:
            sharpe = 0.0
        else:
            std = float(daily.std(ddof=1))
            mean = float(daily.mean())
            sharpe = 0.0 if std == 0 else float(mean / std * math.sqrt(252))

    return BacktestResult(
        strategy=strategy,
        ticker=ticker,
        period_start=period_start,
        period_end=period_end,
        n_trades=n,
        win_rate=win_rate,
        avg_r=avg_r,
        profit_factor=profit_factor,
        max_dd_r=max_dd_r,
        sharpe=sharpe,
        avg_hold_bars=avg_hold_bars,
        trades=list(trades),
    )


# --- Backtest driver ---------------------------------------------------------


_MIN_WARMUP_BARS = 210  # need sma200 + small buffer


def backtest_strategy(
    strategy: BaseStrategy,
    ticker: str,
    lookback_days: int = 730,
    max_hold: int = 20,
) -> BacktestResult:
    """Walk-forward backtest one strategy on one ticker."""
    df = load_ohlcv(ticker, lookback_days=lookback_days)
    if df.empty:
        today = datetime.now(UTC).date()
        return _aggregate([], strategy.name, ticker, today, today)

    df = enrich(df)
    n = len(df)
    period_start = _as_date(df.index[0])
    period_end = _as_date(df.index[-1])

    if n < _MIN_WARMUP_BARS + 2:
        return _aggregate([], strategy.name, ticker, period_start, period_end)

    trades: list[Trade] = []
    open_until_idx = -1  # no overlapping positions for this (strategy, ticker)

    for i in range(_MIN_WARMUP_BARS, n - 1):
        if i <= open_until_idx:
            continue
        view = df.iloc[: i + 1]
        try:
            signals = strategy.generate(view, ticker)
        except Exception as e:
            log.debug("strategy %s failed on %s @ bar %d: %s", strategy.name, ticker, i, e)
            continue
        if not signals:
            continue
        # Take the first (strategies typically emit 0 or 1 per bar).
        sig = signals[0]
        trade = simulate_trade(df, i, sig, max_hold=max_hold)
        if trade is None:
            continue
        trades.append(trade)
        # Block re-entry until this trade exits.
        open_until_idx = i + trade.hold_bars

    return _aggregate(trades, strategy.name, ticker, period_start, period_end)


def _persist_result(result: BacktestResult) -> None:
    """Replace prior rows for (strategy, ticker) with this result."""
    with session_scope() as s:
        s.execute(
            delete(BacktestRow).where(
                BacktestRow.strategy == result.strategy,
                BacktestRow.ticker == result.ticker,
            )
        )
        s.add(
            BacktestRow(
                strategy=result.strategy,
                ticker=result.ticker,
                period_start=result.period_start,
                period_end=result.period_end,
                n_trades=result.n_trades,
                win_rate=result.win_rate,
                avg_r=result.avg_r,
                profit_factor=(
                    result.profit_factor
                    if math.isfinite(result.profit_factor)
                    else 9_999.0
                ),
                max_dd_r=result.max_dd_r,
                sharpe=result.sharpe,
                avg_hold_bars=result.avg_hold_bars,
                ran_at=datetime.now(UTC).replace(tzinfo=None),
            )
        )


def backtest_all(lookback_days: int = 730) -> list[BacktestResult]:
    """Run every strategy over every configured ticker. Persists to DB."""
    strategies = default_strategies()
    results: list[BacktestResult] = []
    for strat in strategies:
        for ticker in settings.tickers:
            try:
                res = backtest_strategy(strat, ticker, lookback_days=lookback_days)
            except Exception as e:
                log.exception("backtest %s/%s failed: %s", strat.name, ticker, e)
                continue
            results.append(res)
            try:
                _persist_result(res)
            except Exception as e:
                log.exception(
                    "persist backtest %s/%s failed: %s", strat.name, ticker, e
                )
    return results


def latest_results(strategy: str | None = None) -> list[dict]:
    """Return summary rows from the backtests table (no per-trade detail)."""
    with session_scope() as s:
        q = select(BacktestRow)
        if strategy:
            q = q.where(BacktestRow.strategy == strategy)
        q = q.order_by(BacktestRow.strategy.asc(), BacktestRow.ticker.asc())
        rows = s.execute(q).scalars().all()

    out: list[dict] = []
    for r in rows:
        out.append(
            dict(
                strategy=r.strategy,
                ticker=r.ticker,
                period_start=r.period_start.isoformat() if r.period_start else None,
                period_end=r.period_end.isoformat() if r.period_end else None,
                n_trades=r.n_trades,
                win_rate=r.win_rate,
                avg_r=r.avg_r,
                profit_factor=r.profit_factor,
                max_dd_r=r.max_dd_r,
                sharpe=r.sharpe,
                avg_hold_bars=r.avg_hold_bars,
                ran_at=r.ran_at.isoformat() if r.ran_at else None,
            )
        )
    return out
