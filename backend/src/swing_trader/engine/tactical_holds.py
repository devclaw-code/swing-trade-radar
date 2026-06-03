"""Data-backed expected-hold estimation for tactical setups.

`max_hold_days` is only a *cap* (the timeout). The actual hold is condition-based
and varies per setup. This module replays each setup's **exact** entry/exit rules
across multi-year history for the whole universe, collects the realised hold-bar
distribution, and exposes the **median** hold as `expected_hold_days`.

Design notes
------------
* Pure replay of the documented exit logic in ``t1_rsi_exhaustion`` /
  ``t2_inside_day_breakout`` — no new trade assumptions are invented here.
* Results are cached (per-setup median + sample size) with a TTL so the live
  ``/api/tactical`` scan never pays the backtest cost on the hot path.
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
from .indicators import enrich

log = logging.getLogger(__name__)

# Exit-rule constants mirrored from the setup modules (kept in sync intentionally).
RSI_LEN = 4
RSI_EXIT = 55.0
DOWN_DAYS = 3
EMA_LEN = 10
ENTRY_BUFFER = 0.10
STOP_BUFFER = 0.05
MIN_RR_BREAKOUT = 2.0
MAX_HOLD = 5  # timeout cap shared by both setups
FILL_WINDOW = 3  # T2 buy-stop must fill within N bars or the signal is voided
MIN_BARS = 205

# Cache: setup_id -> {"median": float, "n": int}. TTL keeps it cheap but fresh.
_CACHE: dict[str, dict] = {}
_CACHE_TS: float = 0.0
_CACHE_TTL_S = 6 * 60 * 60  # 6h
_LOCK = threading.Lock()


def _simulate_t1(df: pd.DataFrame) -> list[int]:
    """Replay T1 (3-Day RSI Exhaustion) and return hold-bar counts."""
    holds: list[int] = []
    closes = df["close"].astype(float).reset_index(drop=True)
    sma200 = df.get("sma200")
    if sma200 is None:
        return holds
    sma200 = sma200.astype(float).reset_index(drop=True)
    rsi = ta.rsi(closes, length=RSI_LEN)
    if rsi is None or rsi.empty:
        return holds
    rsi = rsi.reset_index(drop=True)
    n = len(closes)

    i = DOWN_DAYS
    while i < n:
        c = closes.iloc[i]
        r = rsi.iloc[i]
        s = sma200.iloc[i]
        if (
            c == c and r == r and s == s  # not NaN
            and c > s
            and r < 30.0
            and all(closes.iloc[i - k] < closes.iloc[i - k - 1] for k in range(DOWN_DAYS))
        ):
            entry = c
            exit_j = None
            for j in range(i + 1, min(i + 1 + MAX_HOLD, n)):
                cj = closes.iloc[j]
                rj = rsi.iloc[j]
                if cj != cj:
                    continue
                # Exit on first profitable close OR RSI(4) > 55.
                if cj > entry or (rj == rj and rj > RSI_EXIT):
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
    """Replay T2 (Inside Day Breakout) and return hold-bar counts (from fill)."""
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
            entry = ch + ENTRY_BUFFER
            stop = cl - STOP_BUFFER
            risk = entry - stop
            if risk <= 0:
                i += 1
                continue
            target = entry + MIN_RR_BREAKOUT * risk
            # Look for a fill within FILL_WINDOW bars.
            fill_j = None
            for j in range(i + 1, min(i + 1 + FILL_WINDOW, n)):
                if highs.iloc[j] >= entry:
                    fill_j = j
                    break
            if fill_j is None:
                i += 1  # never filled -> not a trade
                continue
            # Simulate from fill bar to target/stop/timeout.
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
        if holds:
            out[sid] = {"median": float(statistics.median(holds)), "n": len(holds)}
        else:
            out[sid] = {"median": None, "n": 0}
    return out


def get_expected_holds(*, force: bool = False) -> dict[str, dict]:
    """Cached per-setup expected-hold map. Thread-safe, TTL-bounded."""
    global _CACHE, _CACHE_TS
    now = time.time()
    with _LOCK:
        fresh = _CACHE and (now - _CACHE_TS) < _CACHE_TTL_S
        if fresh and not force:
            return _CACHE
    # Compute outside the lock (slow); last writer wins — fine for a cache.
    computed = _compute_all()
    with _LOCK:
        _CACHE = computed
        _CACHE_TS = time.time()
    return computed


def expected_hold_for(setup_id: str) -> float | None:
    """Median expected hold (in trading days) for a setup, or None if unknown."""
    try:
        return get_expected_holds().get(setup_id, {}).get("median")
    except Exception:
        return None
