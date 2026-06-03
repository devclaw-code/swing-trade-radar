"""Data-backed expected-hold estimation for tactical setups.

`max_hold_days` is only a *cap* (the timeout). The actual hold is condition-based
and varies per setup. This module replays each setup's **exact** entry/exit rules
across multi-year history for the whole universe, collects the realised hold-bar
distribution, and exposes the **median** hold as `expected_hold_days`.

Design notes
------------
* The replay uses the *same* risk helpers the live setups use
  (``atr_series`` for the per-bar 1.5xATR stop, ``floor_stop_with_atr`` +
  ``min_rr_target`` for the T2 structural geometry) so the simulated trades
  match what ``t1_rsi_exhaustion`` / ``t2_inside_day_breakout`` would actually
  produce. No new exit assumptions are invented here.
* Results are cached (per-setup median + sample size) with a TTL. The cache is
  warmed off the request path (see ``warm_expected_holds``) so the hot
  ``/api/tactical`` scan never pays the replay cost; a single-flight lock stops
  concurrent cold-start stampedes.
* Everything degrades to ``None`` on missing data; callers fall back to the cap.
"""

from __future__ import annotations

import logging
import statistics
import threading
import time

import pandas as pd
import pandas_ta_classic as ta

from ..config import settings
from ..data.price_fetcher import load_ohlcv
from .atr import atr_series
from .indicators import enrich
from .risk_levels import floor_stop_with_atr, min_rr_target

log = logging.getLogger(__name__)

# Exit-rule constants mirrored from the setup modules (kept in sync intentionally).
RSI_LEN = 4
RSI_OVERSOLD = 30.0
RSI_EXIT = 55.0
DOWN_DAYS = 3
EMA_LEN = 10
ENTRY_BUFFER = 0.10
STOP_BUFFER = 0.05
MIN_RR_BREAKOUT = 2.0
ATR_STOP_MULT = 1.5  # both setups use a 1.5xATR stop / floor
MAX_HOLD = 5  # timeout cap shared by both setups
MIN_BARS = 205

# Cache: setup_id -> {"median": float | None, "n": int}. TTL keeps it fresh.
_CACHE: dict[str, dict] = {}
_CACHE_TS: float = 0.0
_CACHE_TTL_S = 6 * 60 * 60  # 6h
_LOCK = threading.Lock()
_COMPUTE_LOCK = threading.Lock()  # single-flight: only one replay at a time


def _simulate_t1(df: pd.DataFrame) -> list[int]:
    """Replay T1 (3-Day RSI Exhaustion) -> hold-bar counts.

    Entry: close on the bar where 3 lower closes + RSI(4)<30 in an uptrend.
    Exit (whichever first): first profitable close, RSI(4)>55, hard stop
    (entry - 1.5xATR), or the ``MAX_HOLD`` timeout.
    """
    holds: list[int] = []
    closes = df["close"].astype(float).reset_index(drop=True)
    lows = df["low"].astype(float).reset_index(drop=True)
    sma200 = df.get("sma200")
    if sma200 is None:
        return holds
    sma200 = sma200.astype(float).reset_index(drop=True)
    rsi = ta.rsi(closes, length=RSI_LEN)
    if rsi is None or rsi.empty:
        return holds
    rsi = rsi.reset_index(drop=True)
    atr = atr_series(df).reset_index(drop=True)
    n = len(closes)

    i = DOWN_DAYS
    while i < n:
        c = closes.iloc[i]
        r = rsi.iloc[i]
        s = sma200.iloc[i]
        a = atr.iloc[i] if i < len(atr) else float("nan")
        if (
            c == c and r == r and s == s and a == a  # not NaN
            and c > s
            and r < RSI_OVERSOLD
            and all(closes.iloc[i - k] < closes.iloc[i - k - 1] for k in range(DOWN_DAYS))
        ):
            entry = c
            stop = entry - ATR_STOP_MULT * a
            exit_j = None
            for j in range(i + 1, min(i + 1 + MAX_HOLD, n)):
                cj = closes.iloc[j]
                rj = rsi.iloc[j]
                lj = lows.iloc[j]
                if cj != cj:
                    continue
                # Hard stop (intrabar low), first profitable close, or RSI>55.
                if (lj == lj and lj <= stop) or cj > entry or (rj == rj and rj > RSI_EXIT):
                    exit_j = j
                    break
            if exit_j is None:
                exit_j = min(i + MAX_HOLD, n - 1)  # timeout
            holds.append(exit_j - i)
            i = exit_j + 1  # no overlapping trades
            continue
        i += 1
    return holds


def _simulate_t2(df: pd.DataFrame) -> list[int]:
    """Replay T2 (Inside Day Breakout) -> hold-bar counts (from fill).

    Geometry mirrors the live setup exactly: buy-stop at inside_high+0.10,
    structural stop inside_low-0.05 floored at 1.5xATR, target priced to min
    2.0 R:R off that (possibly widened) stop. A trade only counts once the
    buy-stop is tagged; it then runs to target / stop / ``MAX_HOLD`` timeout.
    """
    holds: list[int] = []
    o = df.reset_index(drop=True)
    closes = o["close"].astype(float)
    highs = o["high"].astype(float)
    lows = o["low"].astype(float)
    sma200 = o.get("sma200")
    if sma200 is None:
        return holds
    sma200 = sma200.astype(float)
    ema10 = closes.ewm(span=EMA_LEN, adjust=False).mean()
    atr = atr_series(df).reset_index(drop=True)
    n = len(o)

    i = 1
    while i < n:
        ch, cl, c = highs.iloc[i], lows.iloc[i], closes.iloc[i]
        ph, pl = highs.iloc[i - 1], lows.iloc[i - 1]
        s = sma200.iloc[i]
        if any(v != v for v in (ch, cl, ph, pl, c, s)):
            i += 1
            continue
        inside = (ch < ph) and (cl > pl)
        ema_up = ema10.iloc[i] > ema10.iloc[i - 1]
        if inside and ema_up and c > s:
            entry = round(ch + ENTRY_BUFFER, 2)
            raw_stop = round(cl - STOP_BUFFER, 2)
            a = atr.iloc[i] if i < len(atr) else None
            a = float(a) if a is not None and a == a else None
            stop = floor_stop_with_atr(entry, raw_stop, a, mult=ATR_STOP_MULT)
            if entry - stop <= 0:
                i += 1
                continue
            target = min_rr_target(entry, stop, rr=MIN_RR_BREAKOUT)
            # Fill any time the buy-stop is tagged (no extra fill-window cap).
            fill_j = None
            for j in range(i + 1, min(i + 1 + MAX_HOLD, n)):
                if highs.iloc[j] >= entry:
                    fill_j = j
                    break
            if fill_j is None:
                i += 1  # never filled -> not a trade
                continue
            exit_j = None
            for j in range(fill_j, min(fill_j + MAX_HOLD, n)):
                if lows.iloc[j] <= stop or highs.iloc[j] >= target:
                    exit_j = j
                    break
            if exit_j is None:
                exit_j = min(fill_j + MAX_HOLD - 1, n - 1)
            holds.append(exit_j - fill_j + 1)
            i = exit_j + 1
            continue
        i += 1
    return holds


_SIMULATORS = {
    "T1_rsi_exhaustion": _simulate_t1,
    "T2_inside_day_breakout": _simulate_t2,
}


def _compute_all() -> dict[str, dict]:
    """Run every setup's replay across the universe; return per-setup medians."""
    buckets: dict[str, list[int]] = {sid: [] for sid in _SIMULATORS}
    for ticker in settings.tickers:
        try:
            df = load_ohlcv(ticker)
            if df is None or df.empty or len(df) < MIN_BARS:
                continue
            df = enrich(df)
            for sid, sim in _SIMULATORS.items():
                try:
                    buckets[sid].extend(sim(df))
                except Exception as e:
                    log.debug("hold-sim %s failed on %s: %s", sid, ticker, e)
        except Exception as e:
            log.debug("hold-sim load %s failed: %s", ticker, e)

    out: dict[str, dict] = {}
    for sid, holds in buckets.items():
        out[sid] = (
            {"median": float(statistics.median(holds)), "n": len(holds)}
            if holds
            else {"median": None, "n": 0}
        )
    return out


def get_expected_holds(*, force: bool = False) -> dict[str, dict]:
    """Cached per-setup expected-hold map. Single-flight on cold compute.

    Reads are lock-cheap. On a miss/expiry exactly one thread runs the replay
    (``_COMPUTE_LOCK``); others wait and then read the freshly populated cache.
    """
    global _CACHE, _CACHE_TS
    now = time.time()
    with _LOCK:
        if _CACHE and (now - _CACHE_TS) < _CACHE_TTL_S and not force:
            return _CACHE

    with _COMPUTE_LOCK:
        # Re-check: another thread may have populated while we waited.
        with _LOCK:
            if _CACHE and (time.time() - _CACHE_TS) < _CACHE_TTL_S and not force:
                return _CACHE
        computed = _compute_all()
        with _LOCK:
            _CACHE = computed
            _CACHE_TS = time.time()
            return _CACHE


def warm_expected_holds() -> None:
    """Populate the cache off the request path (call at startup / on a schedule)."""
    try:
        get_expected_holds(force=True)
    except Exception as e:
        log.warning("expected-hold warm failed: %s", e)


def expected_hold_for(setup_id: str) -> float | None:
    """Median expected hold (trading days) for a setup, or None if not yet warmed.

    Non-blocking on the request path: if the cache is cold this returns ``None``
    (card falls back to the cap) and triggers a background warm so the next scan
    has real numbers. It never kicks off an inline full-universe replay.
    """
    with _LOCK:
        have = bool(_CACHE)
        fresh = have and (time.time() - _CACHE_TS) < _CACHE_TTL_S
        val = _CACHE.get(setup_id, {}).get("median") if have else None
    if not fresh:
        # Warm in the background; don't block the API response.
        threading.Thread(target=warm_expected_holds, name="warm-holds", daemon=True).start()
    return val
