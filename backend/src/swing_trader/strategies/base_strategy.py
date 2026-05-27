"""Strategy base + shared dataclasses."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Literal

import pandas as pd

from ..config import settings

Direction = Literal["LONG", "SHORT"]


@dataclass
class Signal:
    """One trade signal produced by a strategy on a given bar."""

    ticker: str
    strategy: str
    direction: Direction
    entry: float
    target: float
    stop: float
    confirmations: list[str] = field(default_factory=list)
    confidence: float = 0.5
    bar_date: date | None = None
    generated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None)
    )


def default_target(entry: float, stop: float, direction: Direction) -> float:
    """Compute a 2R target when a strategy doesn't define one."""
    risk = abs(entry - stop)
    return entry + risk * settings.default_target_rr * (1 if direction == "LONG" else -1)


class BaseStrategy(ABC):
    """Abstract base for all strategies."""

    name: str = "base"

    @abstractmethod
    def generate(self, df: pd.DataFrame, ticker: str) -> list[Signal]:
        """Generate signals from an enriched OHLCV df. Should return [] if no signal."""
