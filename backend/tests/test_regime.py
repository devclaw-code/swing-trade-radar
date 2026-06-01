"""Tests for engine.regime — focused on offline_default + caching path."""

from __future__ import annotations

from datetime import date

from swing_trader.engine.regime import offline_default
from swing_trader.schemas import RegimeContext


def test_offline_default_shape():
    ctx = offline_default()
    assert isinstance(ctx, RegimeContext)
    assert ctx.regime_verdict == "favorable for long swings"
    assert ctx.spy_above_200sma is True
    assert ctx.qqq_above_200sma is True
    assert ctx.vix == 15.0
    assert ctx.vix_term_structure == "contango (healthy)"
    assert isinstance(ctx.as_of, date)


def test_regime_context_serialises_round_trip():
    ctx = offline_default()
    payload = ctx.model_dump(mode="json")
    rebuilt = RegimeContext(**payload)
    assert rebuilt.model_dump(mode="json") == payload
