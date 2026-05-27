"""Risk classifier unit tests (pure functions, no IO)."""

from __future__ import annotations

from swing_trader.engine.risk_classifier import classify
from swing_trader.strategies.base_strategy import Signal


def _sig(*, entry: float, target: float, stop: float, confirmations: list[str], direction="LONG"):
    return Signal(
        ticker="TEST",
        strategy="t",
        direction=direction,
        entry=entry,
        target=target,
        stop=stop,
        confirmations=confirmations,
    )


def test_low_risk():
    s = _sig(entry=100, target=106, stop=98, confirmations=["a", "b", "c"])  # rr=3, stop=2%
    out = classify(s)
    assert out.risk == "LOW"
    assert 0.5 < out.confidence <= 1.0


def test_medium_risk():
    s = _sig(entry=100, target=104, stop=98, confirmations=["a", "b"])  # rr=2, stop=2%, n=2
    out = classify(s)
    assert out.risk == "MED"


def test_high_risk_few_confirmations():
    s = _sig(entry=100, target=106, stop=98, confirmations=["a"])  # n=1
    out = classify(s)
    assert out.risk == "HIGH"


def test_high_risk_bad_rr():
    s = _sig(entry=100, target=101, stop=98, confirmations=["a", "b", "c"])  # rr=0.5
    out = classify(s)
    assert out.risk == "HIGH"


def test_inverted_target_is_high():
    s = _sig(entry=100, target=90, stop=98, confirmations=["a", "b", "c"], direction="LONG")
    out = classify(s)
    assert out.risk == "HIGH"
