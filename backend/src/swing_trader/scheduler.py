"""APScheduler wiring."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .config import settings

log = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


def start_scheduler(refresh_fn: Callable[[], dict]) -> BackgroundScheduler:
    """Start (or return existing) background scheduler running `refresh_fn` every N hours."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    sched = BackgroundScheduler(timezone="UTC")
    sched.add_job(
        refresh_fn,
        IntervalTrigger(hours=settings.refresh_interval_hours),
        id="refresh",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    if settings.refresh_on_boot:
        sched.add_job(
            refresh_fn,
            DateTrigger(run_date=datetime.now(UTC).replace(tzinfo=None) + timedelta(seconds=5)),
            id="boot_refresh",
            replace_existing=True,
        )
    sched.start()
    log.info(
        "scheduler started: interval=%dh, on_boot=%s",
        settings.refresh_interval_hours,
        settings.refresh_on_boot,
    )
    _scheduler = sched
    return sched
