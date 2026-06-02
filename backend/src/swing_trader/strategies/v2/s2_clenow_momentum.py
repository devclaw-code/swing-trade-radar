"""S2 — Clenow Time-Series Momentum (cross-sectional).

Reference: research/01-classic-strategies.md §19 (★ Clenow Time-Series Momentum).
Also: research/00-INDEX.md §C Tier-A row 2, PHASE2_PLAN.md §4.S2.

Per-ticker score:
    1. Fit linear regression on log(close) over last 90 trading days.
    2. annual_return = exp(slope * 252) - 1
    3. score = annual_return * R²   (R² penalises noisy slopes)

Filter (per ticker):
    - close > SMA100 (uptrend)
    - no day in last 90d with abs daily return > 15%  (gap filter)

Cross-sectional fire rule:
    - basket_data must contain a precomputed mapping ``"clenow_scores"`` (dict[ticker → score])
      OR strategy will compute scores from the basket dfs directly.
    - Fire BUY for tickers in the top quintile of the basket.
"""

from __future__ import annotations

import math
from typing import ClassVar

import numpy as np
import pandas as pd
import scipy.stats as sps

from ...engine.risk_levels import atr_stop, min_rr_target
from ...schemas import EvidenceItem
from .base import StrategyResult, V2Strategy

WINDOW = 90
GAP_THRESHOLD = 0.15
TOP_QUINTILE = 0.20


def _clenow_score(close: pd.Series) -> tuple[float, float, float]:
    """Return (score, annualized_slope, r_squared). NaN if insufficient data."""
    s = close.dropna().tail(WINDOW)
    if len(s) < WINDOW:
        return float("nan"), float("nan"), float("nan")
    y = np.log(s.values)
    x = np.arange(len(y))
    slope, _intercept, r, _p, _se = sps.linregress(x, y)
    annual = math.exp(slope * 252) - 1.0
    r2 = float(r) ** 2
    return float(annual * r2), float(annual), r2


def compute_basket_scores(basket: dict[str, pd.DataFrame]) -> dict[str, float]:
    """Compute Clenow scores for an entire basket. Skips tickers without enough data."""
    out: dict[str, float] = {}
    for t, df in basket.items():
        if df is None or df.empty or "close" not in df.columns:
            continue
        score, _annual, _r2 = _clenow_score(df["close"])
        if not math.isnan(score):
            out[t] = score
    return out


class ClenowMomentumStrategy(V2Strategy):
    name: ClassVar[str] = "S2_clenow_momentum"
    doc_refs: ClassVar[list[str]] = ["research/01 §19", "research/00-INDEX.md §C"]
    counter_argument_keys: ClassVar[list[str]] = ["momentum_crash_risk", "concentration_risk_mag7"]
    risk_tier: ClassVar[str] = "LOW"

    def evaluate(
        self,
        df: pd.DataFrame,
        ticker: str,
        basket_data: dict[str, pd.DataFrame] | None = None,
    ) -> StrategyResult:
        if df.empty or len(df) < WINDOW:
            return StrategyResult(self.name, fired=False, score=0.0, doc_refs=list(self.doc_refs))

        # Gap filter
        rets = df["close"].pct_change().tail(WINDOW)
        worst_gap = float(rets.abs().max() or 0.0)
        gap_ok = worst_gap < GAP_THRESHOLD

        # Trend filter
        last = df.iloc[-1]
        close = float(last["close"])
        sma100 = float(df["close"].rolling(100).mean().iloc[-1])
        trend_ok = close > sma100

        # Score
        score_val, annual_slope, r2 = _clenow_score(df["close"])

        # Cross-sectional ranking — derive from basket_data if available.
        rank_pct = float("nan")
        n_basket = 0
        if basket_data:
            scores = (
                basket_data.get("clenow_scores")
                if isinstance(basket_data.get("clenow_scores"), dict)
                else compute_basket_scores(
                    {k: v for k, v in basket_data.items() if isinstance(v, pd.DataFrame)}
                )
            )
            if scores and ticker in scores and not math.isnan(scores[ticker]):
                vals = sorted(scores.values(), reverse=True)
                n_basket = len(vals)
                rank = vals.index(scores[ticker]) + 1
                rank_pct = rank / n_basket

        in_top_quintile = (
            rank_pct == rank_pct  # not nan
            and rank_pct <= TOP_QUINTILE
        )

        fired = bool(gap_ok and trend_ok and in_top_quintile)

        # Score for the synthesizer: combine quintile + trend + gap-clean
        composite = 0.0
        if not math.isnan(rank_pct):
            composite += max(0.0, (1.0 - rank_pct)) * 0.6
        if trend_ok:
            composite += 0.2
        if gap_ok:
            composite += 0.2

        evidence: list[EvidenceItem] = [
            EvidenceItem(
                factor=f"Annualised slope × R² = {score_val:.3f}" if not math.isnan(score_val) else "Score N/A",
                value=round(score_val, 4) if not math.isnan(score_val) else None,
                weight=0.40,
                passed=not math.isnan(score_val),
                note=f"slope_ann={annual_slope:.2%}, R²={r2:.2f}" if not math.isnan(r2) else "insufficient data",
            ),
            EvidenceItem(
                factor=f"Cross-sectional rank top {rank_pct:.0%}" if not math.isnan(rank_pct) else "No basket data",
                value=round(rank_pct, 3) if not math.isnan(rank_pct) else None,
                weight=0.30,
                passed=in_top_quintile,
                note=(
                    f"in top quintile of {n_basket} names" if in_top_quintile
                    else "outside top quintile"
                ),
            ),
            EvidenceItem(
                factor="Trend filter (close > SMA100)",
                value=round(close - sma100, 2),
                weight=0.15,
                passed=trend_ok,
                note="trend up" if trend_ok else "below SMA100",
            ),
            EvidenceItem(
                factor=f"Gap filter (max |day ret| 90d = {worst_gap:.1%})",
                value=round(worst_gap, 4),
                weight=0.15,
                passed=gap_ok,
                note="no >15% gaps" if gap_ok else "had a >15% gap day — exclude",
            ),
        ]

        atr = float(last.get("atr14", float("nan")))
        stop = atr_stop(close, atr, mult=2.5)  # Clenow-style wider trend stop
        # Momentum runs are open-ended: take the further of a 20% chunk or the
        # min-RR target, so a tight ATR stop still yields a >=2.5R objective.
        target = max(round(close * 1.20, 2), min_rr_target(close, stop))

        invalidation = [
            "Drops out of top quintile on weekly re-rank",
            f"Close below stop ({stop:.2f})",
            "Index (SPY) drops below 200-SMA",
        ]
        headline = (
            f"{ticker}: top-quintile Clenow momentum — ride the trend."
            if fired
            else f"{ticker}: not in momentum top quintile."
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
            max_hold_days=60,
            risk_tier=self.risk_tier,
        )
