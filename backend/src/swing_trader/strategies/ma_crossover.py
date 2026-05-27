"""9 EMA / 21 EMA crossover swing strategy on daily bars."""

from __future__ import annotations

import pandas as pd

from .base_strategy import BaseStrategy, Signal, default_target


class MaCrossoverStrategy(BaseStrategy):
    name = "ma_crossover"

    def generate(self, df: pd.DataFrame, ticker: str) -> list[Signal]:
        if df.empty or len(df) < 25:
            return []
        last = df.iloc[-1]
        prev = df.iloc[-2]
        for col in ("ema9", "ema21", "atr14", "sma50"):
            if pd.isna(last.get(col)) or pd.isna(prev.get(col)):
                return []

        signals: list[Signal] = []

        cross_up = prev["ema9"] <= prev["ema21"] and last["ema9"] > last["ema21"]
        cross_down = prev["ema9"] >= prev["ema21"] and last["ema9"] < last["ema21"]

        entry = float(last["close"])
        atr = float(last["atr14"])
        bar_date = last.name.date() if hasattr(last.name, "date") else last.name

        if cross_up:
            stop = float(last["ema21"]) - atr
            if stop >= entry:  # degenerate
                return []
            confirmations = ["EMA9 crossed above EMA21"]
            if entry > last["sma50"]:
                confirmations.append("Price > SMA50 (uptrend filter)")
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
                    confidence=0.6 + 0.1 * (len(confirmations) - 1),
                    bar_date=bar_date,
                )
            )
        elif cross_down:
            stop = float(last["ema21"]) + atr
            if stop <= entry:
                return []
            confirmations = ["EMA9 crossed below EMA21"]
            if entry < last["sma50"]:
                confirmations.append("Price < SMA50 (downtrend filter)")
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
                    confidence=0.6 + 0.1 * (len(confirmations) - 1),
                    bar_date=bar_date,
                )
            )
        return signals
