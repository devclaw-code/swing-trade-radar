"""Macro release calendar (FRED + FOMC).

Fetches scheduled CPI / PCE / NFP / PPI release datetimes from FRED, plus FOMC
meeting dates from the Federal Reserve. Pure read-only; upserts happen in the
caller via ``Event`` rows.

Design notes:
- We treat *event time*, not surprise. Pillar 3 only needs scheduled dates.
- Fail-open: if a source fails we return an empty list and log; the blackout
  helper will treat missing data as "no blackout" and the run-summary will
  surface a stale-calendar banner upstream.
- FRED returns scheduled dates without intraday timestamps; standard print times
  are 08:30 ET (BLS) / 10:00 ET (FOMC presser). We attach the canonical print
  time in UTC per release_id.
"""

from __future__ import annotations

import logging
import time as _time
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from ..config import settings

log = logging.getLogger(__name__)

# FRED release_id → (release_code, canonical print time ET)
# https://fred.stlouisfed.org/docs/api/fred/releases.html
_RELEASES: dict[int, tuple[str, time]] = {
    10: ("CPI", time(8, 30)),
    21: ("CORE_PCE", time(8, 30)),       # PCE bundled in Personal Income & Outlays
    46: ("PPI", time(8, 30)),
    50: ("NFP", time(8, 30)),            # Employment Situation
    53: ("RETAIL_SALES", time(8, 30)),
    175: ("ISM_MFG", time(10, 0)),       # ISM (community, may not always exist on FRED)
}

_ET = ZoneInfo("America/New_York")

# Hard-coded FOMC fallback (statement at 14:00 ET, presser ~14:30 ET).
# Update annually; this is a safety net only — primary source is the Fed JSON.
_FOMC_FALLBACK: list[date] = [
    date(2026, 1, 28),
    date(2026, 3, 18),
    date(2026, 4, 29),
    date(2026, 6, 17),
    date(2026, 7, 29),
    date(2026, 9, 16),
    date(2026, 11, 4),
    date(2026, 12, 16),
]


@dataclass(frozen=True)
class MacroEvent:
    release: str
    scheduled_at: datetime  # UTC
    source: str
    confirmed: bool = True


def _et_to_utc(d: date, t: time) -> datetime:
    return datetime.combine(d, t, tzinfo=_ET).astimezone(UTC)


def fetch_fred_releases(horizon_days: int = 14, *, client: httpx.Client | None = None) -> list[MacroEvent]:
    """Fetch upcoming BLS/BEA macro release datetimes from FRED.

    Returns [] if no API key is set or any error occurs.
    """
    key = settings.fred_api_key
    if not key:
        log.info("fred: no api key set, skipping macro calendar")
        return []

    today = date.today()
    end = today + timedelta(days=horizon_days)
    out: list[MacroEvent] = []
    own = client is None
    c = client or httpx.Client(timeout=10.0)
    try:
        for release_id, (code, print_time_et) in _RELEASES.items():
            payload: dict[str, Any] | None = None
            for attempt in range(3):
                try:
                    r = c.get(
                        f"{settings.fred_base_url}/release/dates",
                        params={
                            "release_id": release_id,
                            "api_key": key,
                            "file_type": "json",
                            "include_release_dates_with_no_data": "true",
                            "realtime_start": today.isoformat(),
                            "realtime_end": end.isoformat(),
                        },
                    )
                    if r.status_code == 429:
                        _time.sleep(0.7 * (attempt + 1))
                        continue
                    r.raise_for_status()
                    payload = r.json()
                    break
                except httpx.HTTPError as e:
                    log.warning("fred release_id=%s attempt=%d failed: %s", release_id, attempt, e)
                    _time.sleep(0.5 * (attempt + 1))
                    continue
            if not payload:
                continue
            for row in payload.get("release_dates", []):
                try:
                    d = date.fromisoformat(row["date"])
                except (KeyError, ValueError):
                    continue
                if d < today or d > end:
                    continue
                out.append(
                    MacroEvent(
                        release=code,
                        scheduled_at=_et_to_utc(d, print_time_et),
                        source="fred",
                    )
                )
            # gentle pacing — FRED's per-IP rate limiter is twitchy
            _time.sleep(0.25)
    finally:
        if own:
            c.close()
    return out


def fetch_fomc_meetings(horizon_days: int = 90, *, client: httpx.Client | None = None) -> list[MacroEvent]:
    """Fetch upcoming FOMC meeting datetimes (statement = 14:00 ET on day 2).

    Tries the public Fed calendar JSON; falls back to the hard-coded list.
    """
    today = date.today()
    end = today + timedelta(days=horizon_days)
    out: list[MacroEvent] = []
    own = client is None
    c = client or httpx.Client(timeout=10.0)
    try:
        try:
            r = c.get(settings.fomc_ics_url)
            r.raise_for_status()
            payload = r.json()
            # Schema is loose; look for any object with 'date' or 'startdate'.
            for row in _walk_objs(payload):
                d = _coerce_meeting_date(row)
                if d is None or d < today or d > end:
                    continue
                out.append(
                    MacroEvent(
                        release="FOMC",
                        scheduled_at=_et_to_utc(d, time(14, 0)),
                        source="fed_json",
                    )
                )
        except (httpx.HTTPError, ValueError) as e:
            log.warning("fomc primary fetch failed (%s); using fallback constants", e)
    finally:
        if own:
            c.close()

    if not out:
        for d in _FOMC_FALLBACK:
            if today <= d <= end:
                out.append(
                    MacroEvent(
                        release="FOMC",
                        scheduled_at=_et_to_utc(d, time(14, 0)),
                        source="fallback_const",
                        confirmed=False,
                    )
                )
    return out


def fetch_next_window(horizon_days: int | None = None) -> list[MacroEvent]:
    """All macro events in the next N days (default from settings)."""
    n = horizon_days or settings.calendar_horizon_days
    return fetch_fred_releases(n) + fetch_fomc_meetings(max(n, 90))


# --- helpers ----------------------------------------------------------------

def _walk_objs(obj: Any):
    """Yield every dict found in a nested JSON structure."""
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk_objs(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk_objs(item)


def _coerce_meeting_date(row: dict[str, Any]) -> date | None:
    """Best-effort parse of a meeting date from various Fed JSON shapes."""
    for key in ("end_date", "endDate", "date", "startdate", "start_date", "meeting_date"):
        v = row.get(key)
        if not v:
            continue
        try:
            if isinstance(v, str):
                return date.fromisoformat(v[:10])
        except ValueError:
            continue
    # Some shapes use month/day fields
    y = row.get("year")
    m = row.get("month")
    d = row.get("day")
    if y and m and d:
        try:
            return date(int(y), int(m), int(d))
        except (TypeError, ValueError):
            return None
    return None
