"""Conservative swing-trader filter mode.

Reuses fields already attached to a ``Verdict`` (no recomputation).

Hard filter rules (must ALL pass for ``conservative`` mode):
    1. stop_loss.risk_pct       <  8%
    2. target.rr                 >= 2.0
    3. |close/SMA50 - 1|         <= 15%       (extension band)
    4. days_to_earnings is None  or            (unknown = pass)
       days_to_earnings >= 7
    5. base_rate.occurrences     >= 20
    6. base_rate.avg_r           >  0

Marginal classification (passes hard filter but downgraded):
    - any score_breakdown component < 50, OR
    - any sanity_flag with severity == "high".

Unknown values are treated as "passes the rule" — we don't punish missing
data here. The dashboard already surfaces sanity flags for that.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Literal

from ..schemas import (
    ConservativeFilterResult,
    FilteredVerdict,
    FilterMode,
    FilterReason,
    MarginalVerdict,
    Verdict,
)

# Thresholds — kept module-level so tests can monkey-patch if needed.
MAX_STOP_LOSS_PCT = 8.0          # %
MIN_REWARD_TO_RISK = 2.0
MAX_PCT_FROM_SMA50 = 15.0        # absolute, %
MIN_DAYS_TO_EARNINGS = 7
MIN_HISTORICAL_SAMPLE = 20
MIN_AVG_R = 0.0                  # strictly greater than 0
MARGINAL_COMPONENT_THRESHOLD = 50.0


# -----------------------------------------------------------------------------
# Field accessors — pull values from the existing Verdict shape.
# -----------------------------------------------------------------------------


def _stop_loss_pct(v: Verdict) -> float | None:
    """Stop-loss size in percent (positive number, e.g. 5.2 means 5.2%)."""
    sl = v.stop_loss
    if sl is None:
        return None
    rp = sl.risk_pct
    if rp is None:
        return None
    return abs(float(rp))


def _reward_to_risk(v: Verdict) -> float | None:
    t = v.target
    if t is None or t.rr is None:
        return None
    return float(t.rr)


def _historical_sample_size(v: Verdict) -> int | None:
    br = v.why.historical_base_rate
    if br is None:
        return None
    return int(br.occurrences)


def _avg_r(v: Verdict) -> float | None:
    br = v.why.historical_base_rate
    if br is None:
        return None
    return float(br.avg_r)


_PCT_FROM_SMA_RE = re.compile(r"\|close/SMA50-1\|=\s*(-?\d+(?:\.\d+)?)%")
_EARNINGS_RE = re.compile(r"earnings\s+in\s+(-?\d+)d", re.IGNORECASE)


def _pct_above_sma50(v: Verdict) -> float | None:
    """Absolute % distance from SMA50, parsed from the score_breakdown note.

    The scoring engine writes a note like ``"|close/SMA50-1|=12.4%, flag"`` which
    we re-use here rather than recomputing. Returns ``None`` if not available
    (treated as passing per the spec).
    """
    sb = v.score_breakdown
    if sb is None:
        return None
    note = sb.extension_risk.note or ""
    m = _PCT_FROM_SMA_RE.search(note)
    if not m:
        return None
    try:
        return abs(float(m.group(1)))
    except ValueError:
        return None


def _days_to_earnings(v: Verdict) -> int | None:
    """Days-to-next-earnings parsed from score_breakdown.earnings_risk.note.

    Returns ``None`` if unknown. Negative values (earnings already passed) also
    return ``None`` — the rule only cares about *upcoming* earnings inside the
    hold window.
    """
    sb = v.score_breakdown
    if sb is None:
        return None
    note = sb.earnings_risk.note or ""
    if "unknown" in note.lower():
        return None
    m = _EARNINGS_RE.search(note)
    if not m:
        return None
    try:
        d = int(m.group(1))
    except ValueError:
        return None
    if d < 0:
        # Earnings already passed (note: "earnings passed Nd ago"); not a chase risk.
        return None
    return d


# -----------------------------------------------------------------------------
# Rule evaluation
# -----------------------------------------------------------------------------


def _check_rules(v: Verdict) -> list[FilterReason]:
    """Return the list of rules that *failed* for this verdict (empty = passes)."""
    reasons: list[FilterReason] = []

    sl = _stop_loss_pct(v)
    if sl is not None and sl >= MAX_STOP_LOSS_PCT:
        reasons.append(
            FilterReason(
                code="stop_loss_pct",
                message=f"stop {sl:.1f}% ≥ {MAX_STOP_LOSS_PCT:.0f}%",
            )
        )

    rr = _reward_to_risk(v)
    if rr is not None and rr < MIN_REWARD_TO_RISK:
        reasons.append(
            FilterReason(
                code="reward_to_risk",
                message=f"R:R {rr:.2f} < {MIN_REWARD_TO_RISK:.1f}",
            )
        )

    pct = _pct_above_sma50(v)
    if pct is not None and pct > MAX_PCT_FROM_SMA50:
        reasons.append(
            FilterReason(
                code="pct_above_sma50",
                message=f"extended {pct:.1f}% from SMA50 (> {MAX_PCT_FROM_SMA50:.0f}%)",
            )
        )

    dte = _days_to_earnings(v)
    if dte is not None and dte < MIN_DAYS_TO_EARNINGS:
        reasons.append(
            FilterReason(
                code="next_earnings_days",
                message=f"earnings in {dte}d (< {MIN_DAYS_TO_EARNINGS}d)",
            )
        )

    n = _historical_sample_size(v)
    if n is not None and n < MIN_HISTORICAL_SAMPLE:
        reasons.append(
            FilterReason(
                code="historical_sample_size",
                message=f"n={n} < {MIN_HISTORICAL_SAMPLE}",
            )
        )

    ar = _avg_r(v)
    if ar is not None and ar <= MIN_AVG_R:
        reasons.append(
            FilterReason(
                code="avg_r",
                message=f"avg_r {ar:+.2f} ≤ {MIN_AVG_R:.1f}",
            )
        )

    return reasons


def _marginal_reasons(v: Verdict) -> list[FilterReason]:
    """Reasons this passing verdict should be downgraded to 'marginal'."""
    reasons: list[FilterReason] = []

    sb = v.score_breakdown
    if sb is not None:
        components = {
            "trend_quality": sb.trend_quality,
            "momentum": sb.momentum,
            "mean_reversion": sb.mean_reversion,
            "risk_reward": sb.risk_reward,
            "volatility": sb.volatility,
            "earnings_risk": sb.earnings_risk,
            "historical_reliability": sb.historical_reliability,
            "extension_risk": sb.extension_risk,
        }
        for name, comp in components.items():
            if comp.value < MARGINAL_COMPONENT_THRESHOLD:
                reasons.append(
                    FilterReason(
                        code=f"low_{name}",
                        message=f"{name.replace('_', ' ')} score {comp.value:.0f} < {MARGINAL_COMPONENT_THRESHOLD:.0f}",
                    )
                )

    for f in v.sanity_flags:
        if f.severity == "high":
            reasons.append(
                FilterReason(
                    code=f"sanity_high:{f.code}",
                    message=f"high-severity sanity flag: {f.code}",
                )
            )

    return reasons


# -----------------------------------------------------------------------------
# Public entry point
# -----------------------------------------------------------------------------


def apply_conservative_filter(
    verdicts: Iterable[Verdict],
    mode: FilterMode | Literal["all", "conservative"] = "all",
) -> ConservativeFilterResult:
    """Partition verdicts into ``passed`` / ``marginal`` / ``filtered_out``.

    When ``mode == "all"``, every verdict ends up in ``passed`` and ``marginal``
    / ``filtered_out`` are empty — callers can use this as a uniform shape.
    """
    verdicts = list(verdicts)

    if mode == "all":
        return ConservativeFilterResult(
            mode="all",
            passed=verdicts,
            marginal=[],
            filtered_out=[],
        )

    passed: list[Verdict] = []
    marginal: list[MarginalVerdict] = []
    filtered_out: list[FilteredVerdict] = []

    for v in verdicts:
        fail_reasons = _check_rules(v)
        if fail_reasons:
            filtered_out.append(FilteredVerdict(verdict=v, reasons=fail_reasons))
            continue
        m_reasons = _marginal_reasons(v)
        if m_reasons:
            marginal.append(MarginalVerdict(verdict=v, reasons=m_reasons))
        else:
            passed.append(v)

    return ConservativeFilterResult(
        mode="conservative",
        passed=passed,
        marginal=marginal,
        filtered_out=filtered_out,
    )
