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
ATR_STOP_MULT_DYNAMIC = 1.5  # volatility-adjusted dynamic stop: entry -/+ 1.5 * ATR(14)
MIN_RR = 2.5                 # minimum reward:risk for a Core (trend) setup
MIN_RR_TACTICAL = 2.0        # minimum reward:risk for the dynamic-ATR tactical model
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
    """Target priced at `rr` x the actual stop distance.

    Rounds in the direction that *preserves* reward (up for LONG, down for SHORT)
    so cent-rounding can never drop the realised reward:risk below `rr` — the
    helper feeds the hard min-RR gate, so a 2.50R request must not become 2.49R.
    """
    risk = abs(entry - stop)
    raw = entry + rr * risk if direction == "LONG" else entry - rr * risk
    cents = raw * 100.0
    rounded = math.ceil(cents) if direction == "LONG" else math.floor(cents)
    return rounded / 100.0


def dynamic_atr_trade(
    entry: float,
    atr14: float | None,
    *,
    stop_mult: float = ATR_STOP_MULT_DYNAMIC,
    rr: float = MIN_RR_TACTICAL,
    direction: Direction = "LONG",
) -> dict[str, float | None]:
    """Volatility-adjusted trade geometry — the dynamic-ATR risk model.

    Replaces the old static 2.50 R:R with a per-ticker, volatility-scaled plan:

      * ``stop_loss``  = entry - (stop_mult * ATR)   for LONG  (default 1.5 * ATR)
      * ``take_profit``= priced to hold a minimum ``rr`` R:R against that stop
                         (default 2.0 R), reward-preserving cent-rounding.

    When ATR is missing/NaN/zero, ``atr_stop`` degrades to the percent fallback,
    so this never raises and always returns a coherent plan. The realised R:R
    (``rr_realized``) is returned so callers can gate on it directly.
    """
    stop = atr_stop(entry, atr14, mult=stop_mult, direction=direction)
    target = min_rr_target(entry, stop, rr=rr, direction=direction)
    return {
        "entry": round(float(entry), 2),
        "stop_loss": stop,
        "take_profit": target,
        "atr": round(float(atr14), 4) if _atr_valid(atr14) else None,
        "rr_realized": round(reward_risk(entry, stop, target), 3),
    }


def reward_risk(entry: float, stop: float, target: float) -> float:
    """Reward:risk ratio. Direction-agnostic (uses absolute distances).

    Returns NaN if any input is NaN so callers can treat non-comparable ratios as
    failing a min-RR gate (``NaN < MIN_RR`` is False, which would otherwise let
    bad data slip through).
    """
    if math.isnan(entry) or math.isnan(stop) or math.isnan(target):
        return math.nan
    risk = abs(entry - stop)
    if risk <= 0:
        return 0.0
    return abs(target - entry) / risk
