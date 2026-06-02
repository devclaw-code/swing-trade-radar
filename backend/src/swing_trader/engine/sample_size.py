"""Sample-size reliability tiers and post-scoring confidence adjustment.

Some signals report very high win rates from tiny historical samples (n=1, 2,
6). At those sizes, the win rate is essentially noise and shouldn't be shown
prominently. This module classifies the historical sample size of a verdict
into one of four reliability tiers, builds a ready-to-render display struct
for the frontend, and exposes a *separate* post-scoring shrinkage applied to
the headline score.

Note on double-shrinking:
    `ScoreBreakdown.historical_reliability` already shrinks the historical
    *component* toward a 0.4 baseline when ``n`` is small. That keeps the
    component itself honest, but the headline `score` (a weighted blend of
    eight components) can still be optimistic when the historical lens is
    drowned out by the other seven. ``confidence_adjusted_for_sample`` is the
    "overall" shrinkage — applied once, to the final post-correlation score
    — and is exposed as a *new* field rather than mutating ``score`` so we
    keep backward compatibility with consumers that already reason about the
    raw score.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from ..schemas import HistoricalStatsDisplay, Reliability, Verdict

__all__ = [
    "RELIABILITY_TIERS",
    "apply_sample_size_adjustment",
    "build_historical_stats_display",
    "classify_reliability",
    "shrinkage_factor",
]


RELIABILITY_TIERS: tuple[tuple[int, Reliability], ...] = (
    (30, "high"),
    (20, "medium"),
    (10, "low"),
    (0, "insufficient"),
)


# Anchor sample size at which we trust the score 1:1. n=30 is a common
# rule-of-thumb breakpoint and aligns with the "high" reliability tier.
_FULL_CONFIDENCE_N = 30


def classify_reliability(n: int) -> Reliability:
    """Map a historical sample size to a reliability tier.

    Tiers:
      - n >= 30 → "high"
      - 20 <= n < 30 → "medium"
      - 10 <= n < 20 → "low"
      - n < 10  → "insufficient"
    """
    if n is None or n < 0:
        n = 0
    if n >= 30:
        return "high"
    if n >= 20:
        return "medium"
    if n >= 10:
        return "low"
    return "insufficient"


def shrinkage_factor(n: int) -> float:
    """Multiplicative confidence factor for a score, given sample size n.

    ``adjusted = score * sqrt(min(n, 30) / 30)``

    Examples:
      - n=0  → 0.0   (no history → full shrink, but only score is *adjusted*)
      - n=2  → ~0.258
      - n=15 → ~0.707
      - n=25 → ~0.913
      - n=30+ → 1.0  (no shrink)
    """
    if n is None or n < 0:
        n = 0
    return math.sqrt(min(n, _FULL_CONFIDENCE_N) / _FULL_CONFIDENCE_N)


def _historical_sample_size(v: Verdict) -> int:
    """Pull the sample size out of the verdict's WhyBlock, defaulting to 0."""
    br = v.why.historical_base_rate if v.why else None
    if br is None:
        return 0
    return int(br.occurrences or 0)


def build_historical_stats_display(v: Verdict) -> HistoricalStatsDisplay:
    """Build the ready-to-render display struct for the frontend.

    For ``insufficient`` (n<10) we *do not* surface the win rate at all —
    the display text is the literal string ``"Insufficient historical sample
    (n=X)"`` so the UI can render it verbatim with no further logic.
    """
    n = _historical_sample_size(v)
    tier = classify_reliability(n)
    show_win_rate = tier != "insufficient"

    if not show_win_rate:
        display_text = f"Insufficient historical sample (n={n})"
    else:
        br = v.why.historical_base_rate
        # br is non-null here (n>=10 implies occurrences>=10 implies base_rate present).
        assert br is not None
        wr = br.win_rate * 100.0
        if tier == "high":
            display_text = f"Win rate {wr:.0f}% (n={n})"
        elif tier == "medium":
            display_text = f"Win rate {wr:.0f}% (n={n}, modest sample)"
        else:  # low
            display_text = f"Win rate {wr:.0f}% (n={n}, small sample — interpret with caution)"

    return HistoricalStatsDisplay(
        tier=tier,
        sample_size=n,
        show_win_rate=show_win_rate,
        display_text=display_text,
    )


def apply_sample_size_adjustment(verdict: Verdict) -> Verdict:
    """Set ``reliability`` and ``confidence_adjusted_for_sample`` on a Verdict.

    Idempotent: re-applying does not compound shrinkage, because the
    adjustment is computed from the *original* ``score`` (which we never
    mutate) and the current sample size.
    """
    n = _historical_sample_size(verdict)
    verdict.reliability = classify_reliability(n)
    verdict.historical_stats_display = build_historical_stats_display(verdict)

    if verdict.score is None:
        verdict.confidence_adjusted_for_sample = None
    else:
        adj = float(verdict.score) * shrinkage_factor(n)
        # Clamp to [0, 100] for safety; score is already bounded but float
        # arithmetic + future score plumbing makes this defensive.
        verdict.confidence_adjusted_for_sample = max(0.0, min(100.0, adj))
    return verdict


@dataclass(frozen=True)
class _Tier:
    """Internal helper used by tests for parametrization."""

    name: Literal["high", "medium", "low", "insufficient"]
    min_n: int
