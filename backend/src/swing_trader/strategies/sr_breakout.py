"""Support/Resistance breakout swing strategy with volume confirmation."""

from __future__ import annotations

import pandas as pd

from ..engine.risk_levels import floor_stop_with_atr
from .base_strategy import BaseStrategy, Signal, default_target


class SrBreakoutStrategy(BaseStrategy):
    name = "sr_breakout"

    def generate(self, df: pd.DataFrame, ticker: str) -> list[Signal]:
        if df.empty or len(df) < 25:
            return []
        last = df.iloc[-1]
        prev = df.iloc[-2]
        for col in ("pivot_high_20", "pivot_low_20", "vol_sma20"):
            if pd.isna(prev.get(col)) or pd.isna(last.get(col)):
                return []
        if pd.isna(last.get("close")) or pd.isna(last.get("volume")):
            return []

        signals: list[Signal] = []

        entry = float(last["close"])
        volume = float(last["volume"])
        vol_avg = float(last["vol_sma20"])
        prev_pivot_high = float(prev["pivot_high_20"])
        prev_pivot_low = float(prev["pivot_low_20"])
        bar_date = last.name.date() if hasattr(last.name, "date") else last.name

        if vol_avg <= 0:
            return []
        vol_multiple = volume / vol_avg
        volume_ok = volume > 1.5 * vol_avg

        broke_up = entry > prev_pivot_high
        broke_down = entry < prev_pivot_low

        if broke_up and volume_ok:
            atr = last.get("atr14")
            stop = floor_stop_with_atr(
                entry, prev_pivot_high * 0.99, atr, mult=2.0, direction="LONG"
            )
            if stop >= entry:
                return []
            confirmations = [
                "Broke 20-day pivot high",
                f"Volume {vol_multiple:.2f}x > 20d average",
            ]
            confidence = 0.6 + (0.1 if vol_multiple > 2 else 0.0)
            confidence = min(confidence, 0.85)
            target = default_target(entry, stop, "LONG")
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
        elif broke_down and volume_ok:
            atr = last.get("atr14")
            stop = floor_stop_with_atr(
                entry, prev_pivot_low * 1.01, atr, mult=2.0, direction="SHORT"
            )
            if stop <= entry:
                return []
            confirmations = [
                "Broke 20-day pivot low",
                f"Volume {vol_multiple:.2f}x > 20d average",
            ]
            confidence = 0.6 + (0.1 if vol_multiple > 2 else 0.0)
            confidence = min(confidence, 0.85)
            target = default_target(entry, stop, "SHORT")
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
