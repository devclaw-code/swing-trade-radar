"""Blackout windows derived from the ``events`` calendar table.

Pure read-only. No external IO. Strategy/synthesizer code asks "is this
ticker/side blackable right now?" and gets either ``None`` (clear) or a short
human-readable reason.

Rules (encode pillar 3 of the AI-Infra Strategist prompt):

1. **Macro long-side blackout**
   No new LONG entries in the ``settings.macro_blackout_hours`` window
   (default 48h) before any of: CPI, CORE_PCE, NFP, PPI, FOMC.
   Shorts unaffected (we don't trade shorts but the API is symmetric for
   future use).

2. **Earnings two-sided blackout**
   No new entries (long or short) in the ``settings.macro_blackout_hours``
   window before a confirmed earnings print for the ticker.

3. **Earnings exit reminder**
   ``next_earnings_for(ticker)`` returns the next earnings datetime so callers
   can clamp ``max_hold_days`` and surface a pre-earnings exit.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from sqlalchemy import select

from ..config import settings
from ..data.db import Event, session_scope

Side = Literal["LONG", "SHORT"]

_MACRO_LONG_RELEASES = {"CPI", "CORE_PCE", "NFP", "PPI", "FOMC", "RETAIL_SALES"}


@dataclass(frozen=True)
class BlackoutReason:
    release: str
    scheduled_at: datetime
    hours_until: float
    confirmed: bool

    def as_text(self) -> str:
        when = self.scheduled_at.astimezone(UTC).strftime("%Y-%m-%d %H:%MZ")
        suffix = "" if self.confirmed else " (unconfirmed)"
        return f"{self.release} {when} (T-{self.hours_until:.0f}h){suffix}"


def is_blackout(
    ticker: str,
    side: Side = "LONG",
    *,
    now: datetime | None = None,
) -> BlackoutReason | None:
    """Return a reason if entry should be suppressed, else ``None``.

    Fail-open: if the events table is empty or the query errors, return
    ``None``. Upstream is responsible for surfacing a "calendar stale" warning.
    """
    if not settings.calendars_enabled:
        return None
    now = (now or datetime.now(UTC)).astimezone(UTC)
    horizon = now + timedelta(hours=settings.macro_blackout_hours)
    sym = ticker.upper()

    try:
        with session_scope() as s:
            # Earnings: any side
            ev = s.scalar(
                select(Event)
                .where(Event.kind == "earnings")
                .where(Event.symbol == sym)
                .where(Event.scheduled_at > now)
                .where(Event.scheduled_at <= horizon)
                .order_by(Event.scheduled_at.asc())
            )
            if ev:
                return _to_reason(ev, now)

            # Macro: only suppress LONG entries
            if side == "LONG":
                ev = s.scalar(
                    select(Event)
                    .where(Event.kind == "macro")
                    .where(Event.release.in_(_MACRO_LONG_RELEASES))
                    .where(Event.scheduled_at > now)
                    .where(Event.scheduled_at <= horizon)
                    .order_by(Event.scheduled_at.asc())
                )
                if ev:
                    return _to_reason(ev, now)
    except Exception:
        # Fail open. The synthesizer can decide to surface a warning.
        return None

    return None


def next_earnings_for(ticker: str, *, now: datetime | None = None) -> datetime | None:
    """Return the next confirmed earnings datetime (UTC) for ``ticker``, or None."""
    now = (now or datetime.now(UTC)).astimezone(UTC)
    sym = ticker.upper()
    try:
        with session_scope() as s:
            ev = s.scalar(
                select(Event)
                .where(Event.kind == "earnings")
                .where(Event.symbol == sym)
                .where(Event.scheduled_at > now)
                .order_by(Event.scheduled_at.asc())
            )
            return ev.scheduled_at.replace(tzinfo=UTC) if ev else None
    except Exception:
        return None


def calendar_is_stale(*, now: datetime | None = None, max_age_hours: int = 36) -> bool:
    """True if the most recent fetch is older than ``max_age_hours``."""
    now = (now or datetime.now(UTC)).astimezone(UTC)
    try:
        with session_scope() as s:
            row = s.scalar(select(Event).order_by(Event.fetched_at.desc()))
            if row is None:
                return True
            fetched = row.fetched_at
            if fetched.tzinfo is None:
                fetched = fetched.replace(tzinfo=UTC)
            return (now - fetched) > timedelta(hours=max_age_hours)
    except Exception:
        return True


def _to_reason(ev: Event, now: datetime) -> BlackoutReason:
    sched = ev.scheduled_at
    if sched.tzinfo is None:
        sched = sched.replace(tzinfo=UTC)
    hours_until = (sched - now).total_seconds() / 3600.0
    return BlackoutReason(
        release=ev.release,
        scheduled_at=sched,
        hours_until=hours_until,
        confirmed=ev.confirmed,
    )
