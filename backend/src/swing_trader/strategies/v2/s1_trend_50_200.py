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

from ...engine.risk_levels import atr_stop, min_rr_target
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

        # Continuous score (only when fired): magnitude of trend, not just boolean pass.
        if fired:
            # ATR-normalized extension above SMA50 (cap 8 ATRs => 1.0; "genuinely extended")
            ext = (close - sma50) / atr if atr == atr and atr > 0 else 0.0
            ext_part = max(0.0, min(1.0, ext / 8.0))
            # Percentage gap of SMA50 above SMA200 (cap 20% => 1.0; deeply established uptrend)
            gap_pct = (sma50 - sma200) / sma200 if sma200 > 0 else 0.0
            gap_part = max(0.0, min(1.0, gap_pct / 0.20))
            # Floor 0.4 (we passed all three legs), then weighted strength.
            score = round(0.4 + 0.35 * ext_part + 0.25 * gap_part, 4)
        else:
            score = passed_count / 3.0

        entry = close
        stop = atr_stop(entry, atr, mult=2.0)
        target = min_rr_target(entry, stop, rr=2.5)

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
