"""W3 — risk geometry: ATR stops, structure-stop ATR floor, min-RR gating."""

from __future__ import annotations

import math

from swing_trader.engine.risk_levels import (
    MIN_RR,
    PCT_FALLBACK,
    atr_stop,
    floor_stop_with_atr,
    min_rr_target,
    reward_risk,
)


# --- atr_stop --------------------------------------------------------------
def test_atr_stop_long_below_entry():
    assert atr_stop(100.0, 2.5, mult=2.0, direction="LONG") == 95.0


def test_atr_stop_short_above_entry():
    assert atr_stop(100.0, 2.5, mult=2.0, direction="SHORT") == 105.0


def test_atr_stop_wider_mult():
    assert atr_stop(100.0, 2.0, mult=2.5, direction="LONG") == 95.0


def test_atr_stop_nan_falls_back_to_pct_long():
    assert atr_stop(100.0, float("nan"), direction="LONG") == round(100.0 * (1 - PCT_FALLBACK), 2)


def test_atr_stop_none_falls_back_to_pct_short():
    assert atr_stop(100.0, None, direction="SHORT") == round(100.0 * (1 + PCT_FALLBACK), 2)


def test_atr_stop_zero_atr_falls_back():
    # ATR of 0 is not a usable distance -> percent fallback, not a stop == entry.
    assert atr_stop(100.0, 0.0, direction="LONG") == 95.0


# --- floor_stop_with_atr (the AAOI-class high-vol case) --------------------
def test_floor_widens_too_tight_long_stop():
    # High-vol name: ATR is 10, but a pivot stop only 1pt below entry would sit
    # *inside* the noise band. The floor must widen it to >= 2x ATR.
    entry = 100.0
    pivot_stop = 99.0  # 1% — way too tight on a 10-ATR name
    floored = floor_stop_with_atr(entry, pivot_stop, 10.0, mult=2.0, direction="LONG")
    assert floored == 80.0  # entry - 2*ATR
    assert floored < pivot_stop


def test_floor_keeps_already_wide_long_stop():
    # Pivot stop already wider than 2x ATR -> keep the structure stop.
    entry = 100.0
    pivot_stop = 70.0
    floored = floor_stop_with_atr(entry, pivot_stop, 5.0, mult=2.0, direction="LONG")
    assert floored == 70.0


def test_floor_widens_too_tight_short_stop():
    entry = 100.0
    pivot_stop = 101.0  # too tight above
    floored = floor_stop_with_atr(entry, pivot_stop, 10.0, mult=2.0, direction="SHORT")
    assert floored == 120.0  # entry + 2*ATR
    assert floored > pivot_stop


def test_floor_nan_atr_returns_structure_stop():
    assert floor_stop_with_atr(100.0, 97.5, float("nan"), direction="LONG") == 97.5


# --- min_rr_target ---------------------------------------------------------
def test_min_rr_target_long():
    # entry 100, stop 96 -> risk 4 -> 2.5R target = 110
    assert min_rr_target(100.0, 96.0, rr=2.5, direction="LONG") == 110.0


def test_min_rr_target_short():
    assert min_rr_target(100.0, 104.0, rr=2.5, direction="SHORT") == 90.0


def test_min_rr_target_default_uses_min_rr():
    t = min_rr_target(100.0, 96.0, direction="LONG")
    assert math.isclose(reward_risk(100.0, 96.0, t), MIN_RR, abs_tol=1e-9)


# --- reward_risk -----------------------------------------------------------
def test_reward_risk_ratio():
    assert reward_risk(100.0, 95.0, 115.0) == 3.0


def test_reward_risk_zero_risk_guarded():
    assert reward_risk(100.0, 100.0, 110.0) == 0.0
