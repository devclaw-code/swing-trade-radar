"""Signal generator: orchestrates strategies across the configured universe."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert_v2  # alias for clarity below

from ..config import settings
from ..data.db import Signal as SignalRow
from ..data.db import VerdictRow, session_scope
from ..data.price_fetcher import load_ohlcv
from ..data.sanity import check_data_sanity
from ..schemas import SanityFlag as SanityFlagSchema
from ..schemas import Verdict
from ..strategies.base_strategy import BaseStrategy, Signal
from ..strategies.bollinger_squeeze import BollingerSqueezeStrategy
from ..strategies.ma_crossover import MaCrossoverStrategy
from ..strategies.macd_trend import MacdTrendStrategy
from ..strategies.rsi_mean_reversion import RsiMeanReversionStrategy
from ..strategies.sr_breakout import SrBreakoutStrategy
from ..strategies.v2.base import StrategyResult, V2Strategy
from ..strategies.v2.s1_trend_50_200 import TrendFiftyTwoHundredStrategy
from ..strategies.v2.s2_clenow_momentum import ClenowMomentumStrategy, compute_basket_scores
from ..strategies.v2.s3_connors_rsi2 import ConnorsRsi2Strategy
from ..strategies.v2.s4_minervini_vcp import MinerviniVcpStrategy
from ..strategies.v2.s5_pead import PeadStrategy
from ..strategies.volume_trend import VolumeTrendStrategy
from .base_rate import compute_base_rate
from .indicators import enrich
from .regime import compute_regime, offline_default
from .risk_classifier import ClassifiedSignal, classify
from .sample_size import apply_sample_size_adjustment
from .scoring import apply_correlation_penalties
from .verdict import attach_score_breakdown, synthesize_verdict

log = logging.getLogger(__name__)


def default_strategies() -> list[BaseStrategy]:
    """Strategy registry. Add new strategies here as they are implemented."""
    return [
        MaCrossoverStrategy(),
        BollingerSqueezeStrategy(),
        MacdTrendStrategy(),
        RsiMeanReversionStrategy(),
        SrBreakoutStrategy(),
        VolumeTrendStrategy(),
    ]


def _merge_duplicates(signals: list[Signal]) -> list[Signal]:
    """If multiple strategies fire for same (ticker, direction, bar) → merge confirmations,
    keep the one with highest confidence."""
    grouped: dict[tuple[str, str, object], list[Signal]] = {}
    for s in signals:
        grouped.setdefault((s.ticker, s.direction, s.bar_date), []).append(s)

    merged: list[Signal] = []
    for group in grouped.values():
        if len(group) == 1:
            merged.append(group[0])
            continue
        primary = max(group, key=lambda x: x.confidence)
        seen = set(primary.confirmations)
        for other in group:
            if other is primary:
                continue
            for c in other.confirmations:
                if c not in seen:
                    primary.confirmations.append(c)
                    seen.add(c)
            primary.confirmations.append(f"Also fired: {other.strategy}")
        merged.append(primary)
    return merged


def _persist(classified: list[ClassifiedSignal]) -> int:
    if not classified:
        return 0
    rows = []
    for cs in classified:
        s = cs.signal
        rows.append(
            dict(
                ticker=s.ticker,
                strategy=s.strategy,
                direction=s.direction,
                entry=s.entry,
                target=s.target,
                stop=s.stop,
                stop_pct=cs.stop_pct,
                rr_ratio=cs.rr_ratio,
                risk=cs.risk,
                confidence=cs.confidence,
                confirmations=s.confirmations,
                bar_date=s.bar_date,
                generated_at=s.generated_at,
                status="open",
            )
        )
    with session_scope() as sess:
        stmt = sqlite_insert(SignalRow).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["ticker", "strategy", "bar_date", "direction"],
            set_={
                "entry": stmt.excluded.entry,
                "target": stmt.excluded.target,
                "stop": stmt.excluded.stop,
                "stop_pct": stmt.excluded.stop_pct,
                "rr_ratio": stmt.excluded.rr_ratio,
                "risk": stmt.excluded.risk,
                "confidence": stmt.excluded.confidence,
                "confirmations": stmt.excluded.confirmations,
                "generated_at": stmt.excluded.generated_at,
            },
        )
        sess.execute(stmt)
    return len(rows)


def generate_all() -> dict:
    """Run all strategies over the full universe. Persists signals. Returns summary."""
    strategies = default_strategies()
    all_signals: list[Signal] = []
    per_ticker: dict[str, int] = {}
    errors = 0
    started = datetime.now(UTC).replace(tzinfo=None)

    for ticker in settings.tickers:
        try:
            df = load_ohlcv(ticker)
            if df.empty:
                continue
            df = enrich(df)
            ticker_signals: list[Signal] = []
            for strat in strategies:
                try:
                    ticker_signals.extend(strat.generate(df, ticker))
                except Exception as e:
                    log.exception("strategy %s failed on %s: %s", strat.name, ticker, e)
                    errors += 1
            per_ticker[ticker] = len(ticker_signals)
            all_signals.extend(ticker_signals)
        except Exception as e:
            log.exception("ticker %s failed: %s", ticker, e)
            errors += 1

    merged = _merge_duplicates(all_signals)
    classified = [classify(s) for s in merged]
    n = _persist(classified)
    return {
        "started_at": started.isoformat(),
        "finished_at": datetime.now(UTC).replace(tzinfo=None).isoformat(),
        "n_signals": n,
        "per_ticker": per_ticker,
        "errors": errors,
    }


def latest_open_signals(
    risk: str | None = None,
    strategy: str | None = None,
    direction: str | None = None,
    ticker: str | None = None,
) -> list[dict]:
    """Fetch open signals, with optional filters. Returns a list of plain dicts."""
    with session_scope() as s:
        q = select(SignalRow).where(SignalRow.status == "open")
        if ticker:
            q = q.where(SignalRow.ticker == ticker.upper())
        if risk:
            q = q.where(SignalRow.risk == risk.upper())
        if strategy:
            q = q.where(SignalRow.strategy == strategy)
        if direction:
            q = q.where(SignalRow.direction == direction.upper())
        q = q.order_by(SignalRow.generated_at.desc())
        rows = s.execute(q).scalars().all()

    out = []
    for r in rows:
        out.append(
            dict(
                id=r.id,
                ticker=r.ticker,
                strategy=r.strategy,
                direction=r.direction,
                entry=r.entry,
                target=r.target,
                stop=r.stop,
                stop_pct=r.stop_pct,
                rr_ratio=r.rr_ratio,
                risk=r.risk,
                confidence=r.confidence,
                confirmations=r.confirmations,
                bar_date=r.bar_date.isoformat() if r.bar_date else None,
                generated_at=r.generated_at.isoformat() if r.generated_at else None,
            )
        )
    return out


# =============================================================================
# V2 — verdict engine (Phase 2)
# =============================================================================


def default_v2_strategies() -> list[V2Strategy]:
    return [
        TrendFiftyTwoHundredStrategy(),
        ClenowMomentumStrategy(),
        ConnorsRsi2Strategy(),
        MinerviniVcpStrategy(),
        PeadStrategy(),
    ]


def _try_fetch_earnings(ticker: str) -> list:
    """Best-effort earnings dates from yfinance. Returns [] on failure."""
    try:
        import yfinance as yf  # local import — keep optional

        tk = yf.Ticker(ticker)
        ed = tk.get_earnings_dates(limit=8) if hasattr(tk, "get_earnings_dates") else None
        if ed is None or ed.empty:
            return []
        return [ts.date() for ts in ed.index.to_pydatetime()]
    except Exception as e:
        log.debug("earnings fetch failed for %s: %s", ticker, e)
        return []


def _build_basket(
    *,
    enriched_by_ticker: dict[str, pd.DataFrame],
    vix: float | None,
    earnings: dict[str, list],
) -> dict:
    from typing import Any

    basket: dict[str, Any] = dict(enriched_by_ticker)
    basket["clenow_scores"] = compute_basket_scores(enriched_by_ticker)
    basket["vix"] = vix
    basket["earnings_dates"] = earnings
    return basket


def _persist_verdicts(verdicts: list[Verdict]) -> int:
    if not verdicts:
        return 0
    rows = [
        dict(
            ticker=v.ticker,
            as_of=v.as_of,
            verdict=v.verdict,
            conviction=v.conviction,
            primary_setup=v.primary_setup,
            risk_tier=v.risk_tier,
            payload=v.model_dump(mode="json"),
            generated_at=datetime.now(UTC).replace(tzinfo=None),
        )
        for v in verdicts
    ]
    with session_scope() as s:
        stmt = sqlite_insert_v2(VerdictRow).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["ticker", "as_of"],
            set_={
                "verdict": stmt.excluded.verdict,
                "conviction": stmt.excluded.conviction,
                "primary_setup": stmt.excluded.primary_setup,
                "risk_tier": stmt.excluded.risk_tier,
                "payload": stmt.excluded.payload,
                "generated_at": stmt.excluded.generated_at,
            },
        )
        s.execute(stmt)
    return len(rows)


def generate_verdicts(
    *,
    use_offline_regime: bool = False,
    persist: bool = True,
) -> dict:
    """Run all v2 strategies for the universe and synthesize per-ticker Verdicts.

    Returns: {summary, verdicts: [Verdict.model_dump]}
    """
    import pandas as pd  # local — keep top-level imports lean

    started = datetime.now(UTC).replace(tzinfo=None)
    strategies = default_v2_strategies()

    # 1. Load + enrich each ticker (universe + macro index ETFs for regime checks)
    macro_tickers = ("SPY", "QQQ")
    enriched: dict[str, pd.DataFrame] = {}
    sanity_by_ticker: dict[str, list[SanityFlagSchema]] = {}
    for t in list(settings.tickers) + list(macro_tickers):
        try:
            df = load_ohlcv(t)
            if df.empty:
                continue
            enriched[t] = enrich(df)
            if t not in macro_tickers:
                raw_flags = check_data_sanity(enriched[t], ticker=t)
                sanity_by_ticker[t] = [
                    SanityFlagSchema(**f.to_dict()) for f in raw_flags
                ]
                if raw_flags:
                    log.info(
                        "sanity flags for %s: %s",
                        t,
                        [(f.code, f.severity) for f in raw_flags],
                    )
        except Exception as e:
            log.warning("enrich failed for %s: %s", t, e)

    # 2. Regime
    if use_offline_regime:
        regime = offline_default()
    else:
        try:
            regime = compute_regime()
        except Exception as e:
            log.warning("regime fetch failed, using offline default: %s", e)
            regime = offline_default()

    # 3. Earnings — fetched once per ticker (best-effort, skip macro ETFs)
    earnings_map = {t: _try_fetch_earnings(t) for t in enriched if t not in macro_tickers}

    basket = _build_basket(
        enriched_by_ticker=enriched,
        vix=regime.vix,
        earnings=earnings_map,
    )

    # 4. Per-ticker eval + synthesize (macro ETFs are basket context, not verdicts)
    verdicts: list[Verdict] = []
    errors = 0
    for ticker, df in enriched.items():
        if ticker in macro_tickers:
            continue
        try:
            results: list[StrategyResult] = []
            for strat in strategies:
                try:
                    results.append(strat.evaluate(df, ticker, basket))
                except Exception as e:
                    log.exception("strat %s failed on %s: %s", strat.name, ticker, e)
                    errors += 1

            as_of = (
                df.index[-1].date()
                if hasattr(df.index[-1], "date")
                else datetime.now(UTC).date()
            )

            def _make_lookup(_df=df, _ticker=ticker):
                def _lookup(primary: StrategyResult):
                    setup_id = primary.strategy_name
                    sig = _proxy_signature(setup_id)
                    if sig is None:
                        return None
                    stats = compute_base_rate(
                        _ticker, setup_id, sig, _df,
                        max_hold_days=primary.max_hold_days or 10,
                    )
                    if not stats or stats.get("occurrences", 0) == 0:
                        return None
                    from ..schemas import BaseRateBlock
                    return BaseRateBlock(
                        occurrences=int(stats["occurrences"]),
                        win_rate=float(stats["win_rate"]),
                        avg_r=float(stats["avg_r"]),
                        median_hold=float(stats["median_hold"]),
                    )

                return _lookup

            verdict = synthesize_verdict(
                ticker=ticker,
                as_of=as_of,
                strategy_results=results,
                regime=regime,
                base_rate_lookup=_make_lookup(),
            )

            # ---- Score breakdown -------------------------------------------------
            # Pick the same `primary` the synthesizer used so scoring lines up.
            fired = [r for r in results if r.fired]
            fired.sort(key=lambda r: r.score, reverse=True)
            if fired:
                primary_for_score = fired[0]
            elif results:
                primary_for_score = max(results, key=lambda r: r.score)
            else:
                primary_for_score = None

            base_rate_for_score = None
            if primary_for_score is not None:
                # Reuse the base rate already attached by synthesize_verdict when
                # the scoring primary matches the verdict's primary setup.
                attached = getattr(verdict.why, "historical_base_rate", None)
                if attached is not None and verdict.primary_setup == primary_for_score.strategy_name:
                    base_rate_for_score = attached
                else:
                    try:
                        base_rate_for_score = _make_lookup()(primary_for_score)
                    except Exception as e:
                        log.debug("base_rate (for scoring) failed for %s: %s", ticker, e)

            dte: int | None = None
            today_dt = as_of
            edates = earnings_map.get(ticker) or []
            future_edates = [d for d in edates if d >= today_dt]
            if future_edates:
                dte = (min(future_edates) - today_dt).days

            attach_score_breakdown(
                verdict,
                df=df,
                primary=primary_for_score,
                sanity_flags=sanity_by_ticker.get(ticker, []),
                base_rate=base_rate_for_score,
                days_to_earnings=dte,
            )

            # Latest-bar enrichment for UI header.
            try:
                closes = df["close"].dropna()
                if len(closes) >= 1:
                    last_close = float(closes.iloc[-1])
                    verdict.price = round(last_close, 4)
                    if len(closes) >= 2:
                        prev = float(closes.iloc[-2])
                        if prev > 0:
                            verdict.day_change_pct = round((last_close - prev) / prev, 6)
                    tail = closes.tail(60).tolist()
                    verdict.sparkline = [float(round(x, 4)) for x in tail]
            except Exception as e:
                log.warning("sparkline/price enrich failed for %s: %s", ticker, e)

            # Attach sanity flags collected during enrich step.
            verdict.sanity_flags = sanity_by_ticker.get(ticker, [])

            verdicts.append(verdict)
        except Exception as e:
            log.exception("verdict synth failed for %s: %s", ticker, e)
            errors += 1

    # ---- Correlation post-pass --------------------------------------------
    # Sort by score descending so higher-scoring trades get priority and
    # downgrade their lower-scoring correlated peers.
    scored = [v for v in verdicts if v.score is not None]
    scored.sort(key=lambda v: v.score or 0.0, reverse=True)
    try:
        apply_correlation_penalties(
            verdicts_in_order=scored,
            enriched_by_ticker={t: d for t, d in enriched.items() if t not in macro_tickers},
        )
    except Exception as e:
        log.warning("correlation post-pass failed: %s", e)

    # ---- Sample-size reliability post-pass --------------------------------
    # Run AFTER scoring + correlation so `confidence_adjusted_for_sample`
    # reflects the *final* score, not an intermediate one. This is also
    # idempotent (see engine.sample_size).
    for v in verdicts:
        try:
            apply_sample_size_adjustment(v)
        except Exception as e:
            log.warning("sample-size post-pass failed for %s: %s", v.ticker, e)

    n_persisted = _persist_verdicts(verdicts) if persist else 0
    finished = datetime.now(UTC).replace(tzinfo=None)
    return {
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "n_verdicts": len(verdicts),
        "n_persisted": n_persisted,
        "errors": errors,
        "verdicts": [v.model_dump(mode="json") for v in verdicts],
        "regime": regime.model_dump(mode="json"),
    }


def _proxy_signature(setup_id: str):
    """Return a fast row-level boolean predicate matching the spirit of the strategy.

    These proxies power the historical base-rate computation. They do NOT exactly
    reproduce the v2 strategy logic (which depends on basket data) — they capture
    the per-ticker, per-bar core conditions.
    """
    import pandas_ta_classic as ta

    if setup_id == "S1_trend_50_200":
        def sig(df, i):
            row = df.iloc[i]
            return (
                row["close"] > row["sma50"]
                and row["sma50"] > row["sma200"]
            )
        return sig

    if setup_id == "S3_connors_rsi2":
        def sig(df, i):
            # Compute RSI(2) for the slice ending at i
            sub = df["close"].iloc[: i + 1]
            rsi = ta.rsi(sub, length=2)
            row = df.iloc[i]
            if rsi is None or rsi.empty:
                return False
            return (
                rsi.iloc[-1] < 10
                and row["close"] > row["sma200"]
            )
        return sig

    if setup_id == "S2_clenow_momentum":
        def sig(df, i):
            row = df.iloc[i]
            sub = df["close"].iloc[: i + 1]
            sma100 = sub.rolling(100).mean().iloc[-1]
            return row["close"] > sma100
        return sig

    if setup_id == "S4_minervini_vcp":
        def sig(df, i):
            row = df.iloc[i]
            if i < 50:
                return False
            prev_high = df["high"].iloc[max(0, i - 20) : i].max()
            return row["close"] > prev_high and row["close"] > row["sma50"]
        return sig

    if setup_id == "S5_pead":
        def sig(df, i):
            if i < 1:
                return False
            prev = df.iloc[i - 1]
            row = df.iloc[i]
            gap = (row["open"] - prev["close"]) / max(prev["close"], 1e-6)
            return gap > 0.03 and row["close"] > row["sma200"]
        return sig

    return None


def latest_verdicts(
    ticker: str | None = None,
    verdict: str | None = None,
) -> list[dict]:
    """Return the most-recent verdict per ticker (or one ticker), as plain dicts."""
    from sqlalchemy import func as sql_func

    with session_scope() as s:
        # Latest as_of per ticker
        latest_q = (
            select(VerdictRow.ticker, sql_func.max(VerdictRow.as_of).label("max_as_of"))
            .group_by(VerdictRow.ticker)
            .subquery()
        )
        q = select(VerdictRow).join(
            latest_q,
            (VerdictRow.ticker == latest_q.c.ticker)
            & (VerdictRow.as_of == latest_q.c.max_as_of),
        )
        if ticker:
            q = q.where(VerdictRow.ticker == ticker.upper())
        if verdict:
            q = q.where(VerdictRow.verdict == verdict.upper())
        q = q.order_by(VerdictRow.conviction.desc())
        rows = s.execute(q).scalars().all()
    return [r.payload for r in rows]
