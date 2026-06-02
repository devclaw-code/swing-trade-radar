"""W2 verdict gating tests: macro + earnings blackout demote BUY \u2192 WATCH and
clamp the hold window.

We monkeypatch the blackout module rather than seeding the events table here \u2014
the events table itself is exercised by `test_calendars.py`. This keeps the
verdict tests pure-fn.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from swing_trader.engine import verdict as verdict_mod
from swing_trader.engine.blackout import BlackoutReason
from swing_trader.engine.regime import offline_default
from swing_trader.engine.verdict import synthesize_verdict
from swing_trader.schemas import EvidenceItem
from swing_trader.strategies.v2.base import StrategyResult


def _mk_result(name: str, *, fired: bool, score: float, **kw) -> StrategyResult:
    return StrategyResult(
        strategy_name=name,
        fired=fired,
        score=score,
        evidence=[EvidenceItem(factor="dummy", weight=1.0, passed=fired, note="t")],
        invalidation_conditions=["close below stop"],
        counter_argument_keys=["trend_late_entry"],
        doc_refs=["research/01 \u00a73"],
        headline=f"{name} headline",
        entry_price=kw.get("entry", 100.0),
        stop_price=kw.get("stop", 95.0),
        target_price=kw.get("target", 115.0),  # rr=3 so test_buy_when_blackout_demotes_to_watch starts at BUY
        max_hold_days=kw.get("max_hold", 10),
        risk_tier=kw.get("risk_tier", "MEDIUM"),
    )


@pytest.fixture(autouse=True)
def _isolate_calendar(monkeypatch):
    \
    """Default to no blackout, no earnings, fresh calendar \u2014 each test overrides."""
    monkeypatch.setattr(verdict_mod, "is_blackout", lambda *a, **k: None)
    monkeypatch.setattr(verdict_mod, "next_earnings_for", lambda *a, **k: None)
    monkeypatch.setattr(verdict_mod, "calendar_is_stale", lambda **k: False)


def test_buy_when_no_blackout_and_no_earnings():
    primary = _mk_result("S1_trend_50_200", fired=True, score=0.95)
    other = _mk_result("S3_connors_rsi2", fired=True, score=0.80)
    v = synthesize_verdict(
        ticker="NVDA",
        as_of=date(2026, 6, 2),
        strategy_results=[primary, other],
        regime=offline_default(),
    )
    assert v.verdict == "BUY"
    assert v.event_blackout is None
    assert v.pre_earnings_exit_by is None
    assert v.calendar_stale is False


def test_earnings_blackout_demotes_buy_to_watch(monkeypatch):
    primary = _mk_result("S1_trend_50_200", fired=True, score=0.95)
    sched = datetime.now(UTC) + timedelta(hours=28)
    br = BlackoutReason(release="EARNINGS", scheduled_at=sched, hours_until=28.0, confirmed=True)
    monkeypatch.setattr(verdict_mod, "is_blackout", lambda t, side, **k: br)
    monkeypatch.setattr(verdict_mod, "next_earnings_for", lambda t, **k: sched)

    v = synthesize_verdict(
        ticker="AVGO",
        as_of=date(2026, 6, 2),
        strategy_results=[primary],
        regime=offline_default(),
    )
    assert v.verdict == "WATCH"
    assert v.event_blackout is not None
    assert v.event_blackout.kind == "earnings"
    assert v.event_blackout.release == "EARNINGS"
    assert v.event_blackout.suppressed_to == "WATCH"
    assert any("Calendar blackout" in s for s in v.why.what_could_invalidate)
    # earnings inside hold window \u2192 pre-earnings exit set
    assert v.pre_earnings_exit_by is not None
    assert "clamped to earnings exit" in v.max_hold


def test_macro_blackout_demotes_long(monkeypatch):
    primary = _mk_result("S1_trend_50_200", fired=True, score=0.95)
    sched = datetime.now(UTC) + timedelta(hours=36)
    br = BlackoutReason(release="CPI", scheduled_at=sched, hours_until=36.0, confirmed=True)
    monkeypatch.setattr(verdict_mod, "is_blackout", lambda t, side, **k: br if side == "LONG" else None)

    v = synthesize_verdict(
        ticker="MSFT",
        as_of=date(2026, 6, 2),
        strategy_results=[primary],
        regime=offline_default(),
    )
    assert v.verdict == "WATCH"
    assert v.event_blackout is not None
    assert v.event_blackout.kind == "macro"
    assert v.event_blackout.release == "CPI"


def test_no_demote_when_no_setup(monkeypatch):
    """Blackout should NOT manufacture an event_blackout when nothing fired."""
    nf = _mk_result("S1_trend_50_200", fired=False, score=0.30)
    sched = datetime.now(UTC) + timedelta(hours=20)
    br = BlackoutReason(release="EARNINGS", scheduled_at=sched, hours_until=20.0, confirmed=True)
    monkeypatch.setattr(verdict_mod, "is_blackout", lambda *a, **k: br)

    v = synthesize_verdict(
        ticker="AAPL",
        as_of=date(2026, 6, 2),
        strategy_results=[nf],
        regime=offline_default(),
    )
    assert v.verdict == "NO_SETUP"
    assert v.event_blackout is None  # not applied when nothing fires


def test_calendar_stale_propagated(monkeypatch):
    monkeypatch.setattr(verdict_mod, "calendar_is_stale", lambda **k: True)
    primary = _mk_result("S1_trend_50_200", fired=True, score=0.95)
    v = synthesize_verdict(
        ticker="NVDA",
        as_of=date(2026, 6, 2),
        strategy_results=[primary],
        regime=offline_default(),
    )
    assert v.calendar_stale is True
