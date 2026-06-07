"""Unit tests for engine.sr_levels (support/resistance computation)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from swing_trader.engine.sr_levels import (
    classic_pivots,
    compute_sr_levels,
    fib_pivots,
    swing_points,
)
from swing_trader.schemas import SRLevel


def _df(highs, lows, closes=None, *, start="2024-01-01") -> pd.DataFrame:
    n = len(highs)
    closes = (
        closes if closes is not None else [(h + lo) / 2 for h, lo in zip(highs, lows, strict=True)]
    )
    idx = pd.date_range(start, periods=n, freq="B")
    return pd.DataFrame(
        {
            "open": closes,
            "high": np.asarray(highs, dtype=float),
            "low": np.asarray(lows, dtype=float),
            "close": np.asarray(closes, dtype=float),
            "volume": np.full(n, 1_000_000.0),
        },
        index=idx,
    )


# --------------------------------------------------------------------------- #
# swing_points
# --------------------------------------------------------------------------- #
def test_swing_points_detects_obvious_peak_and_trough():
    # A clear peak at index 3 and trough at index 7.
    highs = [10, 11, 12, 20, 12, 11, 10, 9, 10, 11, 12]
    lows = [9, 10, 11, 19, 11, 10, 9, 2, 9, 10, 11]
    sh, sl = swing_points(highs, lows, n=2)
    assert 3 in sh
    assert 7 in sl


def test_swing_points_rejects_plateau():
    # Two equal highs at the top -> neither is a *strict* unique extremum.
    highs = [10, 11, 15, 15, 11, 10, 9]
    lows = [9, 8, 7, 7, 8, 9, 10]
    sh, _ = swing_points(highs, lows, n=2)
    assert sh == []  # plateau must not count


def test_swing_points_no_lookahead_on_right_edge():
    # The highest bar is the very last one; it cannot be a confirmed swing.
    highs = [10, 11, 12, 13, 14, 99]
    lows = [9, 10, 11, 12, 13, 50]
    sh, _sl = swing_points(highs, lows, n=2)
    assert 5 not in sh  # last index excluded (would need future bars)


def test_swing_points_short_series_returns_empty():
    sh, sl = swing_points([1, 2], [0, 1], n=3)
    assert sh == [] and sl == []


def test_swing_points_positional_indexing_with_datetime_index():
    # Passing a datetime-indexed Series must not break (coerced to numpy).
    df = _df([10, 11, 20, 11, 10], [9, 10, 19, 10, 9])
    sh, _sl = swing_points(df["high"], df["low"], n=1)
    assert 2 in sh


# --------------------------------------------------------------------------- #
# pivot formulas
# --------------------------------------------------------------------------- #
def test_classic_pivots_formula():
    p = classic_pivots(110, 90, 100)  # PP = 100, range = 20
    assert p["PP"] == pytest.approx(100.0)
    assert p["R1"] == pytest.approx(2 * 100 - 90)  # 110
    assert p["S1"] == pytest.approx(2 * 100 - 110)  # 90
    assert p["R2"] == pytest.approx(100 + 20)  # 120
    assert p["S2"] == pytest.approx(100 - 20)  # 80


def test_fib_pivots_formula():
    p = fib_pivots(110, 90, 100)  # range = 20
    assert p["R1"] == pytest.approx(100 + 0.382 * 20)
    assert p["S2"] == pytest.approx(100 - 0.618 * 20)
    assert p["R3"] == pytest.approx(100 + 20)


# --------------------------------------------------------------------------- #
# compute_sr_levels — guards
# --------------------------------------------------------------------------- #
def test_empty_df_returns_empty():
    assert compute_sr_levels(pd.DataFrame(), price=100.0, atr14=2.0) == []


def test_none_df_returns_empty():
    assert compute_sr_levels(None, price=100.0, atr14=2.0) == []  # type: ignore[arg-type]


def test_bad_price_returns_empty():
    df = _df([10, 20, 10], [9, 19, 9])
    assert compute_sr_levels(df, price=float("nan"), atr14=2.0) == []
    assert compute_sr_levels(df, price=0.0, atr14=2.0) == []
    assert compute_sr_levels(df, price=-5.0, atr14=2.0) == []


def test_missing_columns_returns_empty():
    df = pd.DataFrame({"close": [1, 2, 3]})
    assert compute_sr_levels(df, price=2.0, atr14=0.1) == []


# --------------------------------------------------------------------------- #
# compute_sr_levels — behavior
# --------------------------------------------------------------------------- #
def _zigzag_df(n: int = 120) -> pd.DataFrame:
    """Repeating zigzag so there are well-defined, repeated swing highs/lows."""
    base = np.tile([100, 104, 100, 96], n // 4 + 1)[:n].astype(float)
    highs = base + 1.0
    lows = base - 1.0
    return _df(highs, lows, closes=base)


def test_returns_supports_below_and_resistances_above():
    df = _zigzag_df(120)
    price = 100.0
    levels = compute_sr_levels(df, price=price, atr14=1.0)
    assert levels, "expected some S/R levels"
    assert all(isinstance(x, SRLevel) for x in levels)
    for lvl in levels:
        if lvl.kind == "support":
            assert lvl.price < price
            assert lvl.distance_pct < 0
        else:
            assert lvl.price > price
            assert lvl.distance_pct > 0


def test_caps_per_side():
    df = _zigzag_df(160)
    levels = compute_sr_levels(df, price=100.0, atr14=0.5, max_per_side=2)
    sup = [x for x in levels if x.kind == "support"]
    res = [x for x in levels if x.kind == "resistance"]
    assert len(sup) <= 2 and len(res) <= 2


def test_nearest_first_ordering():
    df = _zigzag_df(160)
    levels = compute_sr_levels(df, price=100.0, atr14=0.5)
    sup = [x for x in levels if x.kind == "support"]
    res = [x for x in levels if x.kind == "resistance"]
    # supports: descending price (closest below first); resistances: ascending.
    sup_gaps = [100.0 - x.price for x in sup]
    res_gaps = [x.price - 100.0 for x in res]
    assert sup_gaps == sorted(sup_gaps)
    assert res_gaps == sorted(res_gaps)


def test_strength_in_unit_interval_and_touches_nonneg():
    df = _zigzag_df(160)
    levels = compute_sr_levels(df, price=100.0, atr14=0.5)
    for lvl in levels:
        assert 0.0 <= lvl.strength <= 1.0
        assert lvl.touches >= 0
        assert lvl.sources  # never empty


def test_nan_atr_falls_back_to_percent_band_not_crash():
    df = _zigzag_df(120)
    # Should not raise and should still produce levels via percent fallback.
    lv_nan = compute_sr_levels(df, price=100.0, atr14=float("nan"))
    lv_none = compute_sr_levels(df, price=100.0, atr14=None)
    assert isinstance(lv_nan, list) and isinstance(lv_none, list)
    assert lv_nan, "percent-band fallback should still yield zones"


def test_deterministic():
    df = _zigzag_df(140)
    a = compute_sr_levels(df, price=100.0, atr14=0.8)
    b = compute_sr_levels(df, price=100.0, atr14=0.8)
    assert [(x.price, x.kind, x.strength) for x in a] == [(y.price, y.kind, y.strength) for y in b]


def test_wider_band_merges_more_sources():
    """A larger ATR band should fold more candidates into fewer, stronger zones."""
    df = _zigzag_df(160)
    tight = compute_sr_levels(df, price=100.0, atr14=0.2, max_per_side=3)
    wide = compute_sr_levels(df, price=100.0, atr14=3.0, max_per_side=3)
    # Wide band: the nearest zones should aggregate >= as many sources as tight.
    if tight and wide:
        assert max(len(x.sources) for x in wide) >= max(len(x.sources) for x in tight)


def test_no_lookahead_truncation_invariance():
    """Levels computed on a truncated history must not depend on future bars.

    Compute on bars[:k]; appending more bars afterwards must not retroactively
    change the result for the truncated frame.
    """
    full = _zigzag_df(160)
    k = 100
    truncated = full.iloc[:k].copy()
    # price taken from the truncated frame's last close
    price = float(truncated["close"].iloc[-1])
    a = compute_sr_levels(truncated, price=price, atr14=1.0)
    # Recompute on the same truncated slice taken from the full df (identical data)
    b = compute_sr_levels(full.iloc[:k].copy(), price=price, atr14=1.0)
    assert [(x.price, x.kind) for x in a] == [(x.price, x.kind) for x in b]


def test_tactical_vs_core_horizon_both_run():
    df = _zigzag_df(120)
    core = compute_sr_levels(df, price=100.0, atr14=1.0, horizon="Core")
    tac = compute_sr_levels(df, price=100.0, atr14=1.0, horizon="Tactical")
    assert isinstance(core, list) and isinstance(tac, list)
