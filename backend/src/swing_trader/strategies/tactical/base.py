"""Tactical strategy base + result dataclass.

Mirrors the v2 ``StrategyResult`` shape but trimmed for short-term setups and
carries the fields the tactical API card needs (``time_horizon``,
``volatility_atr``, structural entry/stop overrides).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar

import pandas as pd

from ...schemas import EvidenceItem

# Every tactical setup shares the same regime gate.
REGIME_FILTER = "Price > 200 SMA"


@dataclass
class TacticalResult:
    """Per-setup, per-ticker tactical evaluation (latest bar)."""

    setup_id: str
    setup_name: str
    fired: bool
    score: float  # 0..1
    evidence: list[EvidenceItem] = field(default_factory=list)
    invalidation_conditions: list[str] = field(default_factory=list)
    headline: str = ""

    # Trade plan (populated when fired).
    entry_price: float | None = None
    stop_price: float | None = None
    target_price: float | None = None
    entry_type: str = "market"  # "market" | "stop" (buy-stop breakout)
    max_hold_days: int = 5
    expected_hold_days: float | None = None  # data-backed median; None -> use cap
    volatility_atr: float | None = None
    rr_realized: float | None = None
    risk_tier: str = "MEDIUM"

    time_horizon: ClassVar[str] = "Tactical"


class TacticalStrategy(ABC):
    """Abstract base for tactical (1\u20135 day) setups."""

    setup_id: ClassVar[str] = "T0"
    setup_name: ClassVar[str] = "base_tactical"
    risk_tier: ClassVar[str] = "MEDIUM"
    max_hold_days: ClassVar[int] = 5

    @abstractmethod
    def evaluate(self, df: pd.DataFrame, ticker: str) -> TacticalResult:
        """Evaluate the most recent bar of an enriched OHLCV frame."""

    # -- shared helpers ----------------------------------------------------

    def _not_fired(self, *, score: float = 0.0, headline: str = "") -> TacticalResult:
        return TacticalResult(
            setup_id=self.setup_id,
            setup_name=self.setup_name,
            fired=False,
            score=score,
            headline=headline or f"{self.setup_name}: no setup.",
            risk_tier=self.risk_tier,
            max_hold_days=self.max_hold_days,
        )

    @staticmethod
    def _regime_ok(close: float, sma200: float) -> bool:
        """Shared regime gate: Price > 200 SMA. NaN sma200 -> fail closed."""
        try:
            return bool(close > sma200) and sma200 == sma200  # NaN check
        except Exception:
            return False
