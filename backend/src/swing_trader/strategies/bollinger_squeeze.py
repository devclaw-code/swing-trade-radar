"""Bollinger Band squeeze + breakout swing strategy."""

from __future__ import annotations

import pandas as pd

from .base_strategy import BaseStrategy, Signal, default_target


class BollingerSqueezeStrategy(BaseStrategy):
    name = "bollinger_squeeze"

    def generate(self, df: pd.DataFrame, ticker: str) -> list[Signal]:
        if df.empty or len(df) < 30:
            return []
        last = df.iloc[-1]
        prev = df.iloc[-2]
        required = ("bb_upper", "bb_lower", "bb_mid", "bb_bandwidth", "bb_bandwidth_sma20")
        for col in required:
            if pd.isna(last.get(col)) or pd.isna(prev.get(col)):
                return []

        # Squeeze: bandwidth on the prior bar was below its 20-bar average.
        squeeze = prev["bb_bandwidth"] < prev["bb_bandwidth_sma20"]
        if not squeeze:
            return []

        entry = float(last["close"])
        bb_mid = float(last["bb_mid"])
        bar_date = last.name.date() if hasattr(last.name, "date") else last.name

        signals: list[Signal] = []

        breakout_up = entry > float(last["bb_upper"])
        breakout_down = entry < float(last["bb_lower"])

        if breakout_up:
            stop = bb_mid
            if stop >= entry:
                return []
            confirmations = [
                "Bollinger squeeze (bandwidth below 20d avg)",
                "Close broke above upper band",
            ]
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
                    confidence=min(0.8, 0.6 + 0.05 * (len(confirmations) - 1)),
                    bar_date=bar_date,
                )
            )
        elif breakout_down:
            stop = bb_mid
            if stop <= entry:
                return []
            confirmations = [
                "Bollinger squeeze (bandwidth below 20d avg)",
                "Close broke below lower band",
            ]
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
                    confidence=min(0.8, 0.6 + 0.05 * (len(confirmations) - 1)),
                    bar_date=bar_date,
                )
            )
        return signals
