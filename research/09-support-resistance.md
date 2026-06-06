# 09 — Support & Resistance: Strategies, Math, and Design Spec

**Scope:** A practical, evidence-graded survey of support/resistance (S/R) methods, plus a concrete design for surfacing **a ranked S/R map on every suggested trade** in `swing-trade-radar`.

**Audience:** Implementers of the radar. Assumes daily bars (Core, ~30d hold) and the existing 1-5d Tactical sleeve.

**Status:** Design doc → feeds an `engine/sr_levels.py` module + a `levels[]` field on each verdict. No code changed by this doc.

**Universe:** Same liquid mega-cap tech basket (AAPL, MSFT, NVDA, GOOGL, META, AMZN, TSLA, AVGO, NFLX, AMD + QQQ).

---

## 0. TL;DR — What we should ship

1. **Compute four methods, merge into ranked zones.** No single method is reliable alone; the edge is **confluence** (multiple methods agreeing within a tolerance band).
2. **Output 3 supports + 3 resistances per trade**, each with a `strength` score, `distance_pct`, and the list of `sources` that voted for it.
3. **Tolerance band = `0.5 × ATR(14)`** (reuse the existing ATR plumbing in `engine/risk_levels.py`). Levels within that band collapse into one zone.
4. **Horizon-aware pivots:** classic/Fib pivots computed on the prior **week** for Core trades, prior **day** for Tactical.
5. **It's a map, not a signal.** S/R augments the existing setups (entry timing, target/stop sanity, "what could invalidate"). It does **not** generate trades on its own — `sr_breakout` already owns the breakout *trigger*.

---

## 1. What S/R actually is (and isn't)

A **support** is a price zone where demand has historically outweighed supply enough to stop/reverse a decline; **resistance** is the mirror. The mechanism is order memory: prior swing points, round numbers, and high-volume nodes are where resting limit orders, stops, and breakeven exits cluster.

Three honest caveats up front (consensus from `07-skeptical-perspective.md` applies):

- **S/R is descriptive, not predictive on its own.** A level only "works" until it doesn't; breaks are common and the most-watched levels are the most likely to be gamed/stopped.
- **Self-fulfilling but also self-defeating.** Widely-drawn levels attract orders (self-fulfilling) *and* attract stop-hunts/fakeouts (self-defeating). Hence the "zone, not a line" rule and volume confirmation.
- **Zones > lines.** Treat every level as a band (~0.5×ATR wide), never an exact price. This is non-negotiable for mega-caps where a single ATR can be several dollars.

---

## 2. The methods (ranked by signal-to-effort)

### Master comparison

| # | Method | What it produces | Horizon fit | Compute cost | Edge quality | Best use in radar |
|---|--------|------------------|-------------|--------------|--------------|-------------------|
| 1 | **Swing pivots (fractals)** | The "real" S/R humans draw; multi-touch zones | All | Low (already have rolling max/min) | **High** (multi-touch zones genuinely sticky) | Core zone source; strength from touch count |
| 2 | **Classic floor pivots** | PP + R1-R3 / S1-S3, deterministic | Intraday→weekly | Trivial | Medium (decays at >1 period) | Weekly basis for Core, daily for Tactical |
| 3 | **Fibonacci pivots** | PP + Fib-weighted R/S | Intraday→weekly | Trivial | Medium (adds confluence) | Confluence votes; pairs with #1 |
| 4 | **Fib retracement of swing** | 23.6/38.2/50/61.8/78.6% pullback levels | Swing | Low | Medium (entry timing) | Pullback-entry zones on trend trades |
| — | Volume profile / VPVR | High-volume nodes (HVN/LVN) | All | High (needs tick/sub-bar) | High but data-heavy | **Deferred** — Phase 2; daily bars too coarse |
| — | Moving averages as dynamic S/R | 50/200-SMA, VWAP-anchored | All | Trivial (already computed) | Medium | Cheap bonus votes (50/200-SMA already in df) |
| — | Round numbers | Psychological levels ($100, $500) | All | Trivial | Low-Medium | Tie-breaker confluence only |

### 2.1 Swing pivots (fractals) — **the gold standard**

A **swing high** at bar *i* = `high[i]` strictly greater than the highs of `N` bars on each side (`N` typically 2-5; we'll use **N=3** for daily, configurable). **Swing low** is the mirror on lows. This is exactly what a discretionary trader eyeballs.

```python
def swing_points(high, low, n=3):
    """Return indices of swing highs and swing lows (fractal definition)."""
    sh, sl = [], []
    for i in range(n, len(high) - n):
        win_h = high[i - n : i + n + 1]
        win_l = low[i - n : i + n + 1]
        if high[i] == win_h.max() and (win_h.argmax() == n):
            sh.append(i)
        if low[i] == win_l.min() and (win_l.argmin() == n):
            sl.append(i)
    return sh, sl
```

> **Note:** the last `N` bars can't be confirmed swings yet (look-ahead). That's fine — confirmed historical pivots are what we plot. Never "peek" the right edge.

**Strength = touch count.** After detecting raw pivots, cluster nearby ones (§3). A zone touched 4 times is far stronger than one touched once. This single signal carries most of the predictive weight.

### 2.2 Classic floor-trader pivot points

Formula-driven, deterministic, zero look-ahead. Computed from the **prior period's** High/Low/Close.

```
PP = (High + Low + Close) / 3

R1 = 2·PP − Low            S1 = 2·PP − High
R2 = PP + (High − Low)     S2 = PP − (High − Low)
R3 = High + 2·(PP − Low)   S3 = Low − 2·(High − PP)
```

*(Source: Investopedia "Pivot Point"; TradingSim "Pivot Points Day Trading Guide".)*

**Horizon caveat (important for us):** classic pivots are traditionally an *intraday/daily* tool — they're recomputed every session and decay fast. For a 30-day Core hold, daily pivots are noise. **Fix:** compute on the prior **week's** OHLC for Core trades; prior **day's** for the 1-5d Tactical sleeve. Weekly pivots are a legitimate swing-horizon tool.

### 2.3 Fibonacci pivot points

Same central PP, but R/S spaced by Fibonacci ratios of the prior range:

```
PP = (High + Low + Close) / 3

R1 = PP + 0.382·(High − Low)   S1 = PP − 0.382·(High − Low)
R2 = PP + 0.618·(High − Low)   S2 = PP − 0.618·(High − Low)
R3 = PP + 1.000·(High − Low)   S3 = PP − 1.000·(High − Low)
```

*(Source: Morpher "Pivot Point Fibonacci"; Zerodha Varsity "Fibonacci retracements".)*

Value is **confluence**: when a Fib pivot lands on a swing-pivot zone, that zone gets a strength bonus. Cheap to compute, so always include.

### 2.4 Fibonacci retracement of the dominant swing

Identify the dominant recent swing (significant low→high in an uptrend, or high→low in a downtrend). Retracement levels mark where pullbacks tend to find support:

```
level(r) = swing_high − r · (swing_high − swing_low)     # uptrend pullback support
r ∈ {0.236, 0.382, 0.500, 0.618, 0.786}
```

- **0.618 ("golden") and 0.500** are the most-defended → weight them higher.
- Best for **entry timing** on trend trades (buy the dip into a Fib support that coincides with a swing pivot), weaker as hard targets.
- Anchor selection matters: use the most recent confirmed swing low→swing high (from §2.1) with the largest amplitude in the lookback. Document the anchor in `sources` so the UI can show *which* swing it's measuring.

---

## 3. The real strategy: confluence + clustering

> Single levels are noise. **A zone where ≥2 independent methods agree within `0.5×ATR` is the signal.**

**Algorithm:**

1. Generate raw candidate levels from all four methods (each tagged with its source, e.g. `swing_pivot`, `fib_pivot_R1`, `fib_retr_0.618`, `classic_pivot_S1`, `sma_200`).
2. **Cluster** candidates whose prices fall within `band = 0.5 × ATR(14)` of each other into a single zone. Zone price = touch-weighted mean of members.
3. **Score** each zone `0..1`:
   ```
   strength = w_touch · norm(touch_count)
            + w_methods · norm(distinct_method_count)
            + w_recency · recency_weight(last_touch_age)
            + w_round · is_round_number_bonus
   ```
   Starting weights (tunable, to be calibrated against the walk-forward harness in `04`/`05`): `w_touch=0.45, w_methods=0.30, w_recency=0.15, w_round=0.10`.
4. **Select** the nearest 3 zones **below** current price as supports, nearest 3 **above** as resistances. (A trade only cares about the few levels it could realistically hit.)
5. **Annotate** each with signed `distance_pct = (zone − price) / price · 100` and the deduped `sources` list.

**Volume sanity (reuse existing `vol_sma20`):** a level that formed on high volume is stickier. Optional `w_volume` term once volume-at-level is wired; deferred to keep v1 lean.

---

## 4. How this plugs into `swing-trade-radar`

### 4.1 What already exists (don't duplicate)

- `engine/indicators.py` computes `pivot_high_20` / `pivot_low_20` (20-day rolling max/min), `atr14`, `vol_sma20`, and (per grep) `bb_*`, `rsi`, MAs.
- `strategies/sr_breakout.py` already **trades** 20-day pivot breakouts with volume confirmation. ← S/R as a *trigger*. We are **not** changing its trade logic.
- `engine/risk_levels.py` is the single source of truth for ATR-based stop/target geometry (`atr_stop`, `floor_stop_with_atr`, `min_rr_target`, `dynamic_atr_trade`). Reuse its `_atr_valid` + ATR access for the tolerance band.
- `schemas.py` already has `PriceLevel{price, method}`, `StopLevel`, `TargetLevel`, and the verdict carries `entry_zone` / `stop_loss` / `target` / `volatility_atr`.

### 4.2 New: `engine/sr_levels.py`

```python
def compute_sr_levels(
    df: pd.DataFrame,
    *,
    price: float,
    atr14: float | None,
    horizon: Literal["Core", "Tactical"] = "Core",
    n_each_side: int = 3,
    max_per_side: int = 3,
) -> list[SRLevel]:
    """Pure function. Detect swing fractals + classic/Fib pivots (weekly for
    Core, daily for Tactical) + Fib retracement of the dominant swing, cluster
    within 0.5*ATR, score by touches/method-agreement/recency, and return the
    nearest `max_per_side` supports below and resistances above `price`."""
```

Properties: **pure & deterministic** (testable), **no right-edge look-ahead**, **degrades gracefully** when ATR is NaN (fall back to a `0.75%` band, mirroring `PCT_FALLBACK` in `risk_levels.py`).

### 4.3 New schema field

```python
class SRLevel(PriceLevel):                       # inherits price, method
    kind: Literal["support", "resistance"]
    strength: float = Field(..., ge=0.0, le=1.0)
    distance_pct: float                          # signed % from current price
    sources: list[str] = Field(default_factory=list)  # ["swing_pivot", "fib_pivot_R1", ...]
    touches: int = Field(default=0, ge=0)
```

Add to the verdict model:

```python
levels: list[SRLevel] = Field(default_factory=list,
    description="Ranked S/R zones near price: up to 3 supports below + 3 resistances above.")
```

`default_factory=list` ⇒ backward-compatible (older payloads/tests just see `[]`).

### 4.4 Wiring point

Call `compute_sr_levels(...)` in the verdict synthesizer (where `volatility_atr`/`entry_zone` are already populated), passing the latest `price`, `atr14`, and the verdict's `time_horizon`. Attach the result to `verdict.levels`. One call site; no strategy code touched.

### 4.5 Frontend (separate follow-up PR)

Draw horizontal lines/bands on each trade's chart:
- **Color:** green = support, red = resistance.
- **Opacity/width ∝ `strength`.**
- **Tooltip:** price, `distance_pct`, `sources`, `touches`.
- A compact "Key Levels" list under the trade card for the no-chart view (and to honor the Discord/WhatsApp "no tables" rule when shared).

---

## 5. Worked example (illustrative)

NVDA, price = \$170.00, ATR(14) = \$6.00 ⇒ band = \$3.00.

| Raw candidates near price | Source |
|---|---|
| 171.20 | swing_high (3 touches) |
| 172.00 | round_number |
| 170.90 | weekly classic R1 |
| 163.50 | swing_low (2 touches) |
| 162.80 | weekly fib pivot S1 |
| 158.10 | fib_retr 0.618 of last up-swing |

**After clustering (band \$3) + scoring:**

| Zone | kind | strength | distance_pct | sources |
|---|---|---:|---:|---|
| **171.4** | resistance | 0.88 | +0.82% | swing_high (×3), classic_pivot_R1, round_number |
| 175.2 | resistance | 0.41 | +3.06% | fib_pivot_R2 |
| **163.2** | support | 0.79 | −4.00% | swing_low (×2), fib_pivot_S1 |
| 158.1 | support | 0.55 | −7.00% | fib_retr_0.618 |

Reading: strong resistance ~\$171.4 (three swing touches + a pivot + round number all stack) — a Core long here has limited room before that wall, and the existing `sr_breakout` would need a volume-confirmed close *above* it to fire. First real support ~\$163.2 — a sane stop reference, cross-checked against the ATR stop from `risk_levels.py`.

---

## 6. Trust & safety rails (consistent with the dossier ethos)

- **S/R never auto-generates a trade.** Map only. Triggers stay with the validated setups.
- **Zones, not lines.** Always ≥0.5×ATR wide; the UI must render bands, not hairlines, so users don't over-trust an exact price.
- **No look-ahead.** Right-edge unconfirmed swings excluded; pivots use only prior-period closed data. Enforced by a unit test that feeds a truncated df and asserts no future bar influences output.
- **Graceful degradation.** NaN/zero ATR ⇒ percent-band fallback, never a crash (mirrors `risk_levels.py`).
- **Calibrate, don't assert.** Strength weights are starting guesses; tune against the walk-forward harness (`04`/`W5`) before trusting them in the score blend. Until calibrated, `levels` is **display-only** and does **not** feed the numeric conviction score.

---

## 7. Implementation checklist

- [ ] `engine/sr_levels.py`: `swing_points`, `classic_pivots`, `fib_pivots`, `fib_retracement`, `cluster_levels`, `score_zone`, `compute_sr_levels`.
- [ ] `schemas.py`: `SRLevel` model + `levels: list[SRLevel]` on the verdict.
- [ ] Wire `compute_sr_levels(...)` into the verdict synthesizer (single call site).
- [ ] Tests: `test_sr_levels.py` — known-fixture swing detection, clustering within band, no-look-ahead guard, NaN-ATR fallback, deterministic ordering (nearest-first), empty-df + short-history guards.
- [ ] Lint + typecheck + full test suite green.
- [ ] (Follow-up PR) Frontend chart overlay + "Key Levels" list.

---

## 8. Sources

- Investopedia — *Support and Resistance Basics*; *Pivot Point: Definition, Formulas, and How to Calculate*.
- TradingSim — *Pivot Points Day Trading Guide* (classic pivot formulas, 7-level set, history).
- Morpher — *Pivot Point Fibonacci: How It Works and Comparing All Types* (Fib pivot formulas).
- Zerodha Varsity — *Fibonacci retracements* (retracement levels + pivot context).
- PriceAction.com — *Support and Resistance Levels Trading Strategy* (swing-point S/R definition).
- TradingCenter.org — *Exact Swing Points – Support & Resistance* (fractal/swing-point rules).
- Internal: `01-classic-strategies.md` (breakout/volume context), `02-risk-management.md` (ATR/zone discipline), `07-skeptical-perspective.md` (S/R-is-not-magic caveats), and existing `sr_breakout.py` / `risk_levels.py`.
