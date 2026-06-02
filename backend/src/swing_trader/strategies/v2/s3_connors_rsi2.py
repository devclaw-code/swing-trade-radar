"""S3 — Connors RSI(2) Mean Reversion (regime-gated).

Reference: research/01-classic-strategies.md §8 (★ Connors RSI(2) < 10 — Deep Dive).
Also: research/00-INDEX.md §C Tier-B row 2, PHASE2_PLAN.md §4.S3.

Fire BUY if (all):
    - RSI(2) < 10
    - close > SMA(200)              (regime gate per ticker)
    - VIX < 25                      (macro regime — passed via basket_data["vix"])
    - no earnings within next 7 days (event-risk gate)

Exit:
    - close > SMA(5), OR
    - 5 trading days elapsed, OR
    - 2× ATR(14) stop hit.

If the optional basket_data fields are missing we degrade gracefully and emit a TODO
in the evidence (still allowed to fire if the per-ticker rules pass).
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import ClassVar

import pandas as pd
import pandas_ta_classic as ta

from ...engine.risk_levels import atr_stop
from ...schemas import EvidenceItem
from .base import StrategyResult, V2Strategy

RSI_THRESHOLD = 10.0
VIX_KILL = 25.0
EARNINGS_WINDOW_DAYS = 7


class ConnorsRsi2Strategy(V2Strategy):
    name: ClassVar[str] = "S3_connors_rsi2"
    doc_refs: ClassVar[list[str]] = ["research/01 §8", "research/00-INDEX.md §C"]
    counter_argument_keys: ClassVar[list[str]] = ["rsi2_edge_decay", "falling_knife_risk"]
    risk_tier: ClassVar[str] = "MEDIUM"

    def evaluate(
        self,
        df: pd.DataFrame,
        ticker: str,
        basket_data: dict[str, pd.DataFrame] | None = None,
    ) -> StrategyResult:
        if df.empty or len(df) < 200:
            return StrategyResult(self.name, fired=False, score=0.0, doc_refs=list(self.doc_refs))

        # Compute RSI(2) on the fly — enrich() only adds RSI(14).
        rsi2_series = ta.rsi(df["close"], length=2)
        rsi2 = float(rsi2_series.iloc[-1]) if rsi2_series is not None and not rsi2_series.empty else float("nan")

        last = df.iloc[-1]
        close = float(last["close"])
        sma200 = float(last.get("sma200", float("nan")))
        atr = float(last.get("atr14", float("nan")))

        c_rsi = rsi2 < RSI_THRESHOLD
        c_regime_ticker = close > sma200

        # VIX gate
        vix_val: float | None = None
        if basket_data and "vix" in basket_data:
            vraw = basket_data["vix"]
            if isinstance(vraw, (int, float)):
                vix_val = float(vraw)
        c_vix = (vix_val is None) or (vix_val < VIX_KILL)
        vix_note = (
            "VIX gate skipped (no macro data)" if vix_val is None
            else f"VIX={vix_val:.1f} < 25" if c_vix
            else f"VIX={vix_val:.1f} ≥ 25 — risk-off"
        )

        # Earnings gate
        # basket_data["earnings_dates"] expected as dict[ticker, list[date]]
        # If absent we set "skipped" and let the gate pass with a TODO note.
        earnings_dates: list[date] = []
        if basket_data and isinstance(basket_data.get("earnings_dates"), dict):
            earnings_dates = list(basket_data["earnings_dates"].get(ticker, []) or [])

        as_of = df.index[-1].date() if hasattr(df.index[-1], "date") else date.today()
        upcoming_earnings = [
            d for d in earnings_dates if as_of <= d <= as_of + timedelta(days=EARNINGS_WINDOW_DAYS)
        ]
        if earnings_dates:
            c_earn = len(upcoming_earnings) == 0
            earn_note = (
                f"no earnings in next {EARNINGS_WINDOW_DAYS}d" if c_earn
                else f"earnings within {EARNINGS_WINDOW_DAYS}d ({upcoming_earnings[0]}) — skip"
            )
        else:
            c_earn = True
            earn_note = "earnings calendar unavailable — TODO(devclaw): wire yfinance earnings_dates"

        evidence: list[EvidenceItem] = [
            EvidenceItem(
                factor=f"RSI(2) = {rsi2:.1f}" if rsi2 == rsi2 else "RSI(2) N/A",
                value=round(rsi2, 2) if rsi2 == rsi2 else None,
                weight=0.40,
                passed=c_rsi,
                note="extreme oversold" if c_rsi else f">{RSI_THRESHOLD} threshold not crossed",
            ),
            EvidenceItem(
                factor=f"Close > SMA200 ({sma200:.2f})",
                value=round(close - sma200, 2),
                weight=0.25,
                passed=c_regime_ticker,
                note="ticker in primary uptrend" if c_regime_ticker else "below SMA200 — falling-knife risk",
            ),
            EvidenceItem(
                factor="VIX < 25 (macro gate)",
                value=vix_val,
                weight=0.20,
                passed=c_vix,
                note=vix_note,
            ),
            EvidenceItem(
                factor=f"No earnings in next {EARNINGS_WINDOW_DAYS}d",
                value=None,
                weight=0.15,
                passed=c_earn,
                note=earn_note,
            ),
        ]

        passes = sum(1 for e in evidence if e.passed)
        fired = c_rsi and c_regime_ticker and c_vix and c_earn
        if fired:
            # Deeper RSI(2) = stronger mean-reversion edge. RSI 0 -> 1.0, RSI 10 -> 0.5
            rsi_strength = max(0.0, min(1.0, (RSI_THRESHOLD - rsi2) / RSI_THRESHOLD))
            score = round(0.5 + 0.5 * rsi_strength, 4)
        else:
            score = passes / 4.0

        # Trade plan — shorter hold (mean-reversion).
        stop = atr_stop(close, atr, mult=2.0)
        # Target: revert to recent SMA(5) or +2R, whichever is higher.
        sma5 = float(df["close"].rolling(5).mean().iloc[-1])
        risk = max(0.01, close - stop)
        target = round(max(sma5, close + 2.0 * risk), 2)

        invalidation = [
            f"Close below stop ({stop:.2f})",
            "VIX spikes above 25",
            "Gap-down >3% on no news (regime shift)",
            "Earnings announced inside hold window",
        ]
        headline = (
            f"{ticker}: RSI(2) extreme oversold inside an uptrend — mean-reversion edge."
            if fired
            else f"{ticker}: RSI(2) setup incomplete ({passes}/4)."
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
            max_hold_days=5,
            risk_tier=self.risk_tier,
        )
