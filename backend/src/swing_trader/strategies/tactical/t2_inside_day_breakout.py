"""T2 \u2014 Inside Day Breakout (tactical breakout).

Reference: tactical short-term setups spec (Setup B).

Regime: Price > SMA(200).
Fire BUY (buy-stop) if (all):
    - Inside day: current High < prev High AND current Low > prev Low,
    - EMA(10) sloping up: EMA10[t] > EMA10[t-1].
Entry: buy-stop at (Inside Day High + $0.10).
Stop:  exactly (Inside Day Low - $0.05)  [structural, NOT the ATR model].
Target: priced to a minimum 2.0 R:R off the structural stop.

ATR is still reported (``volatility_atr``) for the UI / position sizing, and is
used as a floor so the structural stop can't sit inside the noise band on a
high-volatility name. Edge cases (short history, NaN EMA/ATR) degrade cleanly.
"""

from __future__ import annotations

from typing import ClassVar

import pandas as pd

from ...engine.atr import compute_atr14
from ...engine.risk_levels import floor_stop_with_atr, min_rr_target, reward_risk
from ...schemas import EvidenceItem
from .base import TacticalResult, TacticalStrategy

ENTRY_BUFFER = 0.10   # buy-stop above inside-day high
STOP_BUFFER = 0.05    # stop below inside-day low
EMA_LEN = 10
MIN_RR_BREAKOUT = 2.0
MIN_BARS = 205


class InsideDayBreakoutStrategy(TacticalStrategy):
    setup_id: ClassVar[str] = "T2_inside_day_breakout"
    setup_name: ClassVar[str] = "Inside Day Breakout"
    risk_tier: ClassVar[str] = "MEDIUM"
    max_hold_days: ClassVar[int] = 5

    def evaluate(self, df: pd.DataFrame, ticker: str) -> TacticalResult:
        try:
            if df is None or df.empty or len(df) < MIN_BARS:
                return self._not_fired(headline=f"{ticker}: insufficient history.")

            cur = df.iloc[-1]
            prev = df.iloc[-2]
            close = float(cur["close"])
            cur_high = float(cur["high"])
            cur_low = float(cur["low"])
            prev_high = float(prev["high"])
            prev_low = float(prev["low"])
            sma200 = float(cur.get("sma200", float("nan")))

            if any(v != v for v in (cur_high, cur_low, prev_high, prev_low)):
                return self._not_fired(headline=f"{ticker}: NaN OHLC bar.")

            # EMA(10) slope \u2014 enrich() doesn't add ema10, compute it.
            ema10 = df["close"].astype(float).ewm(span=EMA_LEN, adjust=False).mean()
            ema_now = float(ema10.iloc[-1])
            ema_prev = float(ema10.iloc[-2])

            c_regime = self._regime_ok(close, sma200)
            c_inside = (cur_high < prev_high) and (cur_low > prev_low)
            c_ema_up = ema_now > ema_prev

            evidence = [
                EvidenceItem(
                    factor=f"Close > SMA200 ({sma200:.2f})",
                    value=round(close - sma200, 2) if sma200 == sma200 else None,
                    weight=0.30,
                    passed=c_regime,
                    note="uptrend regime intact" if c_regime else "below SMA200 \u2014 regime fails",
                ),
                EvidenceItem(
                    factor="Inside day (H<prevH, L>prevL)",
                    value=None,
                    weight=0.40,
                    passed=c_inside,
                    note="coiled inside-day compression" if c_inside else "not an inside day",
                ),
                EvidenceItem(
                    factor="EMA(10) sloping up",
                    value=round(ema_now - ema_prev, 4),
                    weight=0.30,
                    passed=c_ema_up,
                    note="short-term trend rising" if c_ema_up else "EMA10 flat/down",
                ),
            ]

            fired = c_regime and c_inside and c_ema_up
            passes = sum(1 for e in evidence if e.passed)
            score = round(0.7 if fired else passes / len(evidence), 4)

            if not fired:
                return TacticalResult(
                    setup_id=self.setup_id,
                    setup_name=self.setup_name,
                    fired=False,
                    score=score,
                    evidence=evidence,
                    headline=f"{ticker}: inside-day breakout incomplete ({passes}/3).",
                    risk_tier=self.risk_tier,
                    max_hold_days=self.max_hold_days,
                )

            atr = compute_atr14(df)

            # Structural levels off the inside (current) day.
            entry = round(cur_high + ENTRY_BUFFER, 2)
            raw_stop = round(cur_low - STOP_BUFFER, 2)
            # Floor the structural stop with ATR so it isn't tighter than 1.5xATR.
            stop = floor_stop_with_atr(entry, raw_stop, atr, mult=1.5)
            target = min_rr_target(entry, stop, rr=MIN_RR_BREAKOUT)
            rr = reward_risk(entry, stop, target)

            return TacticalResult(
                setup_id=self.setup_id,
                setup_name=self.setup_name,
                fired=True,
                score=score,
                evidence=evidence,
                invalidation_conditions=[
                    f"No fill if price never tags buy-stop {entry:.2f}",
                    f"Stop at {stop:.2f} (inside-day low - $0.05, ATR-floored)",
                    f"Exit after {self.max_hold_days} trading days if target not hit",
                ],
                headline=f"{ticker}: inside-day compression breakout above {entry:.2f} with EMA10 rising.",
                entry_price=entry,
                entry_type="stop",
                stop_price=stop,
                target_price=target,
                max_hold_days=self.max_hold_days,
                volatility_atr=atr,
                rr_realized=round(rr, 3) if rr == rr else None,
                risk_tier=self.risk_tier,
            )
        except Exception:
            return self._not_fired(headline=f"{ticker}: evaluation error \u2014 skipped.")
