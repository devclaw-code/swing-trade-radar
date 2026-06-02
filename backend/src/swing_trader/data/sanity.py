"""Data sanity checks — flag suspicious price/indicator data BEFORE signals fire.

Catches:
  - Price extended far from SMA50 / SMA200 (chase risk / possible bad data)
  - Stock splits (sudden ~>40% jump/drop without context)
  - Stale prices (close unchanged N consecutive bars)
  - Decimal placement errors (~10x or ~100x intraday move)
  - Abnormal feed values (NaN / zero / negative where impossible,
    RSI outside [0, 100], ATR <= 0)

These flags are advisory — they attach to verdicts so the UI can render a
yellow/red banner. They do NOT short-circuit signal generation; the caller
decides what to do with severity == "high".
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Literal

import numpy as np
import pandas as pd

Severity = Literal["info", "warning", "high"]

FlagCode = Literal[
    "extended_above_sma50",
    "extended_below_sma50",
    "extended_above_sma200",
    "extended_below_sma200",
    "possible_split",
    "stale_price",
    "decimal_shift",
    "nan_price",
    "non_positive_price",
    "rsi_out_of_range",
    "non_positive_atr",
    "insufficient_history",
    "nan_indicator",
]


@dataclass
class SanityFlag:
    """A single data sanity flag attached to a ticker verdict."""

    code: FlagCode
    severity: Severity
    message: str
    value: float | None = None
    threshold: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Tunables (kept module-level so tests can monkey-patch)
# ---------------------------------------------------------------------------

EXTENDED_SMA50_WARN = 0.30   # 30% above/below SMA50 → warning
EXTENDED_SMA50_HIGH = 0.40   # 40%+ above/below SMA50 → high
EXTENDED_SMA200_WARN = 0.40  # 40% from SMA200 → warning
EXTENDED_SMA200_HIGH = 0.60  # 60%+ from SMA200 → high

SPLIT_RATIO = 0.40           # > 40% bar-over-bar move = possible split
DECIMAL_SHIFT_RATIO = 5.0    # >5x intraday range vs prev close = decimal error

STALE_BARS = 5               # N consecutive bars with identical close
RSI_MIN, RSI_MAX = 0.0, 100.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe(x) -> float | None:
    """Coerce to float, returning None for NaN/inf/None."""
    if x is None:
        return None
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(f):
        return None
    return f


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def check_data_sanity(df: pd.DataFrame, *, ticker: str = "") -> list[SanityFlag]:
    """Run all sanity checks on an enriched OHLCV dataframe.

    Args:
        df: Enriched dataframe (post-`indicators.enrich`). Lowercase columns
            with at least: open/high/low/close/volume; indicators optional.
        ticker: Symbol, used only for logging/debug — flags do not embed it.

    Returns:
        A list of SanityFlag — empty when nothing looks suspicious.
    """
    flags: list[SanityFlag] = []

    if df is None or df.empty:
        flags.append(
            SanityFlag(
                code="insufficient_history",
                severity="high",
                message="No price data available.",
            )
        )
        return flags

    # We need at least 1 bar to do anything; ideally 2+ for diff checks.
    if len(df) < 2:
        flags.append(
            SanityFlag(
                code="insufficient_history",
                severity="warning",
                message=f"Only {len(df)} bar(s) of history — checks limited.",
            )
        )

    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else None

    flags.extend(_check_price_validity(last, prev))
    flags.extend(_check_extended_vs_ma(last))
    flags.extend(_check_split(last, prev))
    flags.extend(_check_decimal_shift(last, prev))
    flags.extend(_check_stale(df))
    flags.extend(_check_indicator_ranges(last))

    return flags


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def _check_price_validity(last: pd.Series, prev: pd.Series | None) -> list[SanityFlag]:
    out: list[SanityFlag] = []
    for col in ("open", "high", "low", "close"):
        if col not in last.index:
            continue
        v = _safe(last[col])
        if v is None:
            out.append(
                SanityFlag(
                    code="nan_price",
                    severity="high",
                    message=f"Latest bar `{col}` is NaN/inf.",
                )
            )
            continue
        if v <= 0:
            out.append(
                SanityFlag(
                    code="non_positive_price",
                    severity="high",
                    message=f"Latest bar `{col}` is non-positive ({v}).",
                    value=v,
                )
            )
    if "volume" in last.index:
        vol = _safe(last["volume"])
        if vol is not None and vol < 0:
            out.append(
                SanityFlag(
                    code="non_positive_price",
                    severity="warning",
                    message=f"Latest bar volume is negative ({vol}).",
                    value=vol,
                )
            )
    return out


def _check_extended_vs_ma(last: pd.Series) -> list[SanityFlag]:
    out: list[SanityFlag] = []
    close = _safe(last.get("close"))
    if close is None or close <= 0:
        return out

    sma50 = _safe(last.get("sma50"))
    if sma50 is not None and sma50 > 0:
        diff = (close - sma50) / sma50
        absdiff = abs(diff)
        if absdiff >= EXTENDED_SMA50_HIGH:
            out.append(
                SanityFlag(
                    code="extended_above_sma50" if diff > 0 else "extended_below_sma50",
                    severity="high",
                    message=(
                        f"Price is {diff * 100:+.1f}% vs SMA50 — "
                        "extended / possible data issue / chase risk."
                    ),
                    value=round(diff, 4),
                    threshold=EXTENDED_SMA50_HIGH,
                )
            )
        elif absdiff >= EXTENDED_SMA50_WARN:
            out.append(
                SanityFlag(
                    code="extended_above_sma50" if diff > 0 else "extended_below_sma50",
                    severity="warning",
                    message=(
                        f"Price is {diff * 100:+.1f}% vs SMA50 — extended."
                    ),
                    value=round(diff, 4),
                    threshold=EXTENDED_SMA50_WARN,
                )
            )

    sma200 = _safe(last.get("sma200"))
    if sma200 is not None and sma200 > 0:
        diff = (close - sma200) / sma200
        absdiff = abs(diff)
        if absdiff >= EXTENDED_SMA200_HIGH:
            out.append(
                SanityFlag(
                    code="extended_above_sma200" if diff > 0 else "extended_below_sma200",
                    severity="high",
                    message=(
                        f"Price is {diff * 100:+.1f}% vs SMA200 — "
                        "extended / possible data issue / chase risk."
                    ),
                    value=round(diff, 4),
                    threshold=EXTENDED_SMA200_HIGH,
                )
            )
        elif absdiff >= EXTENDED_SMA200_WARN:
            out.append(
                SanityFlag(
                    code="extended_above_sma200" if diff > 0 else "extended_below_sma200",
                    severity="warning",
                    message=(
                        f"Price is {diff * 100:+.1f}% vs SMA200 — extended."
                    ),
                    value=round(diff, 4),
                    threshold=EXTENDED_SMA200_WARN,
                )
            )

    return out


def _check_split(last: pd.Series, prev: pd.Series | None) -> list[SanityFlag]:
    if prev is None:
        return []
    pc = _safe(prev.get("close"))
    c = _safe(last.get("close"))
    if pc is None or c is None or pc <= 0 or c <= 0:
        return []
    ratio = abs(c - pc) / pc
    if ratio >= SPLIT_RATIO:
        direction = "drop" if c < pc else "jump"
        return [
            SanityFlag(
                code="possible_split",
                severity="warning",
                message=(
                    f"Close moved {ratio * 100:.1f}% bar-over-bar ({direction}) — "
                    "possible stock split or corporate action; verify data feed."
                ),
                value=round(ratio, 4),
                threshold=SPLIT_RATIO,
            )
        ]
    return []


def _check_decimal_shift(last: pd.Series, prev: pd.Series | None) -> list[SanityFlag]:
    """Detect ~10x or ~100x decimal-shift errors. The clearest signature is an
    intraday range that is multiples of the previous close.
    """
    if prev is None:
        return []
    pc = _safe(prev.get("close"))
    hi = _safe(last.get("high"))
    lo = _safe(last.get("low"))
    c = _safe(last.get("close"))
    if pc is None or pc <= 0 or hi is None or lo is None or c is None:
        return []

    # Ratio of close to prev close — close to 10 or 100 (or 0.1, 0.01) is suspect.
    rel = c / pc
    suspicious_ratios = (10.0, 100.0, 0.1, 0.01)
    for target in suspicious_ratios:
        if abs(rel - target) / target <= 0.10:  # within 10% of an integer decimal shift
            return [
                SanityFlag(
                    code="decimal_shift",
                    severity="high",
                    message=(
                        f"Close is {rel:.2f}x prior close — possible decimal placement error."
                    ),
                    value=round(rel, 4),
                    threshold=target,
                )
            ]

    # Fallback: intraday range many multiples of prior close also indicates a glitch.
    rng = hi - lo
    if rng > 0 and rng / pc >= DECIMAL_SHIFT_RATIO:
        return [
            SanityFlag(
                code="decimal_shift",
                severity="high",
                message=(
                    f"Intraday range is {rng / pc:.1f}x prior close — likely bad tick / decimal error."
                ),
                value=round(rng / pc, 4),
                threshold=DECIMAL_SHIFT_RATIO,
            )
        ]
    return []


def _check_stale(df: pd.DataFrame) -> list[SanityFlag]:
    if "close" not in df.columns or len(df) < STALE_BARS + 1:
        return []
    tail = df["close"].tail(STALE_BARS).to_numpy()
    if np.any(~np.isfinite(tail)):
        return []
    if np.allclose(tail, tail[0], rtol=0, atol=1e-9):
        return [
            SanityFlag(
                code="stale_price",
                severity="warning",
                message=(
                    f"Close unchanged for {STALE_BARS} consecutive bars — possible stale feed."
                ),
                value=float(tail[0]),
                threshold=float(STALE_BARS),
            )
        ]
    return []


def _check_indicator_ranges(last: pd.Series) -> list[SanityFlag]:
    out: list[SanityFlag] = []

    if "rsi14" in last.index:
        rsi = _safe(last.get("rsi14"))
        if rsi is None:
            # RSI legitimately NaN early in series — not an error unless deep into history.
            pass
        elif rsi < RSI_MIN or rsi > RSI_MAX:
            out.append(
                SanityFlag(
                    code="rsi_out_of_range",
                    severity="high",
                    message=f"RSI(14) = {rsi:.2f} is outside [0, 100].",
                    value=round(rsi, 4),
                )
            )

    if "atr14" in last.index:
        atr = _safe(last.get("atr14"))
        if atr is not None and atr <= 0:
            out.append(
                SanityFlag(
                    code="non_positive_atr",
                    severity="high",
                    message=f"ATR(14) = {atr:.4f} is non-positive.",
                    value=round(atr, 4),
                )
            )

    return out


def highest_severity(flags: list[SanityFlag]) -> Severity | None:
    """Return the worst severity in a list, or None if empty."""
    if not flags:
        return None
    order = {"info": 0, "warning": 1, "high": 2}
    return max(flags, key=lambda f: order.get(f.severity, 0)).severity


__all__ = [
    "FlagCode",
    "SanityFlag",
    "Severity",
    "check_data_sanity",
    "highest_severity",
]
