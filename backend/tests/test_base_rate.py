"""Tests for engine.base_rate."""

from __future__ import annotations

from swing_trader.engine.base_rate import compute_base_rate, format_base_rate
from swing_trader.engine.indicators import enrich


def test_base_rate_reports_zero_for_never_firing_signature(uptrend_df):
    df = enrich(uptrend_df)
    stats = compute_base_rate(
        ticker="UNUSED_T1",
        setup_id="never",
        setup_signature=lambda d, i: False,
        df=df,
        max_hold_days=5,
        use_cache=False,
    )
    assert stats["occurrences"] == 0
    assert stats["win_rate"] == 0.0
    assert "No prior occurrences" in format_base_rate(stats, "T", "never")


def test_base_rate_simulates_when_signature_fires(uptrend_df):
    df = enrich(uptrend_df)
    # Fire every 25th bar — ensures multiple historical samples
    sig = lambda d, i: i % 25 == 0  # noqa: E731
    stats = compute_base_rate(
        ticker="UNUSED_T2",
        setup_id="every25",
        setup_signature=sig,
        df=df,
        max_hold_days=5,
        use_cache=False,
    )
    assert stats["occurrences"] > 0
    assert 0.0 <= stats["win_rate"] <= 1.0
    assert stats["median_hold"] > 0
    msg = format_base_rate(stats, "TEST", "every25")
    assert "Win rate" in msg


def test_base_rate_cache_round_trip(uptrend_df, tmp_path, monkeypatch):
    # Ensure DB tables exist
    from swing_trader.data.db import init_db
    init_db()
    df = enrich(uptrend_df)
    sig = lambda d, i: i % 30 == 0  # noqa: E731

    s1 = compute_base_rate("CACHE_T", "every30", sig, df, max_hold_days=5, use_cache=True)
    s2 = compute_base_rate("CACHE_T", "every30", sig, df, max_hold_days=5, use_cache=True)
    assert s1 == s2
