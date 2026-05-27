"""Application configuration (env-driven, override via `.env`)."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BACKEND_ROOT / "var"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    """Runtime configuration. All knobs in one place."""

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Universe ----------------------------------------------------------
    tickers: list[str] = Field(
        default=[
            "AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN", "TSLA", "AVGO",
            "AMD", "INTC", "QCOM", "MU", "ORCL", "CRM", "ADBE", "NFLX",
            "PYPL", "CSCO", "TXN", "NOW",
        ]
    )

    # --- Storage -----------------------------------------------------------
    database_url: str = f"sqlite:///{DATA_DIR / 'swing.db'}"

    # --- Scheduler ---------------------------------------------------------
    # Cron mode (default): refresh once per trading day shortly after US close.
    refresh_cron_enabled: bool = True
    refresh_cron_hour: int = 16
    refresh_cron_minute: int = 5
    market_timezone: str = "America/New_York"
    # Interval mode (used when refresh_cron_enabled=False).
    refresh_interval_hours: int = 3
    refresh_on_boot: bool = True

    # --- Data sources ------------------------------------------------------
    alpha_vantage_api_key: str | None = None
    price_history_days: int = 250
    yfinance_request_timeout: float = 20.0

    # --- News --------------------------------------------------------------
    news_feeds: list[str] = Field(
        default=[
            "https://www.cnbc.com/id/100003114/device/rss/rss.html",
            "https://feeds.content.dowjones.io/public/rss/mw_topstories",
            "https://finance.yahoo.com/news/rssindex",
        ]
    )
    news_ttl_days: int = 7

    # --- Risk classifier thresholds ----------------------------------------
    risk_low_min_confirmations: int = 3
    risk_low_max_stop_pct: float = 0.03
    risk_low_min_rr: float = 2.5

    risk_med_min_confirmations: int = 2
    risk_med_max_stop_pct: float = 0.06
    risk_med_min_rr: float = 1.5

    # --- Strategy defaults -------------------------------------------------
    default_target_rr: float = 2.0  # used when a strategy doesn't define a target

    # --- API ---------------------------------------------------------------
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = Field(default=["http://localhost:3000", "http://localhost:8080"])


settings = Settings()
