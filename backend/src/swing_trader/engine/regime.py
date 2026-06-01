"""Macro regime detector.

References:
    research/00-INDEX.md §A row 2 (regime filter is non-negotiable)
    research/02-risk-management.md §8 (regime gates)
    PHASE2_PLAN.md §1 example payload `regime_context`.

Computes:
    - SPY > 200 SMA
    - QQQ > 200 SMA
    - ^VIX latest level
    - VIX term structure: ^VIX vs ^VIX3M  (contango = healthy, backwardation = risk-off)

Caches once per UTC day inside `var/regime_cache.json`.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

from ..config import DATA_DIR
from ..schemas import RegimeContext

log = logging.getLogger(__name__)

CACHE_PATH = DATA_DIR / "regime_cache.json"


def _fetch_close_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=False)
    if df is None or df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def _above_sma(df: pd.DataFrame, length: int = 200) -> bool:
    if df.empty or "Close" not in df.columns or len(df) < length:
        return False
    sma = df["Close"].rolling(length).mean().iloc[-1]
    return bool(df["Close"].iloc[-1] > sma)


def _last_close(df: pd.DataFrame) -> float | None:
    if df.empty or "Close" not in df.columns:
        return None
    val = float(df["Close"].iloc[-1])
    return val


def _term_structure(vix: float | None, vix3m: float | None) -> str:
    if vix is None or vix3m is None:
        return "unknown"
    if vix3m > vix:
        return "contango (healthy)"
    return "backwardation (risk-off)"


def compute_regime(*, force_refresh: bool = False) -> RegimeContext:
    """Compute (and cache for one UTC day) the current regime context."""
    today = datetime.now(UTC).date()
    if not force_refresh and CACHE_PATH.exists():
        try:
            cached = json.loads(CACHE_PATH.read_text())
            if cached.get("as_of") == today.isoformat():
                return RegimeContext(**cached["regime"])
        except (OSError, ValueError, json.JSONDecodeError) as e:
            log.warning("regime cache unreadable: %s", e)

    spy = _fetch_close_history("SPY")
    qqq = _fetch_close_history("QQQ")
    vix_df = _fetch_close_history("^VIX")
    vix3m_df = _fetch_close_history("^VIX3M")

    spy_above = _above_sma(spy)
    qqq_above = _above_sma(qqq)
    vix = _last_close(vix_df)
    vix3m = _last_close(vix3m_df)
    term = _term_structure(vix, vix3m)

    if spy_above and qqq_above and (vix is None or vix < 25):
        verdict = "favorable for long swings"
    elif (not spy_above) and (vix is not None and vix > 25):
        verdict = "unfavorable / risk-off"
    else:
        verdict = "neutral"

    ctx = RegimeContext(
        spy_above_200sma=spy_above,
        qqq_above_200sma=qqq_above,
        vix=round(vix, 2) if vix is not None else None,
        vix_term_structure=term,  # type: ignore[arg-type]
        regime_verdict=verdict,  # type: ignore[arg-type]
        as_of=today,
    )

    try:
        CACHE_PATH.write_text(json.dumps({"as_of": today.isoformat(), "regime": ctx.model_dump(mode="json")}))
    except OSError as e:
        log.warning("regime cache write failed: %s", e)
    return ctx


def offline_default(as_of: date | None = None) -> RegimeContext:
    """Pure-Python neutral regime — used in tests / offline runs."""
    return RegimeContext(
        spy_above_200sma=True,
        qqq_above_200sma=True,
        vix=15.0,
        vix_term_structure="contango (healthy)",
        regime_verdict="favorable for long swings",
        as_of=as_of or datetime.now(UTC).date(),
    )
