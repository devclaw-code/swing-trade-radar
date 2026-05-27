"""OHLCV price fetcher with yfinance + Alpha Vantage fallback + SQLite cache."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

import pandas as pd
import yfinance as yf
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from ..config import settings
from .db import Price, session_scope

log = logging.getLogger(__name__)


def _latest_cached_date(ticker: str) -> date | None:
    with session_scope() as s:
        row = s.execute(
            select(Price.date).where(Price.ticker == ticker).order_by(Price.date.desc()).limit(1)
        ).first()
        return row[0] if row else None


def _upsert_prices(ticker: str, df: pd.DataFrame) -> int:
    """Upsert OHLCV rows. Returns count written."""
    if df.empty:
        return 0
    rows = []
    for ts, r in df.iterrows():
        d = ts.date() if hasattr(ts, "date") else ts
        rows.append(
            dict(
                ticker=ticker,
                date=d,
                open=float(r["Open"]),
                high=float(r["High"]),
                low=float(r["Low"]),
                close=float(r["Close"]),
                volume=float(r["Volume"]),
            )
        )
    with session_scope() as s:
        stmt = sqlite_insert(Price).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["ticker", "date"],
            set_={c: stmt.excluded[c] for c in ("open", "high", "low", "close", "volume")},
        )
        s.execute(stmt)
    return len(rows)


def fetch_ticker(ticker: str, *, full_refresh: bool = False) -> int:
    """Fetch & cache OHLCV for `ticker`. Returns rows written."""
    latest = None if full_refresh else _latest_cached_date(ticker)
    if latest is None:
        period = f"{settings.price_history_days}d"
        start = None
    else:
        # Incremental: refetch last 5 days to patch revisions, then forward.
        start = latest - timedelta(days=5)
        period = None

    try:
        if start is not None:
            df = yf.download(
                ticker,
                start=start,
                interval="1d",
                progress=False,
                auto_adjust=False,
                timeout=settings.yfinance_request_timeout,
            )
        else:
            df = yf.download(
                ticker,
                period=period,
                interval="1d",
                progress=False,
                auto_adjust=False,
                timeout=settings.yfinance_request_timeout,
            )
    except Exception as e:
        log.warning("yfinance failed for %s: %s", ticker, e)
        return 0

    if df is None or df.empty:
        log.warning("yfinance returned empty for %s", ticker)
        return 0

    # Handle yfinance MultiIndex columns when single ticker.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    needed = {"Open", "High", "Low", "Close", "Volume"}
    if not needed.issubset(df.columns):
        log.warning("yfinance missing columns for %s: %s", ticker, df.columns.tolist())
        return 0

    n = _upsert_prices(ticker, df[list(needed)])
    log.info("upserted %d rows for %s", n, ticker)
    return n


def fetch_all() -> dict[str, int]:
    """Fetch all configured tickers. Returns {ticker: rows_written}."""
    out: dict[str, int] = {}
    for t in settings.tickers:
        try:
            out[t] = fetch_ticker(t)
        except Exception as e:
            log.exception("fetch failed for %s: %s", t, e)
            out[t] = 0
    return out


def load_ohlcv(ticker: str, *, lookback_days: int | None = None) -> pd.DataFrame:
    """Load OHLCV from cache as a tz-naive DataFrame indexed by date."""
    with session_scope() as s:
        q = select(Price).where(Price.ticker == ticker).order_by(Price.date.asc())
        rows = s.execute(q).scalars().all()
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(
        [
            dict(
                date=r.date,
                open=r.open,
                high=r.high,
                low=r.low,
                close=r.close,
                volume=r.volume,
            )
            for r in rows
        ]
    )
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    if lookback_days:
        cutoff = datetime.utcnow() - timedelta(days=lookback_days)
        df = df[df.index >= cutoff]
    return df
