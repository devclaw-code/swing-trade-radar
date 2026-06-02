"""REST API routes."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlalchemy import select

from ..config import settings
from ..data.db import Meta, Run, session_scope
from ..data.news_scraper import latest_news
from ..data.price_fetcher import load_ohlcv
from ..engine.backtester import backtest_all, latest_results
from ..engine.conservative import apply_conservative_filter
from ..engine.regime import compute_regime, offline_default
from ..engine.signal_generator import (
    generate_verdicts,
    latest_open_signals,
    latest_verdicts,
)
from ..schemas import RegimeContext, Verdict

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/health")
def health() -> dict:
    return {"ok": True, "ts": datetime.now(UTC).replace(tzinfo=None).isoformat()}


@router.get("/last-updated")
def last_updated() -> dict:
    with session_scope() as s:
        v_row = s.get(Meta, "version")
        version = int(v_row.value) if v_row else 0
        last_run = s.execute(
            select(Run).order_by(Run.started_at.desc()).limit(1)
        ).scalar_one_or_none()
    return {
        "version": version,
        "ts": last_run.finished_at.isoformat()
        if last_run and last_run.finished_at
        else None,
        "errors": last_run.errors if last_run else 0,
    }


@router.get("/strategies")
def strategies(
    risk: str | None = None,
    strategy: str | None = None,
    direction: str | None = None,
) -> dict:
    """List of v2 strategies + their backtest stats placeholder.

    Backwards-compat: if any of the legacy filter params are passed, fall back to
    the legacy open-signals listing (used by the v1 frontend).
    """
    if any(v is not None for v in (risk, strategy, direction)):
        sigs = latest_open_signals(risk=risk, strategy=strategy, direction=direction)
        return {"count": len(sigs), "signals": sigs, "deprecated": True}

    # v2: list strategy metadata
    from ..engine.signal_generator import default_v2_strategies
    from ..strategies.v2.base import V2Strategy

    descriptions: dict[str, str] = {
        "S1_trend_50_200": (
            "Classic trend-following: long when price is above the 50-day SMA and the 50-day "
            "is above the 200-day (golden cross intact). Enters on next-day open, ATR-based stop and target."
        ),
        "S2_clenow_momentum": (
            "Andreas Clenow style momentum: rank the basket by 90-day exponential-regression slope "
            "x R-squared; only top-decile names with low volatility and trend filter qualify."
        ),
        "S3_connors_rsi2": (
            "Larry Connors mean-reversion: 2-period RSI < 10 while price is above its 200-SMA, in a "
            "healthy VIX regime, with no earnings inside the hold window."
        ),
        "S4_minervini_vcp": (
            "Mark Minervini's VCP / Stage 2 trend template: tightening price contractions on "
            "declining volume, breakout above pivot with relative strength vs. the index."
        ),
        "S5_pead": (
            "Post-earnings announcement drift: ride the multi-week drift after a positive earnings "
            "surprise; gated by gap, volume, and surprise magnitude thresholds."
        ),
    }

    strats: list[V2Strategy] = default_v2_strategies()
    info = []
    for s in strats:
        # Derive a short id like "S1" from "S1_trend_50_200"
        short_id = s.name.split("_", 1)[0] if "_" in s.name else s.name
        info.append(
            {
                "id": short_id,
                "name": s.name,
                "description": descriptions.get(s.name, ""),
                "risk_tier": s.risk_tier,
                "doc_refs": list(s.doc_refs),
                "counter_argument_keys": list(s.counter_argument_keys),
                # TODO(devclaw): wire walk-forward backtest stats per strategy.
                "backtest": None,
            }
        )
    return {"count": len(info), "strategies": info}


@router.get("/strategies/legacy/{ticker}", deprecated=True)
def strategies_for_ticker(ticker: str) -> dict:
    sigs = latest_open_signals(ticker=ticker)
    if not sigs:
        raise HTTPException(404, detail=f"no open signals for {ticker.upper()}")
    return {"ticker": ticker.upper(), "count": len(sigs), "signals": sigs}


# ---------------------------------------------------------------------------
# v2 verdict routes
# ---------------------------------------------------------------------------


@router.get("/verdicts")
def verdicts_all(
    verdict: str | None = None,
    mode: str = "all",
) -> dict:
    """All tickers, today's verdicts (most recent per ticker).

    ``mode=all`` (default): legacy shape ``{count, verdicts}``.
    ``mode=conservative``: also includes ``passed``, ``marginal``, ``filtered_out``
    arrays from :func:`apply_conservative_filter`. ``verdicts`` is preserved
    for backward compat and contains the *unfiltered* list.
    """
    items = latest_verdicts(verdict=verdict)
    if mode != "conservative":
        return {"count": len(items), "verdicts": items}

    parsed = [Verdict(**row) for row in items]
    result = apply_conservative_filter(parsed, mode="conservative")
    return {
        "count": len(items),
        "verdicts": items,  # backward-compat: full list
        "mode": result.mode,
        "passed": [v.model_dump(mode="json") for v in result.passed],
        "marginal": [m.model_dump(mode="json") for m in result.marginal],
        "filtered_out": [f.model_dump(mode="json") for f in result.filtered_out],
    }


@router.get("/verdicts/{ticker}", response_model=Verdict)
def verdict_for_ticker(ticker: str) -> Verdict:
    rows = latest_verdicts(ticker=ticker)
    if not rows:
        raise HTTPException(404, detail=f"no verdict for {ticker.upper()}")
    return Verdict(**rows[0])


@router.get("/regime", response_model=RegimeContext)
def regime() -> RegimeContext:
    try:
        return compute_regime()
    except Exception:
        return offline_default()


@router.post("/verdicts/run")
def verdicts_run(bg: BackgroundTasks) -> dict:
    """Trigger a fresh verdict computation in the background."""
    bg.add_task(generate_verdicts)
    return {"status": "started"}


@router.get("/news")
def news(ticker: str | None = None, limit: int = 50) -> dict:
    items = latest_news(ticker=ticker, limit=limit)
    return {"count": len(items), "news": items}


@router.get("/backtest")
def backtest_all_results() -> dict:
    """All latest backtest results grouped by strategy."""
    rows = latest_results()
    grouped: dict[str, list[dict]] = {}
    for r in rows:
        grouped.setdefault(r["strategy"], []).append(r)
    return {"count": len(rows), "strategies": grouped}


@router.get("/backtest/{strategy}")
def backtest_for_strategy(strategy: str) -> dict:
    rows = latest_results(strategy=strategy)
    if not rows:
        raise HTTPException(404, detail=f"no backtest results for strategy '{strategy}'")
    return {"strategy": strategy, "count": len(rows), "results": rows}


@router.get("/ticker/{ticker}")
def ticker_detail(ticker: str, bars: int = 120) -> dict:
    """Per-ticker drill-down: OHLCV + signals + news + backtests."""
    t = ticker.upper()
    if t not in settings.tickers:
        raise HTTPException(404, detail=f"ticker '{t}' not in universe")

    bars = max(1, min(int(bars), 500))
    # Pad lookback_days a bit beyond bars (calendar vs trading days).
    df = load_ohlcv(t, lookback_days=int(bars * 1.7) + 14)
    if df.empty:
        raise HTTPException(404, detail=f"no cached OHLCV for {t}")

    df = df.tail(bars)
    ohlcv = [
        {
            "date": (idx.date().isoformat() if hasattr(idx, "date") else str(idx)),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": float(row["volume"]),
        }
        for idx, row in df.iterrows()
    ]

    signals = latest_open_signals(ticker=t)
    news_items = latest_news(ticker=t, limit=50)
    backtest = [r for r in latest_results() if r.get("ticker") == t]

    return {
        "ticker": t,
        "ohlcv": ohlcv,
        "signals": signals,
        "news": news_items,
        "backtest": backtest,
    }


@router.post("/backtest/run")
def backtest_run(bg: BackgroundTasks) -> dict:
    """Kick off a full backtest run in the background."""
    bg.add_task(backtest_all)
    return {"status": "started"}
