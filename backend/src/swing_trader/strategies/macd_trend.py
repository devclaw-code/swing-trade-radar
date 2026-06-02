"""MACD crossover with SMA200 trend filter swing strategy."""

from __future__ import annotations

import pandas as pd

from ..engine.risk_levels import floor_stop_with_atr
from .base_strategy import BaseStrategy, Signal, default_target


class MacdTrendStrategy(BaseStrategy):
    name = "macd_trend"

    def generate(self, df: pd.DataFrame, ticker: str) -> list[Signal]:
        if df.empty or len(df) < 210:
            return []
        last = df.iloc[-1]
        prev = df.iloc[-2]
        for col in ("macd", "macd_signal", "sma200", "atr14"):
            if pd.isna(last.get(col)) or pd.isna(prev.get(col)):
                return []

        signals: list[Signal] = []

        cross_up = prev["macd"] <= prev["macd_signal"] and last["macd"] > last["macd_signal"]
        cross_down = prev["macd"] >= prev["macd_signal"] and last["macd"] < last["macd_signal"]

        entry = float(last["close"])
        bar_date = last.name.date() if hasattr(last.name, "date") else last.name

        if cross_up and entry > float(last["sma200"]):
            atr = float(last["atr14"])
            stop = floor_stop_with_atr(
                entry, float(df["low"].tail(10).min()), atr, mult=2.0, direction="LONG"
            )
            if stop >= entry:
                return []
            confirmations = [
                "MACD crossed above signal",
                "Close > SMA200 (uptrend)",
            ]
            target = default_target(entry, stop, "LONG")
            confidence = min(0.85, 0.65 + 0.05 * (len(confirmations) - 2))
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
        elif cross_down and entry < float(last["sma200"]):
            atr = float(last["atr14"])
            stop = floor_stop_with_atr(
                entry, float(df["high"].tail(10).max()), atr, mult=2.0, direction="SHORT"
            )
            if stop <= entry:
                return []
            confirmations = [
                "MACD crossed below signal",
                "Close < SMA200 (downtrend)",
            ]
            target = default_target(entry, stop, "SHORT")
            confidence = min(0.85, 0.65 + 0.05 * (len(confirmations) - 2))
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
