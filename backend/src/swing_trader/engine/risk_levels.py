"""Centralised stop/target geometry — single source of truth for ATR-based risk levels.

Every strategy and the verdict synthesizer should price stops/targets through these
helpers so that:
  * a NaN/zero ATR degrades to an explicit percent fallback (never a silent crash),
  * structure-based stops are floored at a minimum ATR distance (so a pivot stop on a
    high-volatility name like an AAOI-class ticker can't land *inside* the noise band),
  * minimum-R:R targets are computed consistently (Aditya's 1:2.5 rule).
"""

from __future__ import annotations

import math
from typing import Literal

Direction = Literal["LONG", "SHORT"]

# --- Tunables --------------------------------------------------------------
ATR_STOP_MULT = 2.0          # default: entry -/+ 2 * ATR(14)
ATR_STOP_MULT_HIVOL = 2.5    # wider stop for Clenow-style trend rides
MIN_RR = 2.5                 # minimum reward:risk for a tradeable setup
PCT_FALLBACK = 0.05          # used only when ATR cannot be computed


def _atr_valid(atr14: float | None) -> bool:
    return atr14 is not None and not math.isnan(atr14) and atr14 > 0


def atr_stop(
    entry: float,
    atr14: float | None,
    *,
    mult: float = ATR_STOP_MULT,
    direction: Direction = "LONG",
) -> float:
    """ATR-based stop. Falls back to a fixed percent when ATR is unavailable.

    LONG  -> stop below entry; SHORT -> stop above entry.
    """
    if not _atr_valid(atr14):
        factor = (1.0 - PCT_FALLBACK) if direction == "LONG" else (1.0 + PCT_FALLBACK)
        return round(entry * factor, 2)
    delta = mult * float(atr14)
    return round(entry - delta if direction == "LONG" else entry + delta, 2)


def floor_stop_with_atr(
    entry: float,
    struct_stop: float,
    atr14: float | None,
    *,
    mult: float = ATR_STOP_MULT,
    direction: Direction = "LONG",
) -> float:
    """Widen a structure-based stop so it is never *tighter* than `mult` * ATR.

    For LONG, a tighter stop is a *higher* price, so we take the lower of the two.
    For SHORT, a tighter stop is a *lower* price, so we take the higher of the two.
    If ATR is unavailable the structure stop is returned unchanged.
    """
    if not _atr_valid(atr14):
        return round(struct_stop, 2)
    floor = atr_stop(entry, atr14, mult=mult, direction=direction)
    widened = min(struct_stop, floor) if direction == "LONG" else max(struct_stop, floor)
    return round(widened, 2)


def min_rr_target(
    entry: float,
    stop: float,
    *,
    rr: float = MIN_RR,
    direction: Direction = "LONG",
) -> float:
    """Target priced at `rr` x the actual stop distance."""
    risk = abs(entry - stop)
    return round(entry + rr * risk if direction == "LONG" else entry - rr * risk, 2)


def reward_risk(entry: float, stop: float, target: float) -> float:
    """Reward:risk ratio. Direction-agnostic (uses absolute distances)."""
    risk = abs(entry - stop)
    if risk <= 0:
        return 0.0
    return abs(target - entry) / risk
