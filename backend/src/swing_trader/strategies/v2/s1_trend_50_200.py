"""S1 — Trend 50/200 SMA + regime filter (Golden Cross family).

Reference: research/01-classic-strategies.md §3 (★ SMA 50/200 Golden Cross — Deep Dive).
Also: research/00-INDEX.md §C Tier-A row 1, PHASE2_PLAN.md §4.S1.

Rules (long-only):
    BUY  if  close > SMA50 > SMA200  AND  SPY > SMA200 (regime favourable)
    WATCH if  any one of the three legs fails (close>SMA50, SMA50>SMA200, regime)
    No-fire otherwise.

    Stop:   2× ATR(14) below entry.
    Target: 4× ATR(14) above entry (≈ 2R, trail-with-chandelier in production).
    Hold:   30 trading days max for swing scope (research notes 60-180d for full position trade).
"""

from __future__ import annotations

from typing import ClassVar

import pandas as pd

from ...schemas import EvidenceItem
from .base import StrategyResult, V2Strategy


class TrendFiftyTwoHundredStrategy(V2Strategy):
    name: ClassVar[str] = "S1_trend_50_200"
    doc_refs: ClassVar[list[str]] = ["research/01 §3", "research/00-INDEX.md §C"]
    counter_argument_keys: ClassVar[list[str]] = ["trend_late_entry", "trend_whipsaw"]
    risk_tier: ClassVar[str] = "LOW"

    def evaluate(
        self,
        df: pd.DataFrame,
        ticker: str,
        basket_data: dict[str, pd.DataFrame] | None = None,
    ) -> StrategyResult:
        if df.empty or len(df) < 200:
            return StrategyResult(self.name, fired=False, score=0.0, doc_refs=list(self.doc_refs))

        last = df.iloc[-1]
        close = float(last["close"])
        sma50 = float(last.get("sma50", float("nan")))
        sma200 = float(last.get("sma200", float("nan")))
        atr = float(last.get("atr14", float("nan")))

        # Regime check — basket_data may carry SPY/QQQ enriched dfs.
        spy_above = True
        spy_note = "regime check skipped (no SPY data)"
        if basket_data and "SPY" in basket_data and not basket_data["SPY"].empty:
            spy_df = basket_data["SPY"]
            spy_last = spy_df.iloc[-1]
            spy_above = float(spy_last["close"]) > float(spy_last.get("sma200", 0.0))
            spy_note = "SPY > 200SMA" if spy_above else "SPY < 200SMA (risk-off)"

        c1 = close > sma50  # short-term trend
        c2 = sma50 > sma200  # medium > long (golden-cross intact)
        c3 = spy_above  # macro regime

        evidence: list[EvidenceItem] = [
            EvidenceItem(
                factor=f"Close ({close:.2f}) > SMA50 ({sma50:.2f})",
                value=round(close - sma50, 2),
                weight=0.25,
                passed=c1,
                note="short-term momentum aligned" if c1 else "below SMA50 — caution",
            ),
            EvidenceItem(
                factor=f"SMA50 ({sma50:.2f}) > SMA200 ({sma200:.2f})",
                value=round(sma50 - sma200, 2),
                weight=0.45,
                passed=c2,
                note="golden cross intact" if c2 else "death-cross territory",
            ),
            EvidenceItem(
                factor="SPY regime filter",
                value=None,
                weight=0.30,
                passed=c3,
                note=spy_note,
            ),
        ]

        passed_count = sum(1 for c in (c1, c2, c3) if c)
        fired = passed_count == 3
        score = passed_count / 3.0

        entry = close
        stop = round(close - 2.0 * atr, 2) if atr == atr else round(close * 0.95, 2)
        target = round(close + 4.0 * atr, 2) if atr == atr else round(close * 1.10, 2)

        invalidation = [
            f"Close below SMA200 ({sma200:.2f})",
            f"Close below stop ({stop:.2f})",
            "SPY closes below its 200-SMA",
        ]

        headline = (
            f"{ticker}: 50/200 trend + regime aligned — bull continuation setup."
            if fired
            else f"{ticker}: trend partially aligned ({passed_count}/3); not a fire."
        )

        return StrategyResult(
            strategy_name=self.name,
            fired=fired,
            score=score,
            evidence=evidence,
            invalidation_conditions=invalidation,
            counter_argument_keys=list(self.counter_argument_keys),
            doc_refs=list(self.doc_refs),
            headline=headline,
            entry_price=round(entry, 2),
            stop_price=stop,
            target_price=target,
            max_hold_days=30,
            risk_tier=self.risk_tier,
        )
