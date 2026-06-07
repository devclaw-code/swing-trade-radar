"""Phase-2 Pydantic schemas — the v2 verdict / why / regime shapes.

These are the I/O contracts for the verdict engine. The frontend will
codegen TypeScript types directly from the OpenAPI dump produced from
these models, so be strict and explicit.

References:
    PHASE2_PLAN.md §1 (target shape)
    research/00-INDEX.md §B-D
"""

from __future__ import annotations

from datetime import date as _date
from datetime import datetime as _datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

VerdictKind = Literal["BUY", "WATCH", "AVOID", "NO_SETUP"]
TimeHorizon = Literal["Core", "Tactical"]
RiskTier = Literal["LOW", "MEDIUM", "HIGH"]
SanitySeverity = Literal["info", "warning", "high"]
Reliability = Literal["high", "medium", "low", "insufficient"]
RegimeVerdict = Literal[
    "favorable for long swings",
    "neutral",
    "unfavorable / risk-off",
]


class SanityFlag(BaseModel):
    """A single data sanity flag attached to a verdict.

    Severities:
      - info: noteworthy but harmless
      - warning: render yellow; trade with skepticism
      - high: render red; data is likely wrong or trade is high-risk chase
    """

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., description="Stable machine-readable flag code.")
    severity: SanitySeverity = Field(..., description="info | warning | high")
    message: str = Field(..., description="Human-readable explanation for the UI.")
    value: float | None = Field(default=None, description="The observed value that tripped the check.")
    threshold: float | None = Field(default=None, description="The threshold the value crossed.")


class EvidenceItem(BaseModel):
    """One piece of evidence supporting/refuting a setup."""

    model_config = ConfigDict(extra="forbid")

    factor: str = Field(..., description="Short label, e.g. 'RSI(2) = 6.4'.")
    value: float | str | None = Field(default=None, description="Underlying numeric/string value.")
    weight: float = Field(..., ge=0.0, le=1.0, description="Contribution weight in the setup [0..1].")
    passed: bool = Field(..., description="Did the factor pass its required threshold?")
    note: str = Field(default="", description="Human-readable note for the UI.")


class RegimeContext(BaseModel):
    """Macro regime snapshot — drives global gating of LONG signals."""

    model_config = ConfigDict(extra="forbid")

    spy_above_200sma: bool
    qqq_above_200sma: bool
    vix: float | None = Field(default=None, description="Current ^VIX level.")
    vix_term_structure: Literal["contango (healthy)", "backwardation (risk-off)", "unknown"] = "unknown"
    regime_verdict: RegimeVerdict = "neutral"
    as_of: _date | None = None


class BaseRateBlock(BaseModel):
    """Structured historical base-rate stats for a (ticker, setup) pair."""

    model_config = ConfigDict(extra="forbid")

    occurrences: int = Field(..., ge=0)
    win_rate: float = Field(..., ge=0.0, le=1.0)
    avg_r: float
    median_hold: float = Field(..., ge=0.0, description="Median hold in bars.")


class WhyBlock(BaseModel):
    """The structured explanation that powers the UI 'why' panel."""

    model_config = ConfigDict(extra="forbid")

    headline: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    historical_base_rate: BaseRateBlock | None = Field(
        default=None,
        description="Structured base-rate stats; null when no prior occurrences are available.",
    )
    what_could_invalidate: list[str] = Field(default_factory=list)
    counter_arguments: list[str] = Field(default_factory=list)
    doc_refs: list[str] = Field(default_factory=list)


class PriceLevel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    price: float
    method: str = ""


class StopLevel(PriceLevel):
    risk_pct: float | None = None


class TargetLevel(PriceLevel):
    rr: float | None = None


class SRLevel(PriceLevel):
    """A ranked support/resistance zone near the current price.

    Inherits `price` (the zone's representative price) and `method` from
    `PriceLevel`. Produced by `engine.sr_levels.compute_sr_levels`. Display-only
    for now — does NOT feed the numeric conviction/score until the strength
    weights are calibrated against the walk-forward harness.
    """

    kind: Literal["support", "resistance"]
    strength: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Confluence score 0..1 (touches + distinct-method agreement + "
            "recency + psychological round-number bonus)."
        ),
    )
    distance_pct: float = Field(
        ..., description="Signed % from current price (negative = below, i.e. support)."
    )
    sources: list[str] = Field(
        default_factory=list,
        description=(
            "Method tags that voted for this zone, e.g. "
            '["swing_low", "classic_pivot_S1", "fib_retr_0.618"].'
        ),
    )
    touches: int = Field(
        default=0, ge=0, description="Number of historical swing touches in the zone."
    )


class ScoreComponent(BaseModel):
    """One component of the transparent score breakdown.

    Each component is normalized to 0..100, where 100 = best possible
    contribution from that lens (most bullish / least risky).
    """

    model_config = ConfigDict(extra="forbid")

    value: float = Field(..., ge=0.0, le=100.0)
    weight: float = Field(..., ge=0.0, le=1.0, description="Blend weight in the final score.")
    note: str = Field(default="", description="Short human-readable rationale for this value.")


class ScoreBreakdown(BaseModel):
    """Transparent 8-component score breakdown.

    `total` is the weighted blend (0..100). Components are independent enough
    that the UI can render them as side-by-side bars.
    """

    model_config = ConfigDict(extra="forbid")

    trend_quality: ScoreComponent
    momentum: ScoreComponent
    mean_reversion: ScoreComponent
    risk_reward: ScoreComponent
    volatility: ScoreComponent
    earnings_risk: ScoreComponent
    historical_reliability: ScoreComponent
    extension_risk: ScoreComponent

    total: float = Field(..., ge=0.0, le=100.0)
    weights: dict[str, float] = Field(
        default_factory=dict,
        description="Component name → blend weight. Sums to ~1.0.",
    )
    correlation_penalty: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Points subtracted from total due to high correlation with already-selected trades.",
    )


class EventBlackout(BaseModel):
    """Set on a Verdict when a calendar event suppresses or warns about the trade."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["macro", "earnings"] = Field(
        ..., description="`macro` for CPI/PCE/NFP/PPI/FOMC; `earnings` for ticker prints."
    )
    release: str = Field(..., description="Release code, e.g. CPI, FOMC, EARNINGS.")
    scheduled_at: _datetime = Field(..., description="Event time in UTC.")
    hours_until: float = Field(..., description="Hours from `as_of` to event.")
    confirmed: bool = Field(default=True, description="False for fallback / unconfirmed dates.")
    suppressed_to: VerdictKind = Field(
        ..., description="What the verdict was demoted to (typically WATCH)."
    )


class Verdict(BaseModel):
    """Per-ticker, per-day output of the engine. The deliverable."""

    model_config = ConfigDict(extra="forbid")

    ticker: str
    as_of: _date
    verdict: VerdictKind
    conviction: float = Field(..., ge=0.0, le=1.0)

    primary_setup: str = Field(default="", description="Name of the highest-scoring fired strategy.")
    supporting_setups: list[str] = Field(default_factory=list)

    time_horizon: TimeHorizon = Field(
        default="Core",
        description="Hold-horizon bucket: 'Core' (30-day trend) or 'Tactical' (1-5 day).",
    )
    volatility_atr: float | None = Field(
        default=None,
        description="Latest daily ATR(14) of the asset, for volatility-adjusted sizing/UI.",
    )

    entry_zone: PriceLevel | None = None
    stop_loss: StopLevel | None = None
    target: TargetLevel | None = None
    max_hold: str = ""

    levels: list[SRLevel] = Field(
        default_factory=list,
        description=(
            "Ranked support/resistance zones near price: up to 3 supports below + "
            "3 resistances above. Display-only; does not affect conviction/score."
        ),
    )

    position_size_hint: str = ""

    regime_context: RegimeContext
    why: WhyBlock
    risk_tier: RiskTier = "MEDIUM"

    # Optional latest-bar enrichment for the UI header.
    price: float | None = Field(default=None, description="Latest close used for this verdict.")
    day_change_pct: float | None = Field(
        default=None,
        description="Fraction (e.g. 0.012 = +1.2%) day-over-day change for the latest bar.",
    )
    sparkline: list[float] | None = Field(
        default=None,
        description="Recent close prices (oldest → newest), ~60 bars, for sparkline rendering.",
    )

    sanity_flags: list[SanityFlag] = Field(
        default_factory=list,
        description="Data-quality / chase-risk flags surfaced to the UI as banners.",
    )

    score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Headline 0-100 trade score (weighted blend of score_breakdown components, minus correlation penalty).",
    )
    score_breakdown: ScoreBreakdown | None = Field(
        default=None,
        description="Transparent component-by-component breakdown of the trade score.",
    )
    correlation_penalty: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Points subtracted from the headline score because of high correlation with higher-scoring trades in the same dashboard run.",
    )

    # ---- Sample-size reliability (added by apply_sample_size_adjustment) ----
    reliability: Reliability = Field(
        default="insufficient",
        description="Reliability tier of the historical stats backing this verdict, derived from the sample size.",
    )
    confidence_adjusted_for_sample: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description=(
            "Headline score multiplicatively shrunk by sqrt(min(n, 30) / 30) to reflect "
            "how much we should trust it given the historical sample size. New field "
            "(separate from `score`) for back-compat."
        ),
    )
    historical_stats_display: HistoricalStatsDisplay | None = Field(
        default=None,
        description="Ready-to-render struct describing how to display the historical stats.",
    )

    # ---- Event-calendar gating (W1 + W2: macro + earnings) ----
    event_blackout: EventBlackout | None = Field(
        default=None,
        description=(
            "Set when a macro release (CPI/PCE/NFP/PPI/FOMC) inside the next "
            "`macro_blackout_hours` (default 48) or a confirmed earnings inside the same "
            "window forced this verdict from BUY down to WATCH. Long entries blacklisted by "
            "both gates; short entries only by earnings."
        ),
    )
    pre_earnings_exit_by: _datetime | None = Field(
        default=None,
        description=(
            "If a confirmed earnings print falls inside the suggested holding window, this is "
            "the UTC datetime by which the position MUST be exited (24h pre-earnings)."
        ),
    )
    calendar_stale: bool = Field(
        default=False,
        description="True when the events table hasn\u2019t been refreshed in >36h; UI should banner this.",
    )


class HistoricalStatsDisplay(BaseModel):
    """Frontend-ready presentation of the historical-stats block.

    The frontend just renders ``display_text``; ``show_win_rate`` is a hint
    for whether to allow the win-rate-styled emphasis at all.
    """

    model_config = ConfigDict(extra="forbid")

    tier: Reliability = Field(..., description="Reliability tier (high/medium/low/insufficient).")
    sample_size: int = Field(..., ge=0, description="Number of historical occurrences (n).")
    show_win_rate: bool = Field(
        ...,
        description="True when the sample is large enough to display the win rate at all (n >= 10).",
    )
    display_text: str = Field(
        ...,
        description=(
            "Verbatim string for the UI. For tier='insufficient' this is the literal "
            "'Insufficient historical sample (n=X)'."
        ),
    )


# ---------------------------------------------------------------------------
# Conservative-mode filter shapes
# ---------------------------------------------------------------------------


FilterMode = Literal["all", "conservative"]


class FilterReason(BaseModel):
    """Why a verdict was filtered out (one rule that failed)."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., description="Stable rule id, e.g. 'stop_loss_pct'.")
    message: str = Field(..., description="Short human-readable reason, e.g. 'stop 12% > 8%'.")


class FilteredVerdict(BaseModel):
    """A verdict that didn't pass the conservative filter, with the reasons it failed."""

    model_config = ConfigDict(extra="forbid")

    verdict: Verdict
    reasons: list[FilterReason] = Field(default_factory=list)


class MarginalVerdict(BaseModel):
    """A verdict that passed the hard filter but is downgraded to 'marginal'."""

    model_config = ConfigDict(extra="forbid")

    verdict: Verdict
    reasons: list[FilterReason] = Field(default_factory=list)


class ConservativeFilterResult(BaseModel):
    """API payload for ``mode=conservative``."""

    model_config = ConfigDict(extra="forbid")

    mode: FilterMode
    passed: list[Verdict] = Field(default_factory=list)
    marginal: list[MarginalVerdict] = Field(default_factory=list)
    filtered_out: list[FilteredVerdict] = Field(default_factory=list)


# Resolve forward reference for HistoricalStatsDisplay used inside Verdict.
Verdict.model_rebuild()
