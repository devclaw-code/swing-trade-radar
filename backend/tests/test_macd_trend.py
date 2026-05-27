"""MACD trend strategy unit test on a synthetic price series."""

from __future__ import annotations

import numpy as np
import pandas as pd

from swing_trader.engine.indicators import enrich
from swing_trader.strategies.macd_trend import MacdTrendStrategy


def _series_with_trend_then_dip(n: int = 250) -> pd.DataFrame:
    # Long uptrend (so close > SMA200), with a late dip then rally to spark a MACD cross up.
    idx = pd.date_range("2023-01-01", periods=n, freq="B")
    trend = np.linspace(80, 180, n)
    # Inject a small dip near the end so MACD dips below signal and then crosses back up.
    dip = np.zeros(n)
    dip[-20:-5] = np.linspace(0, -8, 15)
    dip[-5:] = np.linspace(-8, 2, 5)
    close = trend + dip + np.random.default_rng(0).normal(0, 0.3, n)
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


def test_macd_trend_returns_list():
    df = _series_with_trend_then_dip(250)
    sigs = MacdTrendStrategy().generate(df, "TEST")
    assert isinstance(sigs, list)
    for s in sigs:
        assert s.direction in ("LONG", "SHORT")
        assert s.entry > 0 and s.stop > 0 and s.target > 0
        assert 0.65 <= s.confidence <= 0.85
        assert s.strategy == "macd_trend"


def test_macd_trend_short_df_returns_empty():
    # < 210 bars → no signals (SMA200 not reliable).
    idx = pd.date_range("2024-01-01", periods=50, freq="B")
    close = np.linspace(100, 110, 50)
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
    assert MacdTrendStrategy().generate(df, "TEST") == []
