"""Transparent trade-score breakdown.

Replaces the implicit 'conviction == score' pattern with an explicit, weighted
8-component blend so the UI can render bars and the user can see *why* a trade
scored what it did.

Components (all 0..100, higher = better trade):

    1. trend_quality        — MA stack, slope, ADX-ish proxy
    2. momentum             — RSI(14), 20-bar ROC, MACD histogram sign
    3. mean_reversion       — distance from SMA20 + RSI(2)
    4. risk_reward          — target/stop ratio (and stop width penalty)
    5. volatility           — ATR% normalized (sweet spot 1.5\u20133.5%)
    6. earnings_risk        — proximity to next earnings (default 50 if unknown)
    7. historical_reliability — win_rate \u00d7 avg_R \u00d7 sample-size shrinkage
    8. extension_risk       — penalty for sanity 'extended_*' flags or |close/SMA50\u22121|

The final score is a weighted blend (see WEIGHTS), minus an external
correlation penalty applied in a post-pass over the run's verdicts.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..data.sanity import SanityFlag as SanityFlagDc
from ..schemas import (
    BaseRateBlock,
    SanityFlag,
    ScoreBreakdown,
    ScoreComponent,
)
from ..strategies.v2.base import StrategyResult

# -----------------------------------------------------------------------------
# Weights — tweak here; published on every Verdict.score_breakdown.weights
# -----------------------------------------------------------------------------

WEIGHTS: dict[str, float] = {
    "trend_quality": 0.18,
    "momentum": 0.14,
    "mean_reversion": 0.08,
    "risk_reward": 0.18,
    "volatility": 0.08,
    "earnings_risk": 0.08,
    "historical_reliability": 0.16,
    "extension_risk": 0.10,
}
# Sanity check at import time so a typo can't ship.
_WEIGHT_SUM = round(sum(WEIGHTS.values()), 6)
assert abs(_WEIGHT_SUM - 1.0) < 1e-6, f"WEIGHTS must sum to 1.0, got {_WEIGHT_SUM}"

# Stop-width thresholds (% of entry).
STOP_WIDE_WARN = 0.05   # > 5% stop starts to hurt
STOP_WIDE_BAD = 0.12    # >= 12% stop floors the risk_reward score
# Extension threshold for raw % distance fallback.
EXTENSION_SOFT = 0.15   # 15% above/below SMA50 starts to bite
EXTENSION_HARD = 0.40   # 40%+ floors extension_risk
# Historical reliability sample-size shrinkage knees.
N_LIGHT = 20  # below this, shrinkage applies
N_HEAVY = 10  # below this, heavy shrinkage applies


# -----------------------------------------------------------------------------
# Context object passed into compute_score_breakdown
# -----------------------------------------------------------------------------


@dataclass
class ScoringContext:
    """All inputs needed to score a single (ticker, bar) verdict.

    Keeps `scoring.py` decoupled from the verdict synthesizer wiring.
    """

    ticker: str
    df: pd.DataFrame                                   # enriched OHLCV (lowercase cols + indicators)
    primary: StrategyResult | None
    sanity_flags: Iterable[SanityFlag | SanityFlagDc] = ()
    base_rate: BaseRateBlock | None = None
    days_to_earnings: int | None = None                # None = unknown


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    if not math.isfinite(x):
        return lo
    return max(lo, min(hi, x))


def _safe_last(df: pd.DataFrame, col: str) -> float | None:
    if col not in df.columns or df.empty:
        return None
    v = df[col].iloc[-1]
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(f):
        return None
    return f


def _flag_codes(flags: Iterable[SanityFlag | SanityFlagDc]) -> set[str]:
    out: set[str] = set()
    for f in flags or ():
        code = getattr(f, "code", None)
        if code:
            out.add(str(code))
    return out


# -----------------------------------------------------------------------------
# Per-component scorers — each returns (value, note)
# -----------------------------------------------------------------------------


def _score_trend_quality(df: pd.DataFrame) -> tuple[float, str]:
    close = _safe_last(df, "close")
    sma50 = _safe_last(df, "sma50")
    sma200 = _safe_last(df, "sma200")
    ema21 = _safe_last(df, "ema21")
    if close is None or sma50 is None or sma200 is None:
        return 50.0, "Insufficient MA history."

    score = 0.0
    bits: list[str] = []
    # Stack: close > sma50 > sma200
    if close > sma50:
        score += 25
        bits.append("close>SMA50")
    if sma50 > sma200:
        score += 25
        bits.append("SMA50>SMA200")
    if ema21 is not None and close > ema21:
        score += 10
        bits.append("close>EMA21")

    # Slope of SMA50 over last 20 bars (proxy for trend strength / ADX).
    if "sma50" in df.columns and len(df) >= 30:
        s = df["sma50"].dropna().tail(20)
        if len(s) >= 10 and s.iloc[0] > 0:
            slope_pct = (s.iloc[-1] - s.iloc[0]) / s.iloc[0]
            # +/- 5% over 20 bars maps to +/- 40 points.
            score += float(np.clip(slope_pct * 800.0, -40.0, 40.0))
            bits.append(f"SMA50 slope {slope_pct*100:+.1f}%")

    return _clamp(score), ", ".join(bits) or "neutral"


def _score_momentum(df: pd.DataFrame) -> tuple[float, str]:
    close = _safe_last(df, "close")
    rsi = _safe_last(df, "rsi14")
    macd_hist = _safe_last(df, "macd_hist")
    if close is None:
        return 50.0, "no close"

    bits: list[str] = []
    score = 50.0  # neutral baseline

    if rsi is not None:
        # 50 \u2192 0pts, 70 \u2192 +20pts, 30 \u2192 -20pts. Past 80 we cap (overbought is *not* extra bullish).
        rsi_contrib = float(np.clip((rsi - 50.0), -25.0, 25.0))
        score += rsi_contrib
        bits.append(f"RSI14={rsi:.0f}")

    # 20-bar ROC.
    if "close" in df.columns and len(df) >= 21:
        c0 = float(df["close"].iloc[-21])
        if c0 > 0:
            roc = (close - c0) / c0
            score += float(np.clip(roc * 200.0, -25.0, 25.0))
            bits.append(f"ROC20={roc*100:+.1f}%")

    if macd_hist is not None:
        score += 5.0 if macd_hist > 0 else -5.0
        bits.append(f"MACDh{'+' if macd_hist > 0 else '-'}")

    return _clamp(score), ", ".join(bits) or "neutral"


def _score_mean_reversion(df: pd.DataFrame) -> tuple[float, str]:
    """Higher when the bar is a *good* mean-reversion candidate (oversold + above 200SMA)."""
    close = _safe_last(df, "close")
    sma20 = _safe_last(df, "ema20") or _safe_last(df, "sma50")
    if close is None or sma20 is None or sma20 <= 0:
        return 50.0, "no MA20"

    pct_above = (close - sma20) / sma20
    # RSI(2) — compute on the fly to avoid plumbing through enrich.
    rsi2 = None
    if "close" in df.columns and len(df) >= 4:
        c = df["close"].astype(float)
        delta = c.diff()
        up = delta.clip(lower=0).rolling(2).mean()
        down = (-delta.clip(upper=0)).rolling(2).mean()
        rs = up / down.replace(0, np.nan)
        rsi2_series = 100 - (100 / (1 + rs))
        v = rsi2_series.iloc[-1]
        if pd.notna(v):
            rsi2 = float(v)

    # Best score: small dip below MA20 + RSI(2) low.
    base = 50.0
    bits: list[str] = []
    if pct_above < 0:
        # Dip below MA: -3% \u2192 +20, deeper drops less attractive (catching knife).
        magnitude = abs(pct_above)
        if magnitude <= 0.03:
            base += magnitude * 600.0  # up to +18
        elif magnitude <= 0.08:
            base += 18 - (magnitude - 0.03) * 200.0  # tapers off
        else:
            base -= 10  # too far below = downtrend, not reversion
        bits.append(f"{pct_above*100:+.1f}% vs MA20")
    else:
        # Above MA20 \u2192 not a reversion setup; gently lower.
        base -= float(np.clip(pct_above * 100.0, 0.0, 30.0))
        bits.append(f"{pct_above*100:+.1f}% vs MA20")

    if rsi2 is not None:
        # Lower RSI(2) = better long mean-rev.
        base += float(np.clip((20.0 - rsi2) * 1.5, -20.0, 30.0))
        bits.append(f"RSI(2)={rsi2:.0f}")

    return _clamp(base), ", ".join(bits)


def _score_risk_reward(primary: StrategyResult | None) -> tuple[float, str]:
    if primary is None or primary.entry_price is None or primary.stop_price is None:
        return 50.0, "no plan"
    entry = primary.entry_price
    stop = primary.stop_price
    target = primary.target_price
    if entry <= 0 or stop <= 0 or stop >= entry:
        return 50.0, "invalid stop"

    risk_per_share = entry - stop
    stop_pct = risk_per_share / entry
    rr = ((target - entry) / risk_per_share) if (target and target > entry) else None

    bits: list[str] = []
    # RR baseline: 1R \u2192 30, 2R \u2192 60, 3R \u2192 80, 4R+ \u2192 95.
    if rr is None:
        score = 40.0
        bits.append("no target")
    else:
        score = float(np.clip(20.0 + rr * 20.0, 0.0, 95.0))
        bits.append(f"RR={rr:.2f}")

    # Stop-width penalty.
    if stop_pct > STOP_WIDE_BAD:
        score -= 30
        bits.append(f"stop {stop_pct*100:.1f}% (very wide)")
    elif stop_pct > STOP_WIDE_WARN:
        # linearly subtract 0..30 between WARN and BAD
        frac = (stop_pct - STOP_WIDE_WARN) / (STOP_WIDE_BAD - STOP_WIDE_WARN)
        score -= 30.0 * frac
        bits.append(f"stop {stop_pct*100:.1f}%")
    else:
        bits.append(f"stop {stop_pct*100:.1f}%")

    return _clamp(score), ", ".join(bits)


def _score_volatility(df: pd.DataFrame) -> tuple[float, str]:
    close = _safe_last(df, "close")
    atr = _safe_last(df, "atr14")
    if close is None or atr is None or close <= 0 or atr <= 0:
        return 50.0, "no ATR"
    atr_pct = atr / close
    # Sweet spot 1.5%..3.5%. Below 1% = sleepy. Above 6% = unmanageable.
    if 0.015 <= atr_pct <= 0.035:
        score = 90.0
    elif atr_pct < 0.015:
        score = 60.0 + (atr_pct / 0.015) * 30.0  # 0..30 boost up to sweet spot floor
    elif atr_pct < 0.06:
        # taper from 90 \u2192 30
        score = 90.0 - (atr_pct - 0.035) * (60.0 / 0.025)
    else:
        score = 20.0
    return _clamp(score), f"ATR%={atr_pct*100:.2f}%"


def _score_earnings_risk(days_to_earnings: int | None) -> tuple[float, str]:
    if days_to_earnings is None:
        return 50.0, "earnings unknown"
    d = int(days_to_earnings)
    if d < 0:
        return 60.0, f"earnings passed {abs(d)}d ago"
    if d <= 2:
        return 5.0, f"earnings in {d}d"
    if d <= 5:
        return 25.0, f"earnings in {d}d"
    if d <= 10:
        return 55.0, f"earnings in {d}d"
    if d <= 20:
        return 80.0, f"earnings in {d}d"
    return 95.0, f"earnings in {d}d"


def _score_historical_reliability(base_rate: BaseRateBlock | None) -> tuple[float, str]:
    if base_rate is None or base_rate.occurrences == 0:
        # Unknown \u2192 neutral 40 (slight under-bias to discourage relying on it).
        return 40.0, "no base-rate sample"

    n = base_rate.occurrences
    win = base_rate.win_rate         # 0..1
    avg_r = base_rate.avg_r          # signed, \u22120.5..1.5 typical

    # Raw merit: combine win rate (0..1) and avg_r (clipped to [-0.5, 1.5]).
    avg_r_norm = float(np.clip((avg_r + 0.5) / 2.0, 0.0, 1.0))
    merit = 0.6 * win + 0.4 * avg_r_norm   # 0..1

    # Sample-size shrinkage toward 0.4 (the "unknown" baseline) when n is small.
    if n >= N_LIGHT:
        confidence = 1.0
    elif n >= N_HEAVY:
        confidence = 0.5 + 0.5 * (n - N_HEAVY) / (N_LIGHT - N_HEAVY)
    else:
        confidence = 0.25 * (n / N_HEAVY)  # very small \u2192 \u22640.25

    shrunk = confidence * merit + (1.0 - confidence) * 0.4
    score = shrunk * 100.0
    return _clamp(score), (
        f"n={n}, win={win*100:.0f}%, avgR={avg_r:+.2f}, "
        f"shrink={confidence:.2f}"
    )


def _score_extension_risk(
    df: pd.DataFrame,
    flags: Iterable[SanityFlag | SanityFlagDc],
) -> tuple[float, str]:
    """100 = not extended at all; 0 = severely extended (chase risk)."""
    codes = _flag_codes(flags)
    has_extended_flag = any(
        c.startswith("extended_above_") or c.startswith("extended_below_") for c in codes
    )

    close = _safe_last(df, "close")
    sma50 = _safe_last(df, "sma50")
    pct = None
    if close and sma50 and sma50 > 0:
        pct = abs(close - sma50) / sma50

    score = 100.0
    bits: list[str] = []

    if pct is not None:
        if pct >= EXTENSION_HARD:
            score = 5.0
        elif pct >= EXTENSION_SOFT:
            # linear: SOFT \u2192 70, HARD \u2192 5 (slope across the band).
            frac = (pct - EXTENSION_SOFT) / (EXTENSION_HARD - EXTENSION_SOFT)
            score = 70.0 - 65.0 * frac
        else:
            score = 100.0 - (pct / EXTENSION_SOFT) * 30.0  # 100 \u2192 70 within band
        bits.append(f"|close/SMA50-1|={pct*100:.1f}%")

    if has_extended_flag:
        # If any 'high' severity extended flag is present, additional 25-point
        # haircut on top of the raw % calculation.
        any_high = any(
            getattr(f, "severity", None) == "high"
            and str(getattr(f, "code", "")).startswith("extended_")
            for f in flags
        )
        haircut = 25.0 if any_high else 10.0
        score -= haircut
        bits.append("flag" + ("(high)" if any_high else ""))

    return _clamp(score), ", ".join(bits) or "not extended"


# -----------------------------------------------------------------------------
# Public entry point
# -----------------------------------------------------------------------------


def compute_score_breakdown(ctx: ScoringContext) -> ScoreBreakdown:
    """Compute the full 8-component breakdown + weighted total.

    The returned ScoreBreakdown.correlation_penalty is 0.0; the post-pass in
    ``signal_generator`` is responsible for filling it in and adjusting the total.
    """
    tq_v, tq_n = _score_trend_quality(ctx.df)
    mo_v, mo_n = _score_momentum(ctx.df)
    mr_v, mr_n = _score_mean_reversion(ctx.df)
    rr_v, rr_n = _score_risk_reward(ctx.primary)
    vol_v, vol_n = _score_volatility(ctx.df)
    er_v, er_n = _score_earnings_risk(ctx.days_to_earnings)
    hr_v, hr_n = _score_historical_reliability(ctx.base_rate)
    ext_v, ext_n = _score_extension_risk(ctx.df, ctx.sanity_flags)

    components = {
        "trend_quality": (tq_v, tq_n),
        "momentum": (mo_v, mo_n),
        "mean_reversion": (mr_v, mr_n),
        "risk_reward": (rr_v, rr_n),
        "volatility": (vol_v, vol_n),
        "earnings_risk": (er_v, er_n),
        "historical_reliability": (hr_v, hr_n),
        "extension_risk": (ext_v, ext_n),
    }

    total = sum(WEIGHTS[k] * v for k, (v, _) in components.items())

    def _mk(name: str) -> ScoreComponent:
        v, note = components[name]
        return ScoreComponent(value=round(v, 2), weight=WEIGHTS[name], note=note)

    return ScoreBreakdown(
        trend_quality=_mk("trend_quality"),
        momentum=_mk("momentum"),
        mean_reversion=_mk("mean_reversion"),
        risk_reward=_mk("risk_reward"),
        volatility=_mk("volatility"),
        earnings_risk=_mk("earnings_risk"),
        historical_reliability=_mk("historical_reliability"),
        extension_risk=_mk("extension_risk"),
        total=round(_clamp(total), 2),
        weights=dict(WEIGHTS),
        correlation_penalty=0.0,
    )


# -----------------------------------------------------------------------------
# Correlation post-pass (used by signal_generator)
# -----------------------------------------------------------------------------


CORRELATION_THRESHOLD = 0.7
CORRELATION_LOOKBACK = 60
# Per correlated peer, subtract this many points (capped).
CORRELATION_PENALTY_PER_HIT = 10.0
CORRELATION_PENALTY_CAP = 30.0


def _pct_returns(df: pd.DataFrame, n: int = CORRELATION_LOOKBACK) -> np.ndarray | None:
    if "close" not in df.columns:
        return None
    s = df["close"].dropna().tail(n + 1)
    if len(s) < 10:
        return None
    return s.pct_change().dropna().to_numpy(dtype=float)


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    n = min(len(a), len(b))
    if n < 5:
        return 0.0
    a = a[-n:]
    b = b[-n:]
    if np.std(a) == 0 or np.std(b) == 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def apply_correlation_penalties(
    *,
    verdicts_in_order: list,        # list of Verdict objects, will be mutated
    enriched_by_ticker: dict[str, pd.DataFrame],
    threshold: float = CORRELATION_THRESHOLD,
) -> None:
    """Mutate verdicts: downgrade `score` and set `correlation_penalty` for any
    verdict whose recent returns correlate >threshold with an *already-selected*
    higher-scoring verdict.

    'Selected' = scored verdicts processed earlier in the list. Caller should
    pre-sort by `score` descending.
    """
    selected_returns: list[tuple[str, np.ndarray]] = []
    for v in verdicts_in_order:
        if v.score is None or v.score_breakdown is None:
            continue
        df = enriched_by_ticker.get(v.ticker)
        if df is None:
            continue
        rets = _pct_returns(df)
        if rets is None:
            selected_returns.append((v.ticker, np.array([])))  # placeholder so we don't reuse
            continue

        hits = 0
        worst_corr = 0.0
        peers: list[str] = []
        for peer_ticker, peer_rets in selected_returns:
            if peer_rets.size == 0:
                continue
            corr = abs(_pearson(rets, peer_rets))
            if corr >= threshold:
                hits += 1
                peers.append(f"{peer_ticker}({corr:.2f})")
                worst_corr = max(worst_corr, corr)

        penalty = min(CORRELATION_PENALTY_CAP, hits * CORRELATION_PENALTY_PER_HIT)
        if penalty > 0:
            v.correlation_penalty = round(penalty, 2)
            v.score_breakdown.correlation_penalty = v.correlation_penalty
            new_total = max(0.0, (v.score or 0.0) - penalty)
            v.score = round(new_total, 2)
            # Append a tiny note onto extension_risk note? No — keep components
            # untouched; correlation is its own field. The frontend renders it
            # alongside the total.

        selected_returns.append((v.ticker, rets))


__all__ = [
    "CORRELATION_LOOKBACK",
    "CORRELATION_THRESHOLD",
    "WEIGHTS",
    "ScoringContext",
    "apply_correlation_penalties",
    "compute_score_breakdown",
]
