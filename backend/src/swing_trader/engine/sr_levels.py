"""Multi-method support/resistance level computation.

Pure, deterministic, no look-ahead. See research/09-support-resistance.md for the
design rationale. Produces a ranked set of S/R *zones* (not lines) near the
current price by stacking four methods and rewarding confluence:

  1. Swing pivots (fractals)      -> the gold-standard, multi-touch zones
  2. Classic floor pivot points   -> PP + R1..R3 / S1..S3 (weekly for Core)
  3. Fibonacci pivot points       -> Fib-weighted R/S (confluence votes)
  4. Fibonacci retracement        -> 23.6/38.2/50/61.8/78.6% of dominant swing

Candidates within ``0.5 * ATR(14)`` of each other collapse into one zone.
Each zone is scored 0..1 from touch count + distinct-method agreement +
recency + a psychological round-number bonus (see ``_score_zone``).
The nearest ``max_per_side`` supports below and resistances above price are kept.

This module is **display-only**: it never generates a trade and never feeds the
numeric conviction/score. Strength weights are starting guesses to be calibrated
against the walk-forward harness before they are trusted in any blend.
"""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
import pandas as pd

from ..schemas import SRLevel
from .risk_levels import PCT_FALLBACK, _atr_valid

Horizon = Literal["Core", "Tactical"]

# --- tuning knobs (calibrate against the walk-forward harness; see doc 09) ----
FIB_RATIOS: tuple[float, ...] = (0.236, 0.382, 0.500, 0.618, 0.786)
# Fib levels traders defend hardest get a touch-equivalent weight bonus.
FIB_GOLDEN: frozenset[float] = frozenset({0.500, 0.618})
BAND_ATR_MULT = 0.5  # cluster tolerance = 0.5 * ATR(14)

# Score blend weights (sum ~= 1.0).
W_TOUCH = 0.45
W_METHODS = 0.30
W_RECENCY = 0.15
W_ROUND = 0.10

# Normalization caps so a single huge cluster doesn't saturate the score.
_TOUCH_NORM_CAP = 5.0
_METHOD_NORM_CAP = 4.0
_RECENCY_HALFLIFE_BARS = 60.0  # recency weight decays to 0.5 over ~60 bars


# ---------------------------------------------------------------------------
# 1. Swing pivots (fractals)
# ---------------------------------------------------------------------------
def swing_points(high, low, n: int = 3) -> tuple[list[int], list[int]]:
    """Positional indices of *strict* swing highs/lows (fractal definition).

    Inputs are coerced to numpy arrays so indexing is positional. Passing a
    pandas Series with a datetime index would otherwise make ``high[i]`` a
    label lookup (wrong bar / KeyError). The center bar must be the *unique*
    extremum in its ``2n+1`` window, so a plateau (equal high to the right) is
    NOT counted as a swing.

    The last ``n`` bars are intentionally excluded: they cannot be confirmed
    swings yet (that would require future bars). No look-ahead.
    """
    high = np.asarray(high, dtype=float)
    low = np.asarray(low, dtype=float)
    sh: list[int] = []
    sl: list[int] = []
    if len(high) < 2 * n + 1:
        return sh, sl
    for i in range(n, len(high) - n):
        win_h = high[i - n : i + n + 1]
        win_l = low[i - n : i + n + 1]
        c_h = high[i]
        c_l = low[i]
        if not math.isnan(c_h) and c_h == np.nanmax(win_h) and int((win_h == c_h).sum()) == 1:
            sh.append(i)
        if not math.isnan(c_l) and c_l == np.nanmin(win_l) and int((win_l == c_l).sum()) == 1:
            sl.append(i)
    return sh, sl


# ---------------------------------------------------------------------------
# 2 + 3. Pivot points (classic + Fibonacci) from a prior period's H/L/C
# ---------------------------------------------------------------------------
def classic_pivots(high: float, low: float, close: float) -> dict[str, float]:
    """Floor-trader pivot points (PP + R1..R3 / S1..S3)."""
    pp = (high + low + close) / 3.0
    rng = high - low
    return {
        "PP": pp,
        "R1": 2 * pp - low,
        "S1": 2 * pp - high,
        "R2": pp + rng,
        "S2": pp - rng,
        "R3": high + 2 * (pp - low),
        "S3": low - 2 * (high - pp),
    }


def fib_pivots(high: float, low: float, close: float) -> dict[str, float]:
    """Fibonacci-weighted pivot points."""
    pp = (high + low + close) / 3.0
    rng = high - low
    return {
        "PP": pp,
        "R1": pp + 0.382 * rng,
        "S1": pp - 0.382 * rng,
        "R2": pp + 0.618 * rng,
        "S2": pp - 0.618 * rng,
        "R3": pp + 1.000 * rng,
        "S3": pp - 1.000 * rng,
    }


def _prior_period_hlc(
    df: pd.DataFrame | None, horizon: Horizon
) -> tuple[float, float, float] | None:
    """H/L/C of the prior period: prior *week* for Core, prior *day* for Tactical.

    Uses only fully-closed prior data (no look-ahead): the most recent complete
    week excludes the in-progress week; the prior day is the second-to-last bar.
    """
    if df is None or df.empty or len(df) < 2:
        return None
    if horizon == "Tactical":
        prev = df.iloc[-2]
        return float(prev["high"]), float(prev["low"]), float(prev["close"])
    # Core: resample to weekly, take the last *completed* week.
    if not isinstance(df.index, pd.DatetimeIndex):
        # No datetime index -> approximate "prior week" as the prior 5 bars
        # ending one bar before the latest (exclude the in-progress bar).
        window = df.iloc[-6:-1]
        if window.empty:
            return None
        return (
            float(window["high"].max()),
            float(window["low"].min()),
            float(window["close"].iloc[-1]),
        )
    weekly = df.resample("W").agg({"high": "max", "low": "min", "close": "last"}).dropna()
    if len(weekly) < 2:
        return None
    prev_week = weekly.iloc[-2]  # last fully-closed week
    return float(prev_week["high"]), float(prev_week["low"]), float(prev_week["close"])


# ---------------------------------------------------------------------------
# 4. Fibonacci retracement of the dominant recent swing
# ---------------------------------------------------------------------------
def fib_retracement(
    df: pd.DataFrame | None, swing_highs: list[int], swing_lows: list[int]
) -> list[tuple[float, str]]:
    """Retracement levels of the dominant (largest-amplitude) recent swing.

    Returns ``(price, source)`` pairs. The anchor is the swing-high/swing-low
    pair with the largest ``|high - low|`` amplitude among the confirmed swing
    points (not merely the most recent), so the retracement tracks the move
    traders are actually defending. The source string records which Fib ratio
    produced each level.
    """
    if df is None or df.empty or not swing_highs or not swing_lows:
        return []
    highs = np.asarray(df["high"].to_numpy(), dtype=float)
    lows = np.asarray(df["low"].to_numpy(), dtype=float)

    # Dominant swing = the (high_i, low_i) pair with the largest valid amplitude.
    best: tuple[float, int, int] | None = None  # (amplitude, high_i, low_i)
    for hi_i in swing_highs:
        hi = highs[hi_i]
        if math.isnan(hi):
            continue
        for lo_i in swing_lows:
            lo = lows[lo_i]
            if math.isnan(lo) or not (hi > lo):
                continue
            amp = hi - lo
            if best is None or amp > best[0]:
                best = (amp, hi_i, lo_i)
    if best is None:
        return []

    amplitude, last_high_i, last_low_i = best
    hi = highs[last_high_i]
    lo = lows[last_low_i]
    # Uptrend pullback support if the dominant high is the more recent of the two.
    uptrend = last_high_i >= last_low_i
    out: list[tuple[float, str]] = []
    for r in FIB_RATIOS:
        level = hi - r * amplitude if uptrend else lo + r * amplitude
        out.append((float(level), f"fib_retr_{r:.3f}"))
    return out


# ---------------------------------------------------------------------------
# Clustering + scoring
# ---------------------------------------------------------------------------
class _Candidate:
    __slots__ = ("age_bars", "golden", "is_touch", "price", "source")

    def __init__(self, price: float, source: str, *, is_touch: bool, age_bars: int, golden: bool):
        self.price = price
        self.source = source
        self.is_touch = is_touch  # True for swing-pivot touches (count toward `touches`)
        self.age_bars = age_bars
        self.golden = golden


def _band_width(price: float, atr14: float | None) -> float:
    """Cluster tolerance: 0.5*ATR, or a percent-of-price fallback when ATR is bad."""
    if _atr_valid(atr14):
        return BAND_ATR_MULT * float(atr14)
    return PCT_FALLBACK * abs(price)


def _cluster(cands: list[_Candidate], band: float) -> list[list[_Candidate]]:
    """Greedy single-linkage clustering by price within ``band``.

    Each candidate links to the *previous* one in price order, so a chain of
    candidates each within ``band`` of its neighbour stays in one cluster even
    when the chain's overall span exceeds ``band`` (true single-linkage). The
    break uses the last-added member as the anchor, not the cluster's first
    member, otherwise long confluence chains would be split prematurely.
    """
    if not cands:
        return []
    ordered = sorted(cands, key=lambda c: c.price)
    clusters: list[list[_Candidate]] = [[ordered[0]]]
    for c in ordered[1:]:
        anchor = clusters[-1][-1].price  # last-added member (single-linkage)
        if abs(c.price - anchor) <= band:
            clusters[-1].append(c)
        else:
            clusters.append([c])
    return clusters


def _norm(x: float, cap: float) -> float:
    return min(x, cap) / cap if cap > 0 else 0.0


def _recency_weight(min_age_bars: int) -> float:
    """Exponential decay: 1.0 for a just-formed level, ~0.5 at the half-life."""
    return float(0.5 ** (max(min_age_bars, 0) / _RECENCY_HALFLIFE_BARS))


def _is_round_number(price: float) -> bool:
    """Psychological round number: within 0.1% of a $5 or $10 increment."""
    if price <= 0:
        return False
    for inc in (10.0, 5.0):
        nearest = round(price / inc) * inc
        if nearest > 0 and abs(price - nearest) / price <= 0.001:
            return True
    return False


def _score_zone(members: list[_Candidate]) -> tuple[float, int, list[str]]:
    """Return (strength 0..1, touch_count, deduped sources) for a cluster."""
    sources = sorted({m.source for m in members})
    distinct_methods = len({_method_family(m.source) for m in members})
    touch_count = sum(1 for m in members if m.is_touch)
    # Golden Fib levels count as a partial extra "touch" for weighting.
    golden_bonus = 0.5 if any(m.golden for m in members) else 0.0
    min_age = min((m.age_bars for m in members), default=10_000)

    touch_term = _norm(touch_count + golden_bonus, _TOUCH_NORM_CAP)
    method_term = _norm(distinct_methods, _METHOD_NORM_CAP)
    recency_term = _recency_weight(min_age)
    round_term = 1.0 if any(_is_round_number(m.price) for m in members) else 0.0

    strength = (
        W_TOUCH * touch_term
        + W_METHODS * method_term
        + W_RECENCY * recency_term
        + W_ROUND * round_term
    )
    return float(max(0.0, min(1.0, strength))), touch_count, sources


def _method_family(source: str) -> str:
    """Collapse a source tag into its method family for agreement counting."""
    if source.startswith("swing_"):
        return "swing"
    if source.startswith("classic_"):
        return "classic_pivot"
    if source.startswith("fib_pivot_"):
        return "fib_pivot"
    if source.startswith("fib_retr_"):
        return "fib_retr"
    if source == "round_number":
        return "round"
    return source


def _zone_price(members: list[_Candidate]) -> float:
    """Touch-weighted mean price of a cluster (touches pull the zone toward them)."""
    weights = [2.0 if m.is_touch else 1.0 for m in members]
    total = sum(weights)
    return (
        float(sum(m.price * w for m, w in zip(members, weights, strict=True)) / total)
        if total
        else members[0].price
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def compute_sr_levels(
    df: pd.DataFrame | None,
    *,
    price: float,
    atr14: float | None,
    horizon: Horizon = "Core",
    n_each_side: int = 3,
    max_per_side: int = 3,
) -> list[SRLevel]:
    """Ranked S/R zones near ``price``: up to ``max_per_side`` supports below and
    resistances above. Pure & deterministic; no right-edge look-ahead.

    Degrades gracefully: returns ``[]`` on empty/short data and uses a
    percent-of-price band when ATR is unavailable.
    """
    if df is None or getattr(df, "empty", False):
        return []
    if price is None or not math.isfinite(price) or price <= 0:
        return []
    if not {"high", "low", "close"}.issubset(df.columns):
        return []

    n_bars = len(df)
    sh, sl = swing_points(df["high"], df["low"], n=n_each_side)

    cands: list[_Candidate] = []

    # (1) swing pivots -> touches
    highs = np.asarray(df["high"].to_numpy(), dtype=float)
    lows = np.asarray(df["low"].to_numpy(), dtype=float)
    for i in sh:
        cands.append(
            _Candidate(
                float(highs[i]), "swing_high", is_touch=True, age_bars=n_bars - 1 - i, golden=False
            )
        )
    for i in sl:
        cands.append(
            _Candidate(
                float(lows[i]), "swing_low", is_touch=True, age_bars=n_bars - 1 - i, golden=False
            )
        )

    # (2 + 3) classic + Fib pivots from the prior period
    hlc = _prior_period_hlc(df, horizon)
    if hlc is not None:
        ph, pl, pc = hlc
        if all(math.isfinite(x) for x in (ph, pl, pc)) and ph >= pl:
            for name, lvl in classic_pivots(ph, pl, pc).items():
                if name == "PP":
                    continue
                cands.append(
                    _Candidate(
                        float(lvl),
                        f"classic_pivot_{name}",
                        is_touch=False,
                        age_bars=0,
                        golden=False,
                    )
                )
            for name, lvl in fib_pivots(ph, pl, pc).items():
                if name == "PP":
                    continue
                cands.append(
                    _Candidate(
                        float(lvl), f"fib_pivot_{name}", is_touch=False, age_bars=0, golden=False
                    )
                )

    # (4) Fib retracement of the dominant swing
    for lvl, src in fib_retracement(df, sh, sl):
        ratio = float(src.rsplit("_", 1)[-1])
        cands.append(_Candidate(lvl, src, is_touch=False, age_bars=0, golden=(ratio in FIB_GOLDEN)))

    if not cands:
        return []

    band = _band_width(price, atr14)
    clusters = _cluster(cands, band)

    # Zones essentially *at* the current price are neither support nor
    # resistance; drop anything within a tiny epsilon so distance_pct != 0.
    eps = max(price * 1e-4, 1e-6)

    supports: list[SRLevel] = []
    resistances: list[SRLevel] = []
    for members in clusters:
        zprice = _zone_price(members)
        if not math.isfinite(zprice) or zprice <= 0:
            continue
        if abs(zprice - price) <= eps:
            continue  # sitting on price; not actionable S/R
        strength, touches, sources = _score_zone(members)
        distance_pct = round(100.0 * (zprice - price) / price, 2)
        kind: Literal["support", "resistance"] = "support" if zprice < price else "resistance"
        level = SRLevel(
            price=round(zprice, 2),
            method="confluence" if len(sources) > 1 else (sources[0] if sources else "sr"),
            kind=kind,
            strength=round(strength, 3),
            distance_pct=distance_pct,
            sources=sources,
            touches=touches,
        )
        (supports if kind == "support" else resistances).append(level)

    # Nearest-first selection: closest supports below, closest resistances above.
    supports.sort(key=lambda lvl: price - lvl.price)  # smallest gap below first
    resistances.sort(key=lambda lvl: lvl.price - price)  # smallest gap above first
    return supports[:max_per_side] + resistances[:max_per_side]
