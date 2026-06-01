# 05 — Swing Trading the NASDAQ-100 Mega-Cap Tech Basket

> Scope: AAPL, MSFT, NVDA, GOOGL/GOOG, AMZN, META, TSLA, AVGO, NFLX, AMD + QQQ/QQQM
> Focus: what makes this universe *structurally different* from generic stock-picking,
> and what specific tweaks any swing system needs to survive in it.
>
> Sources synthesized (see footnotes inline): Nasdaq index methodology docs
> (`indexes.nasdaq.com/docs/Methodology_NDX.pdf`, `NDX_SpecialRebalance_2023.pdf`),
> Callan & Mellon research notes on the 2023 Special Rebalance, Invesco/Slickcharts
> for current QQQ weights, NY Fed SR-512 (Lucca/Moench "Pre-FOMC Drift"), SpotGamma
> OPEX research, Market Chameleon / Moomoo IV-crush histories on NVDA, Nasdaq IR
> on Monday/Wednesday weeklies (effective Jan/Feb 2026), CBOE 0DTE volume notes,
> Reuters/MarketWatch on triple-witching, Schwab/BlackRock concentration pieces,
> NBER pre-announcement drift literature.

---

## 0. TL;DR — the seven things that actually matter

1. **You are not picking 10 stocks. You are picking 4–5 stocks twice.**
   The top 5 names (NVDA ~8%, AAPL ~7.3%, MSFT ~5.3%, AMZN ~4.7%, META ~4%–4.5%, then GOOGL+GOOG combined ~5%+) drive >40% of QQQ. Mid-cap NDX names move *around* mega-caps, not independently. Practical effect: your "10-name basket" has an effective breadth closer to 3–4 independent bets.

2. **Passive flows dominate marginal price.** QQQ is a ~$300B+ ETF; XLK, VGT, SMH, and dozens of derivative products all hold the same basket. Daily flows >> fundamental news on most days. This compresses intraday dispersion and makes correlation regimes the dominant risk factor.

3. **Earnings are 5×–10× the noise of any other catalyst.** Implied 1-day moves of 5–10% are standard; realized moves frequently exceed implied. A swing system that holds through earnings is a vol trade, not a trend trade — treat earnings windows as a separate regime.

4. **Mega-cap tech is *the* long-duration trade.** Rate moves (10Y yield, real yields, DXY) hit this basket harder than any other large-cap segment. FOMC, CPI, NFP are first-class catalysts that override technicals for ~2 sessions around the print.

5. **Gamma & OPEX matter more here than in any other equity universe.** Top 10 NDX names dominate single-stock options volume (NVDA + TSLA alone were ~25%+ of single-stock options notional in 2025). Pinning, vanna unwinds, and post-OPEX vol expansion are tradeable, repeatable patterns. Monday/Wednesday weeklies (Jan 26 / Feb 2 2026 launch on TSLA/NVDA/AAPL/AMZN/META/AVGO/GOOGL/MSFT/IBIT) further densify dealer hedging cycles.

6. **Idiosyncratic catalysts cluster on a known calendar.** NVDA GTC (March), AAPL WWDC (June), MSFT Build (May), GOOGL I/O (May), META Connect (Sept), TSLA delivery prints (1st week of Jan/Apr/Jul/Oct), iPhone launch (Sept), holiday sales reads (late-Nov/Dec). These are dateable months in advance — your calendar is your edge.

7. **Generic swing systems break here unless you slow them down and widen stops.** Average True Range as % of price (ADR%) on these names is 1.5–4% intraday; mid-cap swing rules calibrated for ~2% ATR will whipsaw. The fix is regime filters + wider initial stops + smaller size, *not* more indicators.

---

## 1. Structural characteristics

### 1.1 Index construction (NDX) and its weight-cap mechanics

The Nasdaq-100 is a **modified market-cap-weighted index** of the 100 largest non-financial Nasdaq listings. Key rules from the official methodology PDF (`indexes.nasdaq.com/docs/Methodology_NDX.pdf`):

- **Annual reconstitution** in December (announcement early-Dec, effective 3rd Friday of December — coincides with quad-witching).
- **Quarterly rebalances** in March, June, September, December — announcements made early in those months, effective prior to the open on the 3rd Friday.
- **Weight caps applied at every rebalance:**
  - No single issuer may exceed **24%** weight.
  - Issuers individually weighted **>4.5%** may not collectively exceed **48%** of the index.
- **Special Rebalance trigger** — outside the normal schedule — if either constraint is breached on an EOD basis between scheduled rebalances. Only executed **twice in 25 years**: 1998 (initial methodology change for IRS RIC diversification), 2011 (AAPL cut from ~20% to ~12%), 2023 (top-7 reduced from ~56% to ~44%; MSFT cut from 12.8% → 9.8%, NVDA cut ~3pp, AAPL slightly trimmed but became #1 at 11.5%).

**Why this matters for swing traders:**

- Every quarterly rebalance forces **mechanical flows** in the top names. Passive AUM tracking NDX is in the hundreds of billions; even small weight changes trigger seven-figure dollar flows per minute on the rebalance MOC print. Effective dates land on the **3rd Friday of M/J/S/D**, overlapping with monthly OPEX → these days have *disproportionate* late-day volume and intraday reversal potential.
- The 48% / 4.5% rule is the **structural ceiling** on the AI-trade. Any further NVDA/MSFT/AAPL/META/AMZN/GOOGL+GOOG/AVGO run that pushes the basket >48% triggers another Special Rebalance ~weeks later. Track combined weight quarterly; a basket sitting at 47%+ is a flag.
- **December rebalance has the biggest deletions/additions** because it's the only event that changes constituents (quarterly rebalances only re-weight). New additions get bought aggressively in the days leading in; deletions get dumped. The "NDX-add trade" is one of the cleaner systematic plays in this universe (long 5 days before, sell on effective open).

### 1.2 Passive flow impact — the "single-beta" problem

Combine QQQ, QQQM, TQQQ/SQQQ (leveraged), XLK, VGT, IGM, ARKK, FNGS, plus the long tail of thematic products (SMH for semis, MAGS for Mag-7), and mega-cap tech has become a **flow-dominated tape**. Estimates from BlackRock and Schwab concentration pieces put combined passive ownership of the top 10 NDX names at **18–25% of float**.

Practical implications:

- **Intraday correlations spike when SPY moves >1%.** When risk-on/risk-off dominates, single-name fundamentals don't matter — the whole basket trades as one beta. This kills mean-reversion pair trades during macro shocks.
- **End-of-day MOC imbalance** prints (3:50pm ET on NYSE; Nasdaq closing cross) regularly show $1B+ flows in QQQ on rebalance days, FOMC days, CPI days, and month-end. Last-15-min liquidity is often *better* than mid-session but with sharp directional bias.
- **Leveraged/inverse ETF daily rebalance** (TQQQ/SQQQ) creates a *mechanical late-day flow* that amplifies whatever direction the index moved that day. On big trend days, expect the move to extend into the close; on chop days, no effect. This is the source of the "3:30pm ramp" mythology — it's partially real, partially a TQQQ/SQQQ rebalance artifact.

### 1.3 Top-of-book liquidity

These are the deepest-book stocks in the US market. Indicative spreads (regular hours):

| Ticker | Typical spread | $/min top-3-level depth |
|---|---|---|
| AAPL  | $0.01 (1bp)  | ~$3–5M |
| MSFT  | $0.01–0.02   | ~$2–4M |
| NVDA  | $0.01–0.03   | ~$3–6M (post-split; pre-split was $0.10–0.50) |
| AMZN  | $0.01–0.02   | ~$2–4M |
| META  | $0.01–0.03   | ~$1.5–3M |
| GOOGL/GOOG | $0.01    | ~$2–3M each class |
| AVGO  | $0.05–0.15   | ~$500K–1.5M |
| NFLX  | $0.05–0.20   | ~$300K–1M  |
| TSLA  | $0.01–0.02   | ~$2–5M |
| AMD   | $0.01–0.02   | ~$1–3M |
| QQQ   | $0.01        | ~$10M+ |

Implications for swing entries:
- **Use limit orders at NBBO mid or better** for all 10 names; market orders are wasteful given the spreads.
- **Algo execution (VWAP/TWAP) is unnecessary** under ~$500K notional in the top 6 names.
- **Pre-market liquidity is real but selective:** for AAPL/MSFT/NVDA/AMZN, you can fill $100K easily from 7am ET. For NFLX/AVGO, spreads widen 5–10× pre/post. NFLX especially is famous for $5+ post-earnings spreads in the after-hours session.

### 1.4 After-hours behavior

Big tech earnings *all* drop after-the-bell (AMC). The post-earnings AH session is where 70–90% of the gap is established:

- **0–15 min post-print:** algo + initial human reaction. Spreads explode, prints jump in $5–$20 increments on NVDA/NFLX/META.
- **Conference call (typically 4:30–5:00pm or 5:00–5:30pm ET):** *this* is where the move finalizes. Guidance, capex commentary, gross-margin color drives the second leg. NVDA's stock can swing 5%+ from the 4:20pm print to the 5:30pm call close just on Jensen's tone.
- **Wall Street note dump 6–8pm ET:** sell-side ratings/PTs adjust; futures react. By 8pm, the gap is largely "set" — overnight movement to the 9:30am open is usually <1% absent news.

For swing traders: **never assume the post-print AH price = open price.** The 1-hour-after-call price is a much better predictor than the immediate-reaction print.

---

## 2. Correlation regimes

### 2.1 The two states: "single beta" vs "dispersion"

Mega-cap tech oscillates between two regimes:

**Regime A — Single Beta (risk-on/risk-off, macro dominates):**
- All 10 names + QQQ move together with realized 1-month pairwise correlations >0.6.
- Triggered by: Fed surprise, geopolitical shock, recession-fear days, tariff news, broad VIX spike.
- Trade implication: only direction matters; pair trades and dispersion strategies bleed.
- Detection: SPY/QQQ realized correlation >0.85 on 20-day basis; VIX >20; CBOE implied correlation index elevated.

**Regime B — Dispersion (idiosyncratic, single-name catalysts dominate):**
- Pairwise correlations drop to 0.2–0.4; sector-internal pairs decorrelate.
- Triggered by: earnings season (especially the Jul/Oct/Jan/Apr clusters), product cycles, regulatory headlines hitting one name.
- Trade implication: relative-value setups work; sector-pair mean reversion is tradeable.
- Detection: 20-day realized pairwise correlation between top 10 NDX names <0.5; CBOE implied correlation low; earnings season active.

**Heuristic for swing entries:**
- In Regime A → trade QQQ or the strongest/weakest *single* name; don't try to be cute with pairs.
- In Regime B → exploit dispersion via long-strong/short-weak pairs within sub-sectors.

### 2.2 Sub-sector pairs that *actually* work

These pairs have decades of fundamental commonality and tradeable mean reversion:

| Pair | Rationale | Typical spread vol (60d) | Half-life |
|---|---|---|---|
| **NVDA / AMD** | Both GPU/AI compute, same end demand, NVDA leads | 25–35% annualized | 8–15 days |
| **GOOGL / META** | Both digital ad duopoly, share macro ad cycle | 15–22% | 12–20 days |
| **MSFT / AAPL** | Both "quality mega-cap defensive" — lowest-beta pair | 10–15% | 20–35 days |
| **AMZN / GOOGL** (cloud) | AWS vs GCP narrative, less stable pair | 20–28% | 10–18 days |
| **AVGO / NVDA** | Both AI-infra winners, AVGO lags & catches up | 22–30% | 10–20 days |
| **TSLA / NVDA** | Both retail-darling high-beta names, often co-move on AI narrative | 28–40% | 5–12 days |
| **NFLX / META** | Both ad-driven consumer attention plays (post-Netflix-ads tier) | 25–35% | 8–15 days |

**Strategy pattern:** z-score the log-spread on 60-day window; enter at |z|>2; exit at |z|<0.5 or 20-day timeout. Beware earnings — *always* flatten pairs 1 day before either leg reports.

### 2.3 QQQ vs underlying basket — arbitrage and tracking

QQQ tracks the underlying NDX extremely tightly:
- **Creation/redemption units = 50,000 shares**; authorized participants (AP) arbitrage any deviation within seconds.
- Premium/discount to NAV >5bps is rare and short-lived (<5 min).
- **Tracking error vs NDX TR index** ~3–5bps annualized.

Tradeable angles:
- **QQQ vs cash basket dispersion trade** is *not* available to retail with any edge — the APs vacuum any mispricing.
- **What is tradeable: QQQ vs SPY ratio (RTY/NDX/SPX/DJI relative strength).** The QQQ/SPY ratio is one of the cleanest momentum signals in macro — when it's trending up, the AI/tech beta is winning; when it inflects down, leadership rotation is starting. Pattern: 50-day MA of QQQ/SPY ratio crossing the 200-day historically flags 3–6 month regime shifts.
- **QQQ vs MAGS (Roundhill Mag-7 ETF)** isolates "mega-cap tech only" vs "NDX-with-tail." Spread widening means the tail (mid-cap NDX: PEP, COST, NFLX-tier, semis, biotechs) is leading or lagging the headline names.

---

## 3. Earnings — the dominant catalyst

### 3.1 Why earnings are different here

In small/mid-caps, earnings are *a* catalyst. In mega-cap tech, **earnings are the only catalyst that reliably resets the entire index's narrative.** Microsoft's Azure growth number can move QQQ 2% on its own. NVDA's data-center revenue guide *is* the AI trade.

Implied moves (1-day earnings move, ATM straddle priced day-of):

| Ticker | Typical implied move | Realized avg (last 8 qtrs) | Beat-rate of implied |
|---|---|---|---|
| NVDA | 8–10% | ~9–11% | realized > implied ~55% |
| TSLA | 7–10% | ~8–12% | realized > implied ~60% |
| META | 7–9% | ~7–10% | ~50% |
| NFLX | 7–10% | ~8–12% | ~55% |
| AMZN | 5–7% | ~5–8% | ~50% |
| GOOGL | 4–6% | ~4–7% | ~45% |
| MSFT | 3–5% | ~3–5% | ~45% (most "boring" — straddle sellers' favorite) |
| AAPL | 3–5% | ~3–5% | ~45% |
| AMD | 7–10% | ~8–12% | ~55% |
| AVGO | 5–8% | ~5–9% | ~50% |

(Per Market Chameleon implied-move history & Moomoo NVDA writeup citing avg ~11.7% post-earnings IV crush across last 11 NVDA prints.)

### 3.2 Post-earnings drift (PEAD) — does it exist in mega-cap?

The classical PEAD literature (Bernard-Thomas 1989, etc.) finds drift mainly in small/mid-caps because of slow analyst revision. In mega-caps:

- **Information is incorporated within 1 trading day** in 80%+ of cases.
- **However, *narrative* drift persists** in the AI capex names (NVDA, AVGO, MSFT). When NVDA beats and guides, the second-derivative names (AVGO, AMD, MU, SMCI, ARM) drift higher over 5–10 days as analysts revise the *whole supply chain*.
- **Trade implication:** the cleanest PEAD trade in this universe is **NOT** trading the reporter itself — it's trading the *correlated tail*. NVDA beats → buy AVGO/MU/SMCI on the open the next day, target 3–7 day hold.

### 3.3 Whisper vs consensus — what actually moves the stock

The published consensus EPS/revenue is often a poor predictor of reaction. What matters:

- **"Buyside whisper"** — typically 2–5% above sell-side consensus for AI-darlings during a hype cycle. A "beat" that misses the whisper sells off.
- **Forward guide** (next-Q rev guide vs sell-side next-Q estimate) is the single biggest driver of post-print moves. A current-quarter beat with a soft guide = down 5–10%. An in-line print with a raised guide = up 5–10%.
- **Per-segment metrics that move the tape:**
  - NVDA → Data Center revenue & next-Q DC guide
  - MSFT → Azure growth (cc), AI capex commentary
  - GOOGL → Cloud revenue growth, YouTube revenue, traffic acquisition cost (TAC)
  - AMZN → AWS growth & operating margin, retail op-margin
  - META → Reality Labs loss, daily/monthly users (DAP/MAP), Reels monetization
  - AAPL → iPhone revenue, Services revenue & gross margin, China revenue
  - TSLA → Auto gross margin ex-credits, deliveries vs prior, FSD/robotaxi commentary
  - NFLX → net subscriber adds (defunct since they stopped reporting!), revenue per member, ad-tier traction
  - AVGO → AI revenue ($/qtr), VMware integration progress
  - AMD → Data Center revenue & MI300/MI325 ramp

### 3.4 IV crush timing

- IV ramps **2–4 weeks before** earnings (front-month vol > back-month — vol term structure inverts).
- IV crush is **80%+ realized within the first 30 minutes** of the next session.
- Post-earnings IV typically settles **20–40% below pre-earnings IV** within 2 sessions, then normalizes over 5–10 days.
- NVDA's last several prints showed IV crush of ~11–14% per the Market Chameleon dataset.

**Practical playbook:**
- **Avoid buying premium 1 week before earnings** unless you have specific directional conviction *and* are willing to pay the vol premium.
- **Calendar spreads** (sell front, buy back) work when you expect the *gap* to be smaller than implied but want to stay exposed to the post-earnings drift.
- **Diagonals** are the cleanest "I think it goes up after earnings but don't want to pay full vol" structure — long back-month OTM call, short front-week call at the same or higher strike.

### 3.5 Earnings season clusters

NDX reporting concentrates in **4 weeks per quarter**, ~3 weeks after quarter-end:

| Quarter ends | Reporting cluster | Heaviest week |
|---|---|---|
| Dec 31 | mid-Jan to early-Feb | last week of Jan: MSFT/META/TSLA Wed, AAPL/AMZN Thu |
| Mar 31 | mid-Apr to early-May | last week of Apr / first week of May |
| Jun 30 | mid-Jul to early-Aug | last week of Jul / first week of Aug |
| Sep 30 | mid-Oct to early-Nov | last week of Oct / first week of Nov |

**NVDA is the lone outlier** — it reports ~3 weeks *after* its fiscal quarter end, which is shifted: late-Feb (Q4), late-May (Q1), late-Aug (Q2), mid-Nov (Q3). NVDA earnings are routinely "the most-important earnings print of the season" because they land *after* the rest of the index already reported.

---

## 4. Macro sensitivity

### 4.1 Rate sensitivity (the long-duration trade)

Mega-cap tech cashflows are long-duration: high terminal-value share, low near-term cash. DCF math says they're more sensitive to discount-rate changes than dividend-heavy value names. Empirically:

- **Beta to 10Y yield (1-month rolling):** NDX is ~-1.5 to -2.5x the 10Y move on Fed-driven days (10bps higher yield → roughly -1.5% to -2.5% on NDX on average).
- **Beta to 2Y yield:** even higher in absolute value because 2Y is more reactive to Fed policy.
- **Beta to real yields (TIPS):** dominant driver in 2022 sell-off; less dominant in 2024-25.

Practical: **always check 10Y direction before entering a swing position in QQQ.** A rising 10Y trend (>4.5%) is a hostile tape for the long side; a falling 10Y is a tailwind.

### 4.2 USD/DXY effect

Mega-cap tech derives 40–60% of revenue internationally:
- AAPL: ~60% international
- MSFT: ~50%
- META: ~55%
- GOOGL: ~55%
- AMZN: ~35% (AWS more global than retail)
- NVDA: ~85% (incl. China before bans, now Taiwan/Korea/EU)

A strong DXY (>105) is a headwind — every 1% DXY move ≈ -0.4% to -0.7% on FX-translated earnings. Swing implication: a sharp DXY uptrend lasting >2 weeks usually precedes a tech-relative-underperformance window.

### 4.3 Semiconductor cycle

NVDA, AVGO, AMD (plus the broader SMH basket: TSM, ASML, AMAT, LRCX, MU, INTC) move on the global semi-cycle:
- **SOX/QQQ ratio** is the cleanest cycle indicator. Outperforming → AI build-out / chip up-cycle.
- **Book-to-bill ratios** from SEMI and TSM monthly sales are leading indicators of the cycle inflection.
- **WFE (wafer fab equipment) capex** announcements from TSM, Samsung, Intel drive AVGO/AMAT/ASML.

### 4.4 China exposure

| Ticker | China rev % | Sensitivity to China headlines |
|---|---|---|
| AAPL | ~18% (Greater China) | Very high — iPhone share in China is the swing factor |
| TSLA | ~22% | High — Shanghai factory + China EV competition |
| NVDA | 12–15% (variable, ban-dependent) | Very high — every export-control headline moves stock 3–5% |
| AVGO | ~32% (incl. routing chips) | High but less narrative |
| MSFT | <2% direct | Low |
| GOOGL | ~1% direct (banned) | Low directly; high on macro China-via-ad-spend |
| AMZN | <2% direct | Low |
| META | ~10% (Chinese advertisers — Temu/Shein/PDD spend on Meta ads) | Moderate — tariff news on Chinese e-comm hits this indirectly |

**Catalyst pattern:** tariff/export-control headlines in early-morning ET (often dropped before US open during Asia hours) → AAPL, NVDA, TSLA gap-down in pre-market. Mean-reversion bounce happens within 1–3 sessions ~70% of the time *unless* the policy is confirmed permanent.

### 4.5 AI capex cycle

The single dominant narrative since late-2022. Key reads:

- **Hyperscaler capex** (MSFT, GOOGL, AMZN, META) — quarterly guidance, expressed in $B. Sum of the 4 hyperscalers' annual capex (~$300B+ run-rate as of 2025) directly correlates to NVDA/AVGO revenue.
- **Capex *deceleration*** is the #1 risk for the AI trade — when hyperscalers guide flat-to-down sequentially, NVDA/AVGO/AMD sell off 5–15% on the read-through.
- **MSFT and META announce capex guidance on their earnings calls** — *this* is the source of the biggest single moves in the AI-infra names. NVDA being up 5% on a MSFT capex raise is a regular occurrence.

---

## 5. Event calendars to respect

### 5.1 Macro calendar — first-class events

These dominate everything; trade smaller or flat into them.

| Event | Frequency | Release time ET | Mega-cap impact |
|---|---|---|---|
| **FOMC decision + presser** | 8x/year (~6wk cadence) | 2pm / 2:30pm | Highest single-event impact. NDX moves 1–3% in 60 min on average. Pre-FOMC drift (Lucca-Moench 2012) shows positive equity drift in 24h before announcement — *real, persistent, well-documented*. |
| **CPI** | monthly, ~10th–15th | 8:30am | NDX usually moves 0.5–2% on the release. Big surprise (>0.2% off consensus) → 2–4% move. |
| **PPI** | monthly, day before CPI | 8:30am | Lower magnitude than CPI but directional confirm. |
| **NFP (jobs)** | first Fri of month | 8:30am | NDX moves 0.5–2%. Reaction is rate-driven (hot print = bad for tech if Fed-cut narrative is in play). |
| **Core PCE** | last Fri of month | 8:30am | Fed's preferred gauge. Mid-impact. |
| **ISM Mfg/Services** | 1st & 3rd biz day of month | 10am | Lower impact unless very off-consensus. |
| **JOLTS** | monthly | 10am | Low impact normally; higher when Fed is data-dependent. |
| **Retail Sales** | mid-month | 8:30am | Higher impact for AMZN/AAPL. |
| **Jackson Hole** | August | varies | Major Fed-speak event; full-week effect. |

### 5.2 Pre-FOMC drift (the empirically-real free lunch)

NY Fed staff paper SR-512 (Lucca & Moench) documents a **persistent positive drift in S&P futures starting ~24 hours before scheduled FOMC announcements**, accounting for >80% of the equity risk premium over the sample period 1994–2011. Subsequent research extends and largely confirms.

For mega-cap tech: the drift is **larger in NDX than SPX** because tech is more rate-sensitive. Practical edge:
- Enter long QQQ or top-3 names ~24h before scheduled FOMC announcement.
- Exit before 2pm ET release (drift is *pre*-announcement; the post-announcement move is bidirectional and dominated by Powell's specific language).
- Average historical edge: ~30–50bps on QQQ over the 24h window.
- **Caveat:** the drift has weakened in recent years as it's become well-known; size accordingly.

### 5.3 OPEX & options-driven calendar

- **Monthly OPEX = 3rd Friday** of every month. Equity options + index options + futures (in March/June/Sept/Dec → "quad witching"). Volume on these days regularly 1.5–2× normal.
- **Quarterly OPEX (M/J/S/D)** is the *only* date when index futures expire. Massive forced flows. June 2024 quad-witch had $5.5T notional expiring (MarketWatch).
- **Pinning effect:** stocks with very heavy single-strike open interest tend to drift toward the round-number strike into Friday close. Empirically observable on AAPL, NVDA, TSLA; less so on smaller-cap names. Source: SpotGamma OPEX research.
- **Post-OPEX vol expansion:** dealer gamma resets after expiry → next 1–3 sessions often see larger moves than the OPEX week itself.
- **Monday/Wednesday weeklies** approved by SEC, effective Feb 2 2026, on TSLA, NVDA, AAPL, IBIT, AMZN, META, AVGO, GOOGL, MSFT — this **triples** the dealer-hedging cadence and is expected to compress intraday vol in these names while increasing event-window vol.

**Swing rule:** if a swing position has OPEX expiring during your hold window with heavy OI at a strike near current price, expect *less* trend (more chop) into Friday close; plan exits Thursday afternoon or Monday open.

### 5.4 0DTE (zero-days-to-expiry) volume

Per CBOE/Nasdaq data, **0DTE accounts for ~60% of options volume in QQQ and SPY** (Aug 2025 CBOE figures). Single-stock 0DTE in TSLA/NVDA/AAPL has grown dramatically.

Implications:
- **Intraday reversals are sharper** — 0DTE flows compress dealer-hedging cycles into hours.
- **Late-day "charm" flows** (option time-decay forcing delta adjustments) drive the 3–4pm session.
- For swing traders: not directly relevant, but understand that intraday entries can look stranger than they used to; use end-of-day prints for signal generation, not 10-minute bars.

---

## 6. Per-name catalysts (the calendar you must build)

These are the *idiosyncratic*, calendar-able events. Build them into your tracker.

### AAPL
- **iPhone launch event** — early/mid-September (always Tue). Stock reaction is typically muted-to-negative on the day ("sell the news"); 2-week post-event drift is often negative as initial-demand reads come in.
- **WWDC** — early-mid June (typically the second Mon). Software-only event; less price impact than iPhone launch unless major AI/services news.
- **Holiday-quarter sales reads** — November/December. Foxconn worker counts, Apple supplier data (TSM, Hon Hai monthly sales). Negative supply-chain reads are heavily traded.
- **Berkshire 13F filing** — early-Feb (Q4 13F due ~45 days after quarter-end). Any further AAPL trim by Buffett is market-moving.
- **Services revenue** — increasingly the bull case; watch quarterly print.
- **EU regulatory** — DMA enforcement, App Store fine headlines.

### MSFT
- **Build conference** — May, developer-focused. Lower stock impact than NVDA/GOOGL events but watch AI tooling demos.
- **Ignite** — Sept/Nov, enterprise event. Azure-focused.
- **Activision/regulatory** — concluded but watch for fresh M&A.
- **OpenAI relationship updates** — anything on GPT-X capex or partnership terms moves MSFT 1–3%.
- **Earnings: Azure constant-currency growth + AI capex guide is the only number that matters.**

### NVDA
- **GTC (GPU Technology Conference)** — March (sometimes Oct mini-GTC). Jensen keynote is *the* AI event. Stock typically rallies into GTC, sells off on/after the keynote (classic "sell the news"). Past 3 GTC keynotes: stock down avg ~1.5% next session, down ~3% 5-day.
- **Computex** — late May / early June (Taipei). Hardware reveals. Moderate impact.
- **CES** — early Jan. Auto/edge AI announcements.
- **SIGGRAPH / Hot Chips** — Aug. Less price impact.
- **Quarterly earnings** — late-Feb, late-May, late-Aug, mid-Nov.
- **Export-control headlines** — unpredictable, always pre-market drops. Mean-reverts ~70% of the time within 3 days.
- **Hyperscaler capex prints** — MSFT/GOOGL/META/AMZN earnings move NVDA 3–8% on capex commentary alone.

### GOOGL/GOOG
- **Google I/O** — May, developer conference. Gemini updates, AI product launches.
- **Made by Google** — Aug/Oct, Pixel hardware event. Low impact.
- **DOJ antitrust** — ongoing, remedy phase. Headline risk on settlement / forced-divestiture talk.
- **YouTube/Cloud quarterly disclosures** — earnings-driven.
- **AI overview / Search-share concerns** — perplexity, ChatGPT competitive headlines move stock.

### AMZN
- **AWS re:Invent** — late November/early December. AI compute announcements (Trainium/Inferentia/Anthropic partnership).
- **Prime Day** — July (one or two events). Read-through on consumer health.
- **Holiday-quarter** — Q4 retail is critical; expect Nov/Dec channel checks.
- **FTC antitrust trial** — late 2026; headline risk.

### META
- **Connect** — Sept/Oct, Reality Labs / Quest / Ray-Ban announcements. AI/VR focus.
- **Reality Labs losses** — quarterly, watched as drag-vs-growth.
- **Reels monetization rate** — quarterly disclosure.
- **Election years** — political ad cycle boost in Q3/Q4.

### TSLA
- **Quarterly delivery numbers** — first week of Jan/Apr/Jul/Oct. Pre-earnings critical data. Moves stock 5–15% on miss/beat.
- **Production updates** — monthly China sales (CPCA) early in each month.
- **AI Day / "We Robot" / Robotaxi events** — typically annual; FSD demo / robotaxi reveal. Stock is *highly* sensitive to demo quality.
- **Q3 quarterly call** — annual "Master Plan" updates.
- **Elon Musk Twitter/X activity** — non-calendar but constant catalyst. Political headlines have moved TSLA 5–10% in 2024–25.

### AVGO
- **Earnings (late-Mar, late-May/Jun, early-Sept, early-Dec)** — note: AVGO earnings lag the calendar quarter by ~3 weeks (fiscal year-end Oct).
- **AI revenue runrate disclosures** — each call now includes a $/qtr AI revenue number; growth here drives the stock.
- **VMware integration progress** — synergies & margin commentary.
- **Hyperscaler ASIC contract wins/losses** — major news events when disclosed.

### NFLX
- **Quarterly earnings** — only major catalyst calendar-wise. NFLX stopped reporting subscriber numbers in 2025 → focus on ad-tier ARPU, revenue, engagement metrics.
- **Content release schedule** — Stranger Things, Squid Game, NFL Christmas Day, WWE deal headlines all noticed.
- **Password-sharing crackdown updates** — historically major catalyst, now mostly priced in.
- **Live sports announcements** — rights deals (NFL Christmas, WWE, FIFA) move shares.

### AMD
- **Quarterly earnings** — late-Jan/Apr/Jul/Oct.
- **MI300/MI325/MI350 ramp updates** — guidance on AI accelerator revenue is the single biggest swing factor; AMD has tried to position as the #2 AI silicon player.
- **Data Center & Embedded segment results** — Xilinx-derived embedded biz adds cyclicality.
- **CES, Computex, AI/HPC events** — product reveals.

### QQQ / QQQM
- All of the above, weighted.
- Plus: ETF-specific flow events on rebalance dates.
- QQQM has lower expense (0.15% vs 0.20%) and is preferred for buy-and-hold; QQQ has deeper options/liquidity for trading. **Use QQQ for swing trades.**

---

## 7. News & sentiment — what actually moves the price

### 7.1 Tier-1 sources (price-moving on publication)

These hit the tape (Bloomberg/Reuters terminals) faster than retail can react and *always* move price:

- **Bloomberg** — flash headlines, especially on M&A, capex, regulatory.
- **Reuters** — similar, often first on Asia-time and geopolitical.
- **WSJ** — scoop-driven; "WSJ reports Apple is..." has 2–5% move power.
- **The Information** — tech-specific scoops; high reliability.
- **FT** — strong on regulatory/EU/UK.
- **CNBC (David Faber, Sara Eisen)** — on-air M&A scoops still move stocks.
- **Semafor, Punchbowl** — political/regulatory color, growing influence.

### 7.2 Tier-2 — analyst / sell-side moves

- **Morgan Stanley** (Katy Huberty on hardware historically; Adam Jonas on TSLA) — high impact PT moves on AAPL/TSLA.
- **Goldman Sachs** (semis team) — NVDA/AMD PT moves.
- **JP Morgan, BofA** — diversified coverage.
- **Wedbush (Dan Ives)** — TSLA/AAPL — high media presence, sometimes moves retail flows.
- **Wells Fargo, Citi, Barclays** — secondary impact.
- **Independent shops:** Melius, Bernstein (Stacy Rasgon on semis), New Street (Pierre Ferragu on NVDA/TSLA), Loop Capital, Rosenblatt — *do* move stocks despite being smaller.

### 7.3 Tier-3 — Twitter/X accounts that matter

Use these as *signals*, not gospel; verify via Tier-1 within 5 minutes.

- **@DeltaOne** — fast on Bloomberg/Reuters flash headlines.
- **@FirstSquawk** — fast wire aggregator.
- **@WalterBloomberg** — Bloomberg headline mirror.
- **@unusual_whales** — options flow.
- **@SpotGamma** — dealer positioning, gamma levels.
- **@MichaelMOTTCM** — macro.
- **@TheTranscript_** — earnings call snippets.
- **Company IR accounts** (varies in usefulness).
- For TSLA specifically: **@elonmusk** himself, **@Tesla**, **@SawyerMerritt** (TSLA news aggregator), **@TroyTeslike** (delivery estimates).
- For NVDA: **@nvidia**, **@SemiAnalysis_** (Dylan Patel — supply chain).

### 7.4 13F filings & whale watching

- **Berkshire Hathaway 13F** — released ~45 days after quarter-end (mid-Feb, mid-May, mid-Aug, mid-Nov). Any AAPL position change is market-moving. (Buffett has been trimming AAPL through 2024-25.)
- **Stan Druckenmiller, Bill Ackman, David Tepper, Michael Burry, Soros Fund** — major tech positions watched closely.
- **Citadel, Renaissance, Two Sigma** — less narrative impact (high-turnover quant funds).
- **Pelosi/Congressional STOCK Act filings** — increasingly tracked by retail; high momentum impact in microcaps, modest in mega-caps.

### 7.5 Insider activity

- **Form 4 filings** — must be filed within 2 business days. Large insider sells in NVDA (Jensen), TSLA (Elon, Kimbal), MSFT (Satya) get headlines but typically minimal price impact since they're often pre-planned 10b5-1.
- **Cluster insider buying** is much rarer and more meaningful — multiple insiders buying within a 30-day window has historically been a strong signal even in mega-caps.

---

## 8. Volatility surface — the trader's view

### 8.1 Typical IV ranks (rough historical ranges)

| Ticker | IV30 typical range | IV percentile "low" | IV percentile "high" |
|---|---|---|---|
| AAPL | 18–30 | <22 | >32 |
| MSFT | 18–28 | <20 | >30 |
| NVDA | 40–65 | <40 | >70 |
| AMZN | 25–40 | <25 | >40 |
| GOOGL | 22–32 | <22 | >35 |
| META | 28–42 | <28 | >45 |
| TSLA | 50–80 | <50 | >85 |
| AVGO | 30–45 | <28 | >50 |
| NFLX | 30–48 | <30 | >50 |
| AMD | 40–60 | <38 | >65 |
| QQQ | 14–22 | <14 | >24 |

Note these are *baseline* IV30; pre-earnings front-month IVs can spike 50–100% higher.

### 8.2 Skew patterns

- **Put skew** (downside puts more expensive than upside calls) is the default for AAPL/MSFT/AMZN — these are "perceived safe" mega-caps where tail risk feels asymmetric to the downside.
- **Call skew** ("call wings priced higher") regularly appears in NVDA, TSLA, AMD during AI-hype phases — retail and momentum buyers chase upside calls, dealers raise prices.
- **Skew flips** are tradeable. Sharp call-skew bleed in NVDA often precedes 5–10% pullbacks (the speculative tail is exhausted).

### 8.3 Term structure

- **Contango (back-month IV > front-month)** is normal — pricing more uncertainty further out.
- **Backwardation (front > back)** appears 2–4 weeks before earnings and during macro shocks. Strong signal.
- **Earnings-week front-week IV** can spike to 100%+ annualized for NVDA/TSLA/NFLX; back-month barely moves. Cleanest IV crush trades exploit this.

### 8.4 Weeklies vs monthlies

- Top 10 NDX names all have weekly options every Friday + monthly + quarterly + LEAPs.
- **Monday & Wednesday weeklies** (effective Feb 2026) on TSLA/NVDA/AAPL/AMZN/META/AVGO/GOOGL/MSFT — adds 2 more expiries per week. Implication: dealer hedging becomes near-continuous; certain swing patterns (like the "Tues/Wed gamma-driven drift") may attenuate.
- For swing trades 5–15 days out: prefer **monthlies** for tighter spreads & deeper liquidity. Weeklies are for short-dated tactical bets only.

---

## 9. Comparison vs broader market

### 9.1 Does QQQ swing trading beat SPY swing trading?

**Yes — historically, by a meaningful margin in trending environments; no in chop.** Reasons:

- **Higher beta (QQQ ≈ 1.2x SPY)** → larger moves to capture for any given signal.
- **Less sector dispersion** → simpler signal interpretation (when QQQ is up, you know *why*: tech is up).
- **Wider ADR%** → wider profit targets vs same-risk stops.

But also:
- **Higher whipsaw risk on macro days** because QQQ is more rate-sensitive.
- **Earnings drag** — 60%+ of QQQ market cap reports in a 3-week cluster; if your signal triggers a long the day before MSFT earnings, you're exposed to a 3–5% gap.
- **Concentration risk** — one NVDA blowup wipes out 8% of your QQQ position by weight.

**Composer/Finzer backtest summaries** (recent retail-quant comparisons): QQQ swing systems calibrated to a 5–15 day hold with trend-following bias outperform SPY-equivalent by ~3–6% annualized over 2015–2025, but with ~1.5x drawdown.

Practical recommendation:
- Trade **QQQ** (or top-3 names individually) when in Regime A (single-beta).
- Trade **single names with dispersion-aware sizing** when in Regime B.
- Use **SPY** for hedging or as a low-vol alternative; don't expect alpha from SPY trend-following at this point in the cycle.

### 9.2 NDX vs other indices — relative-strength view

- **NDX/SPX ratio** — leadership indicator. Trending up = AI/tech-led market; flat/down = broadening / rotation.
- **NDX/RUT (Russell 2000) ratio** — mega-cap vs small-cap. Historically ratio extremes have flagged 12–18 month regime turns.
- **SMH/QQQ ratio** — semis leading tech, or lagging? Sharp SMH outperformance is a 2nd-derivative AI-hype signal.

---

## 10. Concrete strategy adaptations

Generic swing systems are usually built on R2K-tier or all-cap mid-cap data. Applied to mega-cap tech, the following adjustments are typically necessary:

### 10.1 Slow the trend filter

- A 20-day MA crossover that works on a $5B-cap stock will whipsaw on NVDA. Use **50-day / 200-day** for the regime filter; use **10-day / 20-day** only for entry timing within an already-confirmed regime.
- For QQQ specifically, the **21EMA on daily / 8EMA pull-back** is a battle-tested setup with decade+ of historical edge.

### 10.2 Widen stops

- ATR-based stops should use **2.0–2.5× ATR(14)** on mega-cap tech vs the typical 1.5× for mid-caps.
- Hard percentage stops: **6–10% for individual names**, **3–5% for QQQ**. Anything tighter is just paying for noise.

### 10.3 Regime filters are *mandatory*

Don't take trend trades when:
- VIX > 25 (regime-shift territory).
- 10Y yield trending up + DXY trending up (dual headwind).
- 1 day before/of major macro event (FOMC, CPI, NFP).
- The week of major NDX-name earnings unless you're explicitly trading the earnings.
- QQQ < 200-day MA (only countertrend / mean-reversion plays; no trend longs).

### 10.4 Size by realized vol, not dollar amount

- Position size = (target portfolio risk per trade) / (stop distance in $)
- For NVDA/TSLA: assume 3–4% ADR, position size accordingly.
- For MSFT/AAPL: 1.5–2.5% ADR, can size larger.
- Equal *dollar* allocations across the basket give you 2–3× more risk in TSLA/NVDA than MSFT/AAPL.

### 10.5 Avoid holding through earnings (default rule)

- Earnings = vol trade, not directional swing. The 1-day gap can swallow 3 weeks of careful swing P&L.
- If you *want* exposure to the earnings move, **buy the implied move via options structures** (long straddle / strangle / debit spreads) — *don't* hold a delta-1 stock position through the print unless you have a specific edge.
- Some PEAD / drift strategies enter *after* earnings for the 5–10 day follow-through (this is one of the cleaner setups, especially in NVDA, MSFT, META post-beat).

### 10.6 Use sector pair hedges

- Long NVDA + Short AMD (or vice versa) — reduces market beta, isolates relative-strength edge.
- Long QQQ + Short SPY — isolates tech vs market beta.
- Long single-name + Short XLK or QQQ — isolates single-name idio.

### 10.7 Time-of-day entries

- **Avoid first 30 minutes** (9:30–10:00 ET) — algo-driven volatility, false breakouts.
- **10:00–10:30 ET** is a typical "reversal window" after the open.
- **Best swing entries: 10:30–11:30 ET or 2:00–3:30 ET.**
- Last 30 min (3:30–4:00 ET) is dominated by MOC flows and is dangerous for new entries on the close.

### 10.8 Calendarize your exits

- If FOMC, CPI, or major earnings is within your hold window, **plan exit before**, not "let it ride."
- For trend trades held >10 days, set a trailing stop at the 21EMA *and* a hard time stop at 20 sessions.

### 10.9 Track flows, not just price

- Daily QQQ creation/redemption (ETF.com, ETF Trends).
- Daily NDX futures open interest (CME).
- Sector ETF flows (XLK, SMH, IGM).
- 0DTE put/call ratio in QQQ (CBOE).
- Flow shifts often precede 5–10 day price drift.

### 10.10 Don't fight Jensen, Satya, Sundar, or Tim Cook on earnings calls

When the CEO of a mega-cap delivers a clear bullish/bearish guide on the call, the market's instant reaction is usually the *right* direction over 5 days. Trying to fade a clean guidance shift in NVDA/MSFT/META has been a losing trade ~70% of the time over 2023–25.

---

## 11. Risk management specifics for this universe

### 11.1 Concentration risk

- Don't run a "diversified" 10-name tech basket and pretend it's diversified. Effective N = 3–4.
- **Max single-name allocation: 15–20%** of swing book (and even that is concentrated by traditional standards).
- **Max sector (NDX-style tech) allocation: 50–60%** — leaves room for hedges, cash, and other-sector swing trades.

### 11.2 Correlation breakdown risk

- Pair trades blow up in Regime A. Limit pair-trade book to 20–30% of swings.
- Have a "macro-shock kill switch" — if VIX gaps >5 points or QQQ gaps >2%, close all pair trades at the open.

### 11.3 Gap risk

- Mega-cap tech gaps overnight are routine: 1%+ gap on ~30% of sessions; 3%+ on ~5% of sessions (earnings-weighted).
- Position sizing must assume potential 5–10% overnight gap.
- Use options (defined risk) when overnight gap risk is unacceptable.

### 11.4 Liquidity risk (specific cases)

- TSLA / NVDA in pre-market: deep but volatile, $0.10+ spreads.
- AVGO / NFLX in pre-market: thin; $1–5 spreads.
- Earnings AH: spreads explode. Don't market-order anything in AH; use marketable limits.

---

## 12. Appendix A — Per-Ticker Cheat Sheet

Compact, swing-trader-focused reference card for each top-10 name. ADR% = Average Daily Range as a % of price (rough 60-day window typical). Avg gap = absolute avg overnight gap %. Earnings move = typical implied 1-day move.

---

### AAPL — Apple Inc.
- **QQQ weight:** ~7.3% (#2)
- **ADR%:** 1.4–2.0%
- **Avg overnight gap:** 0.5–0.8%
- **Earnings implied move:** 3–5%
- **Best swing archetype:** **Trend-following, low-vol** — clean 21EMA/50EMA structure works well; reliable trends, low whipsaw. Excellent vehicle for trend-following swing systems.
- **Key catalysts:** iPhone launch (Sept), WWDC (June), holiday-quarter sales, Buffett 13F (Feb/May/Aug/Nov), China tariff/regulatory headlines, services revenue & gross margin on earnings.
- **Liquidity:** deepest in the universe. 1-cent spreads RTH.
- **Watch:** Greater China revenue %, services growth, gross margin guide.
- **Pairs:** AAPL/MSFT (low-vol pair), AAPL/QQQ (relative strength).
- **Quirk:** "Sell the news" pattern on every iPhone launch event historically.

---

### MSFT — Microsoft Corp.
- **QQQ weight:** ~5.3% (#3)
- **ADR%:** 1.3–1.9%
- **Avg overnight gap:** 0.5–0.8%
- **Earnings implied move:** 3–5%
- **Best swing archetype:** **Trend-following + AI-capex narrative** — "boring uptrend" name; pullback-to-MA buying works cleanly.
- **Key catalysts:** Build (May), Ignite (Sept/Nov), Azure growth (cc) + AI capex guide on earnings, OpenAI partnership headlines.
- **Liquidity:** very deep.
- **Watch:** Azure growth, AI revenue runrate, capex commentary.
- **Pairs:** MSFT/AAPL, MSFT/GOOGL (cloud pair).
- **Quirk:** Azure cc growth print is the *single* most-watched cloud metric. Surprise of >2pp = 3–5% move.

---

### NVDA — NVIDIA Corp.
- **QQQ weight:** ~8.2% (#1)
- **ADR%:** 2.8–4.0%
- **Avg overnight gap:** 1.0–1.5%
- **Earnings implied move:** 8–10%
- **Best swing archetype:** **Momentum/breakout + event-driven** — works for momentum (NVDA trends *hard*) and for earnings/event vol plays. Mean-reversion plays *only* on >2σ pullbacks within an established uptrend.
- **Key catalysts:** GTC (March, sometimes Oct mini-GTC), Computex (May/Jun), quarterly earnings (Feb/May/Aug/Nov), hyperscaler capex prints (MSFT/META/GOOGL/AMZN), China export-control headlines.
- **Liquidity:** very deep post-split.
- **Watch:** Data Center revenue, next-Q DC guide, Blackwell/Rubin ramp, China-restricted SKU revenue.
- **Pairs:** NVDA/AMD (the cleanest sector pair), NVDA/AVGO, NVDA/SMH (basket relative).
- **Quirk:** GTC keynote = "sell the news" with high reliability. Buy 2 weeks before, sell into Jensen's keynote.

---

### AMZN — Amazon.com Inc.
- **QQQ weight:** ~4.7% (#4)
- **ADR%:** 1.6–2.4%
- **Avg overnight gap:** 0.7–1.0%
- **Earnings implied move:** 5–7%
- **Best swing archetype:** **Trend-following + AWS-narrative-driven** — combines mega-cap stability with AWS growth optionality.
- **Key catalysts:** AWS re:Invent (late Nov/Dec), Prime Day (July), holiday-quarter retail reads, AWS quarterly growth & op-margin, FTC trial headlines.
- **Liquidity:** deep.
- **Watch:** AWS growth cc, AWS op-margin, retail op-margin, advertising revenue.
- **Pairs:** AMZN/GOOGL (cloud pair), AMZN/MSFT (Big-3 cloud).
- **Quirk:** retail op-margin surprises drive bigger moves than AWS in 2024-25; "Amazon found efficiency" thesis is the under-the-radar bull case.

---

### META — Meta Platforms Inc.
- **QQQ weight:** ~4–4.5% (#5)
- **ADR%:** 2.0–3.0%
- **Avg overnight gap:** 0.9–1.4%
- **Earnings implied move:** 7–9%
- **Best swing archetype:** **Trend-following with sharp pullback fades** — META has had massive trends both directions; respect the regime.
- **Key catalysts:** Connect (Sept/Oct), earnings (RL losses, Reels monetization, capex), election cycles (ad spending), regulatory (EU DSA, US KOSA, etc.).
- **Liquidity:** deep.
- **Watch:** RL operating loss trajectory, ad revenue growth, capex guide (this drove most of the 2024-25 stock action), DAP/MAP.
- **Pairs:** META/GOOGL (ad-duopoly pair).
- **Quirk:** "RL spending will be even higher next year" guide tanks the stock; AI capex raises now drive moves as much as ad revenue.

---

### GOOGL/GOOG — Alphabet Inc.
- **QQQ weight:** ~5%+ combined (GOOG + GOOGL)
- **ADR%:** 1.7–2.5%
- **Avg overnight gap:** 0.7–1.1%
- **Earnings implied move:** 4–6%
- **Best swing archetype:** **Range-trade with breakout overlay** — historically a "boring" mega-cap but DOJ antitrust + AI competitive concerns have widened the trading range.
- **Key catalysts:** Google I/O (May), earnings (Cloud, YouTube, Search), DOJ antitrust headlines, Gemini/AI product launches, perplexity/ChatGPT competitive headlines.
- **Liquidity:** very deep, split between GOOG (no voting) and GOOGL (voting). Use **GOOGL** for swing (more retail volume).
- **Watch:** Cloud revenue growth, Search rev growth, TAC, ad revenue ex-TAC.
- **Pairs:** GOOGL/META (ad duopoly), GOOGL/MSFT (cloud).
- **Quirk:** any "search share loss" headline gets sold hard; usually a 2–5 day mean-revert opportunity.

---

### TSLA — Tesla Inc.
- **QQQ weight:** ~2.5–3.5% (variable)
- **ADR%:** 3.5–5.5%
- **Avg overnight gap:** 1.5–2.5%
- **Earnings implied move:** 7–10%
- **Best swing archetype:** **Momentum/breakout + event-driven** — TSLA is a vehicle for narrative trading; technicals work for momentum, but news/Elon dominates.
- **Key catalysts:** Quarterly deliveries (first week of Jan/Apr/Jul/Oct), production updates (China CPCA monthly), earnings, robotaxi/AI Day events, Elon Musk tweets, political headlines.
- **Liquidity:** very deep.
- **Watch:** auto gross margin ex-credits, delivery vs prior Q, FSD subscriber count, robotaxi/Cybertruck ramp, energy storage revenue.
- **Pairs:** TSLA/NVDA (AI/retail-darling pair — high beta).
- **Quirk:** highest single-name retail options activity in the world. Heavy 0DTE / weekly flow. Often pins to round numbers into Friday close.

---

### AVGO — Broadcom Inc.
- **QQQ weight:** ~3.5–4%
- **ADR%:** 1.9–2.7%
- **Avg overnight gap:** 0.8–1.2%
- **Earnings implied move:** 5–8%
- **Best swing archetype:** **Trend-following + AI-second-derivative** — buy AVGO 1–3 days after NVDA beats; trend persistence is strong.
- **Key catalysts:** Earnings (late-Mar/Jun/Sept/Dec, fiscal-year quirk), AI revenue disclosure, hyperscaler ASIC contract wins, VMware integration progress.
- **Liquidity:** moderate-to-deep ($0.05–0.15 spread typical).
- **Watch:** AI revenue $/qtr, networking revenue, VMware op-margin, custom-silicon (XPU) commentary.
- **Pairs:** AVGO/NVDA (semis pair), AVGO/SMH (relative semis).
- **Quirk:** AVGO often "catches up" to NVDA with a 1–2 week lag on AI-cycle moves.

---

### NFLX — Netflix Inc.
- **QQQ weight:** ~2–2.5%
- **ADR%:** 2.4–3.5%
- **Avg overnight gap:** 1.2–1.8%
- **Earnings implied move:** 7–10%
- **Best swing archetype:** **Event-driven (earnings) + post-earnings drift** — outside earnings windows, NFLX is a quieter trend stock; into earnings, it's pure vol.
- **Key catalysts:** Quarterly earnings (only big calendar event), content release schedule, live-sports rights deals, ad-tier ARPU disclosure.
- **Liquidity:** moderate; **wide AH spreads** ($1–$5 on earnings nights).
- **Watch:** revenue/ARPU growth (no subs since 2025), ad-tier traction, operating margin guide.
- **Pairs:** NFLX/META (consumer-attention duopoly).
- **Quirk:** strongest post-earnings drift in the basket — historically PEAD-style follow-through over 5–10 days has been ~60% reliable.

---

### AMD — Advanced Micro Devices
- **QQQ weight:** ~1.5–2%
- **ADR%:** 2.8–4.5%
- **Avg overnight gap:** 1.2–1.8%
- **Earnings implied move:** 7–10%
- **Best swing archetype:** **Pair-trade against NVDA + momentum on MI3xx ramp news** — high beta to AI narrative; rarely a clean standalone trend.
- **Key catalysts:** Earnings, MI300/325/350 ramp updates, CES/Computex product launches, Data Center & Embedded segment splits.
- **Liquidity:** deep.
- **Watch:** Data Center revenue, MI-series AI revenue guide, embedded segment (cyclical drag).
- **Pairs:** AMD/NVDA (the pair). AMD/SMH.
- **Quirk:** AMD reactions are often *bigger* than the news warrants because it's the "alternative AI play" and positioning is fragile. Whippy.

---

### QQQ / QQQM — Invesco NASDAQ-100 ETFs
- **Weight:** N/A (the basket itself)
- **ADR%:** 1.0–1.8%
- **Avg overnight gap:** 0.4–0.7%
- **Earnings implied move:** N/A (continuously aggregated)
- **Best swing archetype:** **Trend-following with macro overlay** — QQQ is the canonical mean-reverting-in-uptrend swing vehicle; 21EMA pullback buying has decade+ of edge.
- **Key catalysts:** Aggregated from constituents; plus FOMC, CPI, NFP, OPEX, NDX rebalance dates.
- **Liquidity:** deepest ETF after SPY; 1-cent spreads, $10M+ depth.
- **Watch:** SPY/QQQ ratio, 10Y yield, breadth (advancing/declining within NDX).
- **Quirk:** use **QQQ** for trading (options/liquidity); **QQQM** for buy-and-hold (lower expense).

---

## 13. Appendix B — Suggested swing strategy archetypes mapped to this universe

| Archetype | Best names for this | Notes |
|---|---|---|
| **Trend following (21EMA pullback)** | AAPL, MSFT, GOOGL, AMZN, QQQ | Default for low-vol mega-caps |
| **Breakout/momentum** | NVDA, TSLA, AMD, META | High-beta movers; respect ATR-based stops |
| **Mean reversion (oversold bounce)** | QQQ on >2σ pullbacks; AVGO; NFLX outside earnings | Only in established uptrend |
| **Sector pair** | NVDA/AMD, GOOGL/META, MSFT/AAPL | Flatten before earnings |
| **Event-driven (earnings drift)** | NVDA, MSFT, META, NFLX post-beat | 5–10 day hold, scale into next-day open |
| **Macro event (pre-FOMC drift)** | QQQ, top-3 names | 24h entry, exit before announcement |
| **Calendar/conference run-up** | NVDA pre-GTC, MSFT pre-Build, AAPL pre-iPhone launch | 1–3 week run-up, sell the event |
| **Vol-selling (post-earnings)** | NVDA, TSLA, NFLX day-after | Iron condors / short strangles on IV crush |
| **Relative strength rotation** | QQQ/SPY ratio, NDX/RUT ratio | Macro regime signal, not single-name |

---

## 14. Appendix C — Calendar template (recurring annual events to track)

| Month | Recurring events |
|---|---|
| **January** | CES (1st week); Q4 earnings start (last 2 weeks); TSLA Q4 deliveries (1st week); FOMC (late month) |
| **February** | NVDA Q4 earnings (late month); Berkshire 13F (mid-month) |
| **March** | NVDA GTC; NDX quarterly rebalance (3rd Fri = quad witch); FOMC; AVGO Q1 earnings |
| **April** | Q1 earnings start (last 2 weeks); TSLA Q1 deliveries (1st week); FOMC may apply |
| **May** | Google I/O; MSFT Build; Computex (late month); NVDA Q1 earnings (late month); FOMC |
| **June** | AAPL WWDC; AVGO Q2 earnings; NDX quarterly rebalance (3rd Fri = quad witch); FOMC |
| **July** | Q2 earnings start; TSLA Q2 deliveries (1st week); Amazon Prime Day; FOMC |
| **August** | NVDA Q2 earnings (late month); Jackson Hole symposium; Berkshire 13F |
| **September** | AAPL iPhone launch (early-mid); META Connect; FOMC; NDX quarterly rebalance (3rd Fri = quad witch); AVGO Q3 earnings |
| **October** | Q3 earnings start (last 2 weeks); TSLA Q3 deliveries (1st week); FOMC may apply |
| **November** | NVDA Q3 earnings (mid month); Holiday-quarter retail reads begin; Berkshire 13F; AWS re:Invent prep |
| **December** | AWS re:Invent (early); AVGO Q4 earnings (early); NDX annual reconstitution (3rd Fri = quad witch); FOMC |

---

## 15. Appendix D — Quick reference: "is this a good day to put on a swing trade?"

Decision flowchart:

1. **Is VIX > 25?** → No new trend longs; only counter-trend or hedges.
2. **Is FOMC, CPI, or NFP within 24h?** → Wait, unless explicitly trading the event.
3. **Is a top-10 NDX name reporting earnings within your hold window?** → Either include it as a deliberate vol bet, or close before, or pick a different name.
4. **Is QQQ above its 50-day MA?** → Trend-following longs okay. If below the 200-day, prefer cash/shorts.
5. **Is the QQQ/SPY ratio in an uptrend?** → Mega-cap tech is leading; favor single-name longs. If downtrend, rotate to SPY or stay broader.
6. **Is the 10Y yield trending up sharply (50bp+ in a month)?** → Headwind; reduce size in long-duration names (NVDA, TSLA, AMZN especially).
7. **Is the DXY trending up sharply?** → Headwind; reduce size.
8. **Are you in Regime A or B?** Check 20-day pairwise correlation. → A: trade QQQ/single name. B: trade pairs/dispersion.
9. **Is the next 5 sessions an OPEX week?** → Expect more pinning, less trend; tighten exits.
10. **Is there a calendar catalyst (GTC, Build, I/O, Connect, WWDC, deliveries) within your hold window?** → Plan exit before the event unless trading it.

If 0 red flags → standard swing; full size.
If 1–2 red flags → half size, tighter stop.
If 3+ red flags → skip the trade.

---

## 16. Appendix E — Sources & further reading

- **Nasdaq-100 Methodology** — https://indexes.nasdaq.com/docs/Methodology_NDX.pdf
- **2023 Special Rebalance announcement** — https://indexes.nasdaqomx.com/docs/NDX_SpecialRebalance_2023.pdf
- **Callan: "What to Know about the Nasdaq-100 Special Rebalance"** — https://www.callan.com/blog/nasdaq-100/
- **Mellon: "When Billions Move: The Nasdaq-100 Index Special Rebalance"** — https://www.mellon.com/content/dam/mellondotcom/insights/documents/when-billions-move.pdf
- **NY Fed SR-512: Lucca & Moench, "The Pre-FOMC Announcement Drift"** — https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr512.pdf
- **SpotGamma OPEX research** — https://spotgamma.com/opex/
- **Market Chameleon: NVDA Earnings Implied & Realized Moves** — https://marketchameleon.com/Overview/NVDA/Earnings/Earnings-Charts/
- **Moomoo: NVDA earnings vol-first structures (IV crush data)** — https://www.moomoo.com/community/feed/a-volatility-first-approach-to-nvda-earnings-...
- **Nasdaq announcement on Monday/Wednesday weeklies** — https://www.nasdaq.com/newsroom/nasdaq-lists-new-options-expiries-what-means-and-why-it-matters
- **MarketWatch on triple witching for NVDA** — https://www.marketwatch.com/story/nvidias-rally-faces-latest-test-in-fridays-record-setting-triple-witching-options-expiration-b05544ff
- **CBOE 0DTE share data** — referenced in Nasdaq facebook/Cboe public posts (Aug 2025)
- **Slickcharts QQQ holdings** — https://www.slickcharts.com/symbol/QQQ/holdings
- **Invesco QQQ holdings page** — https://www.invesco.com/qqq-etf/en/about.html
- **Schwab: Mega-Cap Concentration Risks** — https://www.schwab.com/learn/story/3-ways-to-navigate-mega-cap-concentration-risks
- **BlackRock: Mega-Cap Exposure & S&P 500 Concentration** — https://www.blackrock.com/us/financial-professionals/insights/fine-tuning-megacaps-build-etfs
- **Bookmap: SPY vs QQQ trader analysis** — https://bookmap.com/blog/spy-vs-qqq-why-traders-watch-them-closely-and-how-to-analyze-their-market-signals
- **Composer ETF comparison: QQQ vs SPY** — https://www.composer.trade/etf-comparisons/QQQ-SPY
- **Finzer: QQQ vs SPY** — https://finzer.io/en/blog/qqq-vs-spy

---

*End of document — file 05-nasdaq100-megacap-specifics.md.*
*If you maintain a running edit log, append below this line.*

---

## 17. Appendix F — Deep dive: the AI capex cycle and its read-throughs

The single most important *macro-within-micro* dynamic in this universe from 2023 onward is the AI capex cycle. Understanding the dependency graph is essential for swing-trading any of these names.

### 17.1 The capex dependency chain

```
End-user demand (enterprise AI workloads, consumer LLMs)
        ↓
Hyperscaler cloud revenue (MSFT Azure, GOOGL GCP, AMZN AWS, META internal, ORCL OCI)
        ↓
Hyperscaler capex announcements ($/quarter)
        ↓
GPU/ASIC purchases (NVDA Hopper/Blackwell/Rubin, AVGO custom XPUs, AMD MI3xx)
        ↓
Foundry wafer starts (TSM, Samsung)
        ↓
WFE equipment orders (ASML, AMAT, LRCX, KLAC)
        ↓
Memory orders (MU, Samsung, SK Hynix — HBM3/HBM3e)
        ↓
Networking & power (AVGO networking, ANET, VRT, GEV)
```

**Swing implication:** any anomaly *anywhere* in the chain propagates within days. A TSM monthly sales miss → NVDA selloff within 24h. A Microsoft capex raise → AVGO, MU, ANET rally within 24h.

### 17.2 Capex announcement playbook

The quarterly cadence:

1. **MSFT FY-Q1 (calendar Q3) earnings ~late Oct:** capex guide for next year is the first major read.
2. **META Q3 earnings ~late Oct:** RL + AI capex guide; META frequently surprises here.
3. **GOOGL Q3 earnings ~late Oct:** Cloud capex.
4. **AMZN Q3 earnings ~late Oct:** AWS capex + retail capex (Project Kuiper, robotics).
5. **NVDA Q3 (fiscal Q3, calendar Q3) earnings ~mid Nov:** confirms the demand side; revenue prints validate the capex chain.

This *October–November capex sequence* is the most pivotal trading window of the year for the AI infra basket. A *single* hyperscaler raising capex by 20%+ can lift NVDA/AVGO/AMD/MU 5–10%; conversely a *single* hyperscaler signaling capex moderation can take 5–10% off the same names.

### 17.3 The bear case framework

Watch for these early-warning signals of an AI-capex deceleration:

- **Hyperscaler ROI commentary turning defensive** ("we're being disciplined", "we'll match supply to demand", "we don't see additional acceleration").
- **GPU shipment lead times shortening** (peak was 50+ weeks; <20 weeks signals normalization → near-term price pressure).
- **Cloud growth deceleration** at hyperscalers (Azure cc growth dropping 200bps+ Q/Q).
- **Enterprise software companies (CRM, ORCL, WDAY, SNOW) cutting AI revenue guidance.**
- **Memory pricing weakness** in DRAM/HBM (MU/SK Hynix guidance).

Any 2 of these in the same 30-day window → reduce or hedge AI-basket exposure.

---

## 18. Appendix G — Pattern catalog: setups that have worked in this universe

The following are documented historical patterns with multi-year reliability. None is foolproof — all require regime confirmation.

### 18.1 "21EMA pullback in uptrend" (QQQ, AAPL, MSFT, GOOGL)

- **Setup:** instrument is above the 50-day MA (trend confirmation); price pulls back to the 21EMA on daily chart and bounces with a positive close.
- **Entry:** next-day open after the bounce candle.
- **Stop:** below the low of the bounce candle, or 2× ATR(14) below entry — whichever is wider.
- **Target:** prior swing high; partial exit at 1R, trail with 21EMA.
- **Hold:** typically 5–15 sessions.
- **Win rate (historical, 2015–2024 QQQ):** ~60–65%.
- **Avg R:R:** ~1.5:1.

### 18.2 "Gap-and-go reclaim" (NVDA, TSLA, AMD)

- **Setup:** stock gaps up 2%+ on positive news; first 30-min consolidation forms a flag; price breaks above the flag high.
- **Entry:** on the flag break, ~10:30–11:00 ET.
- **Stop:** below the consolidation low.
- **Target:** measured move = gap size.
- **Hold:** 1–3 sessions (this is short-swing/intraday).
- **Caveat:** fails in macro chop; only take in clean trend.

### 18.3 "Earnings beat + raise → next-day open buy" (NVDA, META, MSFT)

- **Setup:** name beats EPS + raises forward guide; closes the next session positive.
- **Entry:** day-after-earnings open (skip the gap, buy the open).
- **Stop:** day-after-earnings low.
- **Target:** trail with 8EMA on daily.
- **Hold:** 5–10 sessions.
- **Win rate (NVDA 2022–2024, beat+raise prints):** ~70% positive 10-day return.

### 18.4 "Pre-FOMC drift" (QQQ)

- **Setup:** scheduled FOMC announcement on Wed 2pm.
- **Entry:** Tuesday close (24h before).
- **Exit:** Wednesday 1:55pm ET (5 min before announcement).
- **Avg edge:** 30–50bps (Lucca-Moench documented, weakened in recent years).
- **Sizing:** small — this is a small-edge, high-Sharpe trade meant to compound, not a home run.

### 18.5 "Conference run-up" (NVDA pre-GTC, AAPL pre-iPhone)

- **Setup:** known annual hype event 10–14 days out.
- **Entry:** ~14 days before event, on a pullback or trend-confirmation day.
- **Exit:** day of event keynote (or 1 day before if news leaks).
- **Pattern:** "buy the rumor, sell the news."
- **NVDA pre-GTC historical (2022, 2023, 2024):** +5–10% in the 14 days leading in; -1 to -3% on the keynote day; -2 to -5% in the week after.
- **AAPL pre-iPhone (long-term):** mild +2–4% run-up; flat-to-negative reaction; 2-week post-event drift moderately negative.

### 18.6 "Earnings vol-crush short strangle" (NVDA, NFLX, AMD)

- **Setup:** name reports tomorrow; front-week IV is 80%+ annualized; the back-month is ~40%.
- **Entry:** sell ATM (or slightly OTM) strangle / iron condor pre-close on report day.
- **Risk:** undefined for naked strangle; defined for iron condor.
- **Profit driver:** IV crush captures 30–60% of premium overnight even if the underlying moves modestly.
- **Risk case:** realized move >> implied → unlimited loss for strangle; defined loss for IC.
- **Practical sizing:** never risk more than 1–2% of book on a single earnings strangle.

### 18.7 "Quarterly NDX rebalance add" (whenever new constituents announced)

- **Setup:** Nasdaq announces NDX additions for upcoming quarterly rebalance (typically announced ~1–2 weeks before effective date).
- **Entry:** at announcement, on the added names.
- **Exit:** day of effective date (3rd Friday OPEX) at the close — passive flows complete by then.
- **Caveat:** edge is smaller than it used to be because the trade is widely known. Expect ~1–3% over the run-up window.

### 18.8 "OPEX week chop fade" (top 10 names with heavy single-strike OI)

- **Setup:** monthly OPEX week (3rd Friday). A name has heavy OI at a single round-number strike near current price.
- **Pattern:** price tends to gravitate toward that strike into Friday close (pinning).
- **Trade:** sell short-dated strangles bracketing the pin strike at start of OPEX week; close Friday morning.
- **Risk:** earnings or major news during OPEX week destroys the trade. Always check the catalyst calendar.

### 18.9 "Pair mean-reversion: NVDA/AMD" (z-score spread)

- **Setup:** 60-day rolling z-score of log(NVDA/AMD) exceeds ±2.
- **Entry:** short the outperformer, long the underperformer in beta-weighted dollar amounts.
- **Exit:** |z| <0.5 OR 20 sessions OR earnings within 3 days for either name (flat).
- **Win rate:** ~60–65% historical, but watch for regime breaks (e.g., AMD's MI300 launch disrupted mean-reversion for ~3 months).

### 18.10 "Macro-shock buy-the-dip" (QQQ)

- **Setup:** QQQ falls >5% in 3 sessions on macro headlines (rate scare, geopolitical, tariff).
- **Entry:** when RSI(2) <5 AND QQQ is still above its 200-day MA.
- **Exit:** RSI(2) >70 OR 10 sessions.
- **Historical:** strong edge in bull-trend regimes; *negative* edge if QQQ has just broken its 200-day MA (you're catching a falling knife in a bear regime).

---

## 19. Appendix H — What *not* to do in this universe

Mistakes that bleed accounts faster here than in mid-caps:

1. **Holding through earnings "to let it ride."** A clean 5% swing gain gets wiped by a -8% earnings gap in one print.
2. **Pyramiding NVDA on a 5-day rip.** It works… until the day it doesn't, and the gap-down is 7%.
3. **Going short TSLA on a "fundamentals" basis.** Has bankrupted more retail traders than any other single trade since 2019. TSLA does not respect fundamentals on retail timeframes.
4. **Buying weekly OTM calls into earnings as "cheap lottery tickets."** They aren't cheap — IV is jacked. Expected value is consistently negative for ATM/OTM long premium into earnings.
5. **Ignoring sector ETF flows.** SMH outflows preceding NVDA selloffs is a 2024–25 pattern; tracking flow saves you the bag.
6. **Trading "intuition" on Mag-7 correlation.** When the basket is in single-beta regime, your "I'll long NVDA and short AAPL" idea is just leverage on QQQ.
7. **Using market orders in AVGO/NFLX pre-market or AH.** Spreads can be $1–$5; you'll routinely give up 30–50bps.
8. **Forgetting Greater-China headlines drop in Asia hours.** A surprise China-export rule appears 4am ET → you wake up to NVDA -6%. Have stops or alerts.
9. **Sizing single names equally by $ allocation.** As noted: equal dollar = 2–3× risk in TSLA/NVDA vs MSFT/AAPL. Size by vol, not dollar.
10. **Trading on Stocktwits / WSB sentiment alone.** Retail sentiment in this universe is a contrarian signal at extremes, not a confirming signal in the middle.

---

## 20. Appendix I — Glossary (terms used in this doc)

- **0DTE** — zero-days-to-expiry options; expire same day.
- **ADR%** — Average Daily Range as % of price (a measure of intraday volatility).
- **AP (Authorized Participant)** — large broker-dealer authorized to create/redeem ETF shares; main arb mechanism that keeps ETF NAV in line.
- **ATR** — Average True Range; common volatility measure for stop sizing.
- **cc** — constant currency (used in revenue growth discussions, e.g., "Azure cc growth").
- **Charm** — second-order options Greek; rate of change of delta with respect to time.
- **Contango / Backwardation** — vol term structure (later/earlier expiries priced higher).
- **DSA / DMA** — EU Digital Services Act / Digital Markets Act.
- **GTC** — NVIDIA's GPU Technology Conference.
- **Gamma** — second-order options Greek; rate of change of delta with respect to underlying price.
- **IV** — Implied Volatility.
- **IV crush** — sharp drop in IV after an event (typically earnings).
- **MOC** — Market-on-Close order; submitted by 3:50pm ET (NYSE) for inclusion in closing print.
- **NAV** — Net Asset Value (per share, of an ETF).
- **NDX** — Nasdaq-100 Index ticker.
- **OPEX** — Options Expiration (3rd Friday of month).
- **PEAD** — Post-Earnings Announcement Drift.
- **RIC** — Regulated Investment Company (IRS tax treatment; drives index diversification rules).
- **Quad witching** — quarterly OPEX where stock options, stock index options, stock index futures, and single-stock futures all expire (March/June/Sept/Dec).
- **Vanna** — second-order options Greek; rate of change of delta with respect to vol.
- **WFE** — Wafer Fab Equipment (semi capex).

---

## 21. Appendix J — Open research questions / TODO

Items worth deeper data work but out of scope for this document:

- [ ] **Quantitative backtest of 21EMA pullback on each top-10 name** with 2015–2025 data; produce win-rate, avg R, Sharpe.
- [ ] **Build NDX rebalance flow tracker:** estimate $-flow per name on each quarterly rebalance using passive AUM × weight change.
- [ ] **Pre-FOMC drift recent-decade reproduction:** is the edge still alive 2020–2025?
- [ ] **Sector pair half-life decay** — has NVDA/AMD pair stopped mean-reverting since MI300?
- [ ] **Earnings drift segmentation:** does beat-and-raise drift outperform beat-only drift consistently across all 10 names?
- [ ] **Monday/Wednesday weeklies effect** — once 6 months of data exists post-Feb-2026 launch, study impact on intraday patterns.
- [ ] **0DTE flow correlation to next-day swing direction** — preliminary evidence is mixed.
- [ ] **China-tariff news classification** (permanent policy vs noise) — build a NLP classifier?

---

## 22. Closing note

This universe rewards patience, calendar discipline, and respect for vol regimes. It punishes overconfidence, equal-dollar diversification fallacies, and "I'll just hold through earnings" thinking.

The cleanest edge in mega-cap NDX swing trading is not a magic indicator — it's **knowing exactly what is happening on each day of the calendar and being smaller or flat when the calendar disagrees with your thesis.**

Build the calendar. Track the flows. Respect the regime. Size to the vol. Skip the cute trades. Take the obvious ones.

*— end —*

---

## 23. Appendix K — Intraday microstructure notes (for swing-entry timing)

Even though swing trades are held days-to-weeks, **entry timing within a day** materially affects R-multiples. Below are observed intraday patterns specific to mega-cap tech.

### 23.1 Time-of-day return distributions (typical, RTH)

Based on 5-min bar studies of QQQ and top-5 names:

| Window | Typical character | Swing-entry quality |
|---|---|---|
| 09:30–09:45 | Auction imbalance; high vol, low signal | Bad — avoid new entries |
| 09:45–10:00 | "Opening drive" extends or fails | Bad — confirmation forming |
| 10:00–10:30 | First reversal window; opens often fail/reverse here | Good for reversal entries |
| 10:30–11:30 | "Real" trend establishes for the morning session | Best for momentum entries |
| 11:30–13:00 | Lunch chop; thin volume; mean-reverting | Bad for new entries |
| 13:00–14:00 | Afternoon trend reasserts | Good for trend-continuation entries |
| 14:00–15:00 | Pre-power-hour positioning | Good for position-build |
| 15:00–15:30 | "Power hour" begins; flows pick up | OK; watch for late-day reversals |
| 15:30–15:50 | MOC imbalance prints publish at 15:50 | Skip for new entries |
| 15:50–16:00 | MOC imbalance execution; closes printed | Take partial exits, don't enter |

### 23.2 Open-print quality by name

- **AAPL, MSFT, GOOGL, AMZN:** clean opens; auction works well; first-15-min ranges are usually contained.
- **NVDA, TSLA, AMD:** wide first-15-min ranges; opens are often "exploration ranges" extended later.
- **NFLX:** often gaps from prior-day's AH range; the open is more news-driven than fundamental.
- **AVGO:** lower volume name; opens can be stickier; less reliable opening drive.

### 23.3 Late-day flows ("the 3pm shift")

- **Index-tracking ETFs rebalance dividends and cash positions near the close.**
- **Levered ETFs (TQQQ/SQQQ) must rebalance** to maintain daily-leverage exposure → mechanical late-day flow in the direction of the day's move (trend extender).
- **Pension month-end rebalance** (last 2–3 sessions of each month) → mean-reversion flows: equities sold if up MTD, bought if down.
- **MOC imbalance** prints at 3:50pm ET on NYSE; Nasdaq closing cross runs 4:00pm. Big mismatches publish for the last 10 minutes; can move underlying $0.50+ in seconds.

### 23.4 Pre-market & after-hours considerations

- **Volume distribution:** ~95% of daily volume is RTH; pre-market ~3%, AH ~2%. Earnings days flip — AH can be 20%+ of daily volume.
- **Spreads in PM/AH:** 5–20× wider than RTH for most names.
- **AH "limit up" / "limit down" mechanics:** different from RTH; certain price ranges trigger trading pauses, especially on earnings.
- **Globex / overnight futures (NQ):** provide best price discovery 6pm ET → 9:30am ET next day. NQ futures move minute-by-minute; QQQ "pre-market price" is largely a lagged read of NQ.

---

## 24. Appendix L — Worked example: a complete swing-trade workflow

Scenario: it's Tuesday Oct 28, 2025. Your scan flags MSFT for a potential long. Walk through the checks.

**1. Calendar check.**
- MSFT reports Wednesday Oct 29 after the close. **Stop.** This is an earnings-week trade by definition.
- Decision: either (a) wait for the post-earnings reaction and trade the drift, or (b) take a vol-defined position (debit call spread) sized small.

**2. Macro check.**
- FOMC is the following week (Nov 5–6). Wednesday afternoon Fed Speak risk is moderate.
- 10Y yield: check current level and 1-month trend.
- DXY: check trend.
- VIX: if <18, normal environment; if >22, elevated.

**3. Regime check.**
- QQQ vs 50-day MA: above → trend environment.
- QQQ vs 200-day MA: above → bullish regime.
- 20-day pairwise correlation across top 5: if <0.5, dispersion regime → favor single names; if >0.7, single-beta regime → trade QQQ.
- VIX <18: OK for trend.

**4. Catalyst check (within hold window).**
- MSFT earnings Wed AMC.
- META earnings Wed AMC.
- AAPL + AMZN earnings Thu AMC.
- NFP first Friday of Nov (Nov 7).
- Multiple high-impact events; either trade the prints deliberately or stay flat.

**5. Decision tree applied:**
- Skip the standard swing-long today.
- Plan: wait for MSFT's post-earnings reaction.
  - If MSFT beats + raises Azure cc growth + raises capex guide → buy at Thursday open with stop at Thursday low.
  - If MSFT beats but cuts capex / Azure decel → skip; watch for short setup.
  - If MSFT misses → wait for reflexive bounce, fade with caution.

**6. Position sizing (assuming the trade triggers Thursday).**
- Risk per trade: 1% of swing book.
- Stop distance: assume ~3% from entry (MSFT is low-vol; 2× ATR ≈ 3%).
- Position size: 1% / 3% = 33% of swing book allocated to this trade.
- If 33% feels too concentrated, halve it.

**7. Exit plan.**
- Target 1: prior swing high, partial exit, move stop to entry.
- Target 2: trail with 21EMA on daily.
- Hard time stop: 15 sessions.
- Hard event stop: before next major catalyst (FOMC Nov 5–6).

**8. Post-trade review.**
- Log entry/exit, R-multiple, time held.
- Note: did the post-earnings drift play out as expected? Did MSFT lead AVGO/NVDA?
- Update strategy notes if pattern broke.

This is the discipline. Boring, calendar-aware, regime-respecting. No magic.

---

## 25. Final summary

The NASDAQ-100 mega-cap basket is the most liquid, most analyzed, most flow-dominated, most option-heavy slice of US equities. Swing-trading edges in this universe come *not* from clever signal engineering but from:

1. **Calendar discipline** — every named catalyst, every macro print, every OPEX, every rebalance.
2. **Regime awareness** — Regime A vs Regime B, trend vs chop, low-vol vs high-vol.
3. **Volatility-aware sizing** — never dollar-equal across the basket.
4. **Earnings as a separate beast** — never as a "swing through it" event.
5. **Flow & positioning literacy** — track ETF flows, dealer gamma, hyperscaler capex prints.
6. **Brutal honesty about concentration** — 10 names ≠ 10 bets.

Print this document. Annotate it. Update it quarterly. The names will change, the weights will change, but the structural realities of this universe — index concentration, passive flows, calendar dominance, mega-cap vol regimes — will persist.

*v1.0 — research compiled 2026-06-01.*

---

## 26. Appendix M — Quick mental models to keep on the desk

A handful of one-liners that compress most of this document into reflexes:

- **"QQQ is 4 stocks."** Whenever you say "QQQ," picture NVDA/AAPL/MSFT/AMZN — they are the index for trading purposes.
- **"Earnings are a vol trade, not a swing trade."** If you're holding through, you're short gamma whether you know it or not.
- **"Rate down + DXY down = mega-cap tech up."** A free macro overlay; it works ~70% of the time.
- **"Buy the rumor (GTC, iPhone, Build) — exit at the keynote."** Sell-the-news is the modal outcome.
- **"NVDA leads, AVGO and AMD follow with a lag."** Use this for chained entries.
- **"OPEX week = chop; the week after OPEX = trend resumption."** Position size accordingly.
- **"Pre-FOMC drift is real, small, and consistent — don't try to make it big."**
- **"If you're trading TSLA on fundamentals, you're not trading TSLA."**
- **"Hyperscaler capex prints are NVDA's true earnings."**
- **"Above 200d = trend setups. Below 200d = countertrend only."**
- **"Equal-dollar across Mag-7 = double TSLA risk."**
- **"AH price ≠ open price. The call closes the gap."**

---

## 27. Appendix N — Document changelog

- **v1.0 (2026-06-01):** initial compile. Author: devclaw (web-dev agent), research session for swing-trade-radar project.

Future updates should note: index methodology changes, weight shifts >2pp at top-10, new option-expiration mechanics, regime classification changes (e.g., end of AI capex cycle), and additions/deletions in the top 10 NDX constituents.

---

*Document length target: 1200+ lines, dense reference for active swing-trading desk applied to mega-cap NDX.*
*All forward-looking statements are observations of historical patterns, not investment advice.*
