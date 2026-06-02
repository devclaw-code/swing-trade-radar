"""Verdict synthesizer — combine strategy results into a per-ticker Verdict.

References:
    PHASE2_PLAN.md §1 (target shape), §5 (explanation engine).
    research/02-risk-management.md §3 (position sizing).
    research/00-INDEX.md §B (regime non-negotiable).

Rules:
    - Pick the highest-scoring fired strategy as `primary_setup`.
    - Other fired strategies become `supporting_setups`.
    - Compute conviction as a regime-weighted blend of the primary score
      and the count of additional fired strategies.
    - Verdict mapping:
          fired primary AND regime favourable AND conviction > 0.6 → BUY
          fired primary AND conviction in [0.4, 0.6]                → WATCH
          regime unfavourable                                        → AVOID
          nothing fired                                              → NO_SETUP
    - Position size hint: $25k account, 1% account risk per trade.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from functools import lru_cache
from pathlib import Path

import yaml

from ..config import settings
from ..schemas import (
    BaseRateBlock,
    EventBlackout,
    EvidenceItem,
    PriceLevel,
    RegimeContext,
    StopLevel,
    TargetLevel,
    Verdict,
    VerdictKind,
    WhyBlock,
)
from ..strategies.v2.base import StrategyResult
from .blackout import (
    BlackoutReason,
    calendar_is_stale,
    is_blackout,
    next_earnings_for,
)
from .scoring import ScoringContext, compute_score_breakdown

log = logging.getLogger(__name__)

ACCOUNT_SIZE = 25_000.0
RISK_FRACTION = 0.01  # 1% of account per trade

COUNTER_ARGS_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "counter_arguments.yaml"
)


@lru_cache(maxsize=1)
def load_counter_arguments() -> dict[str, str]:
    if not COUNTER_ARGS_PATH.exists():
        log.warning("counter_arguments.yaml missing at %s", COUNTER_ARGS_PATH)
        return {}
    try:
        data = yaml.safe_load(COUNTER_ARGS_PATH.read_text()) or {}
        return {str(k): str(v).strip() for k, v in data.items()}
    except yaml.YAMLError as e:
        log.error("counter_arguments.yaml parse failed: %s", e)
        return {}


def _position_size_hint(entry: float, stop: float) -> str:
    risk_per_share = max(0.01, entry - stop)
    dollar_risk = ACCOUNT_SIZE * RISK_FRACTION
    shares = int(dollar_risk // risk_per_share)
    notional = shares * entry
    pct = (notional / ACCOUNT_SIZE * 100.0) if notional > 0 else 0.0
    return (
        f"≤ {RISK_FRACTION*100:.0f}% account risk; ~{shares} shares for ${ACCOUNT_SIZE:,.0f} "
        f"(notional ≈ ${notional:,.0f}, {pct:.0f}% of account)."
    )


def _verdict_kind(
    primary: StrategyResult | None,
    n_supporting: int,
    regime: RegimeContext,
    conviction: float,
) -> VerdictKind:
    if primary is None or not primary.fired:
        if regime.regime_verdict == "unfavorable / risk-off":
            return "AVOID"
        return "NO_SETUP"
    if regime.regime_verdict == "unfavorable / risk-off":
        return "AVOID"
    if conviction > 0.6:
        return "BUY"
    if conviction >= 0.4:
        return "WATCH"
    return "NO_SETUP"


def _conviction(primary: StrategyResult, supporting: list[StrategyResult], regime: RegimeContext) -> float:
    base = primary.score
    bonus = min(0.15, 0.05 * len(supporting))
    regime_mult = (
        1.0 if regime.regime_verdict == "favorable for long swings"
        else 0.85 if regime.regime_verdict == "neutral"
        else 0.5
    )
    return round(min(1.0, (base + bonus) * regime_mult), 3)


def synthesize_verdict(
    *,
    ticker: str,
    as_of: date,
    strategy_results: list[StrategyResult],
    regime: RegimeContext,
    base_rate_lookup: Callable[[StrategyResult], BaseRateBlock | None] | None = None,
    df=None,
    sanity_flags=None,
    days_to_earnings: int | None = None,
) -> Verdict:
    """Build a Verdict from the strategy results."""
    fired = [r for r in strategy_results if r.fired]
    fired.sort(key=lambda r: r.score, reverse=True)

    if fired:
        primary = fired[0]
        supporting_results = fired[1:]
    else:
        # Best-effort 'primary' for evidence display: highest scorer even if not fired.
        primary = max(strategy_results, key=lambda r: r.score) if strategy_results else None
        supporting_results = []

    counter_map = load_counter_arguments()
    counter_keys: list[str] = []
    if primary is not None:
        counter_keys.extend(primary.counter_argument_keys)
    for s in supporting_results:
        for k in s.counter_argument_keys:
            if k not in counter_keys:
                counter_keys.append(k)

    counter_args = [counter_map[k] for k in counter_keys if k in counter_map]

    evidence: list[EvidenceItem] = list(primary.evidence) if primary else []
    invalidation = list(primary.invalidation_conditions) if primary else []
    doc_refs: list[str] = list(primary.doc_refs) if primary else []
    for s in supporting_results:
        for ref in s.doc_refs:
            if ref not in doc_refs:
                doc_refs.append(ref)

    base_rate: BaseRateBlock | None = None
    if primary is not None and base_rate_lookup is not None:
        try:
            base_rate = base_rate_lookup(primary)
        except Exception as e:
            log.warning("base_rate lookup failed for %s: %s", ticker, e)

    if primary is not None and primary.fired:
        conviction = _conviction(primary, supporting_results, regime)
    else:
        conviction = round(primary.score * 0.5, 3) if primary else 0.0

    verdict_kind = _verdict_kind(primary, len(supporting_results), regime, conviction)

    # ---- W2: macro + earnings blackout gating ----
    event_blackout: EventBlackout | None = None
    pre_earnings_exit_by: datetime | None = None
    calendar_stale = False
    if settings.calendars_enabled:
        calendar_stale = calendar_is_stale()
        # We treat positive-conviction verdicts as long-side. Demote BUY → WATCH
        # if a blackout is in force; AVOID/NO_SETUP unaffected.
        if verdict_kind in ("BUY", "WATCH") and primary is not None and primary.fired:
            br: BlackoutReason | None = is_blackout(ticker, "LONG")
            if br is not None:
                suppressed_to: VerdictKind = "WATCH"
                event_blackout = EventBlackout(
                    kind="earnings" if br.release == "EARNINGS" else "macro",
                    release=br.release,
                    scheduled_at=br.scheduled_at,
                    hours_until=round(br.hours_until, 1),
                    confirmed=br.confirmed,
                    suppressed_to=suppressed_to,
                )
                # Append to invalidation list so the WhyBlock surfaces it.
                invalidation.append(
                    f"Calendar blackout: {br.as_text()} — demoted from {verdict_kind} to {suppressed_to}."
                )
                verdict_kind = suppressed_to
        # Pre-earnings exit clamp: applies even when no blackout (e.g. earnings 4d out, hold=10d)
        if primary is not None and primary.fired and primary.max_hold_days:
            nxt = next_earnings_for(ticker)
            if nxt is not None:
                exit_by = nxt - timedelta(hours=settings.earnings_exit_hours)
                hold_end = datetime.now(UTC) + timedelta(days=primary.max_hold_days)
                if exit_by < hold_end:
                    pre_earnings_exit_by = exit_by
                    invalidation.append(
                        f"Earnings {nxt.strftime('%Y-%m-%d %H:%MZ')} falls inside the hold window; "
                        f"exit by {exit_by.strftime('%Y-%m-%d %H:%MZ')} (24h pre-print)."
                    )

    headline = (
        primary.headline if primary and primary.headline
        else f"{ticker}: no setup fired today."
    )

    why = WhyBlock(
        headline=headline,
        evidence=evidence,
        historical_base_rate=base_rate,
        what_could_invalidate=invalidation,
        counter_arguments=counter_args,
        doc_refs=doc_refs,
    )

    entry_zone: PriceLevel | None = None
    stop_loss: StopLevel | None = None
    target: TargetLevel | None = None
    max_hold = ""
    pos_hint = ""
    risk_tier = "MEDIUM"

    if primary is not None and primary.fired and primary.entry_price is not None:
        entry_zone = PriceLevel(price=primary.entry_price, method="next-day open")
        if primary.stop_price is not None:
            risk_pct = round(
                100.0 * (primary.entry_price - primary.stop_price) / primary.entry_price, 2
            ) if primary.entry_price else None
            stop_loss = StopLevel(
                price=primary.stop_price,
                method="2x ATR(14) below entry",
                risk_pct=risk_pct,
            )
        if primary.target_price is not None and primary.stop_price is not None:
            risk = primary.entry_price - primary.stop_price
            reward = primary.target_price - primary.entry_price
            rr = round(reward / risk, 2) if risk > 0 else None
            target = TargetLevel(price=primary.target_price, method="ATR-multiple target", rr=rr)
        if primary.max_hold_days is not None:
            max_hold = f"{primary.max_hold_days} trading days"
            if pre_earnings_exit_by is not None:
                max_hold += f" (clamped to earnings exit {pre_earnings_exit_by.strftime('%Y-%m-%d')})"
        if primary.entry_price is not None and primary.stop_price is not None:
            pos_hint = _position_size_hint(primary.entry_price, primary.stop_price)
        risk_tier = primary.risk_tier or "MEDIUM"

    return Verdict(
        ticker=ticker,
        as_of=as_of,
        verdict=verdict_kind,
        conviction=conviction,
        primary_setup=(primary.strategy_name if (primary and primary.fired) else ""),
        supporting_setups=[s.strategy_name for s in supporting_results],
        entry_zone=entry_zone,
        stop_loss=stop_loss,
        target=target,
        max_hold=max_hold,
        position_size_hint=pos_hint,
        regime_context=regime,
        why=why,
        risk_tier=risk_tier,  # type: ignore[arg-type]
        event_blackout=event_blackout,
        pre_earnings_exit_by=pre_earnings_exit_by,
        calendar_stale=calendar_stale,
    )


def attach_score_breakdown(
    verdict: Verdict,
    *,
    df,
    primary: StrategyResult | None,
    sanity_flags=None,
    base_rate: BaseRateBlock | None = None,
    days_to_earnings: int | None = None,
) -> Verdict:
    """Compute and attach the transparent score breakdown to a verdict.

    Kept separate from `synthesize_verdict` so callers can pass the enriched
    dataframe without forcing every test/fixture to do so.
    """
    if df is None or getattr(df, "empty", False):
        return verdict
    breakdown = compute_score_breakdown(
        ScoringContext(
            ticker=verdict.ticker,
            df=df,
            primary=primary,
            sanity_flags=sanity_flags or [],
            base_rate=base_rate,
            days_to_earnings=days_to_earnings,
        )
    )
    verdict.score_breakdown = breakdown
    verdict.score = breakdown.total
    return verdict
