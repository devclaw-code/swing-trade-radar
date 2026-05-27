"""REST API routes."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlalchemy import select

from ..data.db import Meta, Run, session_scope
from ..data.news_scraper import latest_news
from ..engine.backtester import backtest_all, latest_results
from ..engine.signal_generator import latest_open_signals

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
    sigs = latest_open_signals(risk=risk, strategy=strategy, direction=direction)
    return {"count": len(sigs), "signals": sigs}


@router.get("/strategies/{ticker}")
def strategies_for_ticker(ticker: str) -> dict:
    sigs = latest_open_signals(ticker=ticker)
    if not sigs:
        raise HTTPException(404, detail=f"no open signals for {ticker.upper()}")
    return {"ticker": ticker.upper(), "count": len(sigs), "signals": sigs}


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


@router.post("/backtest/run")
def backtest_run(bg: BackgroundTasks) -> dict:
    """Kick off a full backtest run in the background."""
    bg.add_task(backtest_all)
    return {"status": "started"}
