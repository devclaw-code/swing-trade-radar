"""Refresh job: pull macro + earnings calendars and upsert into ``events``.

Idempotent. Safe to call multiple times per day. Uses simple INSERT-or-skip
semantics via the table's UniqueConstraint on (kind, symbol, release,
scheduled_at).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from ..config import settings
from .earnings_calendar import fetch_earnings_window
from .db import Event, session_scope
from .macro_calendar import fetch_next_window

log = logging.getLogger(__name__)


@dataclass
class RefreshSummary:
    macro_inserted: int
    earnings_inserted: int
    macro_total: int
    earnings_total: int
    errors: list[str]

    def as_dict(self) -> dict:
        return {
            "macro_inserted": self.macro_inserted,
            "earnings_inserted": self.earnings_inserted,
            "macro_total": self.macro_total,
            "earnings_total": self.earnings_total,
            "errors": list(self.errors),
        }


def refresh_calendars(tickers: list[str] | None = None) -> RefreshSummary:
    """Fetch and upsert macro + earnings events. Returns counts."""
    if not settings.calendars_enabled:
        return RefreshSummary(0, 0, 0, 0, ["calendars_disabled"])

    errors: list[str] = []
    universe = list(tickers or settings.tickers)
    now = datetime.now(UTC).replace(tzinfo=None)

    try:
        macro = fetch_next_window()
    except Exception as e:
        log.exception("macro fetch failed")
        errors.append(f"macro:{e!s}")
        macro = []

    try:
        earnings = fetch_earnings_window(universe)
    except Exception as e:
        log.exception("earnings fetch failed")
        errors.append(f"earnings:{e!s}")
        earnings = []

    macro_inserted = 0
    earnings_inserted = 0
    with session_scope() as s:
        for m in macro:
            stmt = sqlite_insert(Event).values(
                kind="macro",
                symbol="",
                release=m.release,
                scheduled_at=_naive_utc(m.scheduled_at),
                confirmed=m.confirmed,
                source=m.source,
                fetched_at=now,
            ).on_conflict_do_nothing(
                index_elements=["kind", "symbol", "release", "scheduled_at"]
            )
            res = s.execute(stmt)
            if res.rowcount:
                macro_inserted += 1
            else:
                # already present — bump fetched_at + confirmed/source for staleness tracking
                s.execute(
                    Event.__table__.update()
                    .where(Event.kind == "macro")
                    .where(Event.symbol == "")
                    .where(Event.release == m.release)
                    .where(Event.scheduled_at == _naive_utc(m.scheduled_at))
                    .values(confirmed=m.confirmed, source=m.source, fetched_at=now)
                )

        for e in earnings:
            stmt = sqlite_insert(Event).values(
                kind="earnings",
                symbol=e.symbol,
                release="EARNINGS",
                scheduled_at=_naive_utc(e.scheduled_at),
                confirmed=e.confirmed,
                source=e.source,
                fetched_at=now,
            ).on_conflict_do_nothing(
                index_elements=["kind", "symbol", "release", "scheduled_at"]
            )
            res = s.execute(stmt)
            if res.rowcount:
                earnings_inserted += 1
            else:
                s.execute(
                    Event.__table__.update()
                    .where(Event.kind == "earnings")
                    .where(Event.symbol == e.symbol)
                    .where(Event.release == "EARNINGS")
                    .where(Event.scheduled_at == _naive_utc(e.scheduled_at))
                    .values(confirmed=e.confirmed, source=e.source, fetched_at=now)
                )

    log.info(
        "calendars refreshed: macro=%d (new=%d) earnings=%d (new=%d) errors=%s",
        len(macro), macro_inserted, len(earnings), earnings_inserted, errors,
    )
    return RefreshSummary(
        macro_inserted=macro_inserted,
        earnings_inserted=earnings_inserted,
        macro_total=len(macro),
        earnings_total=len(earnings),
        errors=errors,
    )


def _naive_utc(dt: datetime) -> datetime:
    """SQLite stores naive datetimes; normalise to UTC and drop tzinfo."""
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(UTC).replace(tzinfo=None)
