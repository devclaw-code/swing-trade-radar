"""APScheduler wiring."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
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
    if settings.refresh_cron_enabled:
        # Market-close trigger: weekdays at HH:MM in market timezone (default 16:05 ET).
        sched.add_job(
            refresh_fn,
            CronTrigger(
                day_of_week="mon-fri",
                hour=settings.refresh_cron_hour,
                minute=settings.refresh_cron_minute,
                timezone=settings.market_timezone,
            ),
            id="refresh",
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )
        log.info(
            "refresh cron: %s %02d:%02d (%s)",
            "mon-fri",
            settings.refresh_cron_hour,
            settings.refresh_cron_minute,
            settings.market_timezone,
        )
    else:
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
    log.info("scheduler started (on_boot=%s)", settings.refresh_on_boot)
    _scheduler = sched
    return sched
