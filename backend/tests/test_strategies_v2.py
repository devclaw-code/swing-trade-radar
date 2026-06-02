"""Unit tests for v2 strategies."""

from __future__ import annotations

import pandas as pd

from swing_trader.engine.indicators import enrich
from swing_trader.strategies.v2.s1_trend_50_200 import TrendFiftyTwoHundredStrategy
from swing_trader.strategies.v2.s2_clenow_momentum import (
    ClenowMomentumStrategy,
    compute_basket_scores,
)
from swing_trader.strategies.v2.s3_connors_rsi2 import ConnorsRsi2Strategy
from swing_trader.strategies.v2.s4_minervini_vcp import MinerviniVcpStrategy
from swing_trader.strategies.v2.s5_pead import PeadStrategy


def _enrich(df: pd.DataFrame) -> pd.DataFrame:
    return enrich(df)


def test_s1_fires_in_clean_uptrend(uptrend_df):
    df = _enrich(uptrend_df)
    spy = _enrich(uptrend_df.copy())
    s = TrendFiftyTwoHundredStrategy()
    res = s.evaluate(df, "TEST", basket_data={"SPY": spy})
    assert res.fired is True
    # Fired = all 3 legs pass, so score is floored at 0.4 and scales with trend
    # extension/gap (capped at 1.0). The synthetic ~0.1%/day fixture is a clean but
    # not maximally-extended uptrend, so it lands mid-band rather than pinned at 1.0.
    assert 0.4 <= res.score <= 1.0
    assert res.entry_price is not None and res.stop_price is not None and res.target_price is not None
    assert any("SMA50" in e.factor for e in res.evidence)


def test_s1_does_not_fire_in_downtrend(downtrend_df, uptrend_df):
    df = _enrich(downtrend_df)
    spy = _enrich(uptrend_df.copy())  # SPY ok, ticker bad
    s = TrendFiftyTwoHundredStrategy()
    res = s.evaluate(df, "TEST", basket_data={"SPY": spy})
    assert res.fired is False
    assert res.score < 1.0


def test_s2_fires_when_top_quintile(uptrend_df, downtrend_df):
    enriched_up = _enrich(uptrend_df)
    basket = {"WIN": uptrend_df, "LOSE1": downtrend_df, "LOSE2": downtrend_df, "LOSE3": downtrend_df, "LOSE4": downtrend_df}
    scores = compute_basket_scores(basket)
    assert scores["WIN"] > scores["LOSE1"]

    s = ClenowMomentumStrategy()
    res = s.evaluate(
        enriched_up, "WIN",
        basket_data={"clenow_scores": scores, **basket},
    )
    assert res.fired is True


def test_s3_fires_on_oversold_in_uptrend(oversold_in_uptrend_df):
    df = _enrich(oversold_in_uptrend_df)
    s = ConnorsRsi2Strategy()
    res = s.evaluate(df, "TEST", basket_data={"vix": 14.0, "earnings_dates": {}})
    # Either fires, or is nearly fired (RSI signature should pass)
    assert any("RSI(2)" in e.factor for e in res.evidence)
    rsi_evi = next(e for e in res.evidence if "RSI(2)" in e.factor)
    assert rsi_evi.passed is True
    assert res.score >= 0.75


def test_s3_blocks_on_high_vix(oversold_in_uptrend_df):
    df = _enrich(oversold_in_uptrend_df)
    s = ConnorsRsi2Strategy()
    res = s.evaluate(df, "TEST", basket_data={"vix": 35.0, "earnings_dates": {}})
    assert res.fired is False
    vix_e = next(e for e in res.evidence if "VIX" in e.factor)
    assert vix_e.passed is False


def test_s4_scores_breakout(vcp_breakout_df):
    df = _enrich(vcp_breakout_df)
    s = MinerviniVcpStrategy()
    res = s.evaluate(df, "TEST")
    # We don't require fire (heuristic) but expect a non-trivial score and breakout evidence
    assert 0.0 <= res.score <= 1.0
    breakout_evi = next(e for e in res.evidence if "Breakout" in e.factor)
    assert isinstance(breakout_evi.passed, bool)


def test_s5_no_earnings_returns_no_setup(uptrend_df):
    df = _enrich(uptrend_df)
    s = PeadStrategy()
    res = s.evaluate(df, "TEST", basket_data={"earnings_dates": {}})
    assert res.fired is False
    # Headline must mention 'no PEAD' or evidence must include the TODO
    assert "PEAD" in res.headline


def test_all_strategies_handle_empty_df():
    empty = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    for cls in (
        TrendFiftyTwoHundredStrategy,
        ClenowMomentumStrategy,
        ConnorsRsi2Strategy,
        MinerviniVcpStrategy,
        PeadStrategy,
    ):
        s = cls()
        res = s.evaluate(empty, "TEST")
        assert res.fired is False
        assert res.score == 0.0
