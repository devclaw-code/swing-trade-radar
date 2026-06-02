# 01 — Strategy Fit: "AI-Infra Bottleneck" Prompt vs Existing S1–S5

> Reviews `research/ai-infra-prompt/00-PROMPT.md` against the locked v2 strategy set
> (PHASE2_PLAN §4) and the research dossier. Goal: decide whether the proposal is a
> new strategy, a sector overlay, or a set of cross-cutting modifications — and spec
> exactly what to ship.

## TL;DR

- **The four-pillar prompt is ~70% restatement of things S1–S5 already do** (regime gate, ATR stop, R:R floor, no-earnings hold). Only one piece is genuinely new: the **bottleneck-thesis universe filter** that selects *which* names to evaluate.
- **The named tickers (AXTI, AEHR, AAOI) are out-of-universe.** They are small-caps; the project is locked to NDX-100 mega-cap (research/00 §A.6, research/07 §1.3). Adding them changes the system's risk character, slippage assumptions, and backtest validity — that is a separate Phase-3 conversation, not a strategy add.
- **Recommendation: do NOT ship a new "S6 Bottleneck Breakout" strategy.** Ship two cleanly-scoped, low-risk upgrades instead: (a) a **macro-event gate** in the verdict synthesizer (CPI/FOMC/earnings 48h blackout + earnings-eve exit), and (b) an **AI-infra-capex tag** as a sector overlay that boosts/penalises *existing* S1–S5 verdicts during the Oct–Nov capex window (research/05 §17.2). Both are dossier-supported and don't multiply the testing surface.
- **The user's three concrete fixes are individually correct and should be merged into the codebase regardless** — ATR stops are already standard (no fix needed; sanity-check S5 PEAD which currently uses gap-fill), the negative-beta hedge surfacing is a UI/regime feature not a strategy, and the earnings-gap rule is already in S3 and should be hoisted to a global verdict-synthesizer rule.
- **On the "second-order chokepoint" thesis: ~30% edge, ~70% narrative.** It's a real macro framing (research/05 §17.1 documents the supply-chain propagation in days), but the *named* implementation is a narrative-stock concentration trade that the dossier explicitly warns against (research/07 §G.3, §3 Nifty-50 analogy). Do not let it bypass deflated-Sharpe gating.

---

## 1. Gap Analysis — what the prompt overlaps with vs what's actually new

The proposed prompt has four pillars. Mapped against S1–S5 + the verdict synthesizer:

| Prompt pillar | Already covered by | New content |
|---|---|---|
| **1. Bottleneck thesis (AXTI/AEHR — picks-and-shovels)** | Nothing. S1–S5 are pattern-based, universe-agnostic within NDX-100. | ✅ **Genuinely new** — but it's a *universe selector / sector tag*, not a signal generator. And the named tickers are out-of-universe. |
| **2a. Patterns: Ascending Triangle / Bull Flag** | S4 (Minervini VCP) catches volatility-contraction breakouts; S1 catches trend continuation. Bull Flag ≈ pullback in uptrend, partially in S6-style pullback logic but absent. | ⚠️ Partial — explicit flag/triangle pattern recognition would be additive but is heuristic-heavy and would need its own DSR ≥ 1.0 gate. Cost > value at this stage. |
| **2b. Mean reversion to 20-EMA / 50-SMA** | Not exactly. S3 is RSI(2) mean-reversion to *price extreme*, not to a moving average. PHASE2_PLAN §18.1 (research/05) describes "21-EMA pullback in uptrend" as a documented pattern that S1–S5 don't cleanly capture. | ⚠️ **Modest gap** — could become a small variant on S1 ("S1b: pullback-to-EMA21 entry inside the trend regime"). Cleanest add. |
| **2c. Reject if RSI(14) > 75 or StochRSI pinned** | Not enforced. S1/S2/S4 fire on trend/breakout conditions and don't have a "too-extended" guard. | ✅ **Real gap**. Easy to add as a verdict-synthesizer guard rather than per-strategy. |
| **2d. Stop = entry − 2×ATR(14)** | Already the default in S1, S3, base_strategy. S5 (PEAD) uses gap-fill (intentional — research-justified). S2 (Clenow) uses 100-SMA exit. | ❌ Already done. Spot-check coverage but no change needed. |
| **3a. 7-day macro calendar awareness** | Partial — S3 has earnings-7d gate. No CPI / FOMC / NFP gate anywhere. | ✅ **Real gap**. Should be a global synthesizer rule, not per-strategy. |
| **3b. No new longs 48h before CPI/FOMC** | Not implemented. | ✅ **Real gap**. |
| **3c. Exit 24h before earnings if hold spans it** | Not implemented at synthesizer level (only S3 *gates* entry). PHASE2_PLAN doesn't mention an exit-before-earnings rule. | ✅ **Real gap and high-impact** (research/02 §9, research/05 §11 single biggest blow-up source). |
| **4. Min 1:2.5 R:R, discard if resistance < 2.5×ATR** | Already there as the LOW-tier risk threshold. MEDIUM tier accepts 1.5–2.5. | ⚠️ The prompt is *stricter* than current MEDIUM tier. Defensible but a tuning choice, not a new strategy. |

**Net new content from the prompt:**

1. ⭐ A **macro-event gate** in the synthesizer (CPI/FOMC blackout + exit-before-earnings).
2. ⭐ A **sector/thesis tag** (AI-infra capex chain) that conditions the verdict — not a separate signal.
3. An **over-extended guard** (RSI14 > 75 / StochRSI pinned) at the synthesizer level.
4. (Optional, lower priority) A **pullback-to-EMA21 entry variant** inside an existing trend regime.

The prompt's *named* tickers and the "second-order derivative" framing are interesting but are **outside the project's locked scope and would require a Phase-3 universe expansion with its own backtest validity case** (different liquidity, different slippage model — research/04 §3 calls 5–10 bps for liquid large-caps vs 20–50 bps for small-caps).

---

## 2. Recommendation: overlay + synthesizer rules, NOT a new S6

I recommend **rejecting the "S6 Bottleneck Breakout" framing** and instead shipping the gap items as **cross-cutting modifications**:

**(A) Macro-event gate — global synthesizer rule.** Highest-value, lowest-risk change. Reduces drawdowns without producing new signals to validate.

**(B) AI-infra-capex sector overlay.** A *tag* applied to existing verdicts during the Oct–Nov capex window (research/05 §17.2). Modulates risk tier and conviction; never originates a trade. No DSR test needed because it doesn't generate new entries — it modulates existing ones.

**(C) Over-extended guard.** Two-line addition at synthesizer level. Cheap insurance.

**Defense of this choice:**

1. **Multiple-testing budget.** Research/00 §B explicitly caps strategy count at 3–5 ("more strategies = more PBO"). We are already at S1–S5. A sixth would need its own walk-forward, deflated-Sharpe ≥ 1.0, PBO check. The added testing surface is *more* costly than the marginal alpha.
2. **The prompt's signal logic is not new.** Pillar 2 (Ascending Triangle / Bull Flag / mean-reversion-to-EMA) restates patterns S1+S3+S4 already cover; the over-extended guard improves them all rather than competing with them.
3. **The prompt's true contribution is risk discipline, not signal.** Pillar 3 (macro calendar) and Pillar 4 (R:R asymmetry) are *gates*, not *generators*. Gates belong in the synthesizer.
4. **The named-ticker bottleneck thesis is universe expansion in disguise.** AXTI ($300M cap), AEHR ($600M), AAOI ($800M) trade $20–80M ADV. The dossier's slippage, liquidity, and concentration assumptions break here (research/04 §3.4 — volume participation cap required; research/02 §13 — "Liquidity is risk capacity"). Mixing them with NDX-100 names in the same engine without a separate slippage model would silently inflate backtest Sharpe.
5. **Reflexivity warning is on the record.** Research/07 §3 (Nifty-50), §G.3 (narrative-update problem), and §1.3 (mega-cap-tech is the *worst* place to look for technical edge) all caution against trades whose primary justification is a macro narrative. The bottleneck thesis is exactly that flavour. Encoding it as an *overlay that modulates* rather than a *signal that originates* keeps the discipline.

What we are explicitly NOT doing:

- ❌ Adding AXTI / AEHR / AAOI to the universe.
- ❌ Auto-detecting Ascending Triangles or Bull Flags (heuristic-heavy, would need its own DSR test).
- ❌ Surfacing "negative-beta hedge candidates" (DG, SIXU). Out of universe; the existing regime card already conveys "favorable / unfavorable" — that is the right level of UI.

---

## 3. Concrete spec — what to actually build

### 3.1 Global macro-event gate (highest priority)

Lives in `engine/verdict_synthesizer.py`, applied AFTER strategies fire, BEFORE final verdict.

**Inputs:**
- Earnings calendar per ticker (already used by S3).
- Macro econ-calendar feed (new). Source: `forexfactory` JSON or `tradingeconomics` free RSS — pick one with the next 14 days of events tagged by impact (high/medium/low).

**Rules — applied to any LONG verdict candidate:**

```
DOWNGRADE_TO_WATCH if next high-impact macro event (CPI / Core CPI / FOMC / NFP /
                    PPI) falls within 48h of the proposed entry day.

DOWNGRADE_TO_WATCH if ticker has earnings within (max_hold_days + 1) days
                    AND the strategy does not already exit before earnings.

EARLY_EXIT signal in the verdict ("exit by close T-1") if an OPEN position
                    spans an earnings date.  This is informational only —
                    the system never executes; the user acts.
```

**Why DOWNGRADE_TO_WATCH and not AVOID:** the dossier's evidence (research/05 §6 Lucca-Moench pre-FOMC drift) actually shows positive expected return into FOMC, but with vol expansion. Removing the *new entry* is conservative; existing positions are addressed by a separate conviction-shrink.

**Verdict schema additions:**
```python
class MacroGate(BaseModel):
    next_high_impact_event: Optional[str]       # "CPI" | "FOMC" | "NFP" | ...
    event_date: Optional[date]
    hours_until_event: Optional[float]
    triggered_downgrade: bool
    earnings_within_hold: bool
    earnings_date: Optional[date]
```

Surface in the `why` block under a new evidence row: `"Macro gate: CPI in 36h → entry deferred"`.

### 3.2 Over-extended guard (small, immediate)

Synthesizer rule:

```
If a LONG verdict fires AND last-bar RSI(14) > 75
   → cap risk_tier at MEDIUM (never LOW),
   → cap conviction at 0.55,
   → add evidence row "RSI14=78.4 (extended) — entry caps tier".
If RSI(14) > 80 AND verdict is from S1/S2/S4 (trend/breakout family)
   → DOWNGRADE_TO_WATCH.
S3 (mean-reversion) is exempt — it's *supposed* to fire on extremes, just on the other side.
```

StochRSI is redundant given RSI14 — skip it; one clean rule beats two correlated ones.

### 3.3 AI-infra-capex sector overlay (medium priority)

Lives in `engine/sector_overlay.py`, applied AFTER strategies fire.

**Tag definition.** A static `sector_tags.yaml` mapping NDX-100 mega-caps to capex roles:

```yaml
ai_infra_chain:
  hyperscaler_buyer:   [MSFT, GOOGL, AMZN, META]   # capex announcers
  ai_compute_supplier: [NVDA, AMD, AVGO]            # primary beneficiaries
  ai_infra_adjacent:   [MU, TXN, KLAC, LRCX, AMAT, ASML, ANET]  # secondary
  ai_infra_neutral:    [AAPL, TSLA, NFLX, COST, ...]
```

**Window detection.** A "capex window" is open from 5 trading days before the first hyperscaler earnings report of a calendar quarter through 3 trading days after the last (typically MSFT/META/GOOGL/AMZN late-Oct + NVDA mid-Nov for Q3; same pattern Q1, Q2, Q4).

**Modulation rules** (apply to existing S1–S5 verdicts only; never originate a trade):

```
During capex window:
  - For LONG verdicts on ai_compute_supplier or ai_infra_adjacent tickers:
      conviction *= 1.10  (cap at 0.95)
      add evidence: "Within Q3 hyperscaler capex window — historical positive bias"
                    (doc_ref: research/05 §17.2)
  - If 2+ of research/05 §17.3 bear-case signals are present in the last 30d
    (tracked via a small state file updated manually weekly):
      conviction *= 0.80
      cap risk_tier at MEDIUM
      add counter-arg: "AI capex deceleration signals firing — research/05 §17.3"

Outside the window: no-op.
```

**Why this is safe.** It only modulates; never generates. No new entries means no new multiple-testing burden. Worst case it's a no-op overlay; best case it raises conviction in the documented seasonal window and shrinks it when the bear-case checklist trips.

### 3.4 Risk-profile interaction (LOW / MED / HIGH)

The existing risk classifier (ARCHITECTURE.md §11) sets tier from `(n_confirmations, stop_pct, rr)`. Add post-hoc cap rules:

| Trigger | New cap |
|---|---|
| Macro-event gate triggered | Cap at MED, downgrade to WATCH |
| RSI14 > 75 | Cap at MED |
| AI-infra bear-case checklist tripped (≥2 signals) | Cap at MED |
| Earnings within hold window | Cap at MED, attach "exit T-1" instruction |

These are *caps only* — they never *upgrade* a tier. Composability is monotone.

### 3.5 Things explicitly NOT in this spec

- ❌ Pattern recognition for Ascending Triangle / Bull Flag (defer; would need own DSR test).
- ❌ S6 strategy (rejected per §2).
- ❌ Universe expansion to AXTI / AEHR / AAOI (separate Phase-3 decision with its own slippage and liquidity model).
- ❌ Negative-beta hedge surfacing (out of locked universe; the existing regime card is sufficient).
- ❌ StochRSI as a separate guard (correlated with RSI14, no marginal info).

---

## 4. Backtest plan

The macro-gate + over-extended guard + sector overlay all *modify* existing strategy outputs. Backtesting them well requires the deflated-Sharpe gate (research/04 §10).

### 4.1 Gate-and-overlay backtest (the actual deliverable)

**Method.** Re-run the existing S1–S5 backtest harness twice: once raw, once with the new rules in (A/B/C order). Apply the **trust checklist** verbatim from research/04 §10.

**Window.** 2014-01-01 → 2024-12-31 (10 years), with 2025–2026 reserved as out-of-sample for paper-track confirmation.

**Universe.** The locked NDX-100 mega-cap basket (PHASE2_PLAN §1 — ~20 names) plus QQQ, SPY, ^VIX as regime inputs.

**Walk-forward.** 6-month train / 1-month test rolling, per research/04 §5.

**Metrics required:**
- ΔSharpe (raw → with gate). Expectation: small positive (gate reduces vol more than return).
- Δ deflated Sharpe. The headline number. **Threshold: gate must not *reduce* DSR by more than 0.1 vs raw.** (We accept slightly lower raw return for materially lower max-DD.)
- Δ MaxDD in R. Expectation: -10% to -25% improvement (this is what the gate is for).
- Δ exposure / time-in-market. Expectation: -5% to -15%.
- Per-event-type contribution: how many trades did the CPI gate skip? FOMC? earnings? Did skipped trades' counterfactual returns net positive or negative? (This is the honest test.)

**Pass bar.** The gated system must show:
1. DSR ≥ 1.0 *per remaining strategy* (research/00 §A.4 hard rule — no change here).
2. Lower max drawdown vs raw.
3. The 95% bootstrap CI for ΔSharpe must include zero or be positive (i.e. the gate is at worst neutral, not actively hurting).

### 4.2 Sector overlay backtest

Run an **A/B** on the AI-infra-adjacent subset (NVDA, AMD, AVGO, MU, ANET, AMAT, KLAC, LRCX, ASML):

- A: raw conviction.
- B: capex-window-modulated conviction.

Test whether "fired during capex window" trades have a statistically significant return premium vs "fired outside window" trades on the same tickers, same strategies. If the t-stat doesn't clear 2.0 on the 10-year sample, the overlay is decorative — drop the +10% / -20% modulation, keep only the evidence/counter-arg text.

### 4.3 Benchmark

QQQ buy-and-hold over the same 10-year window. The 8-doc dossier (research/00 §B optimist-vs-skeptic resolution) sets the bar: **net of costs, the system must not underperform QQQ buy-and-hold over a full cycle.** This is the honest hurdle.

### 4.4 What this backtest will *not* prove

- It will not prove the bottleneck thesis is real. The thesis names are out-of-universe.
- It will not prove pattern recognition (Ascending Triangle etc.) would have helped. Out of scope.
- It will not validate the user's named tickers. Different liquidity regime; would need its own study.

---

## 5. Honest call on the "second-order derivative / chokepoint" thesis

**Verdict: ~30% edge, ~70% narrative — and the dossier already flags exactly this risk.**

### 5.1 What's real

- Research/05 §17.1 documents that **AI-infra supply-chain anomalies propagate through the basket within 24–48 hours** (TSM monthly sales miss → NVDA selloff next session). This is a real, fast, mostly-priced-in mechanism — but its half-life is too short for a 3–10 day swing capture *unless* you are systematically positioned ahead of the catalyst, which the prompt does not specify.
- Research/05 §17.2 documents the **Oct–Nov hyperscaler capex sequence** as the most pivotal trading window of the year for AI infra names. *This part of the thesis has direct dossier support.* It is exactly what the §3.3 overlay encodes.
- Research/03 §9 (Mag7 deep dive) confirms the **second-order linkage** (hyperscaler capex → NVDA/AVGO/AMD revenue 1–2 quarters out) is structurally real.

### 5.2 What's narrative

- The prompt's named tickers (AXTI substrates, AEHR test) are **classic narrative-driven small-caps** whose moves are dominated by single-name news, not by the macro chain. Research/02 §9 + research/04 §3.4 both warn that small-cap edges in published backtests are routinely 2–6% CAGR overstated due to slippage and survivorship — exactly where the bottleneck list lives.
- Research/07 §3 (Nifty-50 analogy) is on point: *"a coherent narrative ... that justifies paying any price"* historically precedes multi-year underperformance once the narrative cracks. The "AI capex supercycle" is named explicitly in §3 as the modern Nifty-50 echo. Trading the *thesis* (rather than the *price action*) is the failure mode.
- Research/07 §G.3 ("narrative-update problem") explicitly warns that traders who enter on a narrative ("NVDA AI tailwind") rationalise into a different one when price moves against them ("multiple still has room") — and that narrative-rationalised holding is a primary discipline failure. The chokepoint framing is a fertile breeding ground for this.
- The "second-order derivative" framing is **almost-too-clean storytelling.** The actual chain has ~6 stages (memory → testing → substrate → packaging → board → integrator → hyperscaler), each with its own demand cycles. Picking AXTI and AEHR out of that chain is post-hoc selection. A serious version of the thesis would require a data-driven pick (top-decile composite-score among all chain participants), not two named tickers.

### 5.3 What I'd accept as evidence the thesis has edge

The thesis would deserve its own strategy slot only if all three of these were demonstrated on real data:

1. A backtest on the *full* AI supply chain (TSM, ASML, AMAT, KLAC, LRCX, ANET, MU, AVGO, NVDA, AMD, plus a separately-modeled small-cap subset) over 2015–2024, walk-forward, with research/04 §3.4 small-cap slippage applied, showing **DSR ≥ 1.0 net of frictions**.
2. A demonstration that **timing the chain bottleneck** (not just being long the chain) adds Sharpe vs an equal-weight basket. Otherwise the "chokepoint" claim collapses to "long AI infra basket" — which is just QQQ in disguise.
3. **Out-of-sample stability** across regimes — including 2018-Q4, 2020-Q1, and 2022-H1, the three regime breaks where AI-infra names underperformed materially. Narrative thesis trades typically die in exactly those windows.

### 5.4 Bottom line

The right thing to do is what §3.3 specifies: **encode the *time window* (Oct–Nov capex) as an overlay**, because that piece is dossier-documented and mechanically clean. Do **not** encode the *named-bottleneck stock-picks*, because those are narrative selections in a sub-universe whose backtest validity is fundamentally different and which the dossier specifically warns against.

If the user wants to trade AXTI/AEHR/AAOI personally, that's their call. The system stays disciplined: NDX-100 mega-cap, deflated-Sharpe gated, narrative-skeptical by default — exactly the way research/00, research/02, research/07 say it should.

---

## 6. References

- `research/ai-infra-prompt/00-PROMPT.md` — the proposal under review.
- `PHASE2_PLAN.md` §1, §4 (S1–S5 specs), §5 (explanation engine).
- `ARCHITECTURE.md` §4 (legacy strategies), §11 (risk classification).
- `research/00-INDEX.md` §A (consensus), §B (optimist-vs-skeptic), §C (Tier-A/B shortlist), §D (kill switches), §F (out-of-scope).
- `research/01-classic-strategies.md` §3 (Golden Cross), §8 (Connors RSI(2)), §15 (VCP), §19 (Clenow).
- `research/02-risk-management.md` §3 (sizing), §9 (earnings rule), §13 (safety checklist).
- `research/03-modern-quant.md` §9 (Mag7 deep dive — second-order linkages).
- `research/04-backtesting-methodology.md` §3 (frictions for small-caps), §5 (walk-forward), §10 (trust checklist).
- `research/05-nasdaq100-megacap-specifics.md` §6 (FOMC pre-drift), §11 (regime kill rules), §17.1–17.3 (capex sequence + bear-case checklist), §18.1 (21-EMA pullback pattern).
- `research/07-skeptical-perspective.md` §1.3 (mega-cap is the worst sub-universe for technicals), §3 (Nifty-50 / AI-supercycle analogy), §G.3 (narrative-update problem).

---

*Compiled 2026-06-02 by sub-agent strategy-fit review. Author opinion; not financial advice.*
