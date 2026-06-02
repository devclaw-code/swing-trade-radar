"""Tests for the transparent score breakdown + correlation post-pass."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from swing_trader.data.sanity import SanityFlag
from swing_trader.engine.indicators import enrich
from swing_trader.engine.scoring import (
    WEIGHTS,
    ScoringContext,
    apply_correlation_penalties,
    compute_score_breakdown,
)
from swing_trader.schemas import (
    BaseRateBlock,
    RegimeContext,
    Verdict,
    WhyBlock,
)
from swing_trader.strategies.v2.base import StrategyResult

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _df_uptrend(n: int = 260, start: float = 50.0, step: float = 0.20) -> pd.DataFrame:
    """A clean steady uptrend with mild noise — gives meaningful indicators."""
    rng = np.random.default_rng(42)
    closes = start + np.cumsum(np.full(n, step) + rng.normal(0, 0.10, n))
    closes = np.clip(closes, 1.0, None)
    idx = pd.date_range(end=pd.Timestamp("2026-05-30"), periods=n, freq="B")
    return pd.DataFrame(
        {
            "open": np.r_[closes[0], closes[:-1]],
            "high": closes * 1.01,
            "low": closes * 0.99,
            "close": closes,
            "volume": np.full(n, 1_000_000.0),
        },
        index=idx,
    )


def _primary(entry: float, stop: float, target: float | None = None) -> StrategyResult:
    return StrategyResult(
        strategy_name="S1_trend_50_200",
        fired=True,
        score=0.7,
        entry_price=entry,
        stop_price=stop,
        target_price=target,
        max_hold_days=10,
        risk_tier="MEDIUM",
    )


def _ctx(df: pd.DataFrame, **kw) -> ScoringContext:
    return ScoringContext(
        ticker=kw.pop("ticker", "TST"),
        df=df,
        primary=kw.pop("primary", None),
        sanity_flags=kw.pop("sanity_flags", []),
        base_rate=kw.pop("base_rate", None),
        days_to_earnings=kw.pop("days_to_earnings", None),
    )


# ---------------------------------------------------------------------------
# Sanity tests
# ---------------------------------------------------------------------------


def test_weights_sum_to_one():
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-6


def test_breakdown_has_all_eight_components():
    df = enrich(_df_uptrend())
    bd = compute_score_breakdown(_ctx(df))
    for name in WEIGHTS:
        comp = getattr(bd, name)
        assert 0.0 <= comp.value <= 100.0
        assert comp.weight == WEIGHTS[name]
    assert 0.0 <= bd.total <= 100.0
    assert set(bd.weights.keys()) == set(WEIGHTS.keys())


def test_clean_uptrend_scores_decently():
    df = enrich(_df_uptrend())
    last = float(df["close"].iloc[-1])
    bd = compute_score_breakdown(
        _ctx(df, primary=_primary(entry=last, stop=last * 0.97, target=last * 1.06))
    )
    # Trend stack should be strong.
    assert bd.trend_quality.value >= 60
    # Total in the upper half.
    assert bd.total >= 50


# ---------------------------------------------------------------------------
# (a) Extension penalty
# ---------------------------------------------------------------------------


def test_extended_above_sma50_penalizes_extension_risk():
    df = enrich(_df_uptrend())
    last = float(df["close"].iloc[-1])

    # Baseline (no extension flag, close at trend).
    bd_clean = compute_score_breakdown(
        _ctx(df, primary=_primary(last, last * 0.97, last * 1.06))
    )

    # Now spike the last close to 60% above SMA50.
    df2 = df.copy()
    sma50 = float(df2["sma50"].iloc[-1])
    df2.loc[df2.index[-1], "close"] = sma50 * 1.60
    flags = [
        SanityFlag(
            code="extended_above_sma50",
            severity="high",
            message="extended",
            value=0.60,
            threshold=0.40,
        )
    ]
    bd_ext = compute_score_breakdown(
        _ctx(
            df2,
            primary=_primary(sma50 * 1.60, sma50 * 1.55, sma50 * 1.70),
            sanity_flags=flags,
        )
    )

    assert bd_ext.extension_risk.value < bd_clean.extension_risk.value
    assert bd_ext.extension_risk.value <= 5.0  # severely extended floors near 0


# ---------------------------------------------------------------------------
# (b) Sample-size shrinkage
# ---------------------------------------------------------------------------


def test_low_sample_size_shrinks_reliability():
    df = enrich(_df_uptrend())

    big_n = BaseRateBlock(occurrences=50, win_rate=0.70, avg_r=0.80, median_hold=8)
    medium_n = BaseRateBlock(occurrences=15, win_rate=0.70, avg_r=0.80, median_hold=8)
    tiny_n = BaseRateBlock(occurrences=4, win_rate=0.70, avg_r=0.80, median_hold=8)

    bd_big = compute_score_breakdown(_ctx(df, base_rate=big_n))
    bd_med = compute_score_breakdown(_ctx(df, base_rate=medium_n))
    bd_tiny = compute_score_breakdown(_ctx(df, base_rate=tiny_n))

    assert bd_big.historical_reliability.value > bd_med.historical_reliability.value
    assert bd_med.historical_reliability.value > bd_tiny.historical_reliability.value


# ---------------------------------------------------------------------------
# (c) Wide stop hurts risk_reward
# ---------------------------------------------------------------------------


def test_wide_stop_hurts_risk_reward():
    df = enrich(_df_uptrend())
    last = float(df["close"].iloc[-1])

    tight = _primary(entry=last, stop=last * 0.97, target=last * 1.06)   # ~3% stop, 2R
    wide = _primary(entry=last, stop=last * 0.85, target=last * 1.30)    # 15% stop, 2R

    bd_tight = compute_score_breakdown(_ctx(df, primary=tight))
    bd_wide = compute_score_breakdown(_ctx(df, primary=wide))

    assert bd_wide.risk_reward.value < bd_tight.risk_reward.value


def test_no_target_lower_than_2r_target():
    df = enrich(_df_uptrend())
    last = float(df["close"].iloc[-1])

    no_t = _primary(entry=last, stop=last * 0.97, target=None)
    has_t = _primary(entry=last, stop=last * 0.97, target=last * 1.06)

    bd_no = compute_score_breakdown(_ctx(df, primary=no_t))
    bd_has = compute_score_breakdown(_ctx(df, primary=has_t))
    assert bd_has.risk_reward.value > bd_no.risk_reward.value


# ---------------------------------------------------------------------------
# Earnings risk
# ---------------------------------------------------------------------------


def test_earnings_imminent_tanks_earnings_risk():
    df = enrich(_df_uptrend())
    bd_far = compute_score_breakdown(_ctx(df, days_to_earnings=30))
    bd_near = compute_score_breakdown(_ctx(df, days_to_earnings=1))
    assert bd_near.earnings_risk.value < bd_far.earnings_risk.value


# ---------------------------------------------------------------------------
# (d) Correlation post-pass
# ---------------------------------------------------------------------------


def _verdict_with_score(ticker: str, score: float, df: pd.DataFrame) -> Verdict:
    """Build a minimal Verdict with a populated score_breakdown."""
    bd = compute_score_breakdown(_ctx(df, ticker=ticker))
    # Force the headline score to the chosen value so tie-break order is deterministic.
    bd.total = score
    v = Verdict(
        ticker=ticker,
        as_of=date(2026, 5, 30),
        verdict="WATCH",
        conviction=0.5,
        regime_context=RegimeContext(spy_above_200sma=True, qqq_above_200sma=True),
        why=WhyBlock(headline=f"{ticker} test"),
    )
    v.score = score
    v.score_breakdown = bd
    return v


def test_correlation_pass_downgrades_correlated_peer():
    base = _df_uptrend()
    df_a = enrich(base)
    # df_b is *almost* identical \u2192 returns will correlate ~1.0.
    df_b = enrich(base.copy())

    v_a = _verdict_with_score("AAA", score=80.0, df=df_a)
    v_b = _verdict_with_score("BBB", score=70.0, df=df_b)

    apply_correlation_penalties(
        verdicts_in_order=[v_a, v_b],     # AAA first (higher score), BBB downgraded
        enriched_by_ticker={"AAA": df_a, "BBB": df_b},
    )

    assert v_a.correlation_penalty == 0.0
    assert v_a.score == 80.0
    assert v_b.correlation_penalty > 0.0
    assert v_b.score < 70.0


def test_correlation_pass_leaves_uncorrelated_alone():
    rng = np.random.default_rng(7)
    base_a = _df_uptrend()
    df_a = enrich(base_a)

    # Build df_b with totally independent random walk (very weak correlation).
    n = len(base_a)
    closes = 80 + np.cumsum(rng.normal(0, 0.5, n))
    closes = np.clip(closes, 5, None)
    idx = base_a.index
    base_b = pd.DataFrame(
        {
            "open": np.r_[closes[0], closes[:-1]],
            "high": closes * 1.01,
            "low": closes * 0.99,
            "close": closes,
            "volume": np.full(n, 1_000_000.0),
        },
        index=idx,
    )
    df_b = enrich(base_b)

    v_a = _verdict_with_score("AAA", score=80.0, df=df_a)
    v_b = _verdict_with_score("BBB", score=70.0, df=df_b)

    apply_correlation_penalties(
        verdicts_in_order=[v_a, v_b],
        enriched_by_ticker={"AAA": df_a, "BBB": df_b},
    )

    # No penalty expected.
    assert v_b.correlation_penalty == 0.0
    assert v_b.score == 70.0
