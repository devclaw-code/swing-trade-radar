"""RSI mean reversion swing strategy on daily bars.

Looks for oversold/overbought RSI extremes that align with the longer-term
trend regime (SMA50 vs SMA200) — i.e. a pullback within an established
uptrend (or pop within an established downtrend), not a counter-trend fade.

Note: we deliberately do NOT use ``close > sma50`` as the long trend filter.
By the time RSI dips below 35, price has almost always pulled below SMA50 as
well, so that combination is degenerate and fires ~never. The regime filter
``sma50 > sma200`` captures "uptrend intact" without contradicting the
oversold pullback itself.
"""

from __future__ import annotations

import pandas as pd

from .base_strategy import BaseStrategy, Signal, default_target


class RsiMeanReversionStrategy(BaseStrategy):
    name = "rsi_mean_reversion"

    def generate(self, df: pd.DataFrame, ticker: str) -> list[Signal]:
        if df.empty or len(df) < 60:
            return []
        last = df.iloc[-1]
        for col in ("rsi14", "sma50", "sma200", "atr14", "close"):
            if pd.isna(last.get(col)):
                return []

        signals: list[Signal] = []

        rsi = float(last["rsi14"])
        entry = float(last["close"])
        atr = float(last["atr14"])
        sma50 = float(last["sma50"])
        sma200 = float(last["sma200"])
        bar_date = last.name.date() if hasattr(last.name, "date") else last.name

        uptrend = sma50 > sma200
        downtrend = sma50 < sma200

        long_setup = rsi < 35 and uptrend
        short_setup = rsi > 68 and downtrend

        if long_setup:
            stop = entry - 2 * atr
            if stop >= entry:  # degenerate
                return []
            confirmations = [
                f"RSI {rsi:.1f} < 35 (oversold)",
                "SMA50 > SMA200 (uptrend regime)",
            ]
            if not pd.isna(last.get("ema21")) and entry > float(last["ema21"]):
                confirmations.append("Price > EMA21 (short-term trend intact)")
            if not pd.isna(last.get("vol_sma20")) and not pd.isna(last.get("volume")) and float(last["volume"]) > float(last["vol_sma20"]):
                confirmations.append("Volume > 20d avg (participation)")
            target = default_target(entry, stop, "LONG")
            confidence = min(0.85, 0.55 + 0.1 * (len(confirmations) - 2))
            signals.append(
                Signal(
                    ticker=ticker,
                    strategy=self.name,
                    direction="LONG",
                    entry=entry,
                    target=target,
                    stop=stop,
                    confirmations=confirmations,
                    confidence=confidence,
                    bar_date=bar_date,
                )
            )
        elif short_setup:
            stop = entry + 2 * atr
            if stop <= entry:  # degenerate
                return []
            confirmations = [
                f"RSI {rsi:.1f} > 68 (overbought)",
                "SMA50 < SMA200 (downtrend regime)",
            ]
            if not pd.isna(last.get("ema21")) and entry < float(last["ema21"]):
                confirmations.append("Price < EMA21 (short-term trend intact)")
            if not pd.isna(last.get("vol_sma20")) and not pd.isna(last.get("volume")) and float(last["volume"]) > float(last["vol_sma20"]):
                confirmations.append("Volume > 20d avg (participation)")
            target = default_target(entry, stop, "SHORT")
            confidence = min(0.85, 0.55 + 0.1 * (len(confirmations) - 2))
            signals.append(
                Signal(
                    ticker=ticker,
                    strategy=self.name,
                    direction="SHORT",
                    entry=entry,
                    target=target,
                    stop=stop,
                    confirmations=confirmations,
                    confidence=confidence,
                    bar_date=bar_date,
                )
            )
        return signals
