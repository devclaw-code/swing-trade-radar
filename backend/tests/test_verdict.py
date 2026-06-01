"""End-to-end test of synthesize_verdict with mock strategy results."""

from __future__ import annotations

from datetime import date

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
        doc_refs=["research/01 §3"],
        headline=f"{name} headline",
        entry_price=kw.get("entry", 100.0),
        stop_price=kw.get("stop", 95.0),
        target_price=kw.get("target", 110.0),
        max_hold_days=kw.get("max_hold", 10),
        risk_tier=kw.get("risk_tier", "MEDIUM"),
    )


def test_buy_when_high_conviction_and_favourable_regime():
    primary = _mk_result("S1_trend_50_200", fired=True, score=0.95)
    other = _mk_result("S3_connors_rsi2", fired=True, score=0.80)
    regime = offline_default()
    v = synthesize_verdict(
        ticker="NVDA",
        as_of=date(2026, 5, 30),
        strategy_results=[primary, other],
        regime=regime,
    )
    assert v.verdict == "BUY"
    assert v.primary_setup == "S1_trend_50_200"
    assert "S3_connors_rsi2" in v.supporting_setups
    assert v.entry_zone is not None and v.entry_zone.price == 100.0
    assert v.stop_loss is not None and v.target is not None
    assert v.target.rr == 2.0
    assert "shares" in v.position_size_hint
    assert v.conviction > 0.6


def test_no_setup_when_nothing_fires():
    nf = _mk_result("S1_trend_50_200", fired=False, score=0.30)
    v = synthesize_verdict(
        ticker="AAPL",
        as_of=date(2026, 5, 30),
        strategy_results=[nf],
        regime=offline_default(),
    )
    assert v.verdict == "NO_SETUP"
    assert v.primary_setup == ""


def test_avoid_when_regime_risk_off():
    primary = _mk_result("S1_trend_50_200", fired=True, score=0.9)
    risky = offline_default()
    risky = risky.model_copy(update={"regime_verdict": "unfavorable / risk-off"})
    v = synthesize_verdict(
        ticker="META",
        as_of=date(2026, 5, 30),
        strategy_results=[primary],
        regime=risky,
    )
    assert v.verdict == "AVOID"


def test_counter_arguments_pulled_from_yaml():
    primary = _mk_result("S1_trend_50_200", fired=True, score=0.9)
    v = synthesize_verdict(
        ticker="MSFT",
        as_of=date(2026, 5, 30),
        strategy_results=[primary],
        regime=offline_default(),
    )
    # counter_argument_keys=["trend_late_entry"] should resolve to a non-empty string
    assert len(v.why.counter_arguments) >= 1
    assert any("late" in c.lower() for c in v.why.counter_arguments)
