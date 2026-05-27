"""Volume trend continuation unit test on a synthetic series."""

from __future__ import annotations

import numpy as np
import pandas as pd

from swing_trader.engine.indicators import enrich
from swing_trader.strategies.volume_trend import VolumeTrendStrategy


def _uptrend_with_pullback_bounce(n: int = 250) -> pd.DataFrame:
    """Construct a long uptrend, a small pullback on light volume, then a
    green bounce bar on heavy volume."""
    idx = pd.date_range("2023-01-01", periods=n, freq="B")
    rng = np.random.default_rng(0)

    # Long, steady uptrend so SMA200 sits well below price.
    close = np.linspace(50, 200, n) + rng.normal(0, 0.2, n)

    # Engineer a clean pullback over bars [-6..-2], bouncing on the last bar.
    # Pullback dips price down to roughly the 20 EMA region, then last bar pops up.
    close[-6] = close[-7] - 1.5
    close[-5] = close[-6] - 1.2
    close[-4] = close[-5] - 1.0
    close[-3] = close[-4] - 0.5
    close[-2] = close[-3] + 0.2
    close[-1] = close[-2] + 3.0  # strong green bounce

    high = close + 0.5
    low = close - 0.5
    # Make pullback bars print lows that brush the 20 EMA region.
    low[-5:-1] = close[-5:-1] - 2.0

    # Volume: baseline 2M (so vol_sma20 stays well above pullback avg),
    # light during pullback, moderate spike on bounce bar.
    volume = np.full(n, 2_000_000.0)
    volume[-5:-1] = 400_000.0  # declining/light volume during pullback
    volume[-1] = 2_500_000.0  # bounce spike (> vol_sma20 but doesn't lift 5-bar avg above it)

    df = pd.DataFrame(
        {
            "open": close,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=idx,
    )
    return enrich(df)


def test_volume_trend_long_signal_fires():
    df = _uptrend_with_pullback_bounce(250)
    sigs = VolumeTrendStrategy().generate(df, "TEST")
    assert isinstance(sigs, list)
    # With this construction the strategy should fire LONG.
    assert len(sigs) == 1
    s = sigs[0]
    assert s.direction == "LONG"
    assert s.strategy == "volume_trend"
    assert s.entry > s.stop
    assert s.target > s.entry
    # 1.5R target sanity check.
    risk = s.entry - s.stop
    assert abs((s.target - s.entry) - 1.5 * risk) < 1e-6
    assert 0.7 <= s.confidence <= 0.9
    assert len(s.confirmations) >= 3


def test_volume_trend_returns_empty_when_too_short():
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
    sigs = VolumeTrendStrategy().generate(df, "TEST")
    assert sigs == []
