"""Tests for the macro/earnings calendar plumbing.

We avoid touching the network: monkeypatch the fetcher functions and exercise
the database upsert + blackout helpers end-to-end against a temp SQLite file.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import select


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    """Point settings + db engine at an isolated SQLite file for this test."""
    db_path = tmp_path / "test_swing.db"
    db_url = f"sqlite:///{db_path}"

    # Re-import the modules with a fresh engine bound to tmp_path.
    import importlib

    from swing_trader import config as cfg_mod
    from swing_trader.data import db as db_mod

    monkeypatch.setattr(cfg_mod.settings, "database_url", db_url)
    monkeypatch.setattr(cfg_mod.settings, "calendars_enabled", True)
    monkeypatch.setattr(cfg_mod.settings, "macro_blackout_hours", 48)

    # Rebuild the engine + sessionmaker bound to the new URL.
    new_engine = db_mod.create_engine(
        db_url, future=True, connect_args={"check_same_thread": False}
    )
    new_session = db_mod.sessionmaker(bind=new_engine, autoflush=False, expire_on_commit=False)
    monkeypatch.setattr(db_mod, "engine", new_engine)
    monkeypatch.setattr(db_mod, "SessionLocal", new_session)
    db_mod.Base.metadata.create_all(new_engine)

    yield db_mod


def test_macro_calendar_upserts_and_blackouts(tmp_db, monkeypatch):
    from swing_trader.data import calendar_refresh
    from swing_trader.data.macro_calendar import MacroEvent
    from swing_trader.data.earnings_calendar import EarningsEvent
    from swing_trader.engine import blackout

    now = datetime(2026, 6, 2, 12, 0, tzinfo=UTC)

    # Fake macro events: CPI in 36h (inside 48h window), FOMC in 5d (outside).
    fake_macro = [
        MacroEvent(release="CPI", scheduled_at=now + timedelta(hours=36), source="fred"),
        MacroEvent(release="FOMC", scheduled_at=now + timedelta(days=5), source="fed_json"),
    ]
    fake_earnings = [
        EarningsEvent(symbol="NVDA", scheduled_at=now + timedelta(hours=12), source="finnhub"),
        EarningsEvent(symbol="AAPL", scheduled_at=now + timedelta(days=10), source="finnhub"),
    ]
    monkeypatch.setattr(calendar_refresh, "fetch_next_window", lambda: fake_macro)
    monkeypatch.setattr(calendar_refresh, "fetch_earnings_window", lambda *_a, **_k: fake_earnings)

    summary = calendar_refresh.refresh_calendars(["NVDA", "AAPL"])
    assert summary.macro_total == 2
    assert summary.earnings_total == 2
    assert summary.macro_inserted == 2
    assert summary.earnings_inserted == 2
    assert summary.errors == []

    # Idempotency: second run shouldn't double-count
    summary2 = calendar_refresh.refresh_calendars(["NVDA", "AAPL"])
    assert summary2.macro_inserted == 0
    assert summary2.earnings_inserted == 0

    # NVDA earnings 12h away → blackout for both LONG and SHORT
    r = blackout.is_blackout("NVDA", "LONG", now=now)
    assert r is not None
    assert r.release == "EARNINGS"
    assert r.hours_until == pytest.approx(12.0, abs=0.5)

    r2 = blackout.is_blackout("NVDA", "SHORT", now=now)
    assert r2 is not None  # earnings blackout is two-sided

    # MSFT (no earnings, no targeted macro) but CPI in 36h → macro long blackout
    r3 = blackout.is_blackout("MSFT", "LONG", now=now)
    assert r3 is not None
    assert r3.release == "CPI"

    # SHORT side ignores macro
    r4 = blackout.is_blackout("MSFT", "SHORT", now=now)
    assert r4 is None

    # AAPL earnings 10d out → outside window → clear
    r5 = blackout.is_blackout("AAPL", "LONG", now=now)
    # but CPI macro still hits LONG side
    assert r5 is not None and r5.release == "CPI"

    # FOMC at 5d shouldn't trigger inside a 48h window
    far_now = now + timedelta(days=4)  # FOMC now ~24h away → should hit
    r6 = blackout.is_blackout("AAPL", "LONG", now=far_now)
    assert r6 is not None and r6.release == "FOMC"

    # next_earnings_for returns the soonest future earnings
    nxt = blackout.next_earnings_for("NVDA", now=now)
    assert nxt is not None
    assert (nxt - now).total_seconds() == pytest.approx(12 * 3600, abs=60)


def test_blackout_fail_open_on_empty_db(tmp_db):
    from swing_trader.engine import blackout

    # No events in DB → no blackout, no errors
    r = blackout.is_blackout("NVDA", "LONG")
    assert r is None
    assert blackout.calendar_is_stale() is True


def test_calendars_disabled_short_circuits(tmp_db, monkeypatch):
    from swing_trader import config as cfg_mod
    from swing_trader.engine import blackout

    monkeypatch.setattr(cfg_mod.settings, "calendars_enabled", False)
    assert blackout.is_blackout("NVDA", "LONG") is None
