"""Standalone ATR utility — Wilder's 14-period Average True Range.

`enrich()` already adds an ``atr14`` column via pandas-ta, but the tactical
engine and the dynamic-risk layer need a *self-contained*, dependency-light ATR
that:

  * computes True Range from raw OHLC,
  * smooths with Wilder's RMA (the canonical ATR), and
  * degrades cleanly on short history / NaN bars instead of raising.

Keep this independent of ``enrich()`` so tactical scanners can run on a raw
OHLCV frame (or a yfinance API payload that returned partial bars) without a
full indicator pass.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

DEFAULT_ATR_PERIOD = 14


def true_range(df: pd.DataFrame) -> pd.Series:
    """Per-bar True Range = max(H-L, |H-prevC|, |L-prevC|).

    Expects lowercase ``high``/``low``/``close`` columns. The first bar has no
    previous close, so its TR falls back to (high - low).
    """
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    prev_close = df["close"].astype(float).shift(1)

    hl = (high - low).abs()
    hc = (high - prev_close).abs()
    lc = (low - prev_close).abs()

    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    # First bar: no prev close -> use the high-low range.
    tr.iloc[0] = float(hl.iloc[0]) if len(hl) else math.nan
    return tr


def atr_series(df: pd.DataFrame, period: int = DEFAULT_ATR_PERIOD) -> pd.Series:
    """Full ATR series using Wilder's RMA smoothing.

    Returns an all-NaN series (aligned to ``df.index``) when there is not enough
    data instead of raising — callers can ``.dropna()`` or null-check.
    """
    if df is None or df.empty:
        return pd.Series(dtype=float)

    cols = {c.lower() for c in df.columns}
    if not {"high", "low", "close"}.issubset(cols):
        return pd.Series(np.nan, index=df.index)

    work = df.copy()
    work.columns = [c.lower() for c in work.columns]

    try:
        tr = true_range(work)
        if len(tr) < period:
            # Not enough bars for a stable Wilder average — return NaNs.
            return pd.Series(np.nan, index=df.index)
        # Wilder's RMA: ewm with alpha = 1/period, min_periods = period.
        atr = tr.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
        return atr
    except Exception:
        # Any malformed input (mixed dtypes, all-NaN OHLC) -> NaN series.
        return pd.Series(np.nan, index=df.index)


def compute_atr14(df: pd.DataFrame, period: int = DEFAULT_ATR_PERIOD) -> float | None:
    """Latest-bar ATR(14) as a plain float, or ``None`` if not computable.

    This is the function tactical strategies and the risk layer call. It never
    raises: bad data / short history / NaN all collapse to ``None`` so the caller
    can drop the ticker or fall back to a percent stop.
    """
    try:
        series = atr_series(df, period=period)
        if series.empty:
            return None
        last = series.iloc[-1]
        val = float(last)
        if math.isnan(val) or math.isinf(val) or val <= 0:
            return None
        return val
    except Exception:
        return None
