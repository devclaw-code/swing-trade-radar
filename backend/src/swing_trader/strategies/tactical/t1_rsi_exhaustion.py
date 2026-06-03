"""T1 \u2014 3-Day RSI Exhaustion (tactical mean-reversion).

Reference: tactical short-term setups spec (Setup A).

Regime: Price > SMA(200).
Fire BUY if (all):
    - close lower for 3 consecutive days (close[t] < close[t-1] < close[t-2] < close[t-3]),
    - RSI(4) strictly below 30.
Entry: closing price on the day RSI(4) < 30 is met.
Exit / invalidation (informational \u2014 enforced by the position manager / backtester):
    - first profitable close, OR
    - RSI(4) crosses back above 55.

Risk geometry flows through the dynamic-ATR model (1.5 * ATR stop, 2.0 R:R).
Edge cases (short history, NaN RSI/ATR) degrade to "not fired" cleanly.
"""

from __future__ import annotations

from typing import ClassVar

import pandas as pd
import pandas_ta_classic as ta

from ...engine.atr import compute_atr14
from ...engine.risk_levels import dynamic_atr_trade
from ...schemas import EvidenceItem
from .base import TacticalResult, TacticalStrategy

RSI_LEN = 4
RSI_OVERSOLD = 30.0
RSI_EXIT = 55.0
DOWN_DAYS = 3
MIN_BARS = 205  # need SMA200 + a few RSI bars


class RsiExhaustionStrategy(TacticalStrategy):
    setup_id: ClassVar[str] = "T1_rsi_exhaustion"
    setup_name: ClassVar[str] = "3-Day RSI Exhaustion"
    risk_tier: ClassVar[str] = "MEDIUM"
    max_hold_days: ClassVar[int] = 5

    def evaluate(self, df: pd.DataFrame, ticker: str) -> TacticalResult:
        try:
            if df is None or df.empty or len(df) < MIN_BARS:
                return self._not_fired(headline=f"{ticker}: insufficient history.")

            closes = df["close"].astype(float)
            last = df.iloc[-1]
            close = float(last["close"])
            sma200 = float(last.get("sma200", float("nan")))

            # RSI(4) \u2014 enrich() only adds RSI(14), compute on the fly.
            rsi_series = ta.rsi(closes, length=RSI_LEN)
            if rsi_series is None or rsi_series.empty:
                return self._not_fired(headline=f"{ticker}: RSI unavailable.")
            rsi4 = float(rsi_series.iloc[-1])
            if rsi4 != rsi4:  # NaN
                return self._not_fired(headline=f"{ticker}: RSI NaN.")

            # 3 consecutive lower closes: close[t] < c[t-1] < c[t-2] < c[t-3].
            recent = closes.iloc[-(DOWN_DAYS + 1):].tolist()
            if len(recent) < DOWN_DAYS + 1 or any(v != v for v in recent):
                return self._not_fired(headline=f"{ticker}: incomplete recent closes.")
            c_three_down = all(recent[i] < recent[i - 1] for i in range(1, len(recent)))

            c_regime = self._regime_ok(close, sma200)
            c_rsi = rsi4 < RSI_OVERSOLD

            evidence = [
                EvidenceItem(
                    factor=f"Close > SMA200 ({sma200:.2f})",
                    value=round(close - sma200, 2) if sma200 == sma200 else None,
                    weight=0.30,
                    passed=c_regime,
                    note="uptrend regime intact" if c_regime else "below SMA200 \u2014 regime fails",
                ),
                EvidenceItem(
                    factor="3 consecutive lower closes",
                    value=None,
                    weight=0.35,
                    passed=c_three_down,
                    note="3-day pullback" if c_three_down else "no 3-day down streak",
                ),
                EvidenceItem(
                    factor=f"RSI(4) = {rsi4:.1f} < {RSI_OVERSOLD:.0f}",
                    value=round(rsi4, 2),
                    weight=0.35,
                    passed=c_rsi,
                    note="short-term exhaustion" if c_rsi else "not oversold enough",
                ),
            ]

            fired = c_regime and c_three_down and c_rsi
            passes = sum(1 for e in evidence if e.passed)
            if fired:
                # Deeper RSI -> stronger edge. RSI 0 -> 1.0, RSI 30 -> 0.5.
                rsi_strength = max(0.0, min(1.0, (RSI_OVERSOLD - rsi4) / RSI_OVERSOLD))
                score = round(0.5 + 0.5 * rsi_strength, 4)
            else:
                score = round(passes / len(evidence), 4)

            if not fired:
                return TacticalResult(
                    setup_id=self.setup_id,
                    setup_name=self.setup_name,
                    fired=False,
                    score=score,
                    evidence=evidence,
                    headline=f"{ticker}: RSI exhaustion incomplete ({passes}/3).",
                    risk_tier=self.risk_tier,
                    max_hold_days=self.max_hold_days,
                )

            atr = compute_atr14(df)
            plan = dynamic_atr_trade(close, atr)

            return TacticalResult(
                setup_id=self.setup_id,
                setup_name=self.setup_name,
                fired=True,
                score=score,
                evidence=evidence,
                invalidation_conditions=[
                    "Exit on first profitable close",
                    f"Exit when RSI(4) crosses above {RSI_EXIT:.0f}",
                    f"Hard stop at {plan['stop_loss']:.2f} (1.5\u00d7ATR)",
                ],
                headline=f"{ticker}: 3-day RSI({RSI_LEN}) exhaustion in an uptrend \u2014 mean-reversion bounce.",
                entry_price=round(close, 2),
                entry_type="market",
                stop_price=plan["stop_loss"],
                target_price=plan["take_profit"],
                max_hold_days=self.max_hold_days,
                volatility_atr=atr,
                rr_realized=plan["rr_realized"],
                risk_tier=self.risk_tier,
            )
        except Exception:
            # Any unexpected failure -> drop the ticker cleanly.
            return self._not_fired(headline=f"{ticker}: evaluation error \u2014 skipped.")
