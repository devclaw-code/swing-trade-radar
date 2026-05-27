"""Unit tests for the walk-forward backtester."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from swing_trader.engine.backtester import (
    Trade,
    _aggregate,
    simulate_trade,
)
from swing_trader.strategies.base_strategy import Signal


def _make_df(closes: list[float], *, high_pad: float = 0.5, low_pad: float = 0.5) -> pd.DataFrame:
    n = len(closes)
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    closes_arr = np.array(closes, dtype=float)
    df = pd.DataFrame(
        {
            "open": closes_arr,
            "high": closes_arr + high_pad,
            "low": closes_arr - low_pad,
            "close": closes_arr,
            "volume": np.full(n, 1_000_000.0),
        },
        index=idx,
    )
    return df


def _sig(entry: float, target: float, stop: float, direction: str = "LONG") -> Signal:
    return Signal(
        ticker="TEST",
        strategy="test",
        direction=direction,  # type: ignore[arg-type]
        entry=entry,
        target=target,
        stop=stop,
    )


# --- simulate_trade ----------------------------------------------------------


def test_simulate_trade_hits_target_long():
    # Flat then sharp ramp up — target should fire before stop.
    closes = [100.0] * 6 + [101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
    df = _make_df(closes, high_pad=0.5, low_pad=0.5)

    # Signal at bar 5 (entry fills at bar 6 open ≈ 100).
    sig = _sig(entry=100.0, target=105.0, stop=98.0, direction="LONG")
    trade = simulate_trade(df, entry_idx=5, signal=sig, max_hold=20, slippage_bps=0.0)

    assert trade is not None
    assert trade.exit_reason == "target"
    assert trade.return_R > 0
    assert trade.direction == "LONG"
    assert trade.hold_bars >= 1
    assert trade.max_favorable_R >= trade.return_R - 1e-6


def test_simulate_trade_hits_stop_long():
    # Flat then crash down — stop fires.
    closes = [100.0] * 6 + [99, 98, 97, 96, 95, 94, 93, 92]
    df = _make_df(closes, high_pad=0.2, low_pad=0.2)

    sig = _sig(entry=100.0, target=105.0, stop=98.0, direction="LONG")
    trade = simulate_trade(df, entry_idx=5, signal=sig, max_hold=20, slippage_bps=0.0)

    assert trade is not None
    assert trade.exit_reason == "stop"
    assert trade.return_R == pytest.approx(-1.0, abs=0.05)
    assert trade.max_adverse_R <= -1.0 + 1e-6


def test_simulate_trade_times_out_when_flat():
    # Flat price, no target or stop hit within max_hold.
    closes = [100.0] * 30
    df = _make_df(closes, high_pad=0.1, low_pad=0.1)

    sig = _sig(entry=100.0, target=110.0, stop=90.0, direction="LONG")
    trade = simulate_trade(df, entry_idx=5, signal=sig, max_hold=10, slippage_bps=0.0)

    assert trade is not None
    assert trade.exit_reason == "timeout"
    assert trade.hold_bars == 10
    # Flat price → ~0 R.
    assert abs(trade.return_R) < 0.05


def test_simulate_trade_returns_none_on_last_bar():
    df = _make_df([100.0, 101.0, 102.0])
    sig = _sig(entry=102.0, target=110.0, stop=95.0, direction="LONG")
    trade = simulate_trade(df, entry_idx=2, signal=sig, slippage_bps=0.0)
    assert trade is None


def test_simulate_trade_short_hits_target():
    # Drop fast → SHORT target fires.
    closes = [100.0] * 6 + [99, 98, 97, 96, 95, 94, 93]
    df = _make_df(closes, high_pad=0.2, low_pad=0.2)

    sig = _sig(entry=100.0, target=95.0, stop=102.0, direction="SHORT")
    trade = simulate_trade(df, entry_idx=5, signal=sig, max_hold=20, slippage_bps=0.0)

    assert trade is not None
    assert trade.exit_reason == "target"
    assert trade.direction == "SHORT"
    assert trade.return_R > 0


# --- aggregation -------------------------------------------------------------


def _trade(r: float, hold: int = 5, reason: str = "target") -> Trade:
    return Trade(
        ticker="TEST",
        strategy="test",
        direction="LONG",
        entry_date=date(2024, 1, 1),
        entry_price=100.0,
        exit_date=date(2024, 1, 5),
        exit_price=100.0 + r,
        exit_reason=reason,
        return_R=r,
        return_pct=r / 100.0,
        hold_bars=hold,
        max_adverse_R=min(0.0, r),
        max_favorable_R=max(0.0, r),
    )


def test_aggregate_basic_stats():
    trades = [_trade(2.0), _trade(-1.0, reason="stop"), _trade(1.0)]
    res = _aggregate(trades, "test", "TEST", date(2024, 1, 1), date(2024, 2, 1))

    assert res.n_trades == 3
    assert res.win_rate == pytest.approx(2 / 3)
    assert res.avg_r == pytest.approx((2.0 - 1.0 + 1.0) / 3)
    # profit_factor = (2+1) / 1 = 3
    assert res.profit_factor == pytest.approx(3.0)
    assert res.avg_hold_bars == pytest.approx(5.0)
    # cumulative R = [2, 1, 2]; running max = [2, 2, 2]; dd = [0, 1, 0] → max_dd = 1.0
    assert res.max_dd_r == pytest.approx(1.0)
    assert res.sharpe != 0.0  # has variance


def test_aggregate_empty():
    res = _aggregate([], "test", "TEST", date(2024, 1, 1), date(2024, 2, 1))
    assert res.n_trades == 0
    assert res.win_rate == 0.0
    assert res.avg_r == 0.0
    assert res.profit_factor == 0.0
    assert res.sharpe == 0.0


def test_aggregate_no_losses_profit_factor_inf():
    trades = [_trade(2.0), _trade(1.0)]
    res = _aggregate(trades, "test", "TEST", date(2024, 1, 1), date(2024, 2, 1))
    assert res.profit_factor == float("inf")
    assert res.win_rate == 1.0
