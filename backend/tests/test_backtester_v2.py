"""Tests for the v2 walk-forward backtester (deflated Sharpe + adapter)."""

from __future__ import annotations

import numpy as np

from swing_trader.engine.backtester_v2 import (
    _result_to_signal,
    _test_window_mask,
    deflated_sharpe_ratio,
)
from swing_trader.strategies.v2.base import StrategyResult


def test_result_to_signal_fired_long():
    res = StrategyResult(
        strategy_name="S1_trend_50_200",
        fired=True,
        score=0.8,
        entry_price=100.0,
        stop_price=95.0,
        target_price=110.0,
        max_hold_days=10,
    )
    sig = _result_to_signal(res, "AAPL")
    assert sig is not None
    assert sig.direction == "LONG"
    assert sig.entry == 100.0 and sig.stop == 95.0 and sig.target == 110.0


def test_result_to_signal_not_fired_returns_none():
    res = StrategyResult(strategy_name="S1", fired=False, score=0.2)
    assert _result_to_signal(res, "AAPL") is None


def test_result_to_signal_rejects_bad_geometry():
    # stop above entry — not a valid long
    res = StrategyResult(
        strategy_name="S1",
        fired=True,
        score=0.5,
        entry_price=100.0,
        stop_price=105.0,
        target_price=110.0,
    )
    assert _result_to_signal(res, "AAPL") is None


def test_result_to_signal_rejects_missing_plan():
    res = StrategyResult(
        strategy_name="S1", fired=True, score=0.5, entry_price=100.0, stop_price=None
    )
    assert _result_to_signal(res, "AAPL") is None


def test_test_window_mask_layout():
    # warmup=10, train=5, test=3 -> first test window starts at 15
    mask = _test_window_mask(n=40, train_days=5, test_days=3, warmup=10)
    idx = np.where(mask)[0]
    # First eligible test bar is warmup+train = 15
    assert idx[0] == 15
    # Warmup + train region is never eligible
    assert not mask[:15].any()
    # Total eligible should be a multiple-ish of test_days, all within bounds
    assert mask.sum() > 0
    assert idx.max() < 40


def test_deflated_sharpe_small_sample_returns_zero():
    rs = np.array([0.1, -0.2, 0.3])  # n < 8
    assert deflated_sharpe_ratio(rs, 1.0, n_trials=5) == 0.0


def test_deflated_sharpe_in_unit_interval():
    rng = np.random.default_rng(42)
    rs = rng.normal(0.1, 1.0, size=200)
    dsr = deflated_sharpe_ratio(rs, observed_sharpe_annual=1.0, n_trials=5)
    assert 0.0 <= dsr <= 1.0


def test_deflated_sharpe_more_trials_lowers_score():
    rng = np.random.default_rng(7)
    rs = rng.normal(0.08, 1.0, size=300)
    few = deflated_sharpe_ratio(rs, 1.0, n_trials=2)
    many = deflated_sharpe_ratio(rs, 1.0, n_trials=50)
    # More trials => higher bar => deflated score should not increase.
    assert many <= few + 1e-9


def test_deflated_sharpe_zero_variance_returns_zero():
    rs = np.full(50, 0.5)
    assert deflated_sharpe_ratio(rs, 1.0, n_trials=5) == 0.0
