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
from .data.calendar_refresh import refresh_calendars

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
    if settings.calendars_enabled:
        sched.add_job(
            lambda: refresh_calendars(settings.tickers),
            CronTrigger(
                hour=settings.calendar_refresh_hour_utc,
                minute=settings.calendar_refresh_minute_utc,
                timezone="UTC",
            ),
            id="refresh_calendars",
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )
        log.info(
            "calendar refresh cron: %02d:%02dZ daily",
            settings.calendar_refresh_hour_utc,
            settings.calendar_refresh_minute_utc,
        )
        # boot-time hydrate so a cold start has data immediately
        sched.add_job(
            lambda: refresh_calendars(settings.tickers),
            DateTrigger(run_date=datetime.now(UTC).replace(tzinfo=None) + timedelta(seconds=10)),
            id="boot_calendar_refresh",
            replace_existing=True,
        )
    sched.start()
    log.info("scheduler started (on_boot=%s)", settings.refresh_on_boot)
    _scheduler = sched
    return sched
