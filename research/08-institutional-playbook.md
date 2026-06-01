# 08 — Institutional Playbook: Swing-Trading Mega-Cap US Tech

*Perspective: a multi-strat pod portfolio manager (PM) at a Citadel / Millennium /
Point72 / ExodusPoint-style platform, translated for a $25k–$250k retail trader.*

> **Read this as a hedge-fund-PM monologue, not a textbook.** The point is to
> show how a tactical mega-cap tech book is *actually constructed* inside a
> platform fund — signals, sizing, risk plumbing, infrastructure — and then to
> distill the parts a single human with a brokerage account can realistically
> reproduce.
>
> **Citations** are inline. Where I cite "platform fund convention" without a
> URL, that is well-documented industry knowledge (LCH Investments rankings,
> CNBC / Bloomberg / FT reporting on Millennium / Citadel, Institutional
> Investor profiles, and ex-PM accounts on Substack/Twitter). Specific
> headline numbers (AUM, PM count) are sourced to Wikipedia where given.
>
> **Universe in scope:** AAPL, MSFT, NVDA, GOOGL, META, AMZN, AVGO, TSLA,
> AMD, NFLX, ORCL, CRM, ADBE, QCOM, INTC, plus the obvious ETF wrappers
> (QQQ, XLK, SMH, SOXX, IGV, MTUM, QUAL, USMV).
>
> **Horizon in scope:** 2 days to 6 weeks. Anything shorter is intraday /
> HFT (different game). Anything longer is "investment", not swing.

---

## Table of contents

1.  Pod-shop swing horizons: how Citadel GE, Millennium, Point72, ExodusPoint actually run tactical mega-cap tech books
2.  Sell-side research as input — upgrades/downgrades, target-price revisions, IBES estimate momentum, StarMine
3.  Cross-asset signals — rates, DXY, oil/copper, SMH→QQQ, KRE, credit spreads
4.  Pairs & stat-arb at the mega-cap level — Engle-Granger, Johansen, Kalman, NVDA/AMD, GOOGL/META, MSFT vs eqw-QQQ
5.  Vol targeting and risk-parity overlays — sizing to a 12–15% vol target, Black-Litterman for swing tilts
6.  Options as a swing instrument — verticals, calendars, diagonals, tastytrade short-premium evidence, defined-risk only
7.  Smart-beta lessons — MTUM, QUAL, USMV construction and the rebalance/index-effect inefficiency
8.  Derivatives data — SKEW, VIX/VIX3M term structure, single-stock skew, dealer positioning (SqueezeMetrics, SpotGamma)
9.  Multi-sleeve book construction — trend + mean-reversion + event-driven + vol-arb as uncorrelated sleeves
10. Public-quant lessons — Thorp, Renaissance (what's public), AQR / Asness factor papers, López de Prado
11. **Retail-adapted institutional checklist** ($25k–$250k single trader)

---

## 1. Pod-shop swing horizons — how the platforms actually run tactical mega-cap tech books

### 1.1 The platform model in one paragraph

A "platform" or "pod-shop" hedge fund — Citadel (Global Equities — "GE"),
Millennium Management (MLP), Point72, ExodusPoint, Balyasny (BAM),
Schonfeld, Walleye — runs *hundreds* of semi-autonomous portfolio-manager
teams ("pods"). Each pod gets a capital allocation, a market-neutral or
beta-neutral mandate, a hard volatility budget, and a brutal drawdown
stop-out. The firm captures the alpha; the PM captures a slice of P&L
(typically 15–25% of pod net P&L after costs). Millennium publicly
describes itself as a "platform model" with ~280 investment teams as of
2020, $87B AUM as of 2026, and a stated risk culture built on tight
PM-level loss limits (Wikipedia, *Millennium Management, LLC*; FT, II,
Bloomberg reporting). Citadel has ~$67B AUM as of Jan 2026 (Bloomberg via
Wikipedia, *Citadel LLC*), with Global Equities as one of five major
businesses (Equities, Fixed Income & Macro, Commodities, Credit,
Quantitative Strategies).

### 1.2 The drawdown stop-out — the single most important fact

The defining feature of pod-shop life is *the stop*. Industry reporting
(FT, Bloomberg, II) and ex-PM Substacks converge on roughly the same
numbers, which have been stable for a decade:

| Firm        | Soft DD (de-risk)     | Hard DD (close pod)   | Notes                          |
| ----------- | --------------------- | --------------------- | ------------------------------ |
| Millennium  | ~5% peak-to-trough    | ~7.5–10%              | Halves at -5%, fired at -7.5%  |
| Citadel GE  | ~5%                   | ~7.5–10%              | Similar to MLP                 |
| Point72     | ~5% (drop a level)    | ~8%                   | More tolerant on idiosyncratic |
| ExodusPoint | ~5%                   | ~8%                   | Macro-fixed-income heritage    |
| BAM         | ~5%                   | ~7%                   | Famous "BAM-rate" turnover     |

**The implication is enormous.** A PM running $500M GMV on a 12% vol
target who hits -5% has lost $25M; capital is halved to $250M; they now
must dig out to high-watermark on half the capital. At -7.5–10% they are
flat. *Survival is the strategy.* Everything below — signal selection,
sizing, hedging — is downstream of "don't get stopped".

### 1.3 What a mega-cap tech pod actually trades

Inside Citadel GE / MLP / Point72, a tactical mega-cap tech pod typically
runs a book that looks like this:

-   **Gross**: 400–800% of NAV (so a $200M-NAV pod might run $1.2B gross).
-   **Net**: ±10% to ±25% beta-adjusted (sector-hedged, often factor-
    neutral too).
-   **Position count**: 30–80 single names (long and short), plus an ETF
    hedge sleeve (SPY/QQQ/SMH).
-   **Single-name limit**: usually capped at 1.5–3% of NAV gross, 50–100
    bps net.
-   **Sector limit**: 15–20% net to any GICS sub-industry.
-   **Factor neutrality**: Barra / Axioma / MSCI risk model with hard
    caps (size, momentum, value, growth, volatility, beta) at ±0.5–1.0
    factor-Z relative to benchmark.
-   **Liquidity**: must be able to exit any position in ≤3 trading days
    at ≤10% of ADV (average daily volume).

That is the *cage* a pod lives in. Inside that cage, the swing-trader
runs catalyst-driven and signal-driven trades on the names where they
have an edge.

### 1.4 Signal types a tech-pod PM actually uses

A real mega-cap tech pod blends four to six signal families. None of
them is "I drew a trendline":

1.  **Fundamental / catalyst-driven** — earnings, capex prints,
    guidance, AI/cloud spend datapoints, hyperscaler capex, FX
    translation, regulatory (DOJ/FTC/EU DMA), supply-chain (TSMC,
    SK Hynix, ASML). The pod has a research analyst who builds quarterly
    models (segment-level revenue, OpEx, GM) and triangulates with
    alternative data (Yipit credit-card, Sensor Tower, Similarweb,
    Bloomberg second-measure, M-Science).
2.  **Estimate-revision momentum** — long stocks where consensus EPS
    revisions are accelerating up; short where accelerating down. See
    section 2 — this is the strongest single-name alpha factor that has
    survived 30 years.
3.  **Cross-asset macro overlay** — net exposure is dialled by rates,
    USD, credit. See section 3.
4.  **Pairs / dispersion** — NVDA/AMD, GOOGL/META, MSFT vs eqw-QQQ,
    AAPL vs hardware-basket. See section 4.
5.  **Event-driven** — earnings drift (PEAD), index rebalances (S&P,
    Nasdaq-100, MSCI), index-effect trades (section 7), buyback
    announcement drift.
6.  **Vol-arb / dispersion** — single-stock vs index implied-vol
    dislocations (section 8). Most equity L/S pods *don't* trade this
    directly — they hand it to a vol-arb pod — but the swing PM uses
    skew / term structure as a *signal* for directional sizing.

### 1.5 Holding periods inside a pod

Despite the "high-frequency hedge fund" cliché, a fundamental mega-cap
tech pod's *median holding period* is roughly:

-   **Core fundamental L/S**: 3–8 weeks.
-   **Catalyst trades (earnings, product launch)**: 2–15 trading days.
-   **Pairs / stat-arb (mid-frequency)**: 3–20 trading days.
-   **Event trades (index rebal, buyback)**: 1–10 days.

Citadel/Millennium's *systematic* (quant) pods turn much faster (intraday
to ~5 days). The fundamental pods don't. **"Swing trading" in pod-shop
language = the 3–30 day bucket.** That is the horizon this entire
document is about.

### 1.6 Sizing math the platform actually enforces

Risk is allocated by *volatility contribution*, not dollar notional. The
canonical formula for a single position's vol contribution is:

```
σ_i_contrib  =  w_i * (Σ * w)_i  /  σ_p
```

where `w` is the weight vector, `Σ` is the covariance matrix (Barra
factor + idio), and `σ_p` is portfolio vol. The PM is given a daily
report by risk that shows:

-   Marginal contribution to risk (MCR) per name
-   Factor exposures (beta, size, momentum, value, growth, vol, liquidity)
-   Country and sector exposures
-   Top-10 contributors to gross vol
-   1-day 99% VaR, expected shortfall, stress P&L (2008, 2020-Covid,
    2022-rates, Aug-2024 yen-carry unwind)
-   Crowded-name scores (HF ownership, short-interest, FactSet
    SharkRepellent, etc.)

The PM cannot exceed any limit overnight. *Risk has a kill switch.*
Goldman, MS, JPM and prime-broker risk overlay sit on top. This is the
infrastructure a retail trader cannot replicate but *can mimic in
spirit* — see section 11.

---

## 2. Sell-side research as input — upgrades, downgrades, IBES revisions, StarMine

### 2.1 Why the sell-side still matters in 2026

The pop on a Morgan Stanley upgrade of NVDA at 8:01 a.m. ET is not
"retail buying the news". It is:

1.  Index funds and risk-parity books with mandates that key off
    consensus targets.
2.  Long-only mutual funds whose PMs need analyst air-cover to bump
    a position.
3.  Quant funds whose *analyst-revision factor* is now long that name.
4.  HFs whose risk model just flipped a tilt.
5.  Last and least: discretionary retail.

The pop is real even when the analyst is wrong, because the *flow* it
unlocks is real. The PM who fades it without understanding *why* it
moved gets carried out.

### 2.2 The analyst-revision factor (the actual academic alpha)

The "analyst revisions" factor is one of the most robust, oldest, and
still-working anomalies in equity finance:

-   **Givoly & Lakonishok (1979, JAE)** — first formal documentation
    that consensus EPS revisions predict subsequent returns.
-   **Stickel (1991, JoF)** — magnitude and timing of revisions
    matter; "all-star" analysts have larger impact.
-   **Chan, Jegadeesh & Lakonishok (1996, JoF)** — combining price
    momentum with earnings momentum (revisions + post-earnings drift)
    produces a stronger anomaly than either alone.
-   **Womack (1996, JoF)** — buy recommendations produce ~3% 3-day
    return; sell recommendations produce ~-4.7% with continued drift up
    to 6 months.
-   **Jegadeesh, Kim, Krische & Lee (2004, JoF)** — analyst
    recommendation *changes* (Δ) predict returns; *levels* don't.
-   **AQR / Asness, Frazzini, Pedersen (various)** — "earnings
    momentum" is a robust component of the QMJ ("Quality Minus Junk")
    and momentum factors.

**Translation for the swing PM:** the durable signal is the *change*
in consensus, not the level. A stock at consensus "Buy" with 28 of 35
analysts already Buy and the target up 2% in three months is *not* a
signal. A stock that went from "Hold" to "Buy" with three target hikes
this week and FY+1 EPS revised +4% over 30 days *is* a signal.

### 2.3 Refinitiv I/B/E/S and StarMine

I/B/E/S (Institutional Brokers' Estimate System), now part of Refinitiv,
is the consensus-estimate utility. Every fundamental pod pays for it
($50k–$250k/year per seat range). The core fields a pod consumes:

-   Mean, median, hi, lo EPS for FY0, FY1, FY2, Q1–Q4.
-   *Number of estimates* (depth of consensus — wider = noisier).
-   *Standard deviation of estimates* (analyst dispersion — proxy for
    uncertainty).
-   Revisions over 7d / 30d / 90d (count of up vs down + % magnitude).
-   Recommendation distribution and mean.
-   Target-price mean, median, hi, lo + revisions.

**StarMine** (also Refinitiv) is a layer on top. The key model is the
**SmartEstimate**: a weighted consensus that overweights analysts who
have been historically accurate and recently updated. The
**Predicted Surprise** = (SmartEstimate − Mean Consensus) /
|Mean Consensus|. StarMine's own backtests show:

-   Stocks with **Predicted Surprise > +2%** beat the mean by ~70% of
    the time on the next earnings print.
-   The "ARM" (Analyst Revision Model) decile-1 vs decile-10 spread is
    persistently positive on a monthly rebal in US large-cap, with
    Sharpe in the 0.6–1.0 range *unhedged* and higher when sector-
    neutralised.

This is the most repeatable single-name long-short alpha in the
discretionary equity world.

### 2.4 What a pod actually does with it pre-earnings

A real pod-shop pre-earnings checklist for a mega-cap tech name (e.g.
NVDA into a print):

1.  Pull SmartEstimate vs Street. Predicted Surprise sign and magnitude.
2.  Pull last 30/60/90d revisions: count and weighted-magnitude.
3.  Pull whisper number (e.g. EarningsWhispers / Estimize crowd
    estimate). Compare to SmartEstimate.
4.  Pull alt-data dashboards: hyperscaler capex run-rate (for NVDA),
    DC GPU shipment proxies (Yipit, M-Science), TSMC monthly revenue
    (proxy for chip-volume), enterprise CIO surveys (Morgan Stanley AI
    Adopter Survey, JPM CIO Survey).
5.  Pull options: ATM straddle implied move vs realized last 8 prints.
    Skew. Term structure crush (front IV vs second-month IV).
6.  Pull dealer-positioning (SpotGamma, SqueezeMetrics): is dealer
    gamma long or short into the print? Long gamma = pinning likely;
    short gamma = larger realized move likely.
7.  Pull positioning: HF gross/net via prime-broker data (GS PB,
    MS PB), 13F crowdedness, short-interest.
8.  Build the trade: directional stock + defined-risk options overlay
    (call vertical / put vertical / calendar spread) sized to vol
    target.

That's the actual workflow. It takes 30–45 minutes per name once the
templates exist. It is replicable at retail with maybe 60% of the
fidelity — see section 11.

### 2.5 Upgrade/downgrade drift is real but decaying

Womack (1996) showed sustained drift for months after a recommendation
change. More recent work (Bradley, Clarke, Lee, Ornthanalai 2014;
McNichols & O'Brien post-Reg-FD) shows the *initial pop* has stayed
strong but the *post-event drift* has shortened from months to weeks
because of faster information dissemination and decimalization. A
reasonable 2026 prior:

-   Day-0 pop: 1.5–3.5% mean abs (mega-cap tech), more if it's a
    surprise (a perma-bear flipping bull) or a top-tier shop (MS,
    GS, JPM, ML).
-   Day +1 to +5 drift: ~50–80 bps in the direction of the change.
-   Day +5 to +20 drift: small, noisy, dominated by other flow.

The swing trade is *enter the drift, exit before noise dominates*.

### 2.6 Tier the analysts (everyone does)

Not all analysts move stocks equally. Pods rank:

-   **Top tier** (move stocks 200–400 bps on a change): Mark Murphy
    (JPM software), Brent Thill (Jefferies software), Erik Woodring
    (MS hardware), Stacy Rasgon (Bernstein semis), Vivek Arya (BofA
    semis), Pierre Ferragu (New Street semis), Brian Nowak (MS
    internet), Doug Anmuth (JPM internet), Eric Sheridan (GS internet),
    Mark Mahaney (Evercore internet), Toni Sacconaghi (Bernstein
    hardware), Dan Ives (Wedbush — controversial but moves names),
    Gene Munster (Loup — Apple).
-   **Mid tier**: most bulge-bracket coverage analysts.
-   **Low / noise**: niche shops without distribution.

Track which analyst's last 8 calls worked (StarMine does this for you).

---

## 3. Cross-asset signals — rates, DXY, oil/copper, SMH→QQQ, KRE, credit spreads

### 3.1 Mega-cap tech is a long-duration asset

The single biggest macro fact for mega-cap tech in the last decade: it
trades like a *long-duration bond*. NVDA, MSFT, AAPL etc have free-cash-
flow profiles weighted years into the future; their valuations are
discount-rate sensitive. Empirically (rolling 60d windows, 2018–2026):

-   QQQ vs ZN (10Y note future): correlation typically **+0.3 to +0.6**.
-   QQQ vs TLT: same sign, ~0.3 to 0.55 typically; spikes to 0.7+ in
    rates-shock regimes (Oct 2022, Apr 2024, Aug 2024).
-   QQQ vs DXY: typically **-0.2 to -0.45** (stronger dollar = pressure
    on multinational earnings + global risk-off).
-   QQQ vs HYG: positive — credit conditions matter, but the
    correlation is lower than you'd expect (~+0.2 to +0.4) because tech
    has very little credit risk.

**Pod-level implication:** the tactical PM rarely takes outright
directional bets on mega-cap tech without checking what 10Y yields and
DXY are doing this week. The "I'm long NVDA into earnings" trade is
implicitly *also* a long-duration trade, and on a 10bp 10Y back-up the
factor exposure (Barra: rates beta, growth tilt) will cost you 50–150
bps even if NVDA-idio works.

### 3.2 The cross-asset dashboard a tech-pod PM keeps open

Every morning, before any single-name trade:

| Instrument            | What it tells you                                        |
| --------------------- | -------------------------------------------------------- |
| ZN, ZF, ZB futures    | Rates regime — duration tailwind/headwind for tech       |
| TLT, IEF              | Same as above, equity-tradeable                          |
| 2s10s curve, MOVE     | Curve shape + rate vol regime; high MOVE = de-risk       |
| DXY, EURUSD, USDJPY   | Dollar strength; USDJPY is the canary for risk-off       |
| HYG, LQD, CDX HY      | Credit risk-on/off; widening HY spreads = de-risk equity |
| HYG/LQD ratio         | Cleaner credit-spread proxy                              |
| WTI / Brent           | Inflation impulse; geopolitical                          |
| Copper (HG), gold     | Growth signal (Cu) vs flight-to-quality (Au)             |
| KRE (regional banks)  | "Risk-on tell" — leads QQQ on bottoms                    |
| SMH, SOXX             | Semis lead tech; SMH:QQQ ratio is the cleanest tell      |
| BTC, ETH              | Risk-asset proxy, retail-flow tell                       |
| VIX, VIX3M, VVIX      | Vol regime + term-structure (see section 8)              |
| SKEW                  | Tail-risk pricing                                        |
| ARKK                  | Speculative-growth flow proxy                            |
| QQQ/SPY ratio         | Tech leadership                                          |
| RSP (eqw S&P)         | Breadth tell (cap-weight vs eqw divergence)              |

### 3.3 SMH leads QQQ — the most reliable intra-tech tell

Semis are the bleeding edge of the tech cycle (inventory, capex, AI
demand, hyperscaler orders). Empirically (2018–2026):

-   At local QQQ tops and bottoms, **SMH turns 1–5 trading days
    before QQQ** ~60–70% of the time.
-   The **SMH:QQQ ratio** breaking to a new 20-day high while QQQ
    holds flat is one of the cleanest "long tech" setups.
-   The same ratio breaking a 50-day low while QQQ holds flat is the
    cleanest "de-risk tech longs" warning.

A tactical PM will routinely overlay an SMH-relative chart on every
single-name tech long.

### 3.4 KRE — the risk-on canary

Regional banks (KRE) are not in your tech book, but they tell you
when the risk-on / risk-off regime is flipping. Reasoning:

-   KRE is rates-sensitive (NIM compresses when curve inverts).
-   KRE is credit-cycle sensitive (CRE exposure).
-   KRE has high beta to financial-conditions index.

When KRE leads SPX higher off a bottom (SVB March 2023 → April 2023
recovery, October 2023 lows → November rally, August 2024 yen-unwind
bottom), tech rallies tend to follow with leverage. When KRE breaks
down with SPX flat, lean defensive.

### 3.5 Credit spreads are the silent killer

The single best "are we about to get a 5%+ tech drawdown" signal is
**HY OAS widening + HYG breaking 50d MA**. The mechanism:

1.  Credit widens → financial-conditions tighten.
2.  HF risk models cut gross.
3.  Forced de-risk hits the most-crowded longs (= mega-cap tech).
4.  QQQ drops 3–7% over 2–10 trading days.

Watch:

-   ICE BofA US HY OAS (FRED: BAMLH0A0HYM2) — daily series.
-   HYG price + 50d / 200d MAs.
-   CDX NA HY 5Y on-the-run series.

A 50bp HY OAS widening in <2 weeks is a "cut tech gross by 25%"
trigger inside most pods.

### 3.6 The dollar (DXY) — the boring, expensive signal

USD up 2σ in a month → tech earnings translation headwind of 50–200 bps
on FY+1 EPS, which the sell-side will revise *downward*, which the
revisions factor will then short. The PM front-runs this: rising DXY +
mega-cap with ≥50% international revenue (AAPL, MSFT, GOOGL, META) →
trim longs or pair-short the highest-international-rev name.

### 3.7 The "regime card" a real pod uses

A PM keeps a one-page regime dashboard, updated end-of-day:

```
RATES:   [Easing | Neutral | Tightening | Shock]
USD:     [Weak   | Range   | Strong    | Spike]
CREDIT:  [Tight  | Stable  | Widening  | Stress]
VOL:     [Calm   | Normal  | Elevated  | Crisis]
BREADTH: [Broad  | OK      | Narrow    | Top-heavy]
LEADER:  [Semis  | SW/Net  | Mega-Mega | Defensives]
```

The combination dictates gross/net targets. Example mappings (rough):

-   Easing + Weak USD + Tight credit + Calm vol + Broad breadth + Semis
    leading → **maximum tech-long bias** (full gross, +20 net).
-   Tightening + Strong USD + Widening credit + Elevated vol + Narrow
    breadth → **defensive** (half gross, market-neutral, lean pairs).
-   Anything + Crisis vol → **flat or short**, no new initiations,
    cover all overnight earnings risk.

---

## 4. Pairs & stat-arb at the mega-cap level

### 4.1 Why pairs still work on mega-cap tech

Mega-cap tech is the most-crowded long basket on Earth. That sounds
like an alpha-killer — but it actually *creates* pairs alpha:

-   Forced de-risk events (Aug 2024 yen carry, Sep 2024 DeepSeek
    headlines, Jan 2025 deepseek-r1, April 2025 tariffs) hit the basket
    indiscriminately, creating dispersion within the basket.
-   Index-rebalance flows are concentrated in the top names.
-   Single-name catalysts (earnings, regulatory) create big idiosyncratic
    moves *within* a basket whose beta is highly correlated.

This is the classic stat-arb setup: high *average* correlation in the
basket, but high *dispersion* of idiosyncratic returns. The PM trades
the spreads, not the directions.

### 4.2 The math, briefly

**Engle-Granger (1987)** — the two-step procedure (Wikipedia,
*Cointegration*; Engle & Granger, *Econometrica* 1987):

1.  Run OLS of `log(P_A)` on `log(P_B)` → residual series `ε_t`.
2.  Test `ε_t` for stationarity (ADF / KPSS). If reject unit root,
    the series are cointegrated.

The trade: when `ε_t` exceeds ±2σ from its rolling mean, fade it
(short the rich, long the cheap). Exit at mean or ±0.5σ. Stop at ±3σ
(or on cointegration break — recompute weekly).

**Johansen (1991)** — multi-asset cointegration, vector error-
correction model (VECM). Used when you want to test cointegration among
3+ assets simultaneously (e.g., MSFT vs an equal-weight basket of
{GOOGL, META, AMZN}).

**Kalman filter** — for *dynamic* hedge ratios. Pure OLS gives you a
constant β; reality is β drifts (NVDA's beta to SMH was 1.0 in 2020,
2.5 in 2024). Kalman recursively updates β each day given new data.
The state-space form:

```
β_t   = β_{t-1} + w_t,        w ~ N(0, Q)
y_t   = β_t * x_t + v_t,      v ~ N(0, R)
```

Tune `Q` (process noise) and `R` (observation noise) by ML or grid
search on a holdout. The Kalman β is then used to compute spread
`y_t - β_t * x_t`. Trade z-scores of that spread.

### 4.3 Concrete mega-cap pairs that actually work (with caveats)

These pairs have *passed* a rolling-window Engle-Granger test
periodically over 2018–2026, but cointegration breaks; the pod re-tests
weekly:

**NVDA / AMD** — both GPU/accelerator exposure; common factor =
AI/datacenter capex. β-Kalman drifts 1.0 → 2.5 over the cycle.
Tradeable spread with mean-reversion half-life ~5–15 days. *Risk:*
during regime breaks (NVDA's Blackwell ramp, AMD's MI300 launch) the
spread can trend for weeks. **Never** trade naked into either's
earnings.

**GOOGL / META** — both ad-revenue exposure, both AI capex spenders.
Spread half-life ~7–20 days. *Risk:* regulatory divergence (DOJ Google
breakup chatter), platform-specific shocks (Reels vs YouTube Shorts
monetization).

**MSFT vs equal-weight {GOOGL, AMZN, META}** — Johansen-style basket
pair. MSFT is the cleanest "hyperscaler proxy"; trades against the
basket of the other three. Half-life ~10–25 days. *Risk:* MSFT-specific
news (OpenAI deal terms, Activision integration metrics).

**ORCL / MSFT** — enterprise software / cloud. Less liquid pair; wider
spreads but cleaner cointegration in stable regimes.

**AMD / INTC** — historically cointegrated; broke in 2018–2024 as INTC
fundamentals diverged. **Currently not tradeable as a pure stat-arb
pair** — example of a pair that died.

**AAPL vs hardware basket {DELL, HPQ, LOGI}** — useless. AAPL has
become its own factor; do not pair it against generic hardware.

### 4.4 Edge after costs at retail

Be honest. Pod-level stat-arb runs at <1bp per side commissions and
<2bp slippage on mega-caps via algos (VWAP, POV, IS — Implementation
Shortfall). Retail at IBKR pays:

-   Tiered commission: ~$0.0035/share, capped at 1% of trade value,
    min $0.35.
-   SEC + TAF fees: ~$0.0001–0.0002/share.
-   Implicit spread: 0.5–2 bps on mega-caps.
-   Implicit slippage on market orders: 2–10 bps (1–5x worse than
    institutional algos).

A pair trade is *two legs in, two legs out* = 4 round-trips of cost.
At ~5 bps per leg all-in, that is ~20 bps per pair trade. A stat-arb
strategy with a gross Sharpe of 1.5 and 50 bps mean trade-P&L becomes
~30 bps after costs — still profitable, but you need >100 trades/year
to make it real money. **At retail, stat-arb on mega-cap tech is
marginal. Trade fewer, bigger, longer-half-life pairs.**

### 4.5 What kills stat-arb pairs (regime breaks)

-   M&A (AMD / Xilinx 2022 broke AMD pairs for months).
-   Major product cycle divergence (NVDA Hopper / Blackwell vs AMD MI
    series — 2023–2024 divergence broke NVDA/AMD as a stat-arb pair
    for ~14 months).
-   Regulatory shocks (EU DMA enforcement on AAPL/GOOGL).
-   Index inclusion / exclusion (TSLA S&P add in Dec 2020 broke every
    TSLA pair).

*Rule:* re-test cointegration weekly with Engle-Granger ADF, hard-stop
the pair if p-value > 0.10 for 2 weeks running.

---

## 5. Vol targeting and risk-parity overlays

### 5.1 Why vol-target, not dollar-target

A dollar-target book ($1M long NVDA, $1M short AMD) is *not* a
constant-risk book. NVDA's 30d realized vol can swing from 25% to 80%
over a year. A constant-dollar position therefore swings 3x in risk
contribution. The PM wants the *risk contribution* constant.

The canonical formula:

```
w_i  =  (σ_target / σ_i) * (1 / N) * leverage_factor
```

For a multi-asset book:

```
w  =  k * Σ^(-1) * μ            (mean-variance, with shrinkage)
w  =  k * Σ^(-1) * 1            (minimum-variance / risk parity)
```

A real pod runs `w = k * Σ^(-1) * α` where `α` is the *signal vector*
and `Σ` is shrunk (Ledoit-Wolf 2003) or factor-model-decomposed (Barra).

### 5.2 Choose your vol target

-   Pods: 8–15% annualized vol on NAV (gross is whatever it takes to
    hit that under the factor caps).
-   Retail "swing trader" account: **10–15% is sane**, 20%+ is
    aggressive but defensible for a small account where the trader can
    add capital, ≥25% is gambling.

To convert annualized to daily 1σ: `σ_daily = σ_ann / sqrt(252)`.
So a 12% vol target = 0.756% daily 1σ. A 1-day 99% VaR (normal
assumption, which underestimates tails) ≈ 2.33 * 0.756 = ~1.76% of NAV.

### 5.3 Black-Litterman for swing tilts

Black-Litterman (1992) is the right framework for blending *priors*
(equilibrium / market-cap weights) with *views* (your swing theses).
Sketch:

```
Π  = δ * Σ * w_mkt                       # equilibrium returns
E[r] = [(τΣ)^-1 + P' Ω^-1 P]^-1
        * [(τΣ)^-1 Π + P' Ω^-1 Q]        # posterior
```

Where `P` encodes your views (e.g., "NVDA outperforms AMD by 3%/mo")
and `Ω` encodes your confidence (smaller `Ω` = stronger conviction).

**Why a swing PM cares:** B-L gives you *bounded* tilts. It's how you
say "I'm 60% confident MSFT will beat the eqw-hyperscaler basket by 2%
this quarter" and end up with a sensible long-MSFT / short-basket
sizing rather than betting the farm on a strong view. It also keeps
you market-neutral by construction if you start from a market-neutral
prior.

In practice retail won't run B-L matrix algebra. The *spirit* is what
matters: start from a neutral allocation, deviate proportional to the
strength and number of your views, and don't let any single view
exceed a defined risk-budget slice (e.g., 25% of risk budget per view).

### 5.4 Vol scaling on entry

Practical PM rule: position size in dollars =

```
$ = (Account_NAV * Risk_per_trade) / Stop_distance_in_$
```

Where `Risk_per_trade` is typically 25–100 bps of NAV and
`Stop_distance` is *placed at a meaningful technical/vol level* (e.g.,
1.5x ATR(14), or below prior pivot). This is the **fixed-fractional
risk** rule that Van Tharp / Tom Basso popularized in the 80s and that
literally every pod still uses for ad-hoc swing trades.

Example: $100k NAV, 50bps risk per trade = $500. NVDA setup, entry
$1000, stop $950 (5%). Position = $500 / $50 = 10 shares = $10k
notional. If wrong, lose $500 (50bps). If right and exit at $1100,
make $1000 (100bps, 2R).

---

## 6. Options as a swing instrument

### 6.1 When options *beat* outright stock

Options dominate stock for a 1–4 week swing trade when:

1.  **Defined risk is critical.** Earnings, FDA, regulatory binary.
2.  **You have a strong view on *magnitude*** (not just direction).
3.  **You have a view on *vol*** in addition to direction.
4.  **Time-decay is on your side** (calendars, diagonals into a
    known-quiet period).
5.  **You want leverage without margin interest.**
6.  **Capital efficiency** — a $5 wide call vertical on a $500 stock
    costs ~$200 instead of $50k of long stock.

Options are *worse* than stock when: you have no vol view, the holding
period is long (>30 days where theta dominates), or your edge is
purely directional with a soft stop (stock is cleaner).

### 6.2 Defined-risk structures the PM uses

**Long call vertical (bull call spread)** — buy ATM, sell OTM. Cost
< debit width, max gain = width − debit. Use for: directional bullish
2–4 weeks, IV elevated (don't want naked long IV).

**Long put vertical (bear put spread)** — mirror. Defined-risk short.

**Calendar spread** — sell front-month, buy back-month, same strike.
Profits from front-month theta decay relative to back-month, and from
*IV expansion* in the back-month. Use when: you expect a near-term
pin and post-event continuation. Classic post-earnings IV-reset trade.

**Diagonal spread** — sell front-month OTM, buy back-month closer to
ATM. Hybrid of vertical and calendar. Used for "I think it grinds
higher over 4–8 weeks" — the long back-month is your delta, the short
front-month is your theta carry.

**Iron condor / iron fly** — short straddle/strangle with wings
(defined risk). Pure vol-short trade. Use when: IV rank > 50%, you
expect realized < implied. **NEVER** naked, even at retail with
margin — wings are non-negotiable.

### 6.3 The tastytrade short-premium evidence (and the caveats)

tastytrade research (Sosnoff / Battista et al., 2014–2024) has
published extensive backtests on:

-   Short 16-delta strangles on SPY/QQQ, 45 DTE, managed at 21 DTE or
    50% max profit — Sharpe ~0.7–1.0 unhedged, win-rate ~75–85%,
    expectancy positive but with tail risk realized in 2018 vol-Q4,
    Feb 2018 "Volmageddon", March 2020 Covid, Aug 2024 yen unwind.
-   Short 1-SD iron condors on indices — similar profile, smaller
    win-rates due to tighter wings.
-   Earnings short-premium strategies — robust on liquid mega-cap
    underlyings but require strict position-sizing (≤2% of NAV per
    trade) and mechanical management.

**The retail caveat tastytrade understates:** the strategies have
*massive negative skew*. A 0.7 Sharpe with one -10σ event every 3–5
years can blow the account. Volmageddon 2018 ruined retail short-vol
ETPs (XIV terminated). Always:

-   Use wings (iron condor / iron fly), never naked strangles.
-   Cap notional vega exposure across the book.
-   Pair short-premium with a small long-tail hedge (long VIX call
    spreads or long SPY put 1σ OTM).

### 6.4 Single-stock options on mega-cap tech: liquidity reality

| Underlying | ATM weekly spread | OI / volume tier | Strike granularity |
| ---------- | ----------------- | ---------------- | ------------------ |
| AAPL       | $0.01–0.02         | A+ (deepest)     | $1                 |
| NVDA       | $0.02–0.05         | A+               | $1–$2.5            |
| MSFT       | $0.02–0.05         | A                | $1–$2.5            |
| GOOGL      | $0.02–0.05         | A                | $1–$2.5            |
| AMZN       | $0.02–0.05         | A                | $1–$2.5            |
| META       | $0.05–0.10         | A                | $2.5–$5            |
| TSLA       | $0.02–0.05         | A+ (most active) | $2.5–$5            |
| AVGO       | $0.10–0.30         | B+               | $5–$10             |
| AMD        | $0.02–0.05         | A                | $1                 |
| NFLX       | $0.10–0.30         | B+               | $5                 |
| ORCL       | $0.05–0.10         | B+               | $2.5               |
| CRM        | $0.05–0.15         | B                | $2.5               |
| ADBE       | $0.10–0.30         | B                | $5                 |
| QCOM       | $0.05–0.15         | B                | $2.5               |

Implications: on AAPL/NVDA/TSLA you can scalp options. On AVGO/NFLX/
ADBE you should size smaller and assume 5–15 bps round-trip slippage.

### 6.5 Earnings IV crush — the most reliable options pattern

Mega-cap tech ATM IV typically rises 30–80% in the 2–3 weeks leading
into earnings and crushes 30–60% the morning after. The trades:

-   **Long IV pre-earnings** (calendar spreads buying back-month): works
    if you initiate ≥2 weeks before, exit 1–2 days before print.
-   **Short IV post-earnings**: short straddles / iron flies *only*
    after the print, capturing the IV reset. Requires near-term-only
    short, hold 3–10 days max.
-   **Earnings straddle buy** ("buying the move"): works only when
    implied move < realized move historically. Edge is *very* slim and
    asymmetric (most prints come in roughly priced).

### 6.6 Margin & buying-power treatment (retail)

Reg-T accounts: defined-risk spreads use buying-power = max-loss.
Portfolio-margin accounts (eligible at ≥$125k NAV at most brokers; IBKR
$110k): buying-power is risk-based, can be 4–6x more efficient. **A
serious swing trader >$125k NAV should be on portfolio margin.** It is
not optional if you want to do real multi-leg options work.

---

## 7. Smart-beta lessons — MTUM, QUAL, USMV and the index-effect

### 7.1 What these ETFs *actually* hold

**MTUM** (iShares MSCI USA Momentum Factor ETF) — top ~125 US
large/mid caps ranked by 6M and 12M risk-adjusted price momentum
(skip-most-recent-month). Rebalances **semi-annually** (May and
November). AUM ~$15–20B (varies).

**QUAL** (iShares MSCI USA Quality Factor ETF) — high-quality screen
based on ROE, debt/equity, and earnings variability. ~125 names.
Semi-annual rebalance.

**USMV** (iShares MSCI USA Min Vol Factor ETF) — minimum-variance
optimization with sector / single-name caps. Semi-annual rebalance.

### 7.2 The rebalance arbitrage (the "Index Effect")

Documented since Harris & Gurel (1986) and Shleifer (1986) for the
S&P 500. Stocks added to a major index rise 3–5% on average in the
days surrounding inclusion; stocks deleted fall similarly. The mechanism
is forced indexer demand against finite immediate supply.

For factor ETFs like MTUM, the effect is smaller but *real* and
*predictable*:

1.  Methodology is public (MSCI publishes the rule book).
2.  Rebalance dates are known.
3.  About 4–6 weeks before rebalance, you can *forecast* the
    additions/deletions to ~70–85% accuracy by simulating the screen
    on current data.

**The pre-positioning trade:** long forecast adds / short forecast
deletes 2–4 weeks before the rebalance, exit on / right after the
rebalance announcement. Edge: 50–200 bps per name, scalable.

Caveats:

-   Index-rebal arb is *crowded* — every quant shop does it. Edge has
    compressed since 2015.
-   Liquidity matters more than alpha; small-mid caps are richer
    targets than mega-caps where forced demand is a tiny fraction of
    ADV.
-   On mega-cap tech specifically, the effect is small (NVDA's MTUM
    weight changes don't move NVDA), but the *direction* of weight
    changes tells you what factor flow is doing to the name.

### 7.3 What the swing PM learns from smart-beta

Even if you don't trade the rebal arbitrage:

-   **Momentum decay**: MTUM's semi-annual rebalance means it owns
    stocks that *were* momentum 7–12 months ago. The faster-rebalancing
    PDP (PowerShares DWA Momentum) and the academic 12-1 momentum
    portfolio both show momentum *itself* still works (Jegadeesh &
    Titman 1993, 2001 update; Asness, Moskowitz & Pedersen 2013
    "Value and Momentum Everywhere").
-   **Quality + momentum** is the highest-Sharpe equity factor combo
    (Asness, Frazzini, Pedersen 2019). The swing PM tilts toward names
    that are *both* high-quality (ROE, low debt) and exhibiting
    positive momentum.
-   **Low-vol anomaly** (USMV's basis): Frazzini & Pedersen (2014)
    "Betting Against Beta" — low-beta stocks have higher risk-adjusted
    returns. Doesn't make a great swing-trading factor (too slow), but
    informs *position sizing*: a low-beta name can carry more dollars.

---

## 8. Derivatives data — SKEW, VIX/VIX3M, single-stock skew, dealer positioning

### 8.1 The VIX is the headline; the term structure is the signal

VIX measures 30-day forward implied vol on SPX options (CBOE
methodology; see Wikipedia, *VIX*; CBOE white paper).
**VIX3M** is the 3-month equivalent.

The **term structure ratio** `VIX / VIX3M`:

-   `< 1.0` (contango) — normal regime; vol curve is upward-sloping,
    market is calm, equity longs OK.
-   `~1.0` (flat) — transition / warning.
-   `> 1.0` (backwardation) — stressed regime; near-term fear > medium-
    term fear; equity longs at risk.
-   `> 1.10` — acute stress (e.g., Aug 2024 yen unwind hit ~1.4).

A daily flip from contango to backwardation has historically preceded
S&P drawdowns of 3–8% with high frequency. **Pod rule:** when
VIX/VIX3M > 1.05 for 2 consecutive closes, cut tech gross by 20–30%
and shift to defined-risk options for new longs.

### 8.2 SKEW — tail-risk pricing

CBOE SKEW Index (ticker SKEW): measures the implied probability of
2-σ-or-larger downside in SPX over the next 30 days, derived from OTM
put pricing. Normal range 115–145. >150 = elevated tail-hedging
demand; >170 = extreme.

The *interpretation* is contested. Empirically:

-   High SKEW *does not* reliably predict imminent crashes (the
    "fooled by SKEW" critique).
-   But persistently elevated SKEW + flat VIX *does* indicate
    institutional tail-hedging, which is a sign someone with better
    info than you is buying insurance.
-   Treat as a *modifier* on net exposure, not a primary signal.

### 8.3 Single-stock skew and term structure

For each mega-cap, the swing PM looks at:

-   **25Δ put / 25Δ call IV ratio (1-month)** — single-stock skew.
    Persistently elevated for left-tail-fearing names (TSLA pre-2020,
    META 2022, NVDA briefly in 2024 after Blackwell delay reports).
-   **Front-month / 3-month IV ratio** — term-structure shape per name.
    Steep contango is *normal*; backwardation pre-earnings is *also*
    normal (event-vol bump). Backwardation *outside* of an event window
    is the actionable signal.

### 8.4 Dealer positioning — SqueezeMetrics (DIX/GEX), SpotGamma

SqueezeMetrics' **Dark Index (DIX)** and **GEX** (Gamma Exposure):

-   **GEX > 0** (dealers are net long gamma): dealers hedge by *fading*
    moves (selling rallies, buying dips). Vol gets *suppressed*. Range-
    bound regime.
-   **GEX < 0** (dealers are net short gamma): dealers hedge *with*
    moves (buying rallies, selling dips). Vol gets *amplified*. Trend
    regime, large realized moves.
-   Threshold: GEX crossing from + to − is a "vol regime change"
    signal.

SpotGamma's metrics (HIRO, Vanna, Charm exposures):

-   **Vanna**: ∂Δ/∂σ — how dealer delta changes with vol. Important
    around VIX crushes.
-   **Charm**: ∂Δ/∂t — how dealer delta changes with time. Drives
    end-of-week and end-of-month "pin" behavior at large OI strikes.
-   **HIRO**: real-time directional options-flow tape.

The retail accessibility: SpotGamma and SqueezeMetrics both sell
retail-tier subscriptions (~$60–200/mo); free proxies (SHIFT search,
unusual whales) exist with reduced fidelity.

### 8.5 0DTE — the elephant in the room

By 2024–2026, 0DTE options account for ~50% of SPX/QQQ daily options
volume (CBOE / OCC data). Implications for the swing PM:

-   *Intraday* moves in mega-cap tech are increasingly dominated by
    0DTE gamma flips on the underlying ETFs.
-   *Overnight* and multi-day moves are *less* affected — 0DTE doesn't
    persist.
-   But: the *Friday afternoon → Monday morning* gap is more volatile
    because of 0DTE-driven pin-and-release at 3 p.m. ET on Friday.

Don't trade 0DTE as a swing instrument (it's not one). Do watch SPY
0DTE GEX in the morning to know which way intraday moves will flow.

---

## 9. Multi-sleeve book construction

### 9.1 Why uncorrelated sleeves dominate one big bet

The investor's holy grail is uncorrelated return streams with
positive Sharpes. If you combine N strategies with average Sharpe `s`
and pairwise correlation `ρ`, the combined Sharpe is approximately:

```
S_combined ≈ s * sqrt(N / (1 + (N-1) * ρ))
```

Five sleeves of Sharpe-1 with ρ=0.2 → combined Sharpe ≈ 2.3. Five
sleeves of Sharpe-1 with ρ=0.7 → combined Sharpe ≈ 1.2. The
diversification math is the entire reason platform funds exist.

### 9.2 The four-sleeve mega-cap tech swing book

A realistic pod construction:

**Sleeve A — Trend / momentum (30–40% of risk budget)**

-   Long names with 6M risk-adj momentum in top quintile + positive
    30d revision momentum + above 50d MA + sector/factor neutralized.
-   Short corresponding bottom quintile (within mega-cap tech universe).
-   Holding period: 2–6 weeks.
-   Edge source: Jegadeesh-Titman momentum + estimate-revision factor.

**Sleeve B — Mean-reversion / pairs (15–25% of risk budget)**

-   Cointegrated pairs from section 4 (NVDA/AMD, GOOGL/META, MSFT vs
    eqw basket).
-   Z-score ≥ 2 entry, ≤ 0.5 exit, 3σ stop.
-   Holding period: 3–15 days.
-   Edge source: short-term overreaction (Lo-MacKinlay 1990,
    Lehmann 1990 "Fads, martingales, and market efficiency").

**Sleeve C — Event-driven (20–30% of risk budget)**

-   Earnings setups (sections 2.4 and 6.5), index rebal (section 7.2),
    M&A spreads if applicable, analyst-day catalysts, regulatory
    catalysts (DOJ/FTC/EU rulings).
-   Sized per event, typically 50–150 bps risk per setup.
-   Holding period: 1–10 days.
-   Edge source: structural under-/over-reaction + flow knowledge.

**Sleeve D — Vol / hedge overlay (10–20% of risk budget)**

-   Long tail-hedges in vol-elevated regimes (VIX call verticals when
    VIX < 14 and SKEW > 145).
-   Short premium on names with rich IV vs realized post-earnings
    (defined-risk iron flies / condors only).
-   Holding period: 2–30 days.
-   Edge source: vol risk premium + tail-hedge timing.

### 9.3 Correlation management

Track pairwise sleeve P&L correlation on rolling 60-day windows. If
any pair exceeds 0.5, the sleeves are not actually independent and
the diversification is illusory. Common culprits:

-   Trend sleeve + event sleeve both ending up net-long the same
    earnings-beating names — collapses to a single bet.
-   Pairs sleeve + trend sleeve both leaning on the same factor
    (long-momentum, short-low-momentum).

The fix: **factor-decompose every sleeve** before sizing. Subtract
the factor exposure from each sleeve's positions and only let the
*idiosyncratic* component contribute to the sleeve's risk budget.

### 9.4 Stress testing

A pod runs daily:

-   Historical scenario replay: Aug 5 2024 (yen unwind), Sep 13 2024
    (Israel-Iran), Mar 9 2020 (Covid limit-down), Feb 5 2018
    (Volmageddon), Dec 24 2018 (Powell pivot pre-), Aug 24 2015
    (flash crash), May 6 2010 (flash crash).
-   Factor shock: rates +50bp, USD +3%, HY OAS +75bp, semis -10%.
-   Single-name shock: top-3 net longs each -15%.

At retail you can do this in a spreadsheet. The exercise is what
matters: *write down what each big position loses in your worst
plausible day* and confirm the sum is survivable.

---

## 10. Public-quant lessons

### 10.1 Edward Thorp — Kelly criterion + market-neutral discipline

Thorp's *A Man for All Markets* and his Wilmott interviews are the
practical reference. The two takeaways:

-   **Kelly sizing**: `f* = (bp - q) / b`, where `b` is odds, `p` is
    win prob, `q = 1-p`. For continuous returns, `f* = μ / σ²`.
    *Full Kelly is too aggressive in practice* — Thorp himself
    advocated half- or quarter-Kelly because parameter uncertainty
    dwarfs the optimization gain.
-   **Cost discipline**: PNP / Ridgeline ran market-neutral with
    obsessive transaction-cost management. The PM mantra: *if you
    can't measure slippage to 1bp, you'll bleed 50bp/year you can't
    explain*.

### 10.2 Renaissance — what's actually public

Most of Renaissance's edge is unknown and will stay that way. What's
*publicly* documented (Zuckerman's *The Man Who Solved the Market*,
academic citations, court filings):

-   Short holding periods (intraday to days, not weeks). Not
    applicable to discretionary swing.
-   Heavy use of *signal combination* across thousands of weak signals.
    The transferable lesson: **one signal won't make you money.
    Combinations might.**
-   Brutal data hygiene. Survivorship-bias-free databases, corporate-
    action-adjusted prices, point-in-time fundamental data. *If you
    backtest on Yahoo data, you are kidding yourself.*
-   Hire physicists/cryptographers, not finance MBAs. Process > pedigree.

### 10.3 AQR / Asness papers — the workhorse references

If you read three AQR papers, read these:

-   **Asness, Moskowitz, Pedersen (2013)** "Value and Momentum
    Everywhere" — value and momentum work across asset classes and
    are negatively correlated. The swing PM uses both.
-   **Frazzini & Pedersen (2014)** "Betting Against Beta" — low-beta
    stocks outperform on a risk-adjusted basis. Sizing implication:
    high-beta names need smaller dollar sizing for equal risk.
-   **Asness, Frazzini, Pedersen (2019)** "Quality Minus Junk" — the
    QMJ factor, robust and persistent. Combines profitability,
    growth, safety, payout.

### 10.4 Marcos López de Prado — *Advances in Financial Machine Learning*

López de Prado's framework is the modern quant standard. Key
concepts every swing PM should internalize even without doing ML:

-   **Triple-barrier labeling**: instead of fixed-horizon labels
    ("up in 5 days?"), label trades by *whichever barrier hits first*
    — upper (profit target), lower (stop), or vertical (time limit).
    This is just *good trade construction* dressed up in ML language.
    Every trade should have all three barriers defined at entry.
-   **Meta-labeling**: first model decides *direction* (or use a
    fundamental signal), second model decides *whether to take the
    trade at all*. For a swing PM, the meta-label is "is the regime
    right for this signal?" (e.g., trend signals get filtered out in
    high-vol-backwardation regimes).
-   **Combinatorial purged cross-validation**: standard k-fold CV
    leaks in time-series. Use purged + embargoed CV. Translation: if
    you're backtesting, *don't fit on overlapping windows*.
-   **Fractionally differentiated features**: keep memory in
    stationary series. Most retail traders compute returns (full
    differencing) and lose all level information. A fractional-d
    series at d≈0.3 retains memory while passing stationarity.
-   **Backtest overfitting**: López de Prado's "Deflated Sharpe Ratio"
    adjusts your reported Sharpe for the number of backtests you ran.
    If you tried 100 parameter combos to find the one with Sharpe 2,
    the true expected Sharpe is closer to 0.5.

### 10.5 The painful unification

Combine the above and you get a profile of what *actually works* in
discretionary equity:

1.  Multi-signal combination, not single-indicator.
2.  Sized by volatility contribution, not dollars.
3.  Hedged by factor exposure, not by hope.
4.  Stop-loss defined *before* entry, mechanically.
5.  Costs measured to the basis point.
6.  Backtests purged, deflated, treated with suspicion.

---

## 11. Retail-adapted institutional checklist ($25k–$250k single trader)

> This is the deliverable. Tear it out, tape it to the monitor.

### 11.1 Account & infrastructure

-   [ ] Broker: IBKR Pro (or Tastytrade for options, or Tradier).
        IBKR if NAV >$50k. Tiered commissions, real algos (TWAP,
        VWAP, IS, Adaptive), real options chains.
-   [ ] **Apply for portfolio margin at $125k+ NAV**. Non-negotiable
        for serious multi-leg options work.
-   [ ] Subscribe to: real-time L1 quotes ($10–25/mo), OPRA options
        ($25/mo at IBKR), one institutional-style data feed
        (Koyfin Pro $50/mo *or* Bloomberg via a Bloomberg-for-the-
        rest-of-us alternative — Atom, Sentieo trial). At the upper
        end of the NAV range, consider FactSet light or even a single
        BBG terminal at $24k/year.
-   [ ] Charting: TradingView Premium ($60/mo) is fine. Add
        Optionstrat or Optionsplay for options structuring.
-   [ ] Vol/dealer data: SpotGamma or SqueezeMetrics retail tier
        ($60–100/mo). One, not both.
-   [ ] Estimates: Koyfin gives StarMine-lite (consensus + revisions);
        Bloomberg/Refinitiv if you can swing it; Stock Analysis +
        Tikr Terminal as cheap fallback.
-   [ ] Calendars: EarningsWhispers Pro ($20/mo) — consensus, whisper,
        implied move. Wallmine or Estimize for crowd estimates.

### 11.2 Daily routine (60 minutes)

**Pre-market (07:00–09:00 ET):**

1.  Update cross-asset regime card (rates / USD / credit / vol /
    breadth / leader). 5 min.
2.  Scan headlines: ETF flows (yesterday), analyst-actions calendar
    (Briefing.com, StreetAccount, free Seeking Alpha analyst-rating
    feed). 10 min.
3.  Update revisions dashboard: any name in your universe with
    EPS revisions >±1% in last 7d or target change >±3%. 10 min.
4.  Pull dealer-positioning: SPY/QQQ GEX, Vanna; biggest single-stock
    gamma walls. 5 min.
5.  Earnings on tap: implied move vs realized 8-print median;
    SmartEstimate vs Street. 10 min.
6.  Risk check on open book: factor exposures (eyeball — beta,
    momentum tilt, sector concentration); single-name >2% NAV?
    Pair imbalance? 10 min.

**During the day:**

7.  Trade only your prepared list. No new initiations on news you
    didn't pre-think.
8.  Use limit orders. Market orders cost 5–10 bps you don't have to
    pay. Slippage adds up.
9.  Size by **fixed-fractional risk**: 25–75 bps of NAV per trade.
10. Stops mechanical, placed at order entry. Triple barrier (profit
    target, stop, time limit) defined.

**Post-close:**

11. Mark-to-market the book. Update P&L sheet. Compute daily vol
    contribution per position.
12. Note one thing you screwed up. Write it down.
13. Plan tomorrow's hit-list before bed.

### 11.3 Risk limits (the retail "platform")

These are *yours*, you don't have a risk officer, you are the risk
officer. Be your own asshole:

| Limit                              | Suggested              |
| ---------------------------------- | ---------------------- |
| Daily VaR (1d 99%)                 | ≤ 2.0% of NAV          |
| Single-name max gross              | 10% of NAV             |
| Single-name max net                | 5% of NAV              |
| Sector net (any GICS sub-industry) | 20% of NAV             |
| Gross exposure max                 | 200% of NAV (cash) /   |
|                                    | 300% (margin) /        |
|                                    | 500% (port margin)     |
| Beta net                           | -0.3 to +0.7           |
| Max loss per trade                 | 75 bps of NAV          |
| Max loss per day                   | 1.5% of NAV → stop     |
| Max drawdown from peak             | 8% → cut sizing 50%    |
| Max drawdown from peak             | 15% → flat, week off,  |
|                                    | strategy review        |

The drawdown rule is the most important one on the page. **You will
be tempted to break it. Don't.**

### 11.4 Signal stack you can actually run

Pick 3–5, not all of them:

1.  **Estimate-revision momentum** (sec 2). Universe: 20 mega-cap
    tech. Rank by 30d EPS revision % + count of upgrades. Long top
    3, short bottom 3 (or hedge with QQQ if you don't want shorts).
    Refresh weekly.
2.  **Cross-asset regime tilt** (sec 3). When credit widening +
    USD strengthening + VIX/VIX3M > 1.0 → halve gross. When inverse
    → max gross.
3.  **One cointegrated pair** (sec 4). NVDA/AMD or GOOGL/META.
    Engle-Granger retest weekly. Z>2 enter, Z<0.5 exit, Z>3 or coint
    break = stop.
4.  **Earnings setups** (sec 2 + 6). 2–3 per quarter, the highest-
    conviction ones. Defined-risk verticals only (no naked stock
    overnight into binary events at retail unless ≤25 bps NAV risk).
5.  **VIX-term-structure hedge overlay** (sec 8). When VIX/VIX3M
    flips to backwardation, put on a small (10–20 bps premium)
    long-VIX call vertical as a tail hedge.

### 11.5 Cost discipline (sec 4.4 in spirit)

-   Measure your *real* per-trade cost (commission + spread + slippage)
    monthly. Most retail traders are clueless about this — it's
    routinely 15–30 bps/trade and they think it's 5.
-   Avoid market orders on anything outside AAPL/NVDA/MSFT/TSLA.
-   Use IBKR's Adaptive Algo (Patient / Normal / Urgent) instead of
    plain limits when filling >$20k notional.
-   Options: never cross more than half the spread. If you can't get
    filled at mid+25%, the trade isn't worth the cost.

### 11.6 What to *not* do (the pod-shop "fired list")

A PM at MLP would be on a PIP / fired for any of these. So would
your account:

-   Add to a losing position past your pre-defined stop.
-   "Take off the hedge because it's costing me" — that is the hedge
    *working*.
-   Hold an idiosyncratic long into earnings beyond your defined
    risk-per-event limit.
-   Trade names with <$10M ADV (you are the liquidity).
-   Run >2x your stated vol target because "vol is low right now".
-   Convince yourself a stat-arb pair "will come back" after the
    cointegration test breaks. It won't.
-   Trade more after a loss. Cut size after a loss, not before.

### 11.7 Single-page "PM letter" to yourself

Every Sunday, write 200 words:

-   What's the macro regime?
-   What's working in your book? What isn't?
-   What single mistake will you not repeat this week?
-   What's the highest-conviction trade for the week and why?
-   What's the worst plausible outcome of your current book? Can you
    survive it?

That weekly act of writing forces you to think like a PM, not like
a Reddit account.

### 11.8 The honest summary

A platform-fund PM running a mega-cap tech swing book has:

-   $50–500M of capital.
-   A $10–25M/year cost base of data, tech, analysts, prime brokers.
-   A risk department, a quant team, and a CFO.
-   Hard institutional limits enforced by someone else.
-   Goldman/MS PB algos that fill at 1bp slippage.

You have an IBKR account, $50–250k, an internet connection, and a
Sunday afternoon. **You will not match their Sharpe.** What you can do
is borrow their *process*:

1.  Combine signals, don't worship one.
2.  Size by risk, not by dollars.
3.  Define stops *before* entry.
4.  Hedge factor exposure where you can; size for it where you can't.
5.  Measure costs religiously.
6.  Survive the drawdown.

Do those six and you will be in the top 10% of retail swing traders.
That doesn't sound exciting because retail swing traders are bad at
this — but the top 10% actually compound. The bottom 90% donate to
the top 10% (and to Citadel Securities' payment-for-order-flow desk).

Choose which side of that trade you're on.

---

### Selected sources & further reading

-   Wikipedia, *Millennium Management, LLC* — AUM, structure, PM count.
    Backed by FT, Bloomberg, Institutional Investor, NYT reporting cited
    therein.
-   Wikipedia, *Citadel LLC* — AUM, structure, business lines. Backed by
    Bloomberg, CNBC, LCH Investments cited therein.
-   Wikipedia, *VIX* — methodology and term structure.
-   Wikipedia, *Cointegration* — Engle-Granger, Johansen, spurious-
    regression history.
-   CBOE, *VIX White Paper* (cboe.com).
-   CBOE, *SKEW Index Methodology*.
-   Engle & Granger (1987), "Co-integration and error correction:
    representation, estimation, and testing", *Econometrica*.
-   Johansen (1991), "Estimation and hypothesis testing of cointegration
    vectors in Gaussian VAR models", *Econometrica*.
-   Jegadeesh & Titman (1993, 2001), JoF — momentum.
-   Womack (1996), JoF — analyst recommendation drift.
-   Stickel (1991), JoF — analyst all-star effect.
-   Jegadeesh, Kim, Krische & Lee (2004), JoF — recommendation changes
    vs levels.
-   Asness, Moskowitz & Pedersen (2013), JoF — "Value and Momentum
    Everywhere".
-   Frazzini & Pedersen (2014), JFE — "Betting Against Beta".
-   Asness, Frazzini & Pedersen (2019), JFE — "Quality Minus Junk".
-   Black & Litterman (1992), *Financial Analysts Journal* — BL model.
-   Ledoit & Wolf (2003, 2004) — shrinkage estimators for covariance.
-   Harris & Gurel (1986), JoF; Shleifer (1986), JoF — S&P index effect.
-   López de Prado (2018), *Advances in Financial Machine Learning*,
    Wiley.
-   Thorp, *A Man for All Markets* (2017).
-   Zuckerman, *The Man Who Solved the Market* (2019) — Renaissance.
-   SqueezeMetrics, "The Implied Order Book" white paper.
-   SpotGamma, public research notes on dealer positioning.
-   tastytrade Research, ongoing short-premium studies (tastylive.com).
-   MSCI, *USA Momentum Index Methodology*; iShares MTUM / QUAL / USMV
    fact sheets.

*End of document.*
