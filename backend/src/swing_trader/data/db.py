"""Database models + session factory (SQLAlchemy 2.0)."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from ..config import settings


class Base(DeclarativeBase):
    pass


class Price(Base):
    __tablename__ = "prices"
    ticker: Mapped[str] = mapped_column(String(10), primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float)


class News(Base):
    __tablename__ = "news"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(1024))
    summary: Mapped[str] = mapped_column(String(4096), default="")
    source: Mapped[str] = mapped_column(String(128))
    url: Mapped[str] = mapped_column(String(2048))
    published_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    tickers: Mapped[list[str]] = mapped_column(JSON, default=list)
    sentiment: Mapped[str] = mapped_column(String(8), default="neu")  # pos|neu|neg
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)


class Signal(Base):
    __tablename__ = "signals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), index=True)
    strategy: Mapped[str] = mapped_column(String(64), index=True)
    direction: Mapped[str] = mapped_column(String(8))  # LONG|SHORT
    entry: Mapped[float] = mapped_column(Float)
    target: Mapped[float] = mapped_column(Float)
    stop: Mapped[float] = mapped_column(Float)
    stop_pct: Mapped[float] = mapped_column(Float)
    rr_ratio: Mapped[float] = mapped_column(Float)
    risk: Mapped[str] = mapped_column(String(8))  # LOW|MED|HIGH
    confidence: Mapped[float] = mapped_column(Float)
    confirmations: Mapped[list[str]] = mapped_column(JSON, default=list)
    bar_date: Mapped[date] = mapped_column(Date)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    __table_args__ = (UniqueConstraint("ticker", "strategy", "bar_date", "direction"),)


class Run(Base):
    __tablename__ = "runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    n_signals: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[int] = mapped_column(Integer, default=0)
    log_summary: Mapped[str] = mapped_column(String(4096), default="")


class Meta(Base):
    __tablename__ = "meta"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[Any] = mapped_column(JSON)


class Backtest(Base):
    __tablename__ = "backtests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy: Mapped[str] = mapped_column(String(64), index=True)
    ticker: Mapped[str] = mapped_column(String(10), index=True)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    n_trades: Mapped[int] = mapped_column(Integer)
    win_rate: Mapped[float] = mapped_column(Float)
    avg_r: Mapped[float] = mapped_column(Float)
    profit_factor: Mapped[float] = mapped_column(Float)
    max_dd_r: Mapped[float] = mapped_column(Float)
    sharpe: Mapped[float] = mapped_column(Float)
    avg_hold_bars: Mapped[float] = mapped_column(Float)
    ran_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


# --- Engine + session --------------------------------------------------------

engine = create_engine(
    settings.database_url,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    """Create tables if missing."""
    Base.metadata.create_all(engine)


@contextmanager
def session_scope():
    """Context-managed DB session."""
    s = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
