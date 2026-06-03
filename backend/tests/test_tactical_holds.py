"""Deterministic unit tests for tactical expected-hold replay.

We hand-build tiny OHLCV frames with a known fill/exit so the realised hold is
exact and the simulators can be regression-checked against the documented
setup exit rules.
"""

from __future__ import annotations

import pandas as pd

from swing_trader.engine.tactical_holds import (
    MAX_HOLD,
    _simulate_t1,
    _simulate_t2,
)


def _frame(rows: list[dict], *, sma200: float) -> pd.DataFrame:
    """Build an OHLCV frame with a flat sma200 column (regime gate input)."""
    n = len(rows)
    idx = pd.date_range(end=pd.Timestamp("2026-05-30"), periods=n, freq="B")
    df = pd.DataFrame(rows, index=idx)
    df["sma200"] = sma200
    if "volume" not in df:
        df["volume"] = 1_000_000.0
    return df


# ---------------------------------------------------------------------------
# T1 — 3-Day RSI Exhaustion
# ---------------------------------------------------------------------------


def _t1_setup_rows() -> list[dict]:
    """Long warm-up so ATR(14)/RSI(4) are valid, then 3 lower closes into the
    trigger bar. Prices well above sma200=50 so the regime gate passes."""
    rows: list[dict] = []
    # 30 flat-ish warm-up bars around 100.
    for _ in range(30):
        rows.append({"open": 100, "high": 101, "low": 99, "close": 100})
    # Three consecutive lower closes (drives RSI(4) below 30).
    for c in (97, 94, 91):
        rows.append({"open": c + 1, "high": c + 1.5, "low": c - 1, "close": c})
    return rows


def test_t1_exit_on_first_profitable_close():
    rows = _t1_setup_rows()
    entry = rows[-1]["close"]  # 91
    # Next bar closes above entry -> exit at hold = 1.
    rows.append({"open": 91, "high": 95, "low": 90.9, "close": 93})
    df = _frame(rows, sma200=50.0)
    holds = _simulate_t1(df)
    assert holds, "T1 should have fired on the 3-down + RSI<30 setup"
    assert holds[-1] == 1, f"first profitable close -> hold 1, got {holds[-1]}"
    assert entry < 93


def test_t1_exit_on_hard_stop():
    rows = _t1_setup_rows()
    # Next bar gaps down hard: low far below entry-1.5*ATR -> stop hit, hold = 1.
    rows.append({"open": 90, "high": 90.5, "low": 70.0, "close": 72})
    df = _frame(rows, sma200=50.0)
    holds = _simulate_t1(df)
    assert holds and holds[-1] == 1, f"hard stop -> hold 1, got {holds}"


def test_t1_timeout_when_no_exit_condition():
    rows = _t1_setup_rows()
    entry = rows[-1]["close"]  # 91
    # Several bars that never close above entry, never RSI>55, never hit stop.
    for _ in range(MAX_HOLD + 2):
        rows.append({"open": 90.5, "high": 90.8, "low": 89.5, "close": 90.0})
    df = _frame(rows, sma200=50.0)
    holds = _simulate_t1(df)
    assert holds, "should fire"
    assert holds[-1] == MAX_HOLD, f"timeout -> hold {MAX_HOLD}, got {holds[-1]}"
    assert entry > 90.0  # never profitable


def test_t1_no_fire_below_regime():
    rows = _t1_setup_rows()
    rows.append({"open": 91, "high": 95, "low": 90.9, "close": 93})
    df = _frame(rows, sma200=500.0)  # price < sma200 -> regime fails
    assert _simulate_t1(df) == []


# ---------------------------------------------------------------------------
# T2 — Inside Day Breakout
# ---------------------------------------------------------------------------


def _t2_setup_rows() -> list[dict]:
    """Warm-up with a gentle uptrend (rising EMA10), then a clear inside day.
    Prices above sma200=50."""
    rows: list[dict] = []
    base = 100.0
    for k in range(30):
        c = base + k * 0.2  # steady rise -> EMA10 sloping up
        rows.append({"open": c - 0.1, "high": c + 0.8, "low": c - 0.8, "close": c})
    # Inside day: high < prev high AND low > prev low.
    prev = rows[-1]
    inside_high = prev["high"] - 0.3
    inside_low = prev["low"] + 0.3
    rows.append(
        {
            "open": (inside_high + inside_low) / 2,
            "high": inside_high,
            "low": inside_low,
            "close": (inside_high + inside_low) / 2,
        }
    )
    return rows


def test_t2_fill_then_target():
    rows = _t2_setup_rows()
    inside_high = rows[-1]["high"]
    entry = inside_high + 0.10
    # Bar 1: tags the buy-stop (fill). Bar 2: rips to target.
    rows.append({"open": entry, "high": entry + 0.2, "low": entry - 0.1, "close": entry + 0.1})
    rows.append({"open": entry + 0.1, "high": entry + 50, "low": entry, "close": entry + 40})
    df = _frame(rows, sma200=50.0)
    holds = _simulate_t2(df)
    assert holds, "T2 should fire on inside-day + rising EMA10"
    # Fill on first appended bar, target on the second -> hold = 2 from fill.
    assert holds[-1] == 2, f"fill then target next bar -> hold 2, got {holds[-1]}"


def test_t2_no_fill_is_not_a_trade():
    rows = _t2_setup_rows()
    inside_high = rows[-1]["high"]
    entry = inside_high + 0.10
    # Price never reaches the buy-stop -> no trade recorded.
    for _ in range(MAX_HOLD):
        rows.append(
            {"open": entry - 1, "high": entry - 0.5, "low": entry - 1.5, "close": entry - 1}
        )
    df = _frame(rows, sma200=50.0)
    assert _simulate_t2(df) == []


def test_t2_no_fire_when_not_inside_day():
    rows = _t2_setup_rows()
    # Break the inside-day pattern: make the last bar an outside day.
    rows[-1]["high"] = rows[-2]["high"] + 5
    rows[-1]["low"] = rows[-2]["low"] - 5
    rows.append({"open": 110, "high": 200, "low": 109, "close": 150})
    df = _frame(rows, sma200=50.0)
    assert _simulate_t2(df) == []
