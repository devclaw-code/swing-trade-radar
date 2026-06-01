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
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

VerdictKind = Literal["BUY", "WATCH", "AVOID", "NO_SETUP"]
RiskTier = Literal["LOW", "MEDIUM", "HIGH"]
RegimeVerdict = Literal[
    "favorable for long swings",
    "neutral",
    "unfavorable / risk-off",
]


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


class WhyBlock(BaseModel):
    """The structured explanation that powers the UI 'why' panel."""

    model_config = ConfigDict(extra="forbid")

    headline: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    historical_base_rate: str = Field(
        default="",
        description="Human-readable base-rate string, e.g. '87 occurrences, 68% win rate, +0.83R avg'.",
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


class Verdict(BaseModel):
    """Per-ticker, per-day output of the engine. The deliverable."""

    model_config = ConfigDict(extra="forbid")

    ticker: str
    as_of: _date
    verdict: VerdictKind
    conviction: float = Field(..., ge=0.0, le=1.0)

    primary_setup: str = Field(default="", description="Name of the highest-scoring fired strategy.")
    supporting_setups: list[str] = Field(default_factory=list)

    entry_zone: PriceLevel | None = None
    stop_loss: StopLevel | None = None
    target: TargetLevel | None = None
    max_hold: str = ""

    position_size_hint: str = ""

    regime_context: RegimeContext
    why: WhyBlock
    risk_tier: RiskTier = "MEDIUM"
