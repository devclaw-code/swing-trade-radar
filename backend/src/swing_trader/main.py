"""FastAPI entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router as api_router
from .config import settings
from .data.db import Meta, Run, init_db, session_scope
from .data.news_scraper import scrape_all as scrape_news
from .data.price_fetcher import fetch_all
from .engine.signal_generator import generate_all, generate_verdicts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)
log = logging.getLogger("swing_trader")


def run_refresh_pipeline() -> dict:
    """Full refresh: fetch prices → generate signals → bump version."""
    log.info("refresh pipeline: start")
    with session_scope() as s:
        run = Run()
        s.add(run)
        s.flush()
        run_id = run.id

    errors = 0
    try:
        fetched = fetch_all()
        log.info("fetched: %s", {k: v for k, v in fetched.items() if v})
    except Exception as e:
        log.exception("price fetch failed: %s", e)
        errors += 1
        fetched = {}

    try:
        news_summary = scrape_news()
        log.info("news scraped: %s", news_summary)
    except Exception as e:
        log.exception("news scrape failed: %s", e)
        errors += 1
        news_summary = {}

    try:
        summary = generate_all()
        errors += summary.get("errors", 0)
        n_signals = summary.get("n_signals", 0)
    except Exception as e:
        log.exception("signal generation failed: %s", e)
        errors += 1
        n_signals = 0
        summary = {}

    # Synthesize + persist per-ticker verdicts off the freshly-fetched prices.
    # Without this the verdict cards the UI reads (/api/verdicts) only refresh
    # on a manual POST /api/verdicts/run and silently freeze at the last run.
    try:
        verdict_summary = generate_verdicts()
        verdict_errors = verdict_summary.get("errors", 0)
        n_verdicts = verdict_summary.get("n_verdicts", 0)
        log.info("verdicts synthesized: %d", n_verdicts)
    except Exception as e:
        log.exception("verdict generation failed: %s", e)
        verdict_errors = 1
        n_verdicts = 0
        verdict_summary = {}
    errors += verdict_errors

    # Bump version + close run row.
    from datetime import UTC
    from datetime import datetime as _dt

    with session_scope() as s:
        run = s.get(Run, run_id)
        if run:
            run.finished_at = _dt.now(UTC).replace(tzinfo=None)
            run.n_signals = n_signals
            run.errors = errors
            run.log_summary = str(
                {
                    "fetched": fetched,
                    "news": news_summary,
                    "signals": summary,
                    "verdicts": {
                        "n": n_verdicts,
                        "errors": verdict_errors,
                    },
                }
            )[:4000]
        v = s.get(Meta, "version")
        if v is None:
            s.add(Meta(key="version", value=1))
        else:
            v.value = int(v.value) + 1
    log.info("refresh pipeline: done (signals=%d, errors=%d)", n_signals, errors)
    return {"n_signals": n_signals, "errors": errors}


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Warm the tactical expected-hold cache off the request path so the first
    # /api/tactical scan returns real medians without an inline replay.
    try:
        import threading

        from .engine.tactical_holds import warm_expected_holds

        threading.Thread(target=warm_expected_holds, name="warm-holds-boot", daemon=True).start()
    except Exception as e:
        log.warning("expected-hold warm-on-boot failed to start: %s", e)
    if settings.refresh_on_boot:
        # APScheduler will also be wired in scheduler.py; for now boot kicks once.
        try:
            from .scheduler import start_scheduler

            start_scheduler(run_refresh_pipeline)
        except Exception as e:
            log.exception("scheduler start failed: %s", e)
    yield


app = FastAPI(title="Swing Trade Radar", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)


def main() -> None:
    uvicorn.run(
        "swing_trader.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
