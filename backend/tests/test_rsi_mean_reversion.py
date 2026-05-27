"""RSI mean reversion unit test on a synthetic price series."""

from __future__ import annotations

import numpy as np
import pandas as pd

from swing_trader.engine.indicators import enrich
from swing_trader.strategies.rsi_mean_reversion import RsiMeanReversionStrategy


def _series_with_pullback(n: int = 80) -> pd.DataFrame:
    # Long uptrend then a sharp pullback → price likely above SMA50 with RSI dipping.
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    trend = np.linspace(80, 140, n - 10)
    pullback = np.linspace(140, 128, 10)
    base = np.concatenate([trend, pullback])
    close = base + np.random.default_rng(0).normal(0, 0.3, n)
    df = pd.DataFrame(
        {
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 1_000_000,
        },
        index=idx,
    )
    return enrich(df)


def test_rsi_mean_reversion_returns_valid_signals():
    df = _series_with_pullback(80)
    sigs = RsiMeanReversionStrategy().generate(df, "TEST")
    assert isinstance(sigs, list)
    for s in sigs:
        assert s.direction in ("LONG", "SHORT")
        assert s.entry > 0 and s.stop > 0 and s.target > 0
        assert s.strategy == "rsi_mean_reversion"
        assert 0.0 <= s.confidence <= 0.85
        if s.direction == "LONG":
            assert s.stop < s.entry < s.target
        else:
            assert s.target < s.entry < s.stop


def test_rsi_mean_reversion_short_df_returns_empty():
    idx = pd.date_range("2024-01-01", periods=20, freq="B")
    close = np.linspace(100, 110, 20)
    df = pd.DataFrame(
        {
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 1_000_000,
        },
        index=idx,
    )
    df = enrich(df)
    sigs = RsiMeanReversionStrategy().generate(df, "TEST")
    assert sigs == []
