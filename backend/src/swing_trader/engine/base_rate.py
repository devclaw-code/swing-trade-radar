"""Historical base-rate computer.

Idea: for any setup we can express as a row-level boolean predicate, walk back
through the cached OHLCV for the ticker, find every bar where the predicate
fired, simulate the same exit rules forward, and aggregate stats.

Output:
    {
        "occurrences": int,
        "win_rate": float (0..1),
        "avg_r": float (avg multiple of 1R),
        "median_hold": float (bars),
    }

Cached in SQLite table ``base_rates`` keyed by (ticker, setup_id, as_of_date).
"""

from __future__ import annotations

import logging
import math
from collections.abc import Callable
from datetime import date, datetime

import numpy as np
import pandas as pd
from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    UniqueConstraint,
    select,
)
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Mapped, mapped_column

from ..data.db import Base, session_scope

log = logging.getLogger(__name__)


class BaseRate(Base):
    __tablename__ = "base_rates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), index=True)
    setup_id: Mapped[str] = mapped_column(String(64), index=True)
    as_of_date: Mapped[date] = mapped_column(Date, index=True)
    occurrences: Mapped[int] = mapped_column(Integer)
    win_rate: Mapped[float] = mapped_column(Float)
    avg_r: Mapped[float] = mapped_column(Float)
    median_hold: Mapped[float] = mapped_column(Float)
    extra: Mapped[dict] = mapped_column(JSON, default=dict)
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("ticker", "setup_id", "as_of_date"),)


SetupSignature = Callable[[pd.DataFrame, int], bool]


def _simulate_trade(
    df: pd.DataFrame,
    entry_idx: int,
    *,
    atr_col: str,
    max_hold_days: int,
    atr_stop_mult: float = 2.0,
    atr_target_mult: float = 4.0,
) -> tuple[float, int] | None:
    """Simulate an ATR-bounded long trade. Returns (R-multiple, bars_held) or None."""
    if entry_idx + 1 >= len(df):
        return None
    entry = float(df.iloc[entry_idx + 1]["open"])  # next-bar open
    atr_at_entry = float(df.iloc[entry_idx].get(atr_col, float("nan")))
    if not math.isfinite(atr_at_entry) or atr_at_entry <= 0:
        return None
    stop = entry - atr_stop_mult * atr_at_entry
    target = entry + atr_target_mult * atr_at_entry
    risk = entry - stop
    if risk <= 0:
        return None

    end = min(len(df) - 1, entry_idx + 1 + max_hold_days)
    for i in range(entry_idx + 1, end + 1):
        row = df.iloc[i]
        low = float(row["low"])
        high = float(row["high"])
        if low <= stop:
            r = (stop - entry) / risk
            return r, i - entry_idx
        if high >= target:
            r = (target - entry) / risk
            return r, i - entry_idx
    final = float(df.iloc[end]["close"])
    r = (final - entry) / risk
    return r, end - entry_idx


def compute_base_rate(
    ticker: str,
    setup_id: str,
    setup_signature: SetupSignature,
    df: pd.DataFrame,
    *,
    max_hold_days: int = 10,
    atr_col: str = "atr14",
    use_cache: bool = True,
) -> dict:
    """Walk df backwards, find all setup occurrences, simulate, aggregate.

    Cached per (ticker, setup_id, as_of). Skips the most recent ``max_hold_days+1``
    bars so every historical trade has a complete simulated outcome.
    """
    if df.empty or len(df) < 50:
        return {"occurrences": 0, "win_rate": 0.0, "avg_r": 0.0, "median_hold": 0.0}

    as_of = df.index[-1].date() if hasattr(df.index[-1], "date") else date.today()

    if use_cache:
        with session_scope() as s:
            row = s.execute(
                select(BaseRate).where(
                    BaseRate.ticker == ticker,
                    BaseRate.setup_id == setup_id,
                    BaseRate.as_of_date == as_of,
                )
            ).scalar_one_or_none()
            if row is not None:
                return {
                    "occurrences": row.occurrences,
                    "win_rate": row.win_rate,
                    "avg_r": row.avg_r,
                    "median_hold": row.median_hold,
                }

    rs: list[float] = []
    holds: list[int] = []
    last_safe = len(df) - max_hold_days - 2
    for i in range(50, max(50, last_safe)):
        try:
            if not setup_signature(df, i):
                continue
        except Exception:  # robust against odd row data
            continue
        sim = _simulate_trade(df, i, atr_col=atr_col, max_hold_days=max_hold_days)
        if sim is None:
            continue
        r, h = sim
        rs.append(r)
        holds.append(h)

    occurrences = len(rs)
    if occurrences == 0:
        result = {"occurrences": 0, "win_rate": 0.0, "avg_r": 0.0, "median_hold": 0.0}
    else:
        wins = sum(1 for r in rs if r > 0)
        result = {
            "occurrences": occurrences,
            "win_rate": round(wins / occurrences, 4),
            "avg_r": round(float(np.mean(rs)), 4),
            "median_hold": round(float(np.median(holds)), 2),
        }

    if use_cache:
        try:
            with session_scope() as s:
                stmt = sqlite_insert(BaseRate).values(
                    ticker=ticker,
                    setup_id=setup_id,
                    as_of_date=as_of,
                    occurrences=result["occurrences"],
                    win_rate=result["win_rate"],
                    avg_r=result["avg_r"],
                    median_hold=result["median_hold"],
                    extra={},
                )
                stmt = stmt.on_conflict_do_update(
                    index_elements=["ticker", "setup_id", "as_of_date"],
                    set_={
                        "occurrences": stmt.excluded.occurrences,
                        "win_rate": stmt.excluded.win_rate,
                        "avg_r": stmt.excluded.avg_r,
                        "median_hold": stmt.excluded.median_hold,
                    },
                )
                s.execute(stmt)
        except Exception as e:
            log.warning("base_rate cache write failed for %s/%s: %s", ticker, setup_id, e)

    return result


def format_base_rate(stats: dict, ticker: str, setup_id: str) -> str:
    """Render the numeric base-rate into the human string used in WhyBlock."""
    if stats["occurrences"] == 0:
        return f"No prior occurrences of '{setup_id}' on {ticker} in the cached history."
    return (
        f"On {ticker}, this setup ('{setup_id}') has fired {stats['occurrences']} times in "
        f"the cached window. Win rate {stats['win_rate']*100:.0f}%. Avg R = {stats['avg_r']:+.2f}. "
        f"Median hold {stats['median_hold']:.0f} bars."
    )
