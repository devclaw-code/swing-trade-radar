"""Tests for data sanity checks."""

from __future__ import annotations

import numpy as np
import pandas as pd

from swing_trader.data.sanity import (
    SanityFlag,
    check_data_sanity,
    highest_severity,
)
from swing_trader.engine.indicators import enrich


def _df(closes, *, vol=1_000_000.0):
    n = len(closes)
    idx = pd.date_range(end=pd.Timestamp("2026-05-30"), periods=n, freq="B")
    closes = np.asarray(closes, dtype=float)
    return pd.DataFrame(
        {
            "open": np.r_[closes[0], closes[:-1]],
            "high": closes * 1.005,
            "low": closes * 0.995,
            "close": closes,
            "volume": np.full(n, vol),
        },
        index=idx,
    )


def test_empty_df_flags_high():
    flags = check_data_sanity(pd.DataFrame())
    assert any(f.code == "insufficient_history" and f.severity == "high" for f in flags)


def test_clean_uptrend_no_flags(uptrend_df):
    enriched = enrich(uptrend_df)
    flags = check_data_sanity(enriched)
    # The synthetic uptrend may stretch ~30% from SMA50 sometimes — accept that
    # but the random seed is small drift so we should not get HIGH severities.
    assert highest_severity(flags) != "high"


def test_extended_above_sma50_flags_high():
    # Build uptrend then spike close 80% above SMA50 on last bar.
    closes = np.linspace(100, 110, 220)
    closes[-1] = closes[-2] * 1.80  # ~80% jump (also a possible_split warning)
    df = _df(closes)
    enriched = enrich(df)
    flags = check_data_sanity(enriched)
    codes = {f.code for f in flags}
    assert "extended_above_sma50" in codes
    extended = next(f for f in flags if f.code == "extended_above_sma50")
    assert extended.severity == "high"


def test_split_detected_warning():
    closes = np.linspace(400, 410, 220)
    closes[-1] = closes[-2] / 4.0  # 4-for-1 split on the last bar
    df = _df(closes)
    enriched = enrich(df)
    flags = check_data_sanity(enriched)
    assert any(f.code == "possible_split" for f in flags)


def test_stale_price_flag():
    closes = np.linspace(100, 110, 100)
    closes[-5:] = 110.0  # 5 identical closes
    df = _df(closes)
    enriched = enrich(df)
    flags = check_data_sanity(enriched)
    assert any(f.code == "stale_price" and f.severity == "warning" for f in flags)


def test_decimal_shift_10x_high():
    closes = np.linspace(100, 110, 60)
    closes[-1] = 1100.0  # 10x jump (decimal misplacement)
    df = _df(closes)
    enriched = enrich(df)
    flags = check_data_sanity(enriched)
    assert any(f.code == "decimal_shift" and f.severity == "high" for f in flags)


def test_nan_close_flag_high():
    closes = np.linspace(100, 110, 60)
    df = _df(closes)
    df.iloc[-1, df.columns.get_loc("close")] = np.nan
    enriched = enrich(df)
    flags = check_data_sanity(enriched)
    assert any(f.code == "nan_price" and f.severity == "high" for f in flags)


def test_negative_close_flag_high():
    closes = np.linspace(100, 110, 60)
    df = _df(closes)
    df.iloc[-1, df.columns.get_loc("close")] = -10.0
    enriched = enrich(df)
    flags = check_data_sanity(enriched)
    assert any(f.code == "non_positive_price" and f.severity == "high" for f in flags)


def test_atr_non_positive_flag():
    closes = np.linspace(100, 110, 60)
    df = _df(closes)
    enriched = enrich(df)
    enriched.iloc[-1, enriched.columns.get_loc("atr14")] = 0.0
    flags = check_data_sanity(enriched)
    assert any(f.code == "non_positive_atr" for f in flags)


def test_rsi_out_of_range_flag():
    closes = np.linspace(100, 110, 60)
    df = _df(closes)
    enriched = enrich(df)
    enriched.iloc[-1, enriched.columns.get_loc("rsi14")] = 150.0
    flags = check_data_sanity(enriched)
    assert any(f.code == "rsi_out_of_range" and f.severity == "high" for f in flags)


def test_highest_severity_helper():
    assert highest_severity([]) is None
    fs = [
        SanityFlag(code="stale_price", severity="warning", message=""),
        SanityFlag(code="nan_price", severity="high", message=""),
        SanityFlag(code="extended_above_sma50", severity="info", message=""),
    ]
    assert highest_severity(fs) == "high"


def test_to_dict_round_trip():
    f = SanityFlag(code="stale_price", severity="warning", message="x", value=1.0, threshold=2.0)
    d = f.to_dict()
    assert d == {
        "code": "stale_price",
        "severity": "warning",
        "message": "x",
        "value": 1.0,
        "threshold": 2.0,
    }
