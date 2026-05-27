"""Signal generator: orchestrates strategies across the configured universe."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from ..config import settings
from ..data.db import Signal as SignalRow
from ..data.db import session_scope
from ..data.price_fetcher import load_ohlcv
from ..strategies.base_strategy import BaseStrategy, Signal
from ..strategies.bollinger_squeeze import BollingerSqueezeStrategy
from ..strategies.ma_crossover import MaCrossoverStrategy
from ..strategies.macd_trend import MacdTrendStrategy
from ..strategies.rsi_mean_reversion import RsiMeanReversionStrategy
from ..strategies.sr_breakout import SrBreakoutStrategy
from ..strategies.volume_trend import VolumeTrendStrategy
from .indicators import enrich
from .risk_classifier import ClassifiedSignal, classify

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
