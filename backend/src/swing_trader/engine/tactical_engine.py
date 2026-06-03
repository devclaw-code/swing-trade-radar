"""Tactical Swings engine \u2014 fans the tactical setups across the universe.

Mirrors ``signal_generator.generate_verdicts`` (load \u2192 enrich \u2192 evaluate) but for
the short-term tactical book. Returns plain dicts ready for the ``/api/tactical``
payload. Adding a 3rd/4th setup = one import + one line in ``default_tactical_strategies``.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime

from ..config import settings
from ..data.price_fetcher import load_ohlcv
from ..strategies.tactical.base import REGIME_FILTER, TacticalResult, TacticalStrategy
from ..strategies.tactical.t1_rsi_exhaustion import RsiExhaustionStrategy
from ..strategies.tactical.t2_inside_day_breakout import InsideDayBreakoutStrategy
from .atr import compute_atr14
from .indicators import enrich
from .tactical_holds import expected_hold_for

log = logging.getLogger(__name__)


def default_tactical_strategies() -> list[TacticalStrategy]:
    """Tactical setup registry. Add new setups here."""
    return [
        RsiExhaustionStrategy(),
        InsideDayBreakoutStrategy(),
    ]


def _result_to_card(ticker: str, as_of: date, res: TacticalResult) -> dict:
    """Serialize a fired TacticalResult into the API card shape."""
    exp = res.expected_hold_days
    if exp is not None:
        # 1.5 -> "~1-2", 3.0 -> "~3" days.
        lo = int(exp)
        hi = lo + 1 if exp - lo >= 0.25 else lo
        exp_label = f"~{lo} days" if lo == hi else f"~{lo}-{hi} days"
    else:
        exp_label = None
    return {
        "ticker": ticker,
        "as_of": as_of.isoformat(),
        "time_horizon": "Tactical",
        "setup_id": res.setup_id,
        "setup_name": res.setup_name,
        "score": res.score,
        "headline": res.headline,
        "entry_zone": {"price": res.entry_price, "type": res.entry_type},
        "stop_loss": {"price": res.stop_price},
        "target": {"price": res.target_price, "rr": res.rr_realized},
        "max_hold": f"≤ {res.max_hold_days} trading days",
        "max_hold_days": res.max_hold_days,
        "expected_hold_days": res.expected_hold_days,
        "expected_hold": exp_label,
        "volatility_atr": (
            round(res.volatility_atr, 4) if res.volatility_atr is not None else None
        ),
        "risk_tier": res.risk_tier,
        "regime_filter": REGIME_FILTER,
        "evidence": [e.model_dump() for e in res.evidence],
        "invalidation_conditions": list(res.invalidation_conditions),
    }


def generate_tactical(*, only_fired: bool = True) -> dict:
    """Scan the universe for tactical setups. Returns ``{summary, cards}``.

    Network/parse failures per ticker are logged and skipped so one bad ticker
    never sinks the whole scan.
    """
    started = datetime.now(UTC).replace(tzinfo=None)
    strategies = default_tactical_strategies()
    cards: list[dict] = []
    errors = 0
    scanned = 0

    for ticker in settings.tickers:
        try:
            df = load_ohlcv(ticker)
            if df is None or df.empty:
                continue
            df = enrich(df)
            scanned += 1
            as_of = (
                df.index[-1].date()
                if hasattr(df.index[-1], "date")
                else datetime.now(UTC).date()
            )
            # Latest daily ATR \u2014 attached to every card regardless of which setup fires.
            ticker_atr = compute_atr14(df)

            for strat in strategies:
                try:
                    res = strat.evaluate(df, ticker)
                except Exception as e:
                    log.exception("tactical %s failed on %s: %s", strat.setup_id, ticker, e)
                    errors += 1
                    continue
                if only_fired and not res.fired:
                    continue
                if res.volatility_atr is None:
                    res.volatility_atr = ticker_atr
                if res.expected_hold_days is None:
                    res.expected_hold_days = expected_hold_for(res.setup_id)
                cards.append(_result_to_card(ticker, as_of, res))
        except Exception as e:
            log.warning("tactical ticker %s failed: %s", ticker, e)
            errors += 1

    # Highest-conviction first.
    cards.sort(key=lambda c: c.get("score") or 0.0, reverse=True)
    finished = datetime.now(UTC).replace(tzinfo=None)
    return {
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "regime_filter": REGIME_FILTER,
        "n_scanned": scanned,
        "n_cards": len(cards),
        "errors": errors,
        "cards": cards,
    }
