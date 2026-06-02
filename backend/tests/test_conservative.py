"""Tests for the conservative-mode filter."""

from __future__ import annotations

from datetime import date

import pytest

from swing_trader.engine.conservative import (
    MARGINAL_COMPONENT_THRESHOLD,
    apply_conservative_filter,
)
from swing_trader.schemas import (
    BaseRateBlock,
    PriceLevel,
    RegimeContext,
    SanityFlag,
    ScoreBreakdown,
    ScoreComponent,
    StopLevel,
    TargetLevel,
    Verdict,
    WhyBlock,
)

# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _good_component(value: float = 80.0) -> ScoreComponent:
    return ScoreComponent(value=value, weight=0.1, note="ok")


def _good_breakdown(
    *,
    extension_note: str = "|close/SMA50-1|=4.0%",
    earnings_note: str = "earnings in 30d",
    component_value: float = 80.0,
) -> ScoreBreakdown:
    return ScoreBreakdown(
        trend_quality=_good_component(component_value),
        momentum=_good_component(component_value),
        mean_reversion=_good_component(component_value),
        risk_reward=_good_component(component_value),
        volatility=_good_component(component_value),
        earnings_risk=ScoreComponent(value=80.0, weight=0.08, note=earnings_note),
        historical_reliability=_good_component(component_value),
        extension_risk=ScoreComponent(value=80.0, weight=0.10, note=extension_note),
        total=80.0,
        weights={},
        correlation_penalty=0.0,
    )


def _regime() -> RegimeContext:
    return RegimeContext(
        spy_above_200sma=True,
        qqq_above_200sma=True,
        vix=14.0,
        vix_term_structure="contango (healthy)",
        regime_verdict="favorable for long swings",
    )


def _make_verdict(
    *,
    ticker: str = "TEST",
    stop_pct: float = 5.0,
    rr: float = 3.0,
    sample_size: int = 50,
    avg_r: float = 0.5,
    extension_note: str = "|close/SMA50-1|=4.0%",
    earnings_note: str = "earnings in 30d",
    component_value: float = 80.0,
    sanity_flags: list[SanityFlag] | None = None,
) -> Verdict:
    return Verdict(
        ticker=ticker,
        as_of=date(2026, 6, 1),
        verdict="BUY",
        conviction=0.7,
        primary_setup="S1_trend_50_200",
        supporting_setups=[],
        entry_zone=PriceLevel(price=100.0, method="next-day open"),
        stop_loss=StopLevel(price=95.0, method="2x ATR", risk_pct=stop_pct),
        target=TargetLevel(price=110.0, method="ATR target", rr=rr),
        max_hold="20 trading days",
        position_size_hint="",
        regime_context=_regime(),
        why=WhyBlock(
            headline=f"{ticker} test",
            historical_base_rate=BaseRateBlock(
                occurrences=sample_size,
                win_rate=0.55,
                avg_r=avg_r,
                median_hold=10.0,
            ),
        ),
        risk_tier="MEDIUM",
        score_breakdown=_good_breakdown(
            extension_note=extension_note,
            earnings_note=earnings_note,
            component_value=component_value,
        ),
        sanity_flags=sanity_flags or [],
    )


# ---------------------------------------------------------------------------
# Mode=all is a no-op pass-through
# ---------------------------------------------------------------------------


def test_mode_all_passes_everything_through():
    bad = _make_verdict(stop_pct=20.0, rr=0.5, sample_size=2, avg_r=-0.5)
    res = apply_conservative_filter([bad], mode="all")
    assert res.mode == "all"
    assert len(res.passed) == 1
    assert res.marginal == []
    assert res.filtered_out == []


# ---------------------------------------------------------------------------
# Each filter rule fires on its own
# ---------------------------------------------------------------------------


def test_stop_loss_pct_filters_out():
    v = _make_verdict(stop_pct=12.0)
    res = apply_conservative_filter([v], mode="conservative")
    assert len(res.filtered_out) == 1
    codes = [r.code for r in res.filtered_out[0].reasons]
    assert "stop_loss_pct" in codes
    assert "12.0%" in res.filtered_out[0].reasons[0].message
    assert "8%" in res.filtered_out[0].reasons[0].message


def test_reward_to_risk_filters_out():
    v = _make_verdict(rr=1.2)
    res = apply_conservative_filter([v], mode="conservative")
    assert len(res.filtered_out) == 1
    reason = next(r for r in res.filtered_out[0].reasons if r.code == "reward_to_risk")
    assert "1.20" in reason.message
    assert "2.0" in reason.message


def test_pct_above_sma50_filters_out():
    v = _make_verdict(extension_note="|close/SMA50-1|=22.5%, flag")
    res = apply_conservative_filter([v], mode="conservative")
    assert len(res.filtered_out) == 1
    reason = next(r for r in res.filtered_out[0].reasons if r.code == "pct_above_sma50")
    assert "22.5%" in reason.message


def test_earnings_too_close_filters_out():
    v = _make_verdict(earnings_note="earnings in 4d")
    res = apply_conservative_filter([v], mode="conservative")
    assert len(res.filtered_out) == 1
    reason = next(r for r in res.filtered_out[0].reasons if r.code == "next_earnings_days")
    assert "4d" in reason.message


def test_earnings_unknown_passes():
    v = _make_verdict(earnings_note="earnings unknown")
    res = apply_conservative_filter([v], mode="conservative")
    assert len(res.passed) == 1


def test_earnings_already_passed_does_not_block():
    # "earnings passed 3d ago" — negative day count should not trigger the rule.
    v = _make_verdict(earnings_note="earnings passed 3d ago")
    res = apply_conservative_filter([v], mode="conservative")
    assert len(res.passed) == 1


def test_historical_sample_size_filters_out():
    v = _make_verdict(sample_size=6)
    res = apply_conservative_filter([v], mode="conservative")
    assert len(res.filtered_out) == 1
    reason = next(r for r in res.filtered_out[0].reasons if r.code == "historical_sample_size")
    assert "n=6" in reason.message
    assert "20" in reason.message


def test_avg_r_non_positive_filters_out():
    v = _make_verdict(avg_r=-0.1)
    res = apply_conservative_filter([v], mode="conservative")
    assert len(res.filtered_out) == 1
    reason = next(r for r in res.filtered_out[0].reasons if r.code == "avg_r")
    assert "-0.10" in reason.message


def test_avg_r_exactly_zero_filters_out():
    v = _make_verdict(avg_r=0.0)
    res = apply_conservative_filter([v], mode="conservative")
    assert len(res.filtered_out) == 1


# ---------------------------------------------------------------------------
# Multiple failures collected
# ---------------------------------------------------------------------------


def test_multiple_rules_failing_yield_multiple_reasons():
    v = _make_verdict(stop_pct=12.0, rr=0.5, sample_size=6, avg_r=-0.5)
    res = apply_conservative_filter([v], mode="conservative")
    assert len(res.filtered_out) == 1
    codes = {r.code for r in res.filtered_out[0].reasons}
    assert {"stop_loss_pct", "reward_to_risk", "historical_sample_size", "avg_r"} <= codes


# ---------------------------------------------------------------------------
# Marginal classification
# ---------------------------------------------------------------------------


def test_marginal_when_component_score_low():
    v = _make_verdict(component_value=40.0)  # all components low
    res = apply_conservative_filter([v], mode="conservative")
    assert len(res.marginal) == 1
    assert len(res.passed) == 0
    # All 7 user-set components (earnings_risk forced to 80) should be marginal.
    codes = {r.code for r in res.marginal[0].reasons}
    assert any(c.startswith("low_") for c in codes)


def test_marginal_when_high_severity_sanity_flag():
    flag = SanityFlag(code="extended_above_atr", severity="high", message="big chase")
    v = _make_verdict(sanity_flags=[flag])
    res = apply_conservative_filter([v], mode="conservative")
    assert len(res.marginal) == 1
    codes = {r.code for r in res.marginal[0].reasons}
    assert any(c.startswith("sanity_high:") for c in codes)


def test_clean_verdict_passes():
    v = _make_verdict()
    res = apply_conservative_filter([v], mode="conservative")
    assert len(res.passed) == 1
    assert len(res.marginal) == 0
    assert len(res.filtered_out) == 0


# ---------------------------------------------------------------------------
# Mixed batch — sanity-check the partitioning numbers
# ---------------------------------------------------------------------------


def test_mixed_batch_partitioning():
    verdicts = [
        _make_verdict(ticker="AAA"),                              # passed
        _make_verdict(ticker="BBB"),                              # passed
        _make_verdict(ticker="CCC", component_value=30.0),        # marginal
        _make_verdict(ticker="DDD", stop_pct=12.0),               # filtered
        _make_verdict(ticker="EEE", sample_size=5, avg_r=-0.2),   # filtered (2 reasons)
    ]
    res = apply_conservative_filter(verdicts, mode="conservative")
    assert [v.ticker for v in res.passed] == ["AAA", "BBB"]
    assert [m.verdict.ticker for m in res.marginal] == ["CCC"]
    assert [f.verdict.ticker for f in res.filtered_out] == ["DDD", "EEE"]
    # EEE should carry both sample-size and avg_r reasons.
    eee = res.filtered_out[1]
    eee_codes = {r.code for r in eee.reasons}
    assert {"historical_sample_size", "avg_r"} <= eee_codes


# ---------------------------------------------------------------------------
# Constants sanity
# ---------------------------------------------------------------------------


def test_marginal_threshold_constant_is_50():
    assert MARGINAL_COMPONENT_THRESHOLD == 50.0


# ---------------------------------------------------------------------------
# Edge: missing optional fields are treated as "passes"
# ---------------------------------------------------------------------------


def test_missing_score_breakdown_does_not_explode():
    v = _make_verdict()
    v.score_breakdown = None
    res = apply_conservative_filter([v], mode="conservative")
    # Missing breakdown means we can't read pct_above_sma50 / earnings — both
    # treated as passing. With the rest still good, this verdict passes.
    assert len(res.passed) == 1


def test_missing_base_rate_does_not_explode():
    v = _make_verdict()
    v.why.historical_base_rate = None
    res = apply_conservative_filter([v], mode="conservative")
    # Missing base rate → unknown → passes.
    assert len(res.passed) == 1


@pytest.mark.parametrize("rr", [2.0, 2.5, 5.0])
def test_rr_at_or_above_threshold_passes(rr):
    v = _make_verdict(rr=rr)
    res = apply_conservative_filter([v], mode="conservative")
    assert len(res.passed) == 1
