# 00 — Swing Trade Radar Research: Master Index

> **What this is.** A consolidated, multi-perspective research dossier on swing trading
> NASDAQ-100 mega-cap tech (AAPL, MSFT, NVDA, GOOGL, META, AMZN, TSLA, AVGO, NFLX, AMD + QQQ).
> Produced by 8 parallel research agents across 3 model families (Claude Opus 4.7, GPT-5.1,
> Gemini 3 Pro) to surface gaps and reduce single-model blind spots.
>
> **Total volume.** ~10,500 lines / ~470 KB across 8 documents.
>
> **Goal.** Build a defensible, evidence-based v2 of `swing-trade-radar` whose signals
> we can actually trust before risking real capital.

---

## 📚 Document Map

| # | File | Lines | Author Model | What it answers |
|---|------|------:|--------------|-----------------|
| 01 | [`01-classic-strategies.md`](./01-classic-strategies.md) | 1584 | GPT-5.1 | Every classic swing strategy (trend, mean-rev, breakout, momentum, volume) with rules, win-rates, Python snippets, regime fit, risk tier. Master comparison table at top. |
| 02 | [`02-risk-management.md`](./02-risk-management.md) | 997 | Claude Opus 4.7 | Position sizing models (worked examples), stop methodologies, R-multiples, portfolio heat, regime filters, blow-up case studies, psychology, safety checklist. |
| 03 | [`03-modern-quant.md`](./03-modern-quant.md) | 1547 | Gemini 3 Pro | Factor strategies, vol regimes, dealer gamma, sentiment/alt-data, PEAD, honest ML take, microstructure, Mag7 deep dive (2023-2026), what's overfit. |
| 04 | [`04-backtesting-methodology.md`](./04-backtesting-methodology.md) | 1264 | Claude Opus 4.7 | Vectorized vs event-driven, data biases, walk-forward + CPCV, PBO + deflated Sharpe, frictions, metrics that lie, tool comparison, trust checklist. |
| 05 | [`05-nasdaq100-megacap-specifics.md`](./05-nasdaq100-megacap-specifics.md) | 1227 | Claude Opus 4.7 | What makes this universe different: structure, correlations, earnings stats, macro, event calendar, per-ticker cheat sheet, vol surface. |
| 06 | [`06-implementation-stack.md`](./06-implementation-stack.md) | 1370 | Claude Opus 4.7 | Data sources, broker APIs, Python ecosystem, storage, signal pipeline, alerting, safety rails, deployment, **sub-$50/mo recommended stack**. |
| 07 | [`07-skeptical-perspective.md`](./07-skeptical-perspective.md) | 1219 | Claude Opus 4.7 | The contrarian view: EMH, edge decay, overfitting math, retail-trader behavioral evidence, concentration risk, passive flows eating alpha, anti-patterns. |
| 08 | [`08-institutional-playbook.md`](./08-institutional-playbook.md) | 1313 | Gemini 3 Pro | How pod shops actually run mega-cap tech books: sell-side signals, cross-asset, pairs/stat-arb, vol targeting, options spreads, multi-sleeve construction. Retail-adapted checklist. |
| 09 | [`09-support-resistance.md`](./09-support-resistance.md) | 269 | Claude Opus 4.8 | S/R methods (swing fractals, classic + Fib pivots, Fib retracement) with formulas + confluence/clustering algo, **plus a concrete design spec** for a ranked S/R map (`levels[]`) on every suggested trade. |

---

## 🎯 Executive Summary — The Consolidated Take

Eight research perspectives cross-checked against each other. Here is what **all of them agree on**, what they **disagree on**, and what the **strongest cross-source evidence** suggests we should actually build.

### A. Strongest cross-source consensus

These survived all 8 lenses (classic, modern, institutional, skeptical, methodology, mega-cap, risk, implementation):

1. **Risk management dominates strategy selection.** A mediocre strategy with disciplined ATR-based sizing, 1% account risk, and a regime filter beats a "great" strategy without them. (02 + 07 + 08)
2. **Regime filter is non-negotiable.** Trade longs only when SPY/QQQ above 200-SMA, and reduce exposure when VIX > 25 or VIX term-structure inverts. Most swing strategies' edges live in trending, low-vol regimes. (01 + 02 + 03 + 05)
3. **The earnings-event rule.** Never hold a mega-cap tech name through earnings without an explicit, separate "earnings trade" thesis with options-defined risk. Average single-name earnings move on these tickers: 5-12%, with 3σ tails routinely 15-20%. (02 + 03 + 05)
4. **Backtest distrust by default.** Apply deflated Sharpe ratio (Bailey-Lopez de Prado). Expect live Sharpe ≈ 0.4-0.6× backtest Sharpe. If backtest Sharpe < 1.5 after WFA, do not deploy. (04 + 07)
5. **Position sizing > entry signal.** Fixed-fractional 1% per trade with ATR stops is the boring-but-correct retail default. Kelly should be at most quarter-Kelly. (02 + 07 + 08)
6. **Universe constraint = edge.** Sticking to the top-10 mega-cap tech basket eliminates ~80% of the swing-trading rabbit holes (penny stocks, low-float pumps, illiquid options). It also makes the strategies HARDER (EMH bites worse here) — see point B. (05 + 07)

### B. Where the perspectives disagree (and what to do about it)

| Tension | Optimistic camp (01, 03, 08) | Skeptical camp (07) | Resolution we should code |
|---|---|---|---|
| **Do EOD technical signals work on mega-caps?** | Yes, with regime + size discipline; specific named strategies (VCP, Connors RSI(2), Clenow momentum) have shown >2-decade evidence | These are the most-analyzed names on earth; most retail "edges" decay or are illusory after costs. Barber-Odean / Chague show >95% of day traders lose money | **Treat ALL signals as hypotheses requiring walk-forward validation. Default to skepticism. Cap any single strategy's sleeve at 20% of risk budget.** |
| **Should we automate execution?** | Yes — Alpaca + cron + Telegram alerts (06, 08) | Auto-execution is the fastest path to ruin if a bug emits 50 orders. Human-in-the-loop slows you down enough to catch bugs (07 anti-patterns) | **Default to ALERT-ONLY mode. Live execution requires explicit env flag + per-trade human confirm. Paper trade for 90 days minimum.** |
| **Use ML?** | Gradient-boosted trees on engineered factor features have published, repeatable edge (03, 04) | Most retail ML is feature-leakage and overfitting in disguise; deflated Sharpe usually destroys reported numbers (07) | **No ML in v2. Ship rule-based first. ML is a Phase-3 add-on, AFTER rule-based system has 6+ months of live paper-trading evidence.** |
| **Mag7 concentration** | Liquid, news-driven, high-IV — perfect swing universe (05, 03) | 60%+ of QQQ weight in 7 names = single-factor risk; Nifty-50 and dot-com analogies (07, 05) | **Enforce a max 3 concurrent open positions in the Mag7 names. Track portfolio beta and cap at 1.5x SPY.** |
| **Strategy count** | Multi-sleeve is institutional best practice — uncorrelated alpha sources (08) | More strategies = more multiple-testing = more PBO; better to do one thing well (07) | **Ship 3-5 strategies max, each with documented historical evidence (>10 years of data, papers cited). No "let me try 50 variants".** |

### C. The shortlist of strategies the evidence actually supports

Filtered for: (a) >15 years of published evidence, (b) survived multiple-testing scrutiny in the skeptic doc, (c) practical on the NDX-100 universe, (d) tractable to implement.

| Tier | Strategy | Source doc | Why it survives | Risk tier |
|---|---|---|---|---|
| **A** | **50/200 Golden Cross + 200-SMA regime filter** (long-only, QQQ + components) | 01 §3, 07 §9 | Decades of evidence; simple; benchmark for trend-following; harder to overfit | LOW |
| **A** | **Clenow time-series momentum (top-decile, monthly rebalance)** | 01 §19, 03 §1, 08 §10 | Moskowitz-Ooi-Pedersen 2012 + Antonacci replication; works on NDX universe | LOW-MED |
| **A** | **ATR-based position sizing across ALL strategies** | 02 §3, 08 §5 | Not a strategy — a *requirement*. Without this, nothing else matters. | — |
| **B** | **Minervini VCP (volatility contraction + breakout)** | 01 §15 | Strong 30-year track record; needs visual judgment, hard to fully automate; pair with relative-strength filter | MED |
| **B** | **Connors RSI(2) < 10 mean-reversion (above 200-SMA only)** | 01 §8 | Connors published 2008; degraded but still has documented edge on QQQ when regime-filtered | MED |
| **B** | **Post-earnings drift on positive surprises (SUE > 1.5)** | 03 §5, 05 §3 | PEAD documented since 1968 (Bernard-Thomas); still alive in mega-cap tech with 2-4 week holds | MED |
| **C** | **NVDA/AMD pairs / GOOGL-META pairs (cointegration-filtered)** | 08 §4 | Real but small edge; requires Kalman-filtered ratio; only when ADF p < 0.05 in rolling window | MED-HIGH |
| **C** | **Dealer gamma + VIX term-structure as POSITION-SIZE modulator** (not entry) | 03 §3, 08 §8 | Use to *throttle* exposure during negative gamma / backwardation regimes, not as entry signal | LOW (when used as filter) |

**Explicitly REJECT for v2** (research caught these): single-stock breakouts on low-liquidity names, calendar anomalies (decayed), short-side mean-reversion on mega-caps (squeeze risk), any ML model not yet shown live evidence, leveraged ETFs, naked option selling, anything optimized on < 10 years of data.

### D. The "kill switches" we MUST encode (from 02 + 07 anti-patterns)

These are hard rules. Engine should refuse to emit signals if any are violated.

- ❌ No trade if account drawdown > 15% from peak (cool-off 5 trading days, then half-size for 10)
- ❌ No new position within 5 trading days of the ticker's earnings date
- ❌ No more than 3 concurrent Mag7-name positions
- ❌ No more than 6 total concurrent swing positions
- ❌ Total portfolio risk (sum of all open R) never > 6% of account
- ❌ No position if SPY < 200-SMA AND VIX > 30 (regime kill)
- ❌ No live trading without explicit `LIVE_TRADING=true` env var AND `--confirm` flag per order
- ❌ No deploying a strategy whose deflated Sharpe < 1.0 in WFA
- ❌ No risking > 1% of account on any single trade by default (configurable down, never up without a separate "elevated mode" gated by another env flag)

### E. Recommended Phase-2 build plan (synthesizes 06 + the shortlist)

```
Phase 2.0: Data + backtest skeleton
  - Polygon.io ($29/mo Starter) for adjusted EOD + corporate actions
  - DuckDB for OHLCV cache (NDX-100 daily, ~10 yrs)
  - vectorbt for fast strategy iteration + walk-forward
  - pandas_market_calendars for NYSE/NASDAQ holiday alignment
  - pandas-ta for indicators (cache by symbol+param hash)

Phase 2.1: Implement Tier-A strategies (3 only)
  - 50/200 Golden Cross (QQQ regime + components long-only)
  - Clenow time-series momentum (monthly rebalance top decile)
  - Connors RSI(2) mean reversion (ABOVE 200-SMA only)
  - Each with ATR-based 1% risk position sizing

Phase 2.2: Backtest with the trust checklist (doc 04)
  - 10+ years out-of-sample
  - Walk-forward with 6mo train / 1mo test
  - Deflated Sharpe ratio computed
  - PBO calculated for any parameter touch
  - Transaction cost model: 0.05 ATR slippage + $0.005/share + SEC fees

Phase 2.3: Signal pipeline
  - APScheduler cron @ 16:15 ET (after close, after final prints)
  - FastAPI dashboard: today's setups, open positions, portfolio heat, regime state
  - Telegram bot for alerts (mode: ALERT_ONLY default)
  - SQLite signals + trades audit log (every signal, every fill, every decision)

Phase 2.4: Paper trading 90 days minimum
  - Alpaca paper API
  - Track signal-to-fill slippage, missed signals, false positives
  - DO NOT proceed to live until paper PnL aligns with backtest (within 30%)

Phase 2.5 (gated by Phase 2.4 success): Tier-B strategies
  - Add VCP scanner + PEAD post-earnings drift
  - Keep Tier-A running unchanged

Phase 2.6 (gated by 6mo live evidence): Tier-C
  - Optional: pairs trading, dealer gamma overlay
```

### F. Things explicitly NOT in v2 scope

- Intraday execution (we are EOD/swing only)
- Options strategies (Phase 3+, defined-risk only when introduced)
- Short selling (Phase 3+, requires separate risk framework — squeeze risk on Mag7 is real)
- ML / LLM signals (Phase 3+, only after rule-based has 6mo live track record)
- Crypto, futures, FX, anything not US mega-cap equity
- Auto-execution without per-trade confirm
- More than 5 concurrent strategies
- Leverage > 1x

---

## 🔗 Cross-References / Where to Look for Specific Questions

| Question | Look in |
|---|---|
| "What's a good entry signal for AAPL right now?" | 01 (strategy catalog) + 05 (per-ticker cheat sheet) |
| "How big should this position be?" | 02 §3 (position sizing worked examples) |
| "Should I trade this through earnings?" | 02 §9, 05 §3 — short answer: no |
| "Is my backtest believable?" | 04 §10 (trust checklist) + 07 §3 (deflated Sharpe) |
| "Is the market in a tradeable regime?" | 02 §8 + 05 §11 |
| "What broker / data source / library should I use?" | 06 (decision matrix at end) |
| "Why might this whole project be misguided?" | 07 (read this first if feeling overconfident) |
| "How would a pro at Citadel approach this?" | 08 |
| "What's actually working in 2023-2026 on Mag7?" | 03 §9 (Mag7 deep dive) |
| "What can I safely automate?" | 06 §9 (safety rails) + 07 §10 (anti-patterns) |

---

## 📖 Reading Order Recommendations

**If you have 30 minutes:**
1. This index (00) — 5 min
2. 07 skeptical perspective sections 5 + 10 (cost math + anti-patterns) — 10 min
3. 02 §13 safety checklist — 5 min
4. 06 §11 final recommended stack — 5 min
5. 01 §0 master comparison table — 5 min

**If you have 2 hours:**
1. This index
2. 02 full (risk management) — the foundation
3. 07 full (skeptical) — the reality check
4. 01 §0 + the Tier-A deep dives (Golden Cross, Clenow, Connors RSI(2))

**If you're building Phase 2:**
1. 06 (implementation stack) — what to build with
2. 04 (backtesting methodology) — how to validate
3. 01 (strategies) — what to implement
4. 02 + 07 (risk + skeptic) — guardrails

---

## 🧠 Methodology Note

Research was deliberately distributed across 3 model families to reduce single-model bias:
- **Claude Opus 4.7** wrote docs 02, 04, 05, 06, 07 (long-form analytical + heavy citation work)
- **GPT-5.1** wrote docs 01, (skeptic attempt — replaced by Claude v2)
- **Gemini 3 Pro** wrote docs 03, 08 (modern quant + institutional perspectives)

Each agent had its own task brief, ran isolated (no shared context), and produced citations independently. Cross-references and consensus points in this index emerged from manual synthesis, not from any agent's own claim.

**Known limitations:**
- Some strategy win-rate stats cited in the docs are from secondary sources (blogs, books) rather than peer-reviewed papers; treat single-source numbers skeptically and verify in backtesting.
- "Modern" doc covers up to 2024-2025 published research; very recent regime shifts (2025 H2+) are not all captured.
- All numerical claims should be re-verified in your own backtest before deployment.

---

*Compiled 2026-06-01 by devclaw. Update this index when new research is added.*
