"""Volume-confirmed trend continuation swing strategy (LONG only).

Looks for a healthy uptrend (close > SMA50 > SMA200), a recent pullback to the
20 EMA on declining volume, and a green bounce bar with a volume spike above
the 20-day average. Asymmetric pattern — no SHORT equivalent implemented.
"""

from __future__ import annotations

import pandas as pd

from ..engine.risk_levels import floor_stop_with_atr, min_rr_target
from .base_strategy import BaseStrategy, Signal


class VolumeTrendStrategy(BaseStrategy):
    name = "volume_trend"

    def generate(self, df: pd.DataFrame, ticker: str) -> list[Signal]:
        if df.empty or len(df) < 210:
            return []

        last = df.iloc[-1]
        prev = df.iloc[-2]
        for col in ("ema20", "sma50", "sma200", "vol_sma20"):
            if pd.isna(last.get(col)) or pd.isna(prev.get(col)):
                return []

        close_t = float(last["close"])
        ema20_t = float(last["ema20"])
        sma50_t = float(last["sma50"])
        sma200_t = float(last["sma200"])
        vol_sma20_t = float(last["vol_sma20"])
        vol_t = float(last["volume"])

        # Trend filter: proper uptrend stack.
        if not (close_t > sma50_t > sma200_t):
            return []

        # Pullback detection: at least one of the last 5 bars touched/neared 20 EMA from above.
        last5 = df.tail(5)
        touched = bool((last5["low"] <= last5["ema20"] * 1.01).any())
        if not touched:
            return []

        # Volume pattern: pullback bars (last 5) had declining vol vs 20d avg;
        # current bar shows a bounce volume spike.
        avg_vol_5 = float(last5["volume"].mean())
        if not (avg_vol_5 < vol_sma20_t):
            return []
        if not (vol_t > vol_sma20_t):
            return []

        # Bounce confirmation on the current bar.
        if not (close_t > float(prev["close"])):
            return []
        if not (close_t > ema20_t):
            return []

        entry = close_t
        struct_stop = float(df["low"].tail(5).min())
        stop = floor_stop_with_atr(
            entry, struct_stop, last.get("atr14"), mult=2.0, direction="LONG"
        )
        if stop >= entry:
            return []
        # Honor the min-RR rule (was 1.5R); threshold lives in risk_levels.MIN_RR.
        target = min_rr_target(entry, stop)

        vol_ratio = vol_t / vol_sma20_t if vol_sma20_t > 0 else 0.0
        confirmations = [
            "Strong uptrend (close > SMA50 > SMA200)",
            "Pullback to 20 EMA on declining volume",
            f"Bounce confirmed with volume {vol_ratio:.2f}x > 20d avg",
        ]

        confidence = min(0.9, 0.7 + 0.05 * (len(confirmations) - 3))
        bar_date = last.name.date() if hasattr(last.name, "date") else last.name

        return [
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
        ]
