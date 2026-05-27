"""Indicator computation. Wraps pandas-ta with a single `enrich()` pass."""

from __future__ import annotations

import pandas as pd
import pandas_ta_classic as ta


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Add indicator columns to an OHLCV df (expects lowercase columns).

    Mutates a copy. Safe to call on any length df; columns missing data will be NaN.
    """
    if df.empty:
        return df
    out = df.copy()
    out.columns = [c.lower() for c in out.columns]

    out["ema9"] = ta.ema(out["close"], length=9)
    out["ema21"] = ta.ema(out["close"], length=21)
    out["ema20"] = ta.ema(out["close"], length=20)
    out["sma50"] = ta.sma(out["close"], length=50)
    out["sma200"] = ta.sma(out["close"], length=200)
    out["rsi14"] = ta.rsi(out["close"], length=14)

    bb = ta.bbands(out["close"], length=20, std=2)
    if bb is not None and not bb.empty:
        out["bb_lower"] = bb.iloc[:, 0]
        out["bb_mid"] = bb.iloc[:, 1]
        out["bb_upper"] = bb.iloc[:, 2]
        out["bb_bandwidth"] = bb.iloc[:, 3]
        out["bb_bandwidth_sma20"] = out["bb_bandwidth"].rolling(20).mean()

    macd = ta.macd(out["close"])
    if macd is not None and not macd.empty:
        # cols: MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
        out["macd"] = macd.iloc[:, 0]
        out["macd_hist"] = macd.iloc[:, 1]
        out["macd_signal"] = macd.iloc[:, 2]

    out["atr14"] = ta.atr(out["high"], out["low"], out["close"], length=14)
    out["vol_sma20"] = out["volume"].rolling(20).mean()
    out["pivot_high_20"] = out["high"].rolling(20).max()
    out["pivot_low_20"] = out["low"].rolling(20).min()

    return out
