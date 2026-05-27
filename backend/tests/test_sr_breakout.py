"""SR breakout unit test on a synthetic price series."""

from __future__ import annotations

import numpy as np
import pandas as pd

from swing_trader.engine.indicators import enrich
from swing_trader.strategies.sr_breakout import SrBreakoutStrategy


def _series_with_upside_breakout(n: int = 60) -> pd.DataFrame:
    # Flat range, then a sharp breakout above on the last bar with high volume.
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    rng = np.random.default_rng(0)
    close = 100 + rng.normal(0, 0.5, n)
    # Force last bar to break sharply above the prior 20-bar high.
    close[-1] = close[:-1].max() + 5
    volume = np.full(n, 1_000_000, dtype=float)
    volume[-1] = 5_000_000  # > 1.5x avg, also > 2x for confidence bump
    df = pd.DataFrame(
        {
            "open": close,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": volume,
        },
        index=idx,
    )
    return enrich(df)


def test_sr_breakout_long_signal_fires():
    df = _series_with_upside_breakout(60)
    sigs = SrBreakoutStrategy().generate(df, "TEST")
    assert isinstance(sigs, list)
    assert len(sigs) == 1
    s = sigs[0]
    assert s.direction == "LONG"
    assert s.entry > s.stop
    assert s.target > s.entry
    assert s.confidence <= 0.85
    assert any("Broke 20-day pivot high" in c for c in s.confirmations)
    assert any("Volume" in c and "average" in c for c in s.confirmations)


def test_sr_breakout_no_signal_on_flat_series():
    n = 60
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    close = np.full(n, 100.0)
    df = pd.DataFrame(
        {
            "open": close,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": np.full(n, 1_000_000, dtype=float),
        },
        index=idx,
    )
    df = enrich(df)
    sigs = SrBreakoutStrategy().generate(df, "TEST")
    assert sigs == []


def test_sr_breakout_too_short_returns_empty():
    idx = pd.date_range("2024-01-01", periods=10, freq="B")
    close = np.linspace(100, 110, 10)
    df = pd.DataFrame(
        {
            "open": close,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": np.full(10, 1_000_000, dtype=float),
        },
        index=idx,
    )
    df = enrich(df)
    assert SrBreakoutStrategy().generate(df, "TEST") == []
