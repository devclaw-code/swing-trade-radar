"""Bollinger squeeze unit test on a synthetic price series."""

from __future__ import annotations

import numpy as np
import pandas as pd

from swing_trader.engine.indicators import enrich
from swing_trader.strategies.bollinger_squeeze import BollingerSqueezeStrategy


def _series_squeeze_then_breakout(n: int = 80) -> pd.DataFrame:
    # Long flat (low vol) period to compress bands, then a sharp upward breakout.
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    rng = np.random.default_rng(0)
    flat = 100 + rng.normal(0, 0.1, n - 5)
    breakout = np.linspace(101, 115, 5)
    close = np.concatenate([flat, breakout])
    df = pd.DataFrame(
        {
            "open": close,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": 1_000_000,
        },
        index=idx,
    )
    return enrich(df)


def test_bollinger_squeeze_returns_list():
    df = _series_squeeze_then_breakout(80)
    sigs = BollingerSqueezeStrategy().generate(df, "TEST")
    assert isinstance(sigs, list)
    for s in sigs:
        assert s.direction in ("LONG", "SHORT")
        assert s.entry > 0 and s.stop > 0 and s.target > 0
        assert 0.0 <= s.confidence <= 0.8
        assert any("squeeze" in c.lower() for c in s.confirmations)


def test_bollinger_squeeze_short_df_returns_empty():
    idx = pd.date_range("2024-01-01", periods=10, freq="B")
    df = pd.DataFrame(
        {
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.0,
            "volume": 1_000_000,
        },
        index=idx,
    )
    df = enrich(df)
    assert BollingerSqueezeStrategy().generate(df, "TEST") == []
