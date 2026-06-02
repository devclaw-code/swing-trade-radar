"""S4 — Minervini VCP (Volatility Contraction Pattern) heuristic scorer.

Reference: research/01-classic-strategies.md §15 (★ Minervini VCP — Deep Dive).
Also: PHASE2_PLAN.md §4.S4 — surface as scored signal, not hard fire.

Approach (heuristic — VCP is discretionary in the original):
    Component scores (each 0..1):
      1. Trend template (Minervini's 6-leg test)             weight 0.35
      2. Volatility contraction: ATR(20) / ATR(20)_60-mean   weight 0.30
         (lower is better; <0.7 → full credit)
      3. Volume dry-up: vol_sma20 / vol_sma60                 weight 0.15
      4. Breakout signal: close > 20d high & volume >= 1.5x   weight 0.20

    Final score = weighted sum (0..1).
    Fire only when score > 0.70 AND breakout component is true.
"""

from __future__ import annotations

from typing import ClassVar

import pandas as pd

from ...engine.risk_levels import floor_stop_with_atr
from ...schemas import EvidenceItem
from .base import StrategyResult, V2Strategy

FIRE_THRESHOLD = 0.70
CONTRACTION_FULL_CREDIT_RATIO = 0.70


def _contraction_range() -> float:
    if not 0.0 < CONTRACTION_FULL_CREDIT_RATIO < 1.0:
        raise ValueError("CONTRACTION_FULL_CREDIT_RATIO must be between 0 and 1 (exclusive)")
    return 1.0 - CONTRACTION_FULL_CREDIT_RATIO


def _trend_template_score(df: pd.DataFrame) -> tuple[float, dict[str, bool]]:
    """Return (score 0..1, breakdown dict). Needs >=200 bars."""
    if len(df) < 252:
        return 0.0, {}
    last = df.iloc[-1]
    close = float(last["close"])
    ma50 = float(last.get("sma50", float("nan")))
    ma200 = float(last.get("sma200", float("nan")))
    ma150 = float(df["close"].rolling(150).mean().iloc[-1])
    hi52 = float(df["high"].rolling(252).max().iloc[-1])
    lo52 = float(df["low"].rolling(252).min().iloc[-1])

    legs = {
        "close>MA150": close > ma150,
        "close>MA200": close > ma200,
        "MA50>MA150": ma50 > ma150,
        "MA150>MA200": ma150 > ma200,
        "close>MA50": close > ma50,
        "close>1.30*lo52": close > lo52 * 1.30,
        "close>0.75*hi52": close > hi52 * 0.75,
    }
    score = sum(1 for v in legs.values() if v) / len(legs)
    return score, legs


class MinerviniVcpStrategy(V2Strategy):
    name: ClassVar[str] = "S4_minervini_vcp"
    doc_refs: ClassVar[list[str]] = ["research/01 §15", "research/00-INDEX.md §C"]
    counter_argument_keys: ClassVar[list[str]] = ["vcp_failed_breakouts", "discretionary_pattern"]
    risk_tier: ClassVar[str] = "MEDIUM"

    def evaluate(
        self,
        df: pd.DataFrame,
        ticker: str,
        basket_data: dict[str, pd.DataFrame] | None = None,
    ) -> StrategyResult:
        if df.empty or len(df) < 252:
            return StrategyResult(self.name, fired=False, score=0.0, doc_refs=list(self.doc_refs))

        last = df.iloc[-1]
        close = float(last["close"])

        # 1. Trend template
        tt_score, _legs = _trend_template_score(df)

        # 2. Volatility contraction (ATR ratio)
        high_low_range_sma20 = (
            df["high"].combine(df["low"], lambda high, low: high - low).rolling(20).mean()
        )
        # Use ATR14 already present, fall back to true-range proxy
        atr_now = float(df.get("atr14", high_low_range_sma20).iloc[-1])
        atr_long = float(df.get("atr14", high_low_range_sma20).rolling(60).mean().iloc[-1])
        ratio = atr_now / atr_long if atr_long and atr_long > 0 else 1.0
        # ratio <= 0.7 gets full credit after clipping; ratio >= 1.0 gets zero.
        contraction_score = max(0.0, min(1.0, (1.0 - ratio) / _contraction_range()))

        # 3. Volume dry-up
        vol_sma20 = float(df["volume"].rolling(20).mean().iloc[-1])
        vol_sma60 = float(df["volume"].rolling(60).mean().iloc[-1])
        vol_ratio = vol_sma20 / vol_sma60 if vol_sma60 > 0 else 1.0
        vdu_score = max(0.0, min(1.0, (1.0 - vol_ratio) / 0.30))

        # 4. Breakout
        prev_high = float(df["high"].iloc[-21:-1].max())
        vol_today = float(last["volume"])
        vol_avg = float(df["volume"].rolling(50).mean().iloc[-1])
        breakout = close > prev_high and vol_today > 1.5 * vol_avg
        breakout_score = 1.0 if breakout else 0.0

        composite = (
            0.35 * tt_score
            + 0.30 * contraction_score
            + 0.15 * vdu_score
            + 0.20 * breakout_score
        )

        fired = composite > FIRE_THRESHOLD and breakout

        evidence: list[EvidenceItem] = [
            EvidenceItem(
                factor=f"Trend-template legs passed: {tt_score:.0%}",
                value=round(tt_score, 2),
                weight=0.35,
                passed=tt_score >= 0.85,
                note="Minervini 6-leg trend template",
            ),
            EvidenceItem(
                factor=f"Volatility contraction: ATR ratio {ratio:.2f}",
                value=round(ratio, 3),
                weight=0.30,
                passed=ratio < 0.85,
                note="<0.7 = strong contraction" if ratio < 0.7 else "modest tightening",
            ),
            EvidenceItem(
                factor=f"Volume dry-up: 20d/60d = {vol_ratio:.2f}",
                value=round(vol_ratio, 3),
                weight=0.15,
                passed=vol_ratio < 0.9,
                note="VDU good" if vol_ratio < 0.85 else "no clear dry-up",
            ),
            EvidenceItem(
                factor=(
                    f"Breakout above 20-day high ({prev_high:.2f}) on {vol_today/vol_avg:.1f}x avg volume"
                ),
                value=round(close - prev_high, 2),
                weight=0.20,
                passed=breakout,
                note="confirmed breakout" if breakout else "no breakout today",
            ),
        ]

        # Trade plan
        # Stop just below 20-day contraction low, floored at 2x ATR; target = 2R.
        recent_low = float(df["low"].iloc[-20:].min())
        # Pivot stop, but never tighter than 2x ATR (esp. on high-vol names).
        stop = floor_stop_with_atr(close, recent_low * 0.99, atr_now, mult=2.0, direction="LONG")
        risk = max(0.01, close - stop)
        target = round(close + 2.0 * risk, 2)

        invalidation = [
            f"Close below recent contraction low ({stop:.2f})",
            "Failed breakout: closes back below pivot within 3 days",
            "Earnings inside breakout window",
        ]
        headline = (
            f"{ticker}: VCP-likely breakout with volume confirmation."
            if fired
            else f"{ticker}: VCP score {composite:.2f} — needs cleaner pattern."
        )

        return StrategyResult(
            strategy_name=self.name,
            fired=fired,
            score=min(1.0, composite),
            evidence=evidence,
            invalidation_conditions=invalidation,
            counter_argument_keys=list(self.counter_argument_keys),
            doc_refs=list(self.doc_refs),
            headline=headline,
            entry_price=round(close, 2),
            stop_price=stop,
            target_price=target,
            max_hold_days=30,
            risk_tier=self.risk_tier,
        )
