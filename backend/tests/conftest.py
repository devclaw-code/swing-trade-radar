"""Shared test fixtures: synthetic OHLCV dfs we can shape per-test."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


def _ohlcv(closes: np.ndarray, *, vol: float = 1_000_000.0) -> pd.DataFrame:
    """Build a basic OHLCV dataframe from a close-price array."""
    n = len(closes)
    idx = pd.date_range(end=pd.Timestamp("2026-05-30"), periods=n, freq="B")
    high = closes * 1.005
    low = closes * 0.995
    op = np.r_[closes[0], closes[:-1]]
    df = pd.DataFrame(
        {
            "open": op,
            "high": high,
            "low": low,
            "close": closes,
            "volume": np.full(n, vol),
        },
        index=idx,
    )
    return df


@pytest.fixture
def uptrend_df() -> pd.DataFrame:
    """260 bars of clean ~0.1%/day drift around a 100 base — bullish trend."""
    np.random.seed(7)
    n = 260
    rets = np.random.normal(0.0010, 0.012, n)
    closes = 100.0 * np.exp(np.cumsum(rets))
    return _ohlcv(closes)


@pytest.fixture
def downtrend_df() -> pd.DataFrame:
    np.random.seed(11)
    n = 260
    rets = np.random.normal(-0.0008, 0.014, n)
    closes = 200.0 * np.exp(np.cumsum(rets))
    return _ohlcv(closes)


@pytest.fixture
def oversold_in_uptrend_df() -> pd.DataFrame:
    """260 bars uptrend then a 5-day sharp drop to trigger RSI(2) < 10."""
    np.random.seed(13)
    n = 255
    rets = np.random.normal(0.0012, 0.010, n)
    closes = 100.0 * np.exp(np.cumsum(rets))
    # Append a sharp 5-day pullback (~ -2% / day) to trigger RSI(2) extreme
    last = closes[-1]
    pull = np.array(
        [last * 0.98, last * 0.96, last * 0.945, last * 0.93, last * 0.92]
    )
    closes = np.r_[closes, pull]
    return _ohlcv(closes)


@pytest.fixture
def vcp_breakout_df() -> pd.DataFrame:
    """Long uptrend → contraction → breakout on volume."""
    np.random.seed(17)
    base = 100.0 * np.exp(np.cumsum(np.random.normal(0.0012, 0.012, 250)))
    # 30 bars of compressed range
    flat = base[-1] + np.random.normal(0, 0.5, 30)
    # final breakout day +5%
    breakout = np.array([flat[-1] * 1.05])
    closes = np.r_[base, flat, breakout]
    df = _ohlcv(closes)
    # Spike volume on breakout
    df.iloc[-1, df.columns.get_loc("volume")] = 5_000_000.0
    return df
