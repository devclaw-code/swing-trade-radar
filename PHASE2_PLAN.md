# Phase 2 Plan — Signal Engine + Explanation Dashboard (v2)

> **Purpose.** Re-scope Swing Trade Radar from "trading system" to **"signal advisor with detailed reasoning"**.
> User does NOT want auto-execution. User wants: each market day, for each NDX-100 mega-cap name, a clear
> recommendation ("BUY this setup", "AVOID", "HOLD watchlist") with a full explanation of *why*.
>
> **No trading activity.** This system does not connect to brokers, does not place paper or live orders,
> does not track a portfolio, and does not handle money in any form. It produces **read-only research
> verdicts**. The user reads, decides, and acts (or not) entirely outside this system.
>
> **Driver:** This is the consolidated v2 scope, derived from `research/00-INDEX.md` and 8 underlying research docs.
> **Status:** Plan. No code yet.

---

## 1. Reframed Product

The website is a **daily research desk**, not a broker.

For each ticker on a given trading day, the engine produces:

```
{
  "ticker": "NVDA",
  "as_of": "2026-05-30",
  "verdict": "BUY",                    // BUY | WATCH | AVOID | NO_SETUP
  "conviction": 0.72,                  // 0..1, ensemble across strategies that fired
  "primary_setup": "Connors RSI(2) Mean Reversion",
  "supporting_setups": ["50/200 trend up", "Golden cross intact"],
  "entry_zone":   { "price": 138.20, "method": "next-day open" },
  "stop_loss":    { "price": 132.40, "method": "2x ATR(14) below entry", "risk_pct": 4.2 },
  "target":       { "price": 148.50, "method": "previous swing high", "rr": 1.78 },
  "max_hold":     "10 trading days (RSI(2) reverts or stop)",
  "position_size_hint": "≤ 1% account risk; 145 shares for $25k account",
  "regime_context": {
    "spy_above_200sma": true,
    "qqq_above_200sma": true,
    "vix": 14.8,
    "vix_term_structure": "contango (healthy)",
    "regime_verdict": "favorable for long swings"
  },
  "why": {
    "headline": "RSI(2) hit 6.4 (extreme oversold) inside an established uptrend. Mean reversion edge is strongest in this setup.",
    "evidence": [
      { "factor": "RSI(2) = 6.4", "weight": 0.35, "note": "<10 threshold; Connors documented edge" },
      { "factor": "Above 200-SMA", "weight": 0.25, "note": "regime filter passed" },
      { "factor": "ADX(14) = 22, trending mildly", "weight": 0.15, "note": "trend strong enough not to be choppy" },
      { "factor": "Volume on red candle 1.2x avg", "weight": 0.10, "note": "no panic dump signature" },
      { "factor": "No earnings within 7 days", "weight": 0.15, "note": "event risk clear" }
    ],
    "historical_base_rate": "On NVDA 2010-2025, this exact setup (RSI(2)<10 + above 200SMA + no earnings within 7d) has occurred 87 times. Win rate 68%. Avg R = +0.83. Median hold 4 days.",
    "what_could_invalidate": [
      "Close below 132.40 (the ATR stop)",
      "Gap down >3% on no news (regime shift signal)",
      "VIX spikes above 25 (regime kill)"
    ],
    "counter_arguments": [
      "RSI(2) edge has decayed since 2015 — see research/07 §2",
      "Mag7 concentration risk: NVDA already 8% of QQQ"
    ]
  },
  "risk_tier": "MEDIUM",
  "doc_refs": ["research/01 §8", "research/02 §3", "research/05 cheat-sheet:NVDA"]
}
```

This is the *deliverable per ticker per day*. The frontend renders these as cards with progressive disclosure (headline → evidence list → historical base rate → counter-arguments).

---

## 2. What changes vs original `ARCHITECTURE.md`

The original arch is mostly fine. Changes:

| Layer | Original | New (v2) |
|---|---|---|
| Strategies | 6 generic modules | **Tier-A + Tier-B from research shortlist** (see §4) — 5 strategies max |
| Risk classifier | 🟢🟡🔴 only | Full risk profile: stop, target, R:R, position size hint, regime context |
| Output | Signal list | **Per-ticker daily verdict** with full `why` block |
| News | RSS scraper into list | RSS scraper that **flags catalyst names within 24h** so verdict can downgrade if heavy news ahead |
| Frontend cards | Simple "BUY/SELL" badge | Card with headline + expandable evidence panel + sparkline + "what would invalidate this" |
| Backtesting | Mentioned, not specified | **Walk-forward + deflated Sharpe + trust checklist (research/04)** before any setup goes "live" |
| Auto-execution | ⚠️ was implied | **Removed entirely.** No broker integration. Read-only system. |

---

## 3. Core architecture (revised)

```
┌─ Data layer ─────────────────────────────────────────────┐
│  yfinance (primary) → Alpha Vantage (fallback)           │
│  pandas_market_calendars for trading days                │
│  RSS news (Yahoo per-ticker + earnings calendar)         │
│  Cache: SQLite OHLCV + indicator snapshots               │
└──────────────────────────────────────────────────────────┘
                           ↓
┌─ Strategy layer (5 modules) ─────────────────────────────┐
│  1. trend_50_200          (regime filter + golden cross) │
│  2. clenow_momentum       (cross-sectional rank)         │
│  3. connors_rsi2          (mean rev, regime-gated)       │
│  4. minervini_vcp         (volatility contraction)       │
│  5. pead_drift            (post-earnings drift)          │
│  Each returns: {fired: bool, score: float, evidence: []} │
└──────────────────────────────────────────────────────────┘
                           ↓
┌─ Verdict synthesizer ────────────────────────────────────┐
│  - Combine strategy outputs into per-ticker verdict      │
│  - Apply regime filters (SPY/QQQ 200SMA, VIX)            │
│  - Apply event risk (earnings within 7d → downgrade)     │
│  - Compute stop/target/R:R/position size hint            │
│  - Compute historical base rate for this setup type      │
│  - Compose `why` block with weighted evidence            │
└──────────────────────────────────────────────────────────┘
                           ↓
┌─ Backtest validator (offline) ───────────────────────────┐
│  - Walk-forward 6mo train / 1mo test, 10y window         │
│  - Compute: Sharpe, deflated Sharpe, MaxDD, win rate,    │
│    avg R, profit factor, exposure                        │
│  - PBO if any params were tuned                          │
│  - Block any strategy whose deflated Sharpe < 1.0        │
└──────────────────────────────────────────────────────────┘
                           ↓
┌─ FastAPI ────────────────────────────────────────────────┐
│  GET /api/verdicts                 (today's, all tickers)│
│  GET /api/verdicts/:ticker         (full detail)         │
│  GET /api/historical/:setup        (base rate explorer)  │
│  GET /api/regime                   (current regime card) │
│  GET /api/backtests/:strategy      (deflated metrics)    │
│  GET /api/last-updated                                   │
└──────────────────────────────────────────────────────────┘
                           ↓
┌─ Next.js dashboard ──────────────────────────────────────┐
│  / (today)        ─ regime card + ticker grid + filters  │
│  /ticker/:symbol  ─ full verdict + evidence + chart      │
│  /strategies      ─ each strategy's backtest report      │
│  /history         ─ all past verdicts + did-they-work    │
│  /about           ─ methodology + research/ links        │
└──────────────────────────────────────────────────────────┘
```

---

## 4. The 5 strategies (locked v2)

From `research/00-INDEX.md` Tier A+B shortlist:

### S1: Trend (50/200 SMA + regime)
- **Long bias only.** Fire BUY if: price > 50-SMA > 200-SMA AND SPY > 200-SMA. WATCH if any one fails.
- Stop: 2× ATR(14) below entry. Target: trailing chandelier exit, 3× ATR.
- Hold: 2-6 weeks typical.
- *Why people care:* survives all skeptic tests; benchmark for trend.

### S2: Clenow Time-Series Momentum
- Rank NDX-100 by 90-day risk-adjusted return (slope / vol). Fire BUY on the top decile.
- Re-rank weekly. Exit when ticker drops out of top quintile or below 100-SMA.
- *Why:* Moskowitz-Ooi-Pedersen replicated 2012; Antonacci confirms.

### S3: Connors RSI(2) Mean Reversion (regime-gated)
- Fire BUY if: RSI(2) < 10 AND price > 200-SMA AND no earnings within 7 days AND VIX < 25.
- Exit: RSI(2) > 70 OR 5 trading days OR stop hit.
- Stop: 2× ATR.
- *Why:* Connors 2008 documented; still alive when properly regime-filtered.

### S4: Minervini VCP
- Detect volatility contraction (sequence of ≥3 lower-volatility pullbacks, each <60% of prior).
- Fire BUY on breakout above pivot with volume ≥ 1.5x avg AND in IBD-style RS top quartile.
- Stop: low of last contraction. Target: prior high + measured move.
- Auto-detection is heuristic, so produce a "VCP-likely" score not a hard fire — surface to user for manual chart review.

### S5: PEAD (Post-Earnings Drift)
- Fire BUY if: earnings beat consensus AND positive EPS surprise > 5% AND gap-up day open in top 1/3 of 20-day range.
- Hold 10-20 trading days.
- Stop: gap-fill price (the pre-earnings close).
- *Why:* Bernard-Thomas 1989; PEAD documented for 50+ years; alive in mega-cap tech with 2-4 wk drift.

---

## 5. The "explanation engine"

This is the differentiator. The backend doesn't just emit signals — it composes a structured `why` block:

```python
# pseudocode
def explain(ticker, setup, market_state):
    evidence = []
    for factor in setup.factors:
        evidence.append({
            "factor": factor.label,
            "value": factor.current_value,
            "weight": factor.weight_in_setup,
            "passed": factor.passed,
            "note": factor.human_readable_note,
        })

    base_rate = historical_base_rate(ticker, setup.signature)
    counter = pull_counter_arguments(setup, ticker)  # from research docs

    return {
        "headline": render_headline(setup, ticker, evidence),
        "evidence": evidence,
        "historical_base_rate": base_rate,
        "what_could_invalidate": setup.invalidation_conditions(ticker),
        "counter_arguments": counter,
        "doc_refs": setup.doc_references,
    }
```

**Historical base rate** is the killer feature: for every fired setup, compute on the fly *"how often has this exact pattern, on this exact ticker, worked over the past 10 years?"* using the cached OHLCV.

**Counter-arguments** are pulled from a small `risk_notes.yaml` keyed by setup-type and ticker, sourced from `research/07-skeptical-perspective.md` (e.g. "RSI(2) edge has decayed since 2015") and `research/02` (e.g. "NVDA single-name concentration risk in current QQQ").

**Doc refs** make every claim auditable — clicking opens the research file at the cited section.

---

## 6. Frontend — the "why" UX

Per ticker card on `/`:

```
┌────────────────────────────────────────────────────┐
│ NVDA  $140.50  +1.2%       [BUY • Conviction 0.72] │
│ ─────────────────────────────────────────────────  │
│ Setup: Connors RSI(2) Mean Reversion               │
│                                                    │
│ Headline: RSI(2) hit 6.4 (extreme oversold) inside │
│ an established uptrend. Mean reversion edge is     │
│ strongest in this setup.                           │
│                                                    │
│ ┌────────────[ sparkline 60d ]─────────────────┐   │
│ └──────────────────────────────────────────────┘   │
│                                                    │
│ Entry: $138.20 (next open)                         │
│ Stop:  $132.40 (-4.2%, 2x ATR)                     │
│ Target:$148.50 (R:R 1.78)                          │
│ Hold:  ≤ 10 days                                   │
│                                                    │
│ [▼ Why this trade] [▼ What could invalidate it]    │
│ [▼ Counter-arguments] [▼ Historical base rate]     │
└────────────────────────────────────────────────────┘
```

Click "Why" → expanded evidence list with weights + research links.
Click ticker → full detail page with chart, all strategy outputs (even non-firing), per-strategy backtest stats.

---

## 7. What we are NOT building (still)

- ❌ Broker integration / order routing
- ❌ Auto-execution of any kind
- ❌ Real-time intraday signals (EOD only — runs once per trading day post-close)
- ❌ Options recommendations (Phase 3)
- ❌ Short signals (Phase 3)
- ❌ ML / LLM-based signals (Phase 3, after rule-based has 6mo paper track record)
- ❌ Portfolio tracking / PnL accounting (the user manages their own positions)
- ❌ Watchlist beyond the locked NDX-100 mega-cap basket (~20 tickers)

---

## 8. Build order

1. **Wire the explanation data model** — TypeScript types + Pydantic schemas for the `verdict`/`why` shape above. (1 day)
2. **Implement S1 (Trend) end-to-end** — fetcher → strategy → verdict → API → card. Get one strategy fully working with its `why` block. (2 days)
3. **Backtest harness with deflated Sharpe + WFA** — block-deploy until S1 passes. (2 days)
4. **Add S3 (Connors RSI2) + S5 (PEAD)** — easiest two next, share infra with S1. (2 days)
5. **Historical base-rate computer** — generic over any setup signature. (1 day)
6. **Counter-arguments YAML + research-links UI** — the differentiator. (1 day)
7. **Add S2 (Clenow) — needs cross-sectional ranking**. (1 day)
8. **Add S4 (VCP) as scored signal, not hard fire**. (2 days)
9. **Frontend polish** — regime card, history page, /strategies backtest reports. (3 days)
10. **Deploy + Cloudflare tunnel + paper-track for 30 days before sharing.** (ongoing)

Total: ~2-3 weeks of focused work.

---

## 9. Open questions for the user

1. **Universe size:** lock to 20 mega-cap names, or expand to full NDX-100 for more daily setups? (Default: 20.)
2. **Daily output style:** show only fired setups, or show every ticker with a verdict (including AVOID/NO_SETUP)? (Default: every ticker, AVOID/NO_SETUP shown muted.)
3. **Historical base rate:** compute live on request, or precompute nightly into a base-rate cache? (Default: precompute.)
4. **News integration:** keep current RSS pipeline, or add a paid sentiment API? (Default: keep RSS + earnings-calendar flagging only.)
5. **Frontend hosting:** Cloudflare tunnel like before, or Vercel deploy? (Default: tunnel + IP-restricted for now.)

---

## 10. References

All design choices in this doc trace to:
- [`research/00-INDEX.md`](./research/00-INDEX.md) — exec summary
- [`research/01-classic-strategies.md`](./research/01-classic-strategies.md) — strategy definitions
- [`research/02-risk-management.md`](./research/02-risk-management.md) — sizing + stops
- [`research/04-backtesting-methodology.md`](./research/04-backtesting-methodology.md) — validation rules
- [`research/05-nasdaq100-megacap-specifics.md`](./research/05-nasdaq100-megacap-specifics.md) — universe specifics
- [`research/07-skeptical-perspective.md`](./research/07-skeptical-perspective.md) — counter-arguments source
