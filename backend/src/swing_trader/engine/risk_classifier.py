"""Risk classifier: scores each signal into LOW/MEDIUM/HIGH + confidence %."""

from __future__ import annotations

from dataclasses import dataclass

from ..config import settings
from ..strategies.base_strategy import Signal


@dataclass
class ClassifiedSignal:
    signal: Signal
    risk: str  # LOW|MED|HIGH
    confidence: float  # 0..1
    stop_pct: float
    rr_ratio: float


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _normalize(x: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.0
    return _clamp((x - lo) / (hi - lo))


def classify(signal: Signal) -> ClassifiedSignal:
    """Compute risk bucket + confidence blend for a single signal."""
    entry = signal.entry
    stop = signal.stop
    target = signal.target
    direction = signal.direction

    stop_dist = abs(entry - stop)
    stop_pct = stop_dist / entry if entry else 1.0
    target_dist = abs(target - entry)
    rr = (target_dist / stop_dist) if stop_dist else 0.0

    # Direction sanity: target should be on opposite side of stop relative to entry.
    if direction == "LONG" and (target <= entry or stop >= entry):
        risk = "HIGH"
    elif direction == "SHORT" and (target >= entry or stop <= entry):
        risk = "HIGH"
    else:
        n = len(signal.confirmations)
        low_ok = (
            n >= settings.risk_low_min_confirmations
            and stop_pct < settings.risk_low_max_stop_pct
            and rr >= settings.risk_low_min_rr
        )
        med_ok = (
            n >= settings.risk_med_min_confirmations
            and stop_pct <= settings.risk_med_max_stop_pct
            and rr >= settings.risk_med_min_rr
        )
        if low_ok:
            risk = "LOW"
        elif med_ok:
            risk = "MED"
        else:
            risk = "HIGH"

    confidence = (
        0.4 * _normalize(len(signal.confirmations), 1, 4)
        + 0.3 * _normalize(rr, 1.0, 4.0)
        + 0.3 * (1.0 - _clamp(stop_pct / 0.08))
    )
    confidence = _clamp(confidence)

    return ClassifiedSignal(
        signal=signal,
        risk=risk,
        confidence=confidence,
        stop_pct=stop_pct,
        rr_ratio=rr,
    )
