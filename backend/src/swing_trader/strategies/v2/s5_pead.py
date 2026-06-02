"""S5 — Post-Earnings Announcement Drift (PEAD).

Reference: research/00-INDEX.md §C Tier-B row 3, PHASE2_PLAN.md §4.S5,
research/03-modern-quant.md §5 (PEAD survives in mega-cap tech with 2-4 week drift).

Skeleton (the EPS-surprise data is not free; we approximate with a
gap-up after-earnings heuristic):

Fire BUY if:
    - Most recent earnings was within last 5 trading days.
    - Day-after-earnings open gap > +3% AND that open is in the top 1/3 of the prior 20-day range.
    - Close >= open of gap day (held the gap).
    - Close > SMA200 (trend gate).

If earnings calendar is unavailable we return a no-fire result with a TODO note.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import ClassVar

import pandas as pd

from ...schemas import EvidenceItem
from .base import StrategyResult, V2Strategy

GAP_THRESHOLD = 0.03  # 3%
RECENT_EARN_WINDOW_DAYS = 5


class PeadStrategy(V2Strategy):
    name: ClassVar[str] = "S5_pead"
    doc_refs: ClassVar[list[str]] = ["research/00-INDEX.md §C", "research/03 §5"]
    counter_argument_keys: ClassVar[list[str]] = ["pead_decay_in_largecap", "earnings_event_risk"]
    risk_tier: ClassVar[str] = "MEDIUM"

    def evaluate(
        self,
        df: pd.DataFrame,
        ticker: str,
        basket_data: dict[str, pd.DataFrame] | None = None,
    ) -> StrategyResult:
        if df.empty or len(df) < 200:
            return StrategyResult(self.name, fired=False, score=0.0, doc_refs=list(self.doc_refs))

        earnings_dates: list[date] = []
        if basket_data and isinstance(basket_data.get("earnings_dates"), dict):
            earnings_dates = list(basket_data["earnings_dates"].get(ticker, []) or [])

        last = df.iloc[-1]
        as_of = df.index[-1].date() if hasattr(df.index[-1], "date") else date.today()
        close = float(last["close"])
        sma200 = float(last.get("sma200", float("nan")))

        # Find most recent earnings within window
        recent_earn = None
        for d in earnings_dates:
            if as_of - timedelta(days=20) <= d <= as_of and (
                recent_earn is None or d > recent_earn
            ):
                recent_earn = d

        if recent_earn is None:
            evidence = [
                EvidenceItem(
                    factor="Recent earnings within 5 trading days",
                    value=None,
                    weight=1.0,
                    passed=False,
                    note=(
                        "no earnings calendar provided — TODO(devclaw): wire yfinance earnings_dates"
                        if not earnings_dates
                        else f"no earnings in last 20 calendar days (most recent shown: {earnings_dates[:3]})"
                    ),
                )
            ]
            return StrategyResult(
                strategy_name=self.name,
                fired=False,
                score=0.0,
                evidence=evidence,
                invalidation_conditions=[],
                counter_argument_keys=list(self.counter_argument_keys),
                doc_refs=list(self.doc_refs),
                headline=f"{ticker}: no PEAD setup (no recent earnings).",
                risk_tier=self.risk_tier,
            )

        # Locate earnings bar in the df
        try:
            earn_idx = df.index.get_indexer([pd.Timestamp(recent_earn)], method="nearest")[0]
        except (KeyError, ValueError):
            earn_idx = -1
        gap_pct = 0.0
        gap_open = float("nan")
        in_top_third = False
        held_gap = False

        if 0 < earn_idx < len(df) - 1:
            day_after = df.iloc[earn_idx + 1]
            prev_close = float(df.iloc[earn_idx]["close"])
            gap_open = float(day_after["open"])
            gap_pct = (gap_open - prev_close) / prev_close if prev_close else 0.0

            window20 = df.iloc[max(0, earn_idx - 19) : earn_idx + 1]
            high20 = float(window20["high"].max())
            low20 = float(window20["low"].min())
            band = high20 - low20
            in_top_third = band > 0 and (gap_open >= low20 + 2.0 * band / 3.0)
            held_gap = float(day_after["close"]) >= gap_open

        days_since = (as_of - recent_earn).days
        c_recent = days_since <= RECENT_EARN_WINDOW_DAYS
        c_gap = gap_pct >= GAP_THRESHOLD
        c_topband = in_top_third
        c_held = held_gap
        c_trend = close > sma200

        evidence = [
            EvidenceItem(
                factor=f"Earnings on {recent_earn} ({days_since}d ago)",
                value=days_since,
                weight=0.20,
                passed=c_recent,
                note="within drift window" if c_recent else "too stale for PEAD",
            ),
            EvidenceItem(
                factor=f"Gap-up after earnings = {gap_pct:.1%}",
                value=round(gap_pct, 4),
                weight=0.30,
                passed=c_gap,
                note=">3% positive gap" if c_gap else "gap insufficient",
            ),
            EvidenceItem(
                factor="Gap open in top 1/3 of 20-day range",
                value=round(gap_open, 2) if gap_open == gap_open else None,
                weight=0.20,
                passed=c_topband,
                note="strong open" if c_topband else "weak relative open",
            ),
            EvidenceItem(
                factor="Closed at/above gap open (held gap)",
                value=None,
                weight=0.15,
                passed=c_held,
                note="bulls held the gap" if c_held else "gap faded into close",
            ),
            EvidenceItem(
                factor="Trend gate: close > SMA200",
                value=round(close - sma200, 2) if sma200 == sma200 else None,
                weight=0.15,
                passed=c_trend,
                note="trend up" if c_trend else "below SMA200",
            ),
        ]
        passes = sum(1 for e in evidence if e.passed)
        score = passes / 5.0
        fired = c_recent and c_gap and c_topband and c_held and c_trend

        # Trade plan: hold 10-20 days, stop at pre-earnings close.
        prev_close_for_stop = (
            float(df.iloc[earn_idx]["close"]) if 0 < earn_idx < len(df) else round(close * 0.95, 2)
        )
        stop = round(prev_close_for_stop, 2)
        risk = max(0.01, close - stop)
        target = round(close + 2.0 * risk, 2)

        invalidation = [
            f"Close below pre-earnings close ({stop:.2f}) — gap-fill",
            "Major guidance revision",
            "Sector-wide negative shock",
        ]
        headline = (
            f"{ticker}: PEAD setup — gap-up post-earnings, held strength, drift edge applies."
            if fired
            else f"{ticker}: PEAD partial ({passes}/5)."
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
            entry_price=round(close, 2),
            stop_price=stop,
            target_price=target,
            max_hold_days=15,
            risk_tier=self.risk_tier,
        )
