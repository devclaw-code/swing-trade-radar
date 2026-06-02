"""Earnings calendar.

Primary: Finnhub `/calendar/earnings` (60 req/min free). Returns whole-market
calendar for a date range; we filter to our universe locally.

Fallbacks (in order):
1. AlphaVantage ``EARNINGS_CALENDAR`` CSV (25 req/day; one call covers all tickers).
2. yfinance ``Ticker.get_earnings_dates`` per ticker (rate-limit risk; last resort).

Returns scheduled_at as a UTC datetime. Finnhub gives a ``hour`` enum
(``bmo``/``amc``/``dmh``); we map to canonical UTC times consistent with US
market conventions:

- bmo (before market open) → 08:30 ET
- amc (after market close) → 16:30 ET
- dmh (during market hours) → 12:00 ET
- unknown                    → 16:30 ET (assume after-close, the riskier case)
"""

from __future__ import annotations

import csv
import io
import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import httpx

from ..config import settings

log = logging.getLogger(__name__)

_ET = ZoneInfo("America/New_York")
_FINNHUB_HOUR_TO_ET: dict[str, time] = {
    "bmo": time(8, 30),
    "amc": time(16, 30),
    "dmh": time(12, 0),
    "": time(16, 30),
}


@dataclass(frozen=True)
class EarningsEvent:
    symbol: str
    scheduled_at: datetime  # UTC
    source: str
    confirmed: bool = True


def _et_to_utc(d: date, t: time) -> datetime:
    return datetime.combine(d, t, tzinfo=_ET).astimezone(UTC)


# ---------------- Finnhub primary -----------------------------------------

def fetch_finnhub(
    tickers: list[str],
    horizon_days: int = 14,
    *,
    client: httpx.Client | None = None,
) -> list[EarningsEvent]:
    if not settings.finnhub_api_key:
        return []
    today = date.today()
    end = today + timedelta(days=horizon_days)
    own = client is None
    c = client or httpx.Client(timeout=10.0)
    out: list[EarningsEvent] = []
    universe = {t.upper() for t in tickers}
    try:
        r = c.get(
            f"{settings.finnhub_base_url}/calendar/earnings",
            params={
                "from": today.isoformat(),
                "to": end.isoformat(),
                "token": settings.finnhub_api_key,
            },
        )
        r.raise_for_status()
        rows = r.json().get("earningsCalendar") or []
        for row in rows:
            sym = (row.get("symbol") or "").upper()
            if sym not in universe:
                continue
            try:
                d = date.fromisoformat(row["date"])
            except (KeyError, ValueError):
                continue
            hour = (row.get("hour") or "").lower()
            t_et = _FINNHUB_HOUR_TO_ET.get(hour, _FINNHUB_HOUR_TO_ET[""])
            out.append(
                EarningsEvent(
                    symbol=sym,
                    scheduled_at=_et_to_utc(d, t_et),
                    source="finnhub",
                )
            )
    except httpx.HTTPError as e:
        log.warning("finnhub earnings fetch failed: %s", e)
    finally:
        if own:
            c.close()
    return out


# ---------------- AlphaVantage middle fallback -----------------------------

def fetch_alpha_vantage(
    tickers: list[str],
    horizon_days: int = 14,
    *,
    client: httpx.Client | None = None,
) -> list[EarningsEvent]:
    if not settings.alpha_vantage_api_key:
        return []
    own = client is None
    c = client or httpx.Client(timeout=15.0)
    out: list[EarningsEvent] = []
    universe = {t.upper() for t in tickers}
    # AV only supports 3mo/6mo/12mo windows; our horizon always fits in 3 months.
    horizon = "3month"
    try:
        r = c.get(
            "https://www.alphavantage.co/query",
            params={
                "function": "EARNINGS_CALENDAR",
                "horizon": horizon,
                "apikey": settings.alpha_vantage_api_key,
            },
        )
        r.raise_for_status()
        body = r.text
        # AV occasionally returns a JSON error in CSV mode
        if body.lstrip().startswith("{"):
            log.warning("alpha_vantage returned non-CSV body: %s", body[:200])
            return []
        today = date.today()
        end = today + timedelta(days=horizon_days)
        for row in csv.DictReader(io.StringIO(body)):
            sym = (row.get("symbol") or "").upper()
            if sym not in universe:
                continue
            try:
                d = date.fromisoformat(row["reportDate"])
            except (KeyError, ValueError):
                continue
            if d < today or d > end:
                continue
            out.append(
                EarningsEvent(
                    symbol=sym,
                    scheduled_at=_et_to_utc(d, time(16, 30)),
                    source="alpha_vantage",
                    confirmed=False,
                )
            )
    except httpx.HTTPError as e:
        log.warning("alpha_vantage earnings fetch failed: %s", e)
    finally:
        if own:
            c.close()
    return out


# ---------------- yfinance per-ticker last resort --------------------------

def fetch_yfinance(tickers: list[str], horizon_days: int = 14) -> list[EarningsEvent]:
    """Last-resort per-ticker pull. Avoid in hot paths — slow + rate-limited."""
    try:
        import yfinance as yf
    except ImportError:
        return []

    out: list[EarningsEvent] = []
    today = date.today()
    end = today + timedelta(days=horizon_days)
    for sym in tickers:
        try:
            df = yf.Ticker(sym).get_earnings_dates(limit=4)
        except Exception as e:  # yfinance raises a wide assortment
            log.debug("yfinance earnings %s: %s", sym, e)
            continue
        if df is None or df.empty:
            continue
        for ts in df.index:
            try:
                py_dt = ts.to_pydatetime()
            except AttributeError:
                continue
            if py_dt.tzinfo is None:
                py_dt = py_dt.replace(tzinfo=_ET)
            d = py_dt.astimezone(_ET).date()
            if d < today or d > end:
                continue
            out.append(
                EarningsEvent(
                    symbol=sym.upper(),
                    scheduled_at=py_dt.astimezone(UTC),
                    source="yfinance",
                    confirmed=False,
                )
            )
    return out


# ---------------- Orchestrator --------------------------------------------

def fetch_earnings_window(
    tickers: list[str],
    horizon_days: int | None = None,
) -> list[EarningsEvent]:
    """Try Finnhub → AV → yfinance until we get >=1 row."""
    n = horizon_days or settings.calendar_horizon_days
    if not tickers:
        return []

    rows = fetch_finnhub(tickers, n)
    if rows:
        return rows
    log.info("earnings: finnhub returned 0 rows, falling back to alpha_vantage")

    rows = fetch_alpha_vantage(tickers, n)
    if rows:
        return rows
    log.info("earnings: alpha_vantage returned 0 rows, falling back to yfinance")

    return fetch_yfinance(tickers, n)
