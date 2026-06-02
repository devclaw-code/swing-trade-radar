# 02 — Code Audit: Aditya's AI-Infra Strategist Feedback

Audit date: 2026-06-02
Repo path: `backend/src/swing_trader/`
Source prompt: `research/ai-infra-prompt/00-PROMPT.md`

## TL;DR (5 bullets)

1. **Good news on ATR**: every v2 strategy (`strategies/v2/s1…s5`) already prices stops as `close − k×ATR(14)` with ATR computed centrally in `engine/indicators.py:42`. The only fixed-% stops are *fallback* branches when `atr` is NaN (e.g. `close * 0.95`) and one legacy strategy `volume_trend.py` that uses a 5-bar low. **No high-vol-name fixed-% stop is in production** — but the NaN fallbacks should be tightened.
2. **R:R gating is soft, not hard**: `engine/scoring.py:238` (`_score_risk_reward`) treats RR as a *score component* (weight 0.18), and `engine/risk_classifier.py:48` uses `risk_low_min_rr=2.5` / `risk_med_min_rr=1.5` (`config.py:62-68`) only for tier *labelling*. Aditya's "min 1:2.5 → discard" rule does **not** exist as a verdict-killer; it would slot into `verdict._verdict_kind` (`engine/verdict.py:80`).
3. **RSI(14) > 75 / StochRSI overbought rejection: nowhere as a hard reject.** `engine/scoring.py:172` *caps* the RSI bull contribution but never rejects. There is no StochRSI in `indicators.enrich()` at all. Cleanest home: a new gate in `verdict.synthesize_verdict` or per-strategy in each `s*.evaluate`.
4. **Earnings calendar is wired** (`engine/signal_generator.py:222-234, 334`) via yfinance `get_earnings_dates`, threaded into `basket["earnings_dates"]` and consumed by `s3_connors_rsi2.py:78-96` (no-new-long gate, 7d) and `s5_pead.py:47-60` (PEAD ignition). The "exit 24h before earnings" *exit rule* does NOT exist anywhere — `days_to_earnings` is computed (`signal_generator.py:419-423`) and only feeds the *score* (`scoring.py:294-308`). It should own a new field on `Verdict` and an exit hint in `verdict.synthesize_verdict`.
5. **Negative-beta hedge surfacing on NDX RSI > 70**: not implemented. `engine/regime.py` checks SPY/QQQ-vs-200SMA + VIX, but nothing reads `qqq_above_200sma` together with QQQ RSI(14), and `schemas.Verdict` has no `hedge_candidate` slot. Needs (a) RSI(14) on QQQ in `regime.py`, (b) a hedge basket in `config.py`, (c) a surfaced field on `RegimeContext` or top-level run summary.

---

## 1) Fixed-% stops vs ATR usage

### Where stops are set today

| File | Lines | Stop formula | Notes |
|---|---|---|---|
| `strategies/v2/s1_trend_50_200.py` | **101** | `close − 2.0×ATR(14)` ✓ | Fallback `close*0.95` when ATR NaN |
| `strategies/v2/s2_clenow_momentum.py` | **160** | `close − 2.5×ATR(14)` ✓ | Fallback `close*0.92` when ATR NaN |
| `strategies/v2/s3_connors_rsi2.py` | **139** | `close − 2.0×ATR(14)` ✓ | Fallback `close*0.95` when ATR NaN |
| `strategies/v2/s4_minervini_vcp.py` | **144** | `recent_low * 0.99` (structure-based) | NOT ATR — pivot stop, can be *wider* than 2×ATR on illiquid names |
| `strategies/v2/s5_pead.py` | **161-164** | pre-earnings prior close | structure-based; appropriate for PEAD |
| `strategies/ma_crossover.py` | **32, 53** | `EMA21 ± ATR` ✓ | legacy v1 |
| `strategies/macd_trend.py` | **31, 54** | 10-bar swing low/high | structure-based |
| `strategies/rsi_mean_reversion.py` | **48, 75** | `entry ± 2×ATR` ✓ | legacy v1 |
| `strategies/sr_breakout.py` | **42, 66** | `pivot * 0.99` / `*1.01` | structure-based, fixed-% buffer |
| `strategies/volume_trend.py` | **60, 63** | 5-bar low; **target = entry + 1.5×risk** | **only true fixed-multiple**, no ATR floor |
| `strategies/base_strategy.py` | **35-38** | `default_target = entry + 2R` | uses `settings.default_target_rr=2.0` (`config.py:71`) |

### ATR usage today

- **Definition**: `engine/indicators.py:42` — `out["atr14"] = ta.atr(high, low, close, length=14)` via `pandas_ta_classic`. Single source of truth, called on every ticker by `enrich()`.
- **Consumers**: every v2 strategy reads `last.get("atr14")`. `engine/scoring.py:281` ("volatility" score) normalises ATR%. `s4_minervini_vcp.py:79-81` uses ATR ratio for VCP contraction confirmation.

### Verdict (Q1)

**No production strategy uses a hard-coded percent stop on a *successful* signal.** What exists:

- Three NaN-fallback fixed-% stops (`s1`, `s2`, `s3` lines 101/160/139). On thin-data names like AAOI in early bars, these fire silently.
- One legacy strategy `volume_trend.py` (still registered in `signal_generator.default_strategies()` at line 49) that ignores ATR entirely.
- Structure-based stops (`s4`, `sr_breakout`, `macd_trend`, `volume_trend`) which on a high-vol name like AAOI can land **inside** 1×ATR — the opposite of Aditya's complaint, but equally dangerous.

**Action items**: see Punchline §6 item A.

---

## 2) Where to plug "entry − 2×ATR(14)" cleanly

Two layers exist: per-strategy (already mostly correct for v2) and a **central enforcement floor** that no code currently owns.

### Recommended plug-point: a helper in `engine/indicators.py` (or new `engine/risk_levels.py`), then called from every `evaluate()` and from `verdict.synthesize_verdict`.

#### Diff sketch (NOT applied)

```python
# backend/src/swing_trader/engine/risk_levels.py  (NEW)
"""Centralised stop/target geometry. Single source of truth for ATR-based stops."""
from __future__ import annotations
import math
import pandas as pd

ATR_STOP_MULT = 2.0          # Aditya: entry − 2×ATR(14)
ATR_STOP_MULT_HIVOL = 2.5    # Clenow-style trend wider stop
PCT_FALLBACK = 0.05          # only when ATR cannot be computed

def atr_stop(entry: float, atr14: float | None, *, mult: float = ATR_STOP_MULT) -> float:
    if atr14 is None or math.isnan(atr14) or atr14 <= 0:
        return round(entry * (1.0 - PCT_FALLBACK), 2)
    return round(entry - mult * atr14, 2)

def min_rr_target(entry: float, stop: float, *, rr: float = 2.5) -> float:
    return round(entry + rr * (entry - stop), 2)
```

```diff
# backend/src/swing_trader/strategies/v2/s1_trend_50_200.py
@@ -99,6 +99,7 @@
         entry = close
-        stop = round(close - 2.0 * atr, 2) if atr == atr else round(close * 0.95, 2)
-        target = round(close + 4.0 * atr, 2) if atr == atr else round(close * 1.10, 2)
+        from ...engine.risk_levels import atr_stop, min_rr_target
+        stop = atr_stop(entry, atr, mult=2.0)
+        target = min_rr_target(entry, stop, rr=2.5)   # was 4×ATR ≈ 2R; tighten to spec
```

Apply the same two-line swap to `s2:160`, `s3:139`, and the v1 ATR users (`ma_crossover.py:32,53`, `rsi_mean_reversion.py:48,75`).

For the **structure-based** strategies (`s4`, `sr_breakout`, `macd_trend`, `volume_trend`) wrap the existing stop with a *floor*:

```diff
# backend/src/swing_trader/strategies/v2/s4_minervini_vcp.py
@@ -142,6 +142,8 @@
         stop = round(recent_low * 0.99, 2)
+        # Never let pivot stop be tighter than 2×ATR (esp. on AAOI-class vol).
+        stop = min(stop, atr_stop(close, atr_now, mult=2.0))
         risk = max(0.01, close - stop)
         target = round(close + 2.0 * risk, 2)
```

### Why this is the right seam

- All v2 strategies already import `atr14` from the enriched df → no plumbing.
- `verdict.synthesize_verdict` already computes `risk_pct` (`engine/verdict.py:188`) but trusts the strategy. A central helper keeps the *display* in sync (`StopLevel.method="2x ATR(14) below entry"` is hard-coded at `verdict.py:191` — it currently lies for `s2` (2.5×) and `s4` (pivot)).

---

## 3) 1:2.5 R:R minimum filter — where it belongs

### Today

- **Computed**: `engine/risk_classifier.py:34` (`rr = target_dist / stop_dist`) and `engine/scoring.py:249`.
- **Used as a tier label**: `risk_classifier.py:48-58` — `risk_low_min_rr=2.5` only labels a signal `LOW` (best) tier. `MED` accepts `rr ≥ 1.5`. Falls through to `HIGH`, **but signal still fires and persists** (`signal_generator._persist`).
- **Used as a score component**: `scoring._score_risk_reward` (`engine/scoring.py:238-260`) — RR<1 still scores ~20, RR=2.5 scores ~70. No cliff.
- **Hard discard at "technical resistance < 2.5×ATR-stop"**: does **not exist anywhere**. There is no resistance-distance check vs ATR-stop.

### Recommended plug-point

A new **risk-quality gate** in `engine/verdict.py:_verdict_kind` (line 80) plus an explicit `WhyBlock.what_could_invalidate` entry. Pseudocode:

```python
# engine/verdict.py:_verdict_kind
MIN_RR = 2.5
if primary and primary.fired:
    rr = (primary.target_price - primary.entry_price) / max(1e-6, primary.entry_price - primary.stop_price)
    if rr < MIN_RR:
        return "NO_SETUP"   # or new "LOW_QUALITY"
```

For the *resistance* leg: add a helper in `engine/indicators.py` (or risk_levels.py) that returns the nearest pivot-high above entry (we already compute `pivot_high_20`, `indicators.py:44`):

```python
def nearest_resistance(df, entry):
    return float(df["pivot_high_20"].iloc[-1])  # 20-bar swing high

# In each v2 strategy after computing stop:
res = nearest_resistance(df, entry)
if (res - entry) < 2.5 * (entry - stop):
    return StrategyResult(..., fired=False, headline="resistance < 2.5×stop, low quality")
```

There is already a `risk_quality` *concept* via the LOW/MED/HIGH classifier, so the new gate should reuse `ClassifiedSignal` rather than parallel state.

---

## 4) RSI(14) > 75 / StochRSI overbought rejection

### Today

- `RSI(14)` is enriched at `indicators.py:24` and consumed only as a *bull-bias score* in `scoring.py:162-174`. Past 75 it is **clipped, not rejected** (clip range `(rsi-50, -25, 25)` line 172).
- **StochRSI is not computed** anywhere. `pandas_ta_classic` exposes `ta.stochrsi` — never imported.
- No strategy exits or refuses a long on overbought.
- Only RSI(2) extremes drive `s3_connors_rsi2` (the *opposite* direction — oversold entries).

### Cleanest plug-points

**Per-strategy** (best — preserves existing single-strategy reasoning paths):

```diff
# backend/src/swing_trader/strategies/v2/s1_trend_50_200.py
@@ -45,6 +45,11 @@
         atr = float(last.get("atr14", float("nan")))
+        rsi14 = float(last.get("rsi14", 50.0))
+        c_not_overbought = rsi14 < 75.0
+        if not c_not_overbought:
+            return StrategyResult(strategy_name=self.name, fired=False, score=0.0,
+                                  headline=f"{ticker}: RSI(14)={rsi14:.0f} — overbought, no entry")
```

Same gate applies to `s2_clenow_momentum.py` (around line 159) and `s4_minervini_vcp.py` (around line 79). `s3_connors_rsi2` and `s5_pead` are intentionally *contrarian / event-driven* and should be exempt.

**StochRSI**: add to `engine/indicators.py:23` block:

```diff
+    sr = ta.stochrsi(out["close"], length=14)
+    if sr is not None and not sr.empty:
+        out["stochrsi_k"] = sr.iloc[:, 0]   # %K (0..100)
+        out["stochrsi_d"] = sr.iloc[:, 1]   # %D
```

Then per-strategy gate `c_stoch_ok = stochrsi_k < 95 or stochrsi_d < 95` (i.e. not "pinned at 100" for two consecutive readings).

---

## 5) "Exit 24h before earnings" — what's missing

### What's already wired

- **Source**: `engine/signal_generator.py:222-234` — `_try_fetch_earnings(ticker)` calls `yfinance.Ticker(t).get_earnings_dates(limit=8)`. Best-effort, returns `[]` on failure.
- **Distribution**: `signal_generator.py:334` builds `earnings_map`, passed into `_build_basket` at line 248 as `basket["earnings_dates"]`.
- **Per-bar `days_to_earnings`**: computed at `signal_generator.py:419-423` and passed to `attach_score_breakdown` at line 430.
- **Used today by**:
  - `s3_connors_rsi2.py:78-96` — entry gate: no new long if earnings within 7 days.
  - `s5_pead.py:47-60` — entry trigger: requires earnings within last 5 days.
  - `engine/scoring.py:294-308` — penalises score when earnings within 0–3 days, boosts when freshly past.

### What's missing for "exit 24h before announcement"

There is no concept of an **active position** in this codebase — it is a daily-scan *signal generator*, not a portfolio engine. So "exit 24h before" must surface as:

1. **A `pre_earnings_exit_date` field on the trade plan** (analogous to `max_hold` at `verdict.py:188`). Owner file: **`engine/verdict.py`**, populate inside `synthesize_verdict` near line 195 using the `days_to_earnings` already passed to `attach_score_breakdown`.
2. **An invalidation entry** appended to `WhyBlock.what_could_invalidate` (`verdict.py:165-168`) when `days_to_earnings ≤ max_hold_days + 1`.
3. **Schema add**: a new `pre_earnings_exit_by: date | None` on `schemas.Verdict` (line 159).

There is no separate "exit engine" file today — `engine/backtester.py` (419 LOC) handles backtest exits but not live position state. A future `engine/exits.py` would be the right place once positions exist.

### Owner mapping

| Concern | File | Why |
|---|---|---|
| Wire `days_to_earnings` into Verdict trade-plan | `engine/verdict.py:155-200` | already gets the value |
| Add `pre_earnings_exit_by` schema field | `schemas.py:159` (`Verdict`) | single render contract |
| Surface in UI evidence | `engine/scoring.py:294-308` already does for scoring; reuse string | — |
| Source robustness | `engine/signal_generator.py:222-234` | yfinance is sole source — add Finnhub or `data/calendar/*.csv` fallback |

---

## 6) Concrete punch list (ordered, with effort estimates)

Effort key: **S** = ≤ ½ day, **M** = 1-2 days, **L** = ≥ 3 days incl. tests.

### A. ATR-stop replacement (Aditya bullet 1)

| # | Change | File(s) | Effort |
|---|---|---|---|
| A1 | New module `engine/risk_levels.py` with `atr_stop()` + `min_rr_target()` + `PCT_FALLBACK=0.05` | new file | **S** |
| A2 | Replace inline ATR-stop in v2 strategies | `strategies/v2/s1_trend_50_200.py:101`, `s2_clenow_momentum.py:160`, `s3_connors_rsi2.py:139` | **S** |
| A3 | Wrap structure stops with ATR floor (`stop = min(struct_stop, atr_stop)`) | `strategies/v2/s4_minervini_vcp.py:144`, `strategies/sr_breakout.py:42,66`, `strategies/macd_trend.py:31,54`, `strategies/volume_trend.py:60` | **S** |
| A4 | Update `StopLevel.method` to reflect actual mult (drop hard-coded "2x ATR(14)") | `engine/verdict.py:191` | **S** |
| A5 | Tighten v1 `volume_trend.py` target from `1.5×risk` to `2.5×risk` to honor min RR | `strategies/volume_trend.py:63` | **S** |
| A6 | Bump `risk_med_min_rr` from 1.5 → 2.5 (or keep MED for triage but add `verdict_min_rr=2.5`) | `config.py:62-68` | **S** |
| A7 | Hard discard in `_verdict_kind` when RR < 2.5 OR `(resistance - entry) < 2.5*(entry-stop)` | `engine/verdict.py:80-100` + add `nearest_resistance()` helper | **M** |
| A8 | Tests: ATR fallback NaN path, AAOI-style high-vol fixture, RR-discard verdict | `backend/tests/...` (new) | **M** |

### B. Negative-beta hedge surfacing when NDX RSI(14) > 70 (Aditya bullet 2)

| # | Change | File(s) | Effort |
|---|---|---|---|
| B1 | Add `qqq_rsi14` (and optionally `ndx_rsi14`) to regime fetch | `engine/regime.py:78-88` (compute via `ta.rsi` on QQQ close) | **S** |
| B2 | Extend `RegimeContext` schema with `qqq_rsi14: float \| None` and `hedge_recommended: bool` | `schemas.py:69` (`RegimeContext`) | **S** |
| B3 | Config: hedge basket env var, default `["DG","SIXU","XLP"]` | `config.py` (new `hedge_tickers: list[str]`) | **S** |
| B4 | New helper `engine/hedge.py` → returns highest-quality negative-beta candidate (lowest 60d corr to QQQ from `hedge_tickers`) | new file | **M** |
| B5 | When `qqq_rsi14 > 70 and qqq_above_200sma`, populate `Verdict`-run-level summary or add `hedge_candidate: HedgeBlock` to each BUY verdict | `engine/signal_generator.py:480` (run summary) and/or `schemas.py:159` (`Verdict`) | **M** |
| B6 | Frontend hook (out of scope for this audit but flag for FE ticket) | `frontend/...` | **M** |
| B7 | Tests: regime fixture with QQQ RSI=72, assert hedge candidate emitted | new tests | **S** |

### C. Earnings-gap pre-exit (Aditya bullet 3)

| # | Change | File(s) | Effort |
|---|---|---|---|
| C1 | Add `pre_earnings_exit_by: date \| None` to `Verdict` schema | `schemas.py:159` | **S** |
| C2 | In `synthesize_verdict`, if `days_to_earnings is not None and days_to_earnings ≥ 1`, set `pre_earnings_exit_by = as_of + (days_to_earnings - 1) days` AND clamp `max_hold_days` accordingly | `engine/verdict.py:155-200` (extend existing block; pass `days_to_earnings` through — it is already a parameter at line 121, currently unused inside the function) | **S** |
| C3 | Append "Exit by EOD `<date>` — earnings the next session" to `WhyBlock.what_could_invalidate` | `engine/verdict.py:163-168` | **S** |
| C4 | New `s3_connors_rsi2` & all v2 strategies: shorten `max_hold_days` if earnings within window | per-strategy `evaluate()` (each `s*.py`) | **M** |
| C5 | Robustness: yfinance returns empty silently — add a CSV/Finnhub fallback in `_try_fetch_earnings` | `engine/signal_generator.py:222-234` | **M** |
| C6 | Surface a daily "positions to flatten today" view (post-MVP, depends on a positions table that does not exist yet) | new `engine/exits.py` + `data/db.py` table | **L** |
| C7 | Tests: ticker with earnings in 3 days → verdict carries `pre_earnings_exit_by = today+2`; ticker with earnings in 1 day + WATCH → invalidation note | new tests | **S** |

### Suggested execution order

1. **A1, A2, A3, A6, A7** (1 day) — hardens stop geometry; immediate effect on AAOI-class names.
2. **C1, C2, C3** (½ day) — purely additive, no breakage risk; immediately surfaces in UI.
3. **B1, B2, B3, B4, B5** (1.5 days) — biggest user-visible win; needs a pinned hedge basket decision.
4. **A8, B7, C7** tests bundled (1 day).
5. **A4, A5, B6, C4, C5** polish (1 day).
6. **C6** parked until a positions table exists.

---

## Appendix — files read

- `research/ai-infra-prompt/00-PROMPT.md`
- `backend/src/swing_trader/strategies/base_strategy.py`, `bollinger_squeeze.py`, `ma_crossover.py`, `macd_trend.py`, `rsi_mean_reversion.py`, `sr_breakout.py`, `volume_trend.py`
- `backend/src/swing_trader/strategies/v2/{base,s1_trend_50_200,s2_clenow_momentum,s3_connors_rsi2,s4_minervini_vcp,s5_pead}.py`
- `backend/src/swing_trader/engine/{indicators,risk_classifier,regime,scoring,verdict,signal_generator,base_rate,sample_size}.py`
- `backend/src/swing_trader/{config,schemas}.py`

No code was modified.
