"""Tests for engine.sample_size — reliability tiers + post-scoring shrinkage."""

from __future__ import annotations

import math
from datetime import date

import pytest

from swing_trader.engine.regime import offline_default
from swing_trader.engine.sample_size import (
    apply_sample_size_adjustment,
    build_historical_stats_display,
    classify_reliability,
    shrinkage_factor,
)
from swing_trader.schemas import (
    BaseRateBlock,
    Verdict,
    WhyBlock,
)


def _mk_verdict(*, n: int | None, score: float | None = 80.0, win_rate: float = 0.7) -> Verdict:
    base = (
        BaseRateBlock(occurrences=n, win_rate=win_rate, avg_r=0.5, median_hold=4.0)
        if n is not None
        else None
    )
    return Verdict(
        ticker="TEST",
        as_of=date(2024, 1, 1),
        verdict="WATCH",
        conviction=0.5,
        regime_context=offline_default(),
        why=WhyBlock(headline="t", historical_base_rate=base),
        score=score,
    )


# ---------------------------------------------------------------------------
# classify_reliability — tier boundaries
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("n", "expected"),
    [
        (0, "insufficient"),
        (1, "insufficient"),
        (9, "insufficient"),
        (10, "low"),
        (15, "low"),
        (19, "low"),
        (20, "medium"),
        (25, "medium"),
        (29, "medium"),
        (30, "high"),
        (50, "high"),
        (500, "high"),
    ],
)
def test_classify_reliability_boundaries(n: int, expected: str) -> None:
    assert classify_reliability(n) == expected


def test_classify_reliability_negative_treated_as_zero() -> None:
    assert classify_reliability(-5) == "insufficient"


# ---------------------------------------------------------------------------
# shrinkage_factor — sample numerical examples (n=2, 15, 25, 50)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("n", "expected"),
    [
        (0, 0.0),
        (2, math.sqrt(2 / 30)),
        (15, math.sqrt(15 / 30)),
        (25, math.sqrt(25 / 30)),
        (30, 1.0),
        (50, 1.0),  # capped
    ],
)
def test_shrinkage_factor_values(n: int, expected: float) -> None:
    assert shrinkage_factor(n) == pytest.approx(expected, rel=1e-9)


# ---------------------------------------------------------------------------
# build_historical_stats_display — all four tiers
# ---------------------------------------------------------------------------


def test_display_insufficient_hides_win_rate() -> None:
    v = _mk_verdict(n=2, win_rate=1.0)  # 100% from n=2 — exactly the misleading case
    d = build_historical_stats_display(v)
    assert d.tier == "insufficient"
    assert d.show_win_rate is False
    assert d.display_text == "Insufficient historical sample (n=2)"
    # Crucially, the win-rate value must NOT appear anywhere in the display text.
    assert "100" not in d.display_text
    assert "%" not in d.display_text


def test_display_low_warns_with_caution() -> None:
    v = _mk_verdict(n=15, win_rate=0.6)
    d = build_historical_stats_display(v)
    assert d.tier == "low"
    assert d.show_win_rate is True
    assert "n=15" in d.display_text
    assert "caution" in d.display_text.lower()
    assert "60%" in d.display_text


def test_display_medium_modest_caveat() -> None:
    v = _mk_verdict(n=25, win_rate=0.55)
    d = build_historical_stats_display(v)
    assert d.tier == "medium"
    assert d.show_win_rate is True
    assert "n=25" in d.display_text
    assert "modest" in d.display_text.lower()
    assert "55%" in d.display_text


def test_display_high_clean() -> None:
    v = _mk_verdict(n=50, win_rate=0.62)
    d = build_historical_stats_display(v)
    assert d.tier == "high"
    assert d.show_win_rate is True
    assert "n=50" in d.display_text
    assert "62%" in d.display_text
    assert "caution" not in d.display_text.lower()
    assert "modest" not in d.display_text.lower()


def test_display_no_base_rate_is_insufficient() -> None:
    v = _mk_verdict(n=None)
    d = build_historical_stats_display(v)
    assert d.tier == "insufficient"
    assert d.sample_size == 0
    assert d.show_win_rate is False
    assert d.display_text == "Insufficient historical sample (n=0)"


# ---------------------------------------------------------------------------
# apply_sample_size_adjustment — wires it all together
# ---------------------------------------------------------------------------


def test_apply_adjustment_sets_all_fields() -> None:
    v = _mk_verdict(n=15, score=80.0)
    apply_sample_size_adjustment(v)
    assert v.reliability == "low"
    assert v.historical_stats_display is not None
    assert v.historical_stats_display.tier == "low"
    # adjusted = 80 * sqrt(15/30) ≈ 80 * 0.7071 ≈ 56.57
    assert v.confidence_adjusted_for_sample == pytest.approx(80.0 * math.sqrt(0.5), rel=1e-6)


def test_apply_adjustment_high_sample_no_shrink() -> None:
    v = _mk_verdict(n=50, score=80.0)
    apply_sample_size_adjustment(v)
    assert v.reliability == "high"
    assert v.confidence_adjusted_for_sample == pytest.approx(80.0, rel=1e-9)


def test_apply_adjustment_score_none_keeps_none() -> None:
    v = _mk_verdict(n=25, score=None)
    apply_sample_size_adjustment(v)
    assert v.reliability == "medium"
    assert v.confidence_adjusted_for_sample is None


def test_apply_adjustment_does_not_mutate_score() -> None:
    v = _mk_verdict(n=2, score=85.0)
    apply_sample_size_adjustment(v)
    # Original score is preserved; only the new field carries the shrunk value.
    assert v.score == 85.0
    assert v.confidence_adjusted_for_sample is not None
    assert v.confidence_adjusted_for_sample < 85.0


def test_apply_adjustment_idempotent() -> None:
    """Re-applying must not compound shrinkage — the adjustment is computed
    from the original (unmutated) ``score`` each time."""
    v = _mk_verdict(n=15, score=80.0)
    apply_sample_size_adjustment(v)
    first = v.confidence_adjusted_for_sample
    apply_sample_size_adjustment(v)
    apply_sample_size_adjustment(v)
    second = v.confidence_adjusted_for_sample
    assert first == second
    assert v.score == 80.0  # untouched


# ---------------------------------------------------------------------------
# Sample numerical examples called out in the task spec.
# ---------------------------------------------------------------------------


def test_spec_examples_n_2_15_25_50() -> None:
    """n=2, n=15, n=25, n=50 — matrix of expected tier + shrinkage + display."""
    cases = [
        (2, "insufficient", False),
        (15, "low", True),
        (25, "medium", True),
        (50, "high", True),
    ]
    for n, tier, show in cases:
        v = _mk_verdict(n=n, score=70.0, win_rate=0.65)
        apply_sample_size_adjustment(v)
        assert v.reliability == tier, f"n={n}"
        assert v.historical_stats_display is not None
        assert v.historical_stats_display.show_win_rate is show, f"n={n}"
        expected_factor = math.sqrt(min(n, 30) / 30)
        assert v.confidence_adjusted_for_sample == pytest.approx(
            70.0 * expected_factor, rel=1e-6
        ), f"n={n}"
