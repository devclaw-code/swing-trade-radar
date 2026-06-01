"""V2 strategy base + StrategyResult dataclass."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar

import pandas as pd

from ...schemas import EvidenceItem


@dataclass
class StrategyResult:
    """Per-strategy, per-ticker evaluation."""

    strategy_name: str
    fired: bool
    score: float  # 0..1 — strategy's confidence/strength signal
    evidence: list[EvidenceItem] = field(default_factory=list)
    invalidation_conditions: list[str] = field(default_factory=list)
    counter_argument_keys: list[str] = field(default_factory=list)
    doc_refs: list[str] = field(default_factory=list)
    headline: str = ""

    # Trade plan — only populated when fired (or when WATCH-able)
    entry_price: float | None = None
    stop_price: float | None = None
    target_price: float | None = None
    max_hold_days: int | None = None
    risk_tier: str = "MEDIUM"  # LOW | MEDIUM | HIGH


class V2Strategy(ABC):
    """Abstract base for v2 verdict-style strategies."""

    name: ClassVar[str] = "base_v2"
    doc_refs: ClassVar[list[str]] = []
    counter_argument_keys: ClassVar[list[str]] = []
    risk_tier: ClassVar[str] = "MEDIUM"

    @abstractmethod
    def evaluate(
        self,
        df: pd.DataFrame,
        ticker: str,
        basket_data: dict[str, pd.DataFrame] | None = None,
    ) -> StrategyResult:
        """Evaluate the most recent bar. ``df`` is enriched OHLCV."""
