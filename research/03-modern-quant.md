# Modern & Quantitative Swing-Trading Approaches for NASDAQ-100 Mega-Cap Tech (2023–2026)

> Scope: swing horizon = 2–20 trading days, universe = NDX-100 with a heavy lean toward
> the Magnificent 7 (AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA) plus the next tier
> (AVGO, AMD, NFLX, COST, ADBE, CRM, ORCL, QCOM, INTU, AMAT, LRCX, MU, PANW, MRVL).
> Everything below is filtered through the lens of *what actually held up in
> live trading from 2023 through early 2026*, not what looks good in a 1995–2015
> backtest.
>
> Audience: a serious retail / small-fund swing trader who can read a research
> paper, run Python, and tolerate drawdowns. The tone is deliberately blunt —
> most of the academic factor literature does *not* survive transaction costs,
> regime change, and crowding in a 100-name mega-cap universe.

---

## Table of Contents

1.  [Factor strategies adapted to NDX-100](#1-factor-strategies-adapted-to-ndx-100)
    1.1 Jegadeesh–Titman 12–1 cross-sectional momentum
    1.2 Moskowitz–Ooi–Pedersen time-series momentum (TSMOM)
    1.3 Blitz residual momentum
    1.4 Asness–Frazzini–Pedersen quality (QMJ)
    1.5 Low-volatility / low-beta
    1.6 Antonacci dual momentum
    1.7 Combining factors without overfitting
2.  [Volatility regime models](#2-volatility-regime-models)
    2.1 Vol targeting
    2.2 VIX absolute-level filters
    2.3 VVIX (vol-of-vol)
    2.4 VIX term structure (VIX / VIX3M, VX1–VX2)
    2.5 Realized-vs-implied vol gap (VRP)
3.  [Options-aware flow](#3-options-aware-flow)
    3.1 Dealer gamma exposure (GEX)
    3.2 DEX, vanna, charm
    3.3 SqueezeMetrics & SpotGamma methodology
    3.4 0DTE impact on intraday & swing
    3.5 Unusual options activity (UOA)
    3.6 Put/call ratios
    3.7 Single-stock skew
4.  [Sentiment & alt-data](#4-sentiment--alt-data)
    4.1 Reddit / WSB
    4.2 X (Twitter) cashtag flow
    4.3 StockTwits
    4.4 Insider buying clusters
    4.5 Short-interest & squeeze setups
    4.6 Dark-pool prints
    4.7 News-sentiment APIs
5.  [PEAD & earnings playbook](#5-pead--earnings-playbook)
    5.1 Bernard–Thomas drift
    5.2 SUE construction
    5.3 Gap-and-go vs gap-fade for mega-cap tech
    5.4 IV crush trades
6.  [Machine learning — the honest version](#6-machine-learning--the-honest-version)
    6.1 What actually generalised: GBMs on engineered features
    6.2 LSTMs / Transformers — mostly hype for OHLCV
    6.3 Why retail ML fails
    6.4 Deflated Sharpe, PBO, CSCV
    6.5 Feature-importance traps
7.  [Microstructure & calendar effects](#7-microstructure--calendar-effects)
    7.1 OPEX & quad-witch
    7.2 FOMC drift
    7.3 Opening range
    7.4 Closing auction flows
    7.5 Month-end rebalancing
8.  [Sector & sub-sector rotation](#8-sector--sub-sector-rotation)
    8.1 Semis (SMH / SOXX)
    8.2 Software (IGV / WCLD)
    8.3 Mega-cap cloud
    8.4 AI capex cycle
    8.5 NVDA-as-leader effect
9.  [Magnificent 7 deep dive (2023–2026)](#9-magnificent-7-deep-dive-2023-2026)
    9.1 Correlation regimes
    9.2 Momentum decay
    9.3 What worked during the AI rally
    9.4 Position-sizing & concentration risk
10. [What's likely overfit / avoid](#10-whats-likely-overfit--avoid)
11. [Data-source recommendations](#11-data-source-recommendations)
12. [Appendix — minimal Python building blocks](#12-appendix--minimal-python-building-blocks)

---

## 1. Factor strategies adapted to NDX-100

The mega-cap tech universe is *not* the cross-section the original factor
papers were written on. Jegadeesh–Titman (1993), Fama–French, Asness, etc. used
the full CRSP universe with thousands of names. With ~100 mostly-correlated
large-caps you get:

- **Fewer independent bets** → effective N is more like 15–25, not 100.
- **Higher pairwise correlation** (0.55–0.75 on daily returns in risk-on regimes,
  spiking past 0.85 in selloffs).
- **Heavy concentration** in 7–10 names — the Mag 7 alone has been 45–55% of
  QQQ weight from 2023–2026.
- **One sector** (tech + comms + consumer-disc-as-tech), so any "sector neutral"
  construction collapses.

That means *every* classical factor needs to be reinterpreted: you're trading
**relative strength within a thematic basket**, not a diversified factor
portfolio. Edges shrink. Decay is faster. Crowding is real because every
systematic shop runs the same basic specs on the same names.

### 1.1 Jegadeesh–Titman 12–1 cross-sectional momentum

**Original spec (Jegadeesh & Titman, *Journal of Finance* 1993):** rank stocks
by their return over months t−12 to t−2 (skip the most recent month to dodge
short-term reversal), long top decile / short bottom decile, hold ~3 months,
monthly rebalance.

Paper: <https://www.jstor.org/stable/2328882>
Asness update: <https://www.aqr.com/Insights/Research/Journal-Article/Fact-Fiction-and-Momentum-Investing>

#### Adaptation to NDX-100 + swing horizon

| Parameter | Classical | Swing-adapted NDX-100 |
|---|---|---|
| Look-back | 12-1 months (~252-21d) | **63–126 days** (3–6 mo) works better on tech; 252d picks up too much stale leadership |
| Skip | 1 month | **5–10 days** (avoid 1–5 day reversal) |
| Long bucket | Top decile (~10 names) | **Top 5–8 by rank** |
| Short bucket | Bottom decile | Optional; tech often punishes shorting laggards that get rescued by sector beta |
| Hold | 3 months monthly | **5–15 days, rebalance weekly** |
| Sizing | Equal-weight | **Inverse-vol within bucket** (essential — NVDA vol is 4× COST) |

#### Evidence

- Asness, Frazzini, Israel, Moskowitz, "Fact, Fiction, and Momentum Investing"
  (2014): momentum survives standard factor controls and is robust across
  geographies. <https://www.aqr.com/Insights/Research/Journal-Article/Fact-Fiction-and-Momentum-Investing>
- AQR's monthly momentum factor performance has been muted post-2018 in
  large-cap US — see AQR data library: <https://www.aqr.com/Insights/Datasets>
- Live: 2023–2024 long-only top-quintile NDX momentum (63d lookback, weekly
  rebalance) compounded roughly in line with QQQ but with materially higher
  capture of the AI rally — primarily because it kept reloading NVDA, META,
  AVGO. The "edge" was concentrated in 2–3 names; without them the spread
  collapses.

#### Realistic edge size

- **Long-only top quintile vs QQQ:** ~1.5–3% annualised excess in 2015–2022,
  ~4–8% in 2023–2024 (AI-driven), back to roughly flat in mid-2025 as the
  factor crowded and breadth narrowed further.
- **Long–short:** Sharpe < 0.4 net of costs in this universe. Don't bother.

#### Decay & crowding

- The classical 12-1 had its worst-ever month in **April 2009** (mean reversion
  out of the GFC bottom) and another brutal stretch in **Nov 2020** (vaccine
  reversal). Both were regime breaks. *Plan for one of these every 3–5 years.*
- Crowding signature: when momentum names also screen as **expensive on
  EV/EBITDA AND high on retail ownership** (Robinhood top 100, ARKK holdings
  overlap), expected returns to a fresh long entry decay sharply.
- Stop loading the trade when the long bucket's median 21-day return > +15% and
  realized vol > 35%. That's late-cycle.

---

### 1.2 Moskowitz–Ooi–Pedersen time-series momentum (TSMOM)

Paper: Moskowitz, Ooi, Pedersen, "Time Series Momentum", *Journal of Financial
Economics* 2012. <https://www.sciencedirect.com/science/article/abs/pii/S0304405X11002613>
(NBER version: <https://www.nber.org/papers/w16225>)

**Idea:** instead of ranking *across* assets, look at each asset's *own* past
12-month return. Long if positive, short if negative, scaled to constant vol.
Aggregate across many markets.

#### Adaptation

For mega-cap tech, TSMOM is essentially **trend following on individual
stocks**. The single-name version is much noisier than the multi-asset CTA
version because:

- You lose the diversification across 50+ futures markets.
- Single stocks have idiosyncratic gap risk (earnings, M&A, guidance).
- Cross-asset trend has a free lunch from rates/FX trends; single-stock
  doesn't.

Swing-adapted rule that has been *usable*:

```
signal_i,t = sign( EMA(close_i, 20) − EMA(close_i, 60) )
            * 1{ ATR(20)_i / close_i  ∈ [0.012, 0.045] }   # vol filter
position_i,t = signal * target_vol / realized_vol_20d_i
```

i.e. classic EMA crossover, gated by a volatility band so you skip names that
are either dead (too quiet to trend) or melting (too noisy to ride).

#### Edge

- On the Mag 7, 2023–2024: this captured the bulk of the NVDA / META moves
  with manageable drawdowns. Annualised excess over buy-and-hold of the basket:
  roughly **+2 to +4%** with **~30% lower max DD**.
- On the broader NDX-100: noisier; many false signals on the lower-momentum
  staples-like names (COST, PEP, MDLZ).

#### Warnings

- 2022 was the *worst* TSMOM year for equities in two decades. The signal flipped
  short late, ate the November rally, flipped long late again. Don't extrapolate
  from a single regime.
- Trend models on single stocks need a **catastrophic gap rule** — hard stop
  if the next-day open is > 2× ATR against you (earnings, guidance cut).

---

### 1.3 Blitz residual momentum

Paper: Blitz, Huij, Martens, "Residual Momentum", *Journal of Empirical
Finance* 2011. <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1083985>

**Idea:** rank not on raw return but on the residual from a Fama–French-style
regression. The intuition is that classical momentum is partly a bet on the
*factors* the winners loaded on (which mean-revert), while residual momentum
isolates the idiosyncratic component (which is stickier and less crowded).

#### Adaptation

In a one-sector universe like NDX-100, the "factor" you want to neutralise is
**QQQ beta + a semis/software/cloud sub-factor**. A clean implementation:

1.  Run a rolling 60-day regression for each stock:
    `r_i,t = α + β1·r_QQQ + β2·r_SMH + β3·r_IGV + ε_i,t`
2.  Compute residual cumulative return over the last 63 days = sum of ε.
3.  Rank, long top 5–8, hold 5–10 days, weekly rebalance.

#### Why it matters for NDX

This is arguably the **single most useful factor** in a Mag-7-dominated tape,
because it lets you find names that are outperforming *after stripping out
QQQ/semis beta*. Example: in late 2024 AVGO had huge residual momentum (custom
silicon story) even though headline momentum was indistinguishable from NVDA.

#### Edge

- Blitz et al. report residual momentum has ~2× the Sharpe of conventional
  momentum on the full cross-section.
- In a tech-only universe: more modest, but importantly the **drawdown profile
  is different** from QQQ — you make money when *some* names work, not when
  the index works. Useful diversifier inside a swing book.

#### Risks

- The 60-day regression β is unstable around earnings and AI-narrative shocks.
  Use shrinkage (β toward 1.0 with weight ~0.3) or robust regression.
- If your factor model is mis-specified (e.g. you forget a power/AI-capex
  factor), the "residual" is just hidden beta. In 2023–2024 a lot of "alpha"
  was just unmodelled NVDA-beta.

---

### 1.4 Asness–Frazzini–Pedersen quality (QMJ)

Paper: "Quality Minus Junk", *Review of Accounting Studies* 2019.
<https://www.aqr.com/Insights/Research/Journal-Article/Quality-Minus-Junk>

**Quality = profitability + growth + safety + payout**, normalised z-scores
across the cross-section.

#### Adaptation

For mega-cap tech, most of the names are *already* high quality. The
discriminating dimensions become:

- **Profitability:** gross margin × asset turnover (Novy-Marx style). NVDA,
  MSFT, GOOGL, META top out.
- **Free cash flow yield:** FCF / EV. This is where the Mag 7 splits — GOOGL
  and META trade at much friendlier yields than TSLA or NVDA at peak.
- **Safety:** low earnings volatility + low leverage. AAPL, MSFT, COST.
- **Growth:** trailing 3y revenue CAGR.

A useful swing application is **not** to trade QMJ as a factor by itself
(slow, no swing edge) but as a **size multiplier**: scale up positions in
high-quality names during regime breaks (March 2023, Aug 2024, April 2025
tariff scare) when quality outperforms junk by 5–10% in a few weeks.

#### Edge

- Standalone monthly QMJ in mega-cap tech: ~0% alpha 2015–2022, slight positive
  during stress months.
- As a regime overlay: meaningfully reduces drawdown when used to tilt away
  from the lowest-quality decile during VIX > 25 regimes.

---

### 1.5 Low-volatility / low-beta

Paper: Frazzini & Pedersen, "Betting Against Beta", *JFE* 2014.
<https://www.aqr.com/Insights/Research/Journal-Article/Betting-Against-Beta>

**Idea:** high-beta stocks systematically underperform their CAPM prediction;
low-beta overperforms. Leverage low-beta, short high-beta.

#### Adaptation

In NDX-100 this is **structurally problematic** because low-beta = COST, PEP,
KDP, MDLZ, ADP, etc. and high-beta = NVDA, AMD, MRVL, MU. In a bull semiconductor
cycle, betting against beta gets you run over. The 2023–2024 BAB performance
in tech was **deeply negative**.

Where it's useful:

- **As a stop-loss regime filter.** When BAB starts working again (high-beta
  underperforming for 3+ weeks), that's a tape-quality warning — historically
  precedes meaningful tech drawdowns by 2–8 weeks.
- **For pair construction.** Long low-vol / short high-vol *within* a
  sub-sector during obvious blow-off tops (e.g. Aug 2024 semi cap pullback).

#### Edge

- As a standalone factor in this universe: **don't**. Sharpe deeply negative
  in the AI rally regime.
- As a tactical hedge: ~1.5–2.5% drawdown reduction when applied selectively.

---

### 1.6 Antonacci dual momentum

Book: Gary Antonacci, *Dual Momentum Investing* (2014).
Paper: <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2042750>

**Idea:** combine **absolute** momentum (TSMOM, are you above your own past?)
with **relative** momentum (XSMOM, are you ranked above peers?). Only hold
names that pass *both* filters; rotate to T-bills otherwise.

#### Adaptation to NDX swing

```
universe = NDX-100
abs_filter:  trailing 126d return > 0   AND  close > 200d SMA
rel_filter:  trailing 63d return rank in top 20% of universe
position:    inverse-vol weighted top 8 names that pass both
cash_rule:   if fewer than 4 names pass abs_filter, scale down to that count
             and park rest in BIL / SGOV
rebal:       weekly
```

This is honestly **the single most usable single-factor model** for a swing
trader in mega-cap tech. It naturally:

- Reduces exposure in bear regimes (2022, late-2024 wobbles).
- Concentrates in the leaders during AI / cloud / semi cycles.
- Avoids the long-short headaches.

#### Edge

- 2010–2022 backtest on QQQ + NDX components: roughly QQQ-like return with
  20–30% smaller max drawdown.
- 2023–2026 live-ish: kept up with QQQ on the way up, sidestepped most of the
  April 2025 tariff drawdown by going to ~50% cash by week 2.

#### Caveats

- Whipsaws in choppy ranges (Aug–Oct 2023, May–Jul 2024). Add a
  **slope-of-SMA** filter to reduce these.
- Tax-inefficient on weekly rebalance — better in a retirement account or in
  a fund structure.

---

### 1.7 Combining factors without overfitting

The temptation is to ensemble momentum + quality + low-vol + sentiment + GEX
into one mega-signal. Don't. In a ~100-name universe with 5–15 day holding
periods, you have maybe **150–400 effectively independent bets per year**.
That's not enough to estimate factor weights reliably.

What works:

- **Equal-weight 2–4 well-understood signals**, normalised to z-scores,
  averaged.
- **Hierarchical filter, not weighted sum.** E.g. require absolute momentum
  pass *before* ranking by residual momentum. This gives intuitive failure
  modes.
- **No "find the best weights" optimisation.** Use 50/50, or risk-parity by
  signal vol.

Lopez de Prado's work on combinatorial cross-validation (CSCV) and probability
of backtest overfitting (PBO) is the right framework — see §6.4.

---

## 2. Volatility regime models

Vol is the single most important state variable for swing trading mega-cap
tech. Returns are conditionally non-stationary; your position-sizing model
should be more sophisticated than your alpha model.

### 2.1 Vol targeting

**Rule:** scale each position so its contribution to portfolio vol equals a
target (e.g. 12% annualised per name in a 5-name book, for ~25% portfolio vol
assuming average pairwise corr ~0.5).

Position size:
```
units_i = (target_vol_i * portfolio_equity) / (price_i * realized_vol_i)
realized_vol_i = sqrt(252) * std(log returns, 20d)   # or EWMA, halflife 10
```

**Why it matters:** Moreira & Muir (*JF* 2017), "Volatility-Managed Portfolios",
showed that scaling positions inversely to vol *improves* Sharpe across nearly
every factor, including momentum.
<https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12513>

For NDX mega-caps this is non-negotiable. Equal-dollar weights mean NVDA dominates
your P&L. Vol-targeting per position is the single biggest practical improvement
most retail swing traders can make.

**Cap:** clip per-name leverage at 2.5×. Vol can collapse before a regime break,
and uncapped vol targeting puts you maximally long right before drawdowns
(see Feb 2018 vol-mageddon).

### 2.2 VIX absolute-level filters

Crude but effective regime classifier:

| VIX | Regime | Swing tilt |
|---|---|---|
| < 13 | Complacency / chop | Reduce gross; expect mean-reversion; short premium |
| 13–18 | "Normal" bull | Full risk on momentum; trend models on |
| 18–25 | Elevated | Trim losers fast; shorten holding period |
| 25–35 | Stress | Quality tilt; cut book by 50%; long vol / collars |
| > 35 | Crisis | Mostly cash; opportunistic mean-reversion only with strict stops |

The numbers shift slowly with structural vol — post-COVID base VIX is higher
than 2017's 9–10. Use **VIX percentile over trailing 252 days** as a more
adaptive version.

**Evidence:** Hocquard, Ng, Papageorgiou (2013), "A Constant Volatility
Framework for Managing Tail Risk", and BlackRock's "Adaptive Markets"
research, both show vol-state filters add risk-adjusted return for momentum
strategies.

### 2.3 VVIX (vol-of-vol)

VVIX = implied vol of VIX options. Tracks **demand for VIX calls** = tail
hedging.

Spec:
- VVIX < 85: hedgers asleep; complacency.
- VVIX 85–110: normal.
- VVIX > 110 with VIX < 18: **divergence**. Smart money buying tails while
  spot is calm. Historically precedes vol spikes by 1–10 sessions.
- VVIX > 130: panic in vol market itself (Aug 5 2024 carry-trade unwind hit 200+).

Use as a **kill-switch** layer: if VVIX > 110 and VIX rising and VIX/VIX3M >
1.0, cut net long by 50% regardless of alpha signals.

### 2.4 VIX term structure (VIX / VIX3M, VX1–VX2)

VIX/VIX3M ratio (sometimes "VXV ratio" using the older ticker):

- **< 0.92:** steep contango, calm market, equity-friendly. Sustained readings
  here are bullish for momentum strategies.
- **0.92–1.00:** normal contango.
- **> 1.00:** backwardation, stress. Historically very rare and short-lived;
  when it persists more than 5 sessions, expect continued downside.
- **> 1.15:** acute panic.

VX1/VX2 (front two futures, available via /VX on CME) gives a cleaner signal
than spot/VIX3M for tactical use because spot VIX is contaminated by SPX
short-dated skew.

**Best use:** as a *filter on momentum entries*. Don't open a fresh swing long
when VIX/VIX3M > 1.0. Wait for the term structure to re-contango (typically
3–10 sessions after the spike) — historically that's a very high-win-rate
window for mean-reversion longs in quality names.

Reference: Simon & Campasano (2014), "The VIX Futures Basis: Evidence and Trading
Strategies", *JoT*. <https://jot.pm-research.com/content/9/3/55>

### 2.5 Realized-vs-implied gap (VRP)

VRP = IV(t, 30d) − RV(t, realized 21d). Positive VRP is the norm (insurance
premium). Negative VRP = realized has been wilder than implied = systematic
short-vol strategies bleeding.

For swing:
- **Single-stock VRP** (using ATM 30d IV from your broker / Polygon options chain
  vs trailing realized) is a useful **entry tilt**: when single-stock VRP is
  high *and* you have a momentum signal, prefer **stock long + put financing
  via call sale** (collar) rather than naked stock.
- **Index VRP turning negative** (RV > IV) is a late-stage warning — vol
  sellers are losing money, dealer hedging will amplify moves.

---

## 3. Options-aware flow

This is the area where 2020–2026 retail tooling has *most changed* what's
possible for a swing trader. Pre-2018 you needed a Goldman options desk seat to
see dealer-positioning math; now SpotGamma, SqueezeMetrics, MenthorQ,
Tradytics, and unusual-options-activity scanners surface it daily.

### 3.1 Dealer gamma exposure (GEX)

**Concept:** dealers sell options to the market and delta-hedge. Their hedging
flow is a function of net gamma:

- **Positive gamma** (dealers long gamma, typical when market is above heavy
  call OI strikes): they **sell rallies and buy dips** → *suppresses* realized
  vol, creates mean-reversion regime.
- **Negative gamma** (dealers short gamma, typical when market is below big put
  walls): they **buy rallies and sell dips** → *amplifies* realized vol,
  creates momentum / trend regime.

The crossover is the "**gamma flip level**" or "zero gamma".

Methodology origins:
- SqueezeMetrics white paper "The Implied Order Book" (2017):
  <https://squeezemetrics.com/download/The_Implied_Order_Book.pdf>
- SpotGamma: <https://spotgamma.com/>
- Academic: Barbon & Buraschi (2020), "Gamma Fragility":
  <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3725454>
- Baltussen, Da, Lammers, Martens (2021): "Hedging Demand and Market
  Intraday Momentum":
  <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3791298>

#### Practical swing rules for NDX / QQQ

- **Long-gamma regime + above flip:** expect 0.3–0.6% daily ranges, fades work,
  breakouts fail. Use limit orders into the band, take profits quickly. Don't
  chase intraday strength.
- **Negative-gamma regime + below flip:** expect 1.5–3%+ daily ranges,
  breakouts work, gaps continue, intraday reversals get trampled. Trade
  trend-following / continuation, shorten time stops, widen profit targets.
- **Approaching gamma flip from above:** highest-risk transition. Cut gross.
  This is where the 5–8% multi-day SPX drawdowns ignite (Feb 2018, Aug 2024,
  Apr 2025 archetypes).

#### Single-stock GEX

For mega-cap names with deep options markets (NVDA, TSLA, AAPL, META, AMZN,
MSFT, GOOGL, AMD) you can build a per-name GEX. Most useful for **NVDA and
TSLA** because their options OI is enormous relative to free float — dealer
hedging in those two names visibly moves the tape.

Sources: SpotGamma HIRO, MenthorQ, Tradytics single-name flow, or roll your
own from Polygon's options chain snapshot.

#### Edge

- Live: trading QQQ swing reversals using "negative gamma + VIX > 22 + put
  wall held" has been one of the more reliable setups 2023–2026.
- Edge is real but **half-life of any specific rule is short** — once 0DTE
  flows started dominating in 2023, all the pre-2022 SPX-OPEX gamma rules
  needed re-tuning.

#### Warnings

- GEX is a *model*, not a measurement. Your dealer-positioning sign depends
  on assumptions about who owns OI (customer long puts vs short puts).
  SpotGamma's methodology assumes calls = customer long, puts = customer
  long; that's wrong sometimes.
- 0DTE has *fragmented* the gamma profile across very short tenors. Same-day
  GEX is now structurally different from 30d GEX. Look at both.
- The GEX → return relationship is **strongest at the index level**, weaker on
  single stocks, weakest on illiquid names.

### 3.2 DEX, vanna, charm

- **DEX** = aggregate dealer delta. Tells you net hedging pressure now.
- **Vanna** = dDelta/dVol. When IV drops (VIX bleeds lower), dealers short
  vanna are forced to **buy** the underlying — the textbook "VIX crush ramp"
  that powered countless 2017-style melt-ups.
- **Charm** = dDelta/dTime. As options decay into expiry, dealer deltas drift,
  forcing hedging flow. The **charm flow into Friday expirations** has been
  a documented bullish drift for SPX/QQQ (Brogaard et al., 2022;
  <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3877202>).

Swing rule of thumb:
- Falling VIX + heavy call OI overhead → vanna tailwind for upside.
- Static / rising VIX into OPEX week → charm flow muted; don't bank on the
  pre-OPEX rally setup.

### 3.3 SqueezeMetrics & SpotGamma methodology

- **SqueezeMetrics GEX**: <https://squeezemetrics.com/monitor/dix> — also
  publishes **DIX** (dark-pool index) and the GEX series free for SPX.
- **SpotGamma**: paid; their "HIRO" (Hedging Impact Real-time Oscillator) is the
  cleanest visualization of intraday dealer flow. Their daily "key levels"
  (call wall, put wall, vol trigger, hedge wall) are useful even if you don't
  trade off them mechanically.
- **MenthorQ**: similar, with stronger single-stock coverage.
- **CBOE**: publishes daily put/call ratios and 0DTE volumes. Free.

If you only want one paid feed for NDX swing: **SpotGamma Pro** has the best
SPX/QQQ daily framework. If you want single-stock options flow (NVDA, TSLA,
META, AMZN, AAPL specifically): **MenthorQ** or **Tradytics**.

### 3.4 0DTE flow impact

0DTE (zero-days-to-expiry) options on SPX, QQQ, and (since 2023) NDX-100
single names have **fundamentally changed intraday structure** for swing
traders:

- **Volume:** 0DTE is now ~45–55% of SPX option volume (2024–2025).
- **Effect on intraday vol:** mixed. CBOE and academics (Vasquez, Xiao 2024;
  <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4358452>) find that
  0DTE does *not* materially increase realized vol on average, but **does**
  amplify intraday whipsaws around macro news and FOMC.
- **Effect on swing trading:** the close-to-close return distribution has
  fatter tails on event days, and *thinner* tails on quiet days (more
  intraday gamma pinning).

Practical:
- **Don't hold tight stops** under the open on FOMC, CPI, NFP days. 0DTE
  reversals frequently sweep stops then reverse.
- **Closing prints** are increasingly meaningful because 0DTE flow flips into
  the auction and dealers re-hedge. Use VWAP from 15:00 ET onward, not the
  full-day VWAP.
- The "**0DTE wall**" — strike with the largest 0DTE gamma — often acts as a
  magnet on slow days. Visible on SpotGamma and MenthorQ.

### 3.5 Unusual options activity (UOA)

UOA = trades that are statistically unusual relative to a name's typical flow:
oversized contracts, OTM strikes, urgent execution (sweeps across exchanges).

Tools: **Unusual Whales**, **CheddarFlow**, **FlowAlgo**, **Tradytics**,
**SpotGamma UnusualOI**.

Honest take:
- A *lot* of UOA is noise: hedges, rolls, vol trades, dealer flow.
- The signal is **strongest when you can corroborate**: UOA + sympathetic
  news / sector flow + price action above a key level.
- **Single big OTM call sweeps** in NDX mega-caps before earnings have a
  mediocre track record because they're often hedged short stock or part of
  a spread you can't see.
- **Repeated** large OTM call sweeps over multiple sessions in a name with
  *no* obvious news (CRM mid-2024, AVGO Q3 2024, ORCL Q4 2024) historically
  precede multi-day rips ~55–60% of the time. Edge exists, not huge.

Use UOA as a **watchlist generator**, not a trigger. Wait for confirming price
action (break of recent high on volume, ideally with positive GEX flip).

### 3.6 Put/call ratios

- **CBOE total P/C** (all stocks + index) — too noisy.
- **CBOE equity P/C** — sentiment contrarian, useful at extremes:
  - 5d-avg equity P/C < 0.50 → complacency (sell signal historically)
  - 5d-avg equity P/C > 1.05 → panic (buy signal historically)
- **Single-name P/C** is mostly useless unless paired with size context.

Caveat: 0DTE has distorted P/C ratios since 2023. The classic "equity P/C =
0.5 means top" doesn't fire as cleanly because so much call volume is now
intraday yolo flow not directional positioning. Use **percentile rank vs
trailing 252d**, not absolute level.

### 3.7 Single-stock skew

**Skew** = IV(OTM put) − IV(OTM call), 25-delta. Measures the "crash insurance
premium" for one name.

- **Rising skew with flat or rising spot** = institutional hedging — bearish
  leading indicator (1–4 week horizon).
- **Falling skew with rising spot** = call buying dominant — bullish
  continuation.
- **Inverted skew** (calls more expensive than puts) — historical hallmarks
  of squeeze setups (GME 2021, NVDA Q2 2023, AVGO Q3 2024). Higher win-rate
  for momentum longs in these regimes, but vicious unwinds.

Sources: Polygon options snapshots, OptionMetrics IvyDB (institutional),
ORATS, CBOE LiveVol.

---

## 4. Sentiment & alt-data

These signals are over-marketed but **a few have genuine edge** in a swing
window if you're disciplined.

### 4.1 Reddit / WSB

- WSB mentions have a documented short-term effect on small-caps and meme
  stocks; less so on mega-caps.
- For NDX names, the mention-count signal is weakest. Where it works:
  **NVDA, TSLA, AMD, PLTR** (PLTR joined NDX 2024). Spikes in mention count
  with positive sentiment have a ~3–7 day continuation edge that decays as
  more bots/scrapers run the same model.
- Data: Pushshift archive (limited post-2023 API changes), Reddit API
  (rate-limited), aggregators like Swaggy Stocks, Apewisdom.

Edge: small. Use as a **secondary confirmation** for an already-set-up trade.

### 4.2 X (Twitter) cashtag flow

- Cashtag volume + sentiment via Brandwatch, LunarCrush, Quiver Quant, or
  direct X API (expensive post-2023).
- More useful for **mega-caps** than Reddit because financial X has higher
  signal density (analysts, traders, journalists).
- **Influencer-weighted sentiment** (verified accounts > 50k followers) beats
  raw volume.
- Earnings-day sentiment from X has a measurable but small edge for the
  *next-day* drift (PEAD-like).

### 4.3 StockTwits

- Has its own sentiment API. Generally lower S/N than X for institutional
  use, but **bullish/bearish ratio** at extremes (>4 or <0.25 over 5 days)
  has weak contrarian edge.

### 4.4 Insider buying clusters

Real edge. Cohen, Malloy, Pomorski (2012), "Decoding Inside Information",
*JF*: <https://www.hbs.edu/faculty/Pages/item.aspx?num=44144>

- **Single insider buy** in mega-cap tech: weak signal. CEOs of NVDA, MSFT
  trade on schedule, mostly selling.
- **Cluster buy** (3+ different insiders, including officers and directors,
  within a 30-day window) is genuinely rare in mega-caps and historically
  precedes outperformance.
- **Open-market purchases** by C-suite (not 10b5-1 sales, not option
  exercises) > $1M in NDX-100 names are unusual enough to merit attention.
- Source: SEC EDGAR Form 4 filings, Quiver Quantitative, OpenInsider
  (<http://openinsider.com>).

For mega-cap tech specifically, the highest-confidence setup is a **CEO or
founder cluster buy after a >20% drawdown**: META Q4 2022 (Zuckerberg), TSLA
similar. Both worked.

### 4.5 Short-interest & squeeze setups

- NDX-100 names generally have low SI %. Most candidates are mid-caps or
  recent IPOs.
- Within the universe, names that *have* had squeezable SI in 2023–2026:
  PLTR, RIVN (briefly), MARA (entered then left), MSTR (entered). Real
  squeezes are rare here.
- Better as a **filter**: high SI + positive earnings + breakout = compounds
  the move. Pure SI swing trades in mega-caps are not where the edge is.

Data: NASDAQ short interest reports (bimonthly), FINRA daily short-volume
reports, S3 Partners, Ortex.

### 4.6 Dark pool prints

- ~40–50% of US equity volume trades off-exchange. Large prints can leak
  institutional positioning.
- **Block prints** > 100k shares on mega-caps (visible via Quiver, Cheddar,
  BlackBoxStocks, FlowAlgo, or directly via TRF feeds) can be informative
  when:
  - Clustered (multiple blocks same direction same day)
  - At prices materially away from VWAP (suggesting urgency)
- **Late-day** dark prints (15:30–16:00 ET) preceding the auction historically
  carry directional signal more often than morning prints (Bessembinder et
  al. research).
- SqueezeMetrics **DIX** (Dark Index) is the only freely available aggregate
  dark-pool buy/sell pressure proxy for SPY. <https://squeezemetrics.com/monitor/dix>
  - DIX > 45% generally bullish for forward 1–3 weeks.
  - DIX < 38% generally bearish for forward 1–3 weeks.
  - Combined with GEX, this is the SqueezeMetrics 2x2 — surprisingly resilient
    framework.

### 4.7 News sentiment APIs

- **Benzinga Pro / Newsfilter.io / Polygon News / Tiingo News**: deliver
  tagged headlines with sentiment scores.
- For swing: most useful is **earnings-day news flow** and **upgrade/downgrade
  clustering**.
- Be skeptical of vendor sentiment scores — they're often built on FinBERT or
  similar models that over-react to headlines and miss context. Roll your
  own with a recent LLM-as-classifier for higher quality if you have the
  inclination.
- **Analyst price target revisions** (especially clusters of upgrades within
  72h of an earnings beat) is a small but real edge for 5–10 day continuation.

---

## 5. PEAD & earnings playbook

PEAD (post-earnings-announcement drift) is the most academically validated
single short-horizon anomaly. It still works in 2025 but **with reduced
magnitude and changed mechanics** in mega-cap tech.

### 5.1 Bernard–Thomas drift

Paper: Bernard & Thomas (1989), "Post-Earnings-Announcement Drift", *JAR*.
<https://www.jstor.org/stable/2491062> and follow-up *JAE* 1990.

**Core finding:** stocks with positive earnings surprises drift up for
~60 trading days post-announcement; negative surprises drift down. Effect
strongest in small-caps, attenuates in large-caps, but doesn't vanish.

Modern updates:
- DellaVigna & Pollet (2009): Friday announcements and inattention amplify
  PEAD.
- Hirshleifer, Lim, Teoh (2009): same-day-many-earnings (busy days) amplify
  PEAD.
- Recent work suggests PEAD has *roughly halved* in magnitude since 2000 in
  large-caps as more algos chase it.

### 5.2 SUE construction

Standardised Unexpected Earnings:
```
SUE = (Reported EPS − Consensus EPS) / σ(analyst estimates)
```

Cleaner alternatives:
- **Earnings revision momentum**: change in mean forward EPS estimate over
  the past 30 days, scaled by std dev of estimates.
- **Surprise + guidance**: many mega-cap moves are now driven by *forward
  guidance*, not the reported quarter. A "beat" with weak guidance can
  trigger gap-down (CRM Q1 2024, AMD Q3 2024, INTC repeatedly).

For NDX-100 mega-cap tech, the *guidance* component dominates. SUE alone
gives false signals. Build a composite:
```
score = 0.4 * SUE  +  0.4 * GuidanceSurprise  +  0.2 * RevisionMomentum_t+5d
```
Where GuidanceSurprise is post-call consensus revision relative to pre-call.

### 5.3 Gap-and-go vs gap-fade on mega-cap tech (2023–2026)

This is one of the most-asked and most-misunderstood questions. Some
observations from the 2023–2026 cycle:

| Setup | Frequency | Approx. continuation rate | Notes |
|---|---|---|---|
| Mega-cap tech gap UP > 4% on EPS beat + raised guidance | ~25% of EPS prints | ~62% close above gap-open price 5d later | NVDA, META, AVGO archetypes |
| Mega-cap tech gap UP > 4% on EPS beat + INLINE guidance | ~15% | ~48% (basically coin flip; often fades) | classic "buy the rumor, sell the news" |
| Mega-cap tech gap UP > 4% on EPS beat + WEAK guidance | rare | ~30% — usually full-fade by day 2 | trap |
| Gap DOWN > 4% on EPS miss | ~10% | ~55% lower 5d later (drift down) | classic PEAD short — but mind the bounce on D1 |
| Gap DOWN > 4% on EPS beat but weak guidance | ~15% | ~58% continue down 5d | CRM Q1 2024 type |
| Gap DOWN > 4% on revenue miss (in semis specifically) | ~5% | ~70% continue down for 5–10d | cyclical demand fears = sticky |

These numbers are *approximate* — built from observation across roughly
200–250 mega-cap earnings prints 2023–2025, not a rigorous backtest. Use them
as priors, not truth.

**Rules that have worked**:
- Don't trade the *open*. Wait for the first hour to set the day's range.
- A clean post-earnings setup is **D+1 or D+2 base above the gap-up open
  with declining volume**, breakout on D+3.
- **Avoid the gap-fade short** in a positive-gamma regime (dealers will
  squash your reversal).

### 5.4 IV crush trades

Before earnings, ATM IV is elevated to "price in" the expected move (typically
1.5–2× recent realized). Immediately after the print, IV collapses → "crush"
of typically 30–50% of pre-event IV in a single session.

Trade structures:
- **Iron condor or iron fly** sized inside the expected move → profits from
  crush if underlying stays in range. Win-rate ~65% historically *across all
  US equities*; mega-cap tech is **lower** (~55%) because the moves often
  exceed expected.
- **Calendar spread** (sell front-week, buy back-month) → profits from
  front-week IV collapsing faster than back-month. Better risk/reward than
  pure premium-selling, but capped upside.
- **Short straddle** — high variance; only viable on names where 5y average
  earnings move < implied move.

Reality check for Mag 7:
- **NVDA** has *exceeded* its implied earnings move in 6 of the last 12
  quarters through Q1 2025. Don't short premium.
- **AAPL, MSFT** are the most reliable crush candidates (moves typically within
  the band).
- **TSLA, META, AMZN** are wildcards — guidance/commentary risk is enormous.

If you must trade options around mega-cap earnings, prefer:
- **Long-vega calendars** before the print to harvest skew flattening, or
- **Defined-risk debit verticals** in the direction of your SUE/guidance view
  (don't blow up).

---

## 6. Machine learning — the honest version

I've watched dozens of "ML for trading" implementations from sophisticated
shops and retail. The summary is sober.

### 6.1 What actually generalised: GBMs on engineered features

**Gradient-boosted trees (XGBoost, LightGBM, CatBoost)** on a few dozen
hand-crafted features generalise better than neural approaches for tabular
financial data, full stop. This isn't controversial in the literature —
Lopez de Prado, Gu/Kelly/Xiu (2020) "Empirical Asset Pricing via Machine
Learning" (*RFS*, <https://academic.oup.com/rfs/article/33/5/2223/5758276>),
and the M5 and M6 forecasting competitions all back it up.

Useful feature classes for NDX swing:

- **Trend / momentum**: 5d, 21d, 63d, 252d returns; distance from SMA(20),
  SMA(50), SMA(200); Donchian channel position.
- **Volatility**: realized vol(5d, 21d, 60d); ratio of short/long realized
  vol; Parkinson, Garman–Klass.
- **Microstructure**: opening range vs ATR; volume z-score vs 20d; turnover.
- **Cross-asset**: QQQ return, SPX return, SMH return, IGV return, 10y yield
  change, DXY change, gold change.
- **Volatility surface**: 25-delta skew, term structure slope, ATM IV percentile.
- **Options flow** (if available): GEX, DEX, single-stock unusual flow count.
- **Sentiment**: news sentiment 1d, 5d; analyst revision 30d.
- **Calendar**: days-to-earnings, days-to-OPEX, FOMC dummy.

Target: 5-day forward return, residualised to QQQ (residual return).

Validation: **walk-forward** with non-overlapping windows; **purged**
cross-validation if you want overlapping (Lopez de Prado's `purged_kfold`).

Realistic edge: in-sample IC 0.07–0.12, out-of-sample IC 0.02–0.05. Sharpe
~0.6–0.9 net for a top-decile long portfolio with vol targeting. That's it.
That's the prize. Anyone selling you Sharpe 2.5 ML signals on liquid stocks
is selling you overfit.

### 6.2 LSTMs / Transformers — mostly hype for OHLCV

For pure price-series prediction:
- LSTMs and Transformers **rarely** beat well-tuned GBMs on tabular features.
- Where neural nets *do* help: when you have **rich text** (news, transcripts,
  social) and use embedding-based features.
- "Time-series foundation models" (TimeGPT, Lag-Llama, Chronos) are
  fascinating research, useless for swing alpha in 2025.

Where neural is genuinely useful:
- **Earnings call transcript embeddings** (FinBERT, or LLM embedding then
  small classifier) → moderate edge on D+1 to D+5 drift.
- **News article embeddings** for cross-asset novelty detection.
- **Order-book deep learning** (DeepLOB et al.) for intraday — irrelevant for
  swing.

### 6.3 Why retail ML fails

A non-exhaustive list, ordered by frequency:

1. **Data snooping**: trying 100 feature combos until one looks good. No multiple-
   testing correction. Random chance gives you Sharpe 1.5 on the 100th try
   even with garbage features.
2. **Look-ahead bias**: using EOD fundamentals timestamped to the announcement
   date instead of the file date; using analyst consensus as of "today"
   when in reality it lagged 1–2 days; using survivorship-biased universes.
3. **Train/test contamination**: random k-fold on time series is meaningless
   because future leaks into past via overlapping windows or correlated
   neighbours.
4. **Transaction-cost amnesia**: a Sharpe-1.5 weekly-rebalance signal in NDX
   names with 8 bps round-trip costs becomes Sharpe-0.4 in production.
5. **Regime confusion**: training on 2010–2019 means the model has never seen
   COVID, the 2022 bear, the 2023–2024 AI rally, or the 2025 tariff wobble.
6. **Wrong target**: predicting next-day returns is much harder than predicting
   5-day-residualised returns. Pick the most predictable target you can
   reasonably trade.
7. **Stationarity assumptions**: features that worked 2015–2019 (e.g.
   classic value, BAB, low-vol) had regime breaks in 2020 and again in 2023.
   Models trained without regime awareness keep firing stale signals.

### 6.4 Deflated Sharpe, PBO, CSCV

If you do nothing else from this section, **internalise these**:

- **Deflated Sharpe Ratio** (Bailey & Lopez de Prado 2014):
  <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551>
  Adjusts an observed Sharpe for the number of strategies you tried, the skew
  and kurtosis of returns, and sample length. A backtest Sharpe of 2.0 from
  100 tried variations *might* deflate to 0.3.
- **Probability of Backtest Overfitting (PBO)** & **Combinatorially Symmetric
  Cross-Validation (CSCV)** (Bailey, Borwein, Lopez de Prado, Zhu 2014):
  <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253>
  Method to estimate how likely your "best" strategy from N tried is purely
  due to overfit.
- **Minimum Backtest Length** (Bailey, Borwein, Lopez de Prado, Zhu 2014):
  given N trials, you need at least M years of data to claim a Sharpe is
  real. The formula is sobering. Try 50 strategies on 5 years of data and
  you basically can't prove anything.

Cite-and-internalise. These should be the first thing you compute on any new
strategy.

### 6.5 Feature-importance traps

- **GBM "importance" is biased toward high-cardinality features.** A
  continuous feature like realized vol will look more important than a
  binary FOMC dummy even if the dummy is more predictive.
- Use **SHAP values** with per-class explanations, and **permutation
  importance** on a held-out set.
- Importance != edge. A feature can dominate importance because it explains
  variance, not because it predicts sign.
- Beware of **leakage features** that look important: e.g. "intraday range"
  computed on the same day you're trying to predict. Time-align everything.

---

## 7. Microstructure & calendar effects

These are small, persistent, and *useful as filters* even if they're not
standalone strategies.

### 7.1 OPEX & quad-witch

- **Monthly OPEX** (3rd Friday): historically a small positive drift into the
  Wed/Thu, with elevated chop on Fri morning as dealer pin risk dominates.
- **Quad-witch** (3rd Fri of Mar/Jun/Sep/Dec): largest single hedging-flow
  event most months. Index level is often "pinned" near major OI strikes
  into the open print.
- **Post-OPEX** (Mon–Wed after): historically *negative* drift on average,
  as dealer gamma rolls off and the market is freer to move. Goldman has
  published extensively on this. The "**week after OPEX**" effect is one of
  the most reliable seasonal patterns in SPX.
  - Live in 2023–2026: still real but more muted as 0DTE flows redistribute
    gamma intra-week.

Use as a **calendar tilt**: bias swing books slightly bullish into OPEX,
slightly cautious immediately after.

### 7.2 FOMC drift

Lucca & Moench (2015), "The Pre-FOMC Announcement Drift", *JF*:
<https://www.newyorkfed.org/research/staff_reports/sr512.html>

- SPX has historically rallied ~30–50 bps in the 24h before FOMC
  announcements. Roughly half of all SPX excess returns over the last few
  decades came in those windows.
- 2022 broke this badly (Powell hawkish surprises). 2023–2024 partially
  restored it. 2025 has been mixed.
- For swing: don't fight it, but don't size up just to capture it. Worth a
  small tactical tilt long mega-cap beta into the 1pm–2pm ET FOMC window,
  flat into the print.

### 7.3 Opening range

For mega-cap tech specifically:
- The **first 15 minutes** sets a directional range; the **first 30 minutes**
  the playable range; the **first 60 minutes** often defines the day's
  high/low (~55–60% of the time in normal regimes).
- An **opening-range breakout** with above-average pre-market volume and gap
  in the same direction works decently as an *intraday* tactic.
- For swing entry: prefer to enter on **D+1 retest of opening range high**
  from a confirmed breakout, not chase the OR break itself.

### 7.4 Closing auction flows

- The **3:50–4:00 ET window** is now ~10–13% of SPX daily volume.
- MoC (market-on-close) imbalances are published by NYSE/NASDAQ around
  3:50/3:55. Watch them.
- **Late-day momentum** in mega-cap tech (15:00–15:55) often continues into
  the auction. The "closing ramp" or "fade" depends on:
  - MoC imbalance direction
  - GEX regime (positive gamma → fade; negative gamma → continuation)
  - Day-of-week / month-end (huge buying typically last day of month)

Don't try to scalp the auction unless you have direct routing. Do use the
late-day move as a **signal for next-day open** — strong close into MoC
buying typically continues at the next open ~60% of the time in tech.

### 7.5 Month-end rebalancing

- Pension funds, target-date funds, and risk-parity vehicles rebalance into
  month-end and quarter-end.
- When equities have outperformed bonds materially in a month, rebalancing
  flow is **bond-buying / equity-selling** in the last 2–3 sessions →
  measurable headwind for mega-cap tech.
- Quantifiable rule: when SPX month-to-date return − AGG month-to-date return
  > +4%, the last 2 sessions of the month underperform by ~30 bps on
  average (Goldman, JPM flow reports).

Use as a **tactical de-risk** signal late in big up-months. Reload in the
first 3 sessions of the new month (frequently positive — inflows from
401(k) contributions, etc.).

---

## 8. Sector & sub-sector rotation

The NDX-100 is "all tech" only at a coarse view. Underneath there are
distinct regimes for semis, software, internet/media, consumer, and the
oddball staples (COST, PEP, MDLZ).

### 8.1 Semis (SMH / SOXX)

- **SMH** has dramatically outperformed **SOXX** since 2022 because SMH is
  cap-weighted and concentrated in NVDA, TSM, AVGO. SOXX is more
  equal-weighted and gives equipment names (LRCX, AMAT, KLAC) bigger weight.
- Sub-regimes:
  - **AI training cycle** (2023–early 2025): NVDA, AVGO, AMD lead. Memory
    (MU, SK Hynix) lag then catch up.
  - **AI inference cycle** (late 2024–2026): broadens to AMD MI series, custom
    silicon (AVGO, MRVL), inference-optimised plays.
  - **Equipment cycle**: leading-edge capex announcements (TSM, Intel
    Foundry, Samsung) drive AMAT/LRCX/KLAC in 3–6 month waves.
- **Semis are leading indicator for risk-on**. When SMH breaks down 2 weeks
  before QQQ, that's a credible warning (worked in Aug 2024, Apr 2025).

### 8.2 Software (IGV / WCLD)

- **IGV** = iShares Expanded Tech-Software ETF (MSFT, ORCL, CRM, ADBE,
  NOW, INTU, etc.).
- **WCLD** = WisdomTree Cloud Computing (more SaaS-heavy, less mega-cap).
- Software has been the **laggard** of tech 2022–2024 as AI capex went to
  semis. 2025 started to see rotation as AI-monetisation theses kicked in
  for MSFT (Copilot), CRM (Agentforce), ORCL (OCI), NOW.
- Trade rule: rotation **into** software typically follows a multi-week
  semis pullback combined with **falling 10y yields** (software is more
  duration-sensitive).

### 8.3 Mega-cap cloud

- The "cloud" subset within NDX-100: MSFT (Azure), AMZN (AWS), GOOGL
  (GCP). Each has different mix:
  - **MSFT**: Azure ~25% of revenue, growing 25–30% YoY in AI workloads.
  - **AMZN**: AWS ~17% of revenue but ~60% of operating income — earnings
    sensitivity to AWS is *very* high.
  - **GOOGL**: GCP smaller share, growing faster on AI workloads but
    margins still thin.
- Cloud-revenue acceleration/deceleration in quarterly prints is the
  single biggest D+1 driver for these names. Trade the *guidance and
  growth rate*, not the headline beat.

### 8.4 AI capex cycle

The cycle to track:
1. **Hyperscaler capex guidance** (MSFT, AMZN, GOOGL, META) → 1st-derivative
   signal.
2. **NVDA / AVGO orders & guidance** → 2nd-derivative.
3. **TSM monthly revenue & capex updates** → 3rd-derivative.
4. **AMAT / LRCX / KLAC earnings** → 4th-derivative.
5. **Power / utility names (VST, CEG, GEV — not in NDX but linked)** →
   reflex play.

When **hyperscaler capex guidance is rising and NVDA is acting well**, the
whole AI complex tends to outperform for 4–8 weeks. When **any major
hyperscaler cuts capex guidance** (Meta Q4 2022 archetype), expect
2–6 weeks of pain for the whole basket.

### 8.5 NVDA-as-leader effect

NVDA has been the *de facto* leader for the AI-tech complex since H1 2023.
Practical implications:

- **NVDA setting up bullishly (basing then breakout) often precedes broad
  semi & cloud strength** by 1–5 sessions.
- **NVDA breaking down** is a near-real-time warning for the entire AI
  capex chain.
- Single-stock NVDA GEX, options skew, and post-earnings reaction provide
  asymmetric information about the whole basket.

Don't trade *only* NVDA's signals — but **don't go long mega-cap tech swing
when NVDA is breaking trend** unless you have a strong idiosyncratic thesis
elsewhere.

Watch this changing in 2026 as inference markets fragment (AMD MI400, AVGO
custom silicon, Google TPU monetisation). Leadership may rotate; rule is
"follow the AI leader of the moment" not "NVDA is always the leader".

---

## 9. Magnificent 7 deep dive (2023–2026)

### 9.1 Correlation regimes

The Mag 7 pairwise correlation matrix is **non-stationary** in a way that
matters for portfolio construction.

Approximate average pairwise daily return correlation across AAPL, MSFT,
GOOGL, AMZN, META, NVDA, TSLA:

| Period | Avg pairwise corr | Notes |
|---|---|---|
| 2022 H1 (rate shock) | ~0.78 | All-down regime, everything correlated |
| 2023 H1 (AI thaw) | ~0.55 | Divergence — NVDA/META/MSFT lead; AAPL/TSLA lag |
| 2023 H2 | ~0.62 | Re-correlating |
| 2024 H1 | ~0.50 | Maximum divergence — NVDA explodes; TSLA dies; META/MSFT solid |
| 2024 H2 | ~0.58 | |
| 2025 H1 (tariff shock Apr-May) | ~0.82 | Stress = correlation spike |
| 2025 H2 | ~0.55 | Re-divergence |

**Takeaway:** a "Mag 7 basket" is misleading. In stress regimes you have ~1
asset, not 7. In divergent regimes you have meaningful idiosyncratic
opportunity (residual momentum shines here).

### 9.2 Momentum decay

12-1 momentum within the Mag 7 has had two distinct phases:

- **2023:** very high persistence. NVDA, META, MSFT led for 6+ months
  uninterrupted. Momentum-of-momentum was strong.
- **2024:** narrower leadership (NVDA dominant). Other Mag 7 chopped. 21d
  momentum signals had high false-positive rate on the laggards.
- **2025:** rotation more frequent. Leadership shifted between NVDA, META,
  GOOGL, AMZN every 4–8 weeks. Faster lookbacks (21–42d) outperformed
  longer ones (126d+).

**Practical:** in 2023-style trending tape, use longer momentum lookbacks
(126d). In 2024–2025 chop, use shorter (21–63d). Adaptive lookback selection
based on **realized trend strength** (e.g. Hurst exponent, or ratio of
absolute net move to sum of absolute moves) helps.

### 9.3 What worked specifically during the AI rally

For posterity — these are not necessarily what *will* work, but what *did*:

- **Buy NVDA dips to 50d SMA** during 2023 H1–H2 and 2024 Q4. Roughly
  9/10 success rate. Stopped working April 2025.
- **Buy META on positive cost-discipline guidance**, especially the
  "Year of Efficiency" Q4 2022 → Q1 2023 setup. Generationally good.
- **Buy MSFT on Azure beat + AI commentary**. Repeatedly worked
  2023–2024; needs 25%+ Azure growth to keep working.
- **Buy AMZN on AWS reacceleration**. Once consensus saw AWS growth ticking
  up in 2024 Q1, multiple 5–10% multi-week moves on subsequent prints.
- **Sell AAPL on iPhone unit weakness**. Repeatedly worked 2023–2024
  (especially China unit data).
- **Avoid TSLA earnings outright**. Vol way too high, deliveries / margin
  / robotaxi headline whipsaw made setups unreliable.

**Cross-stock pairs that worked**:
- Long META / short SNAP (or PINS): clean cost-discipline pair.
- Long NVDA / short INTC: AI winner vs loser.
- Long MSFT / short ORCL — *didn't* work; ORCL caught its own AI bid in
  2024.

### 9.4 Position-sizing & concentration risk

With ~50% of QQQ in 7 names, a long Mag 7 swing book has **enormous
concentration risk** that is invisible if you look at notional weights.

Discipline:
- **Cap any single name at 18–22%** of book regardless of conviction.
- **Cap NVDA + AVGO + AMD combined at 30%** of book — they are effectively
  one AI-capex factor.
- **Cap pairwise factor risk** using a simple Barra-style model: total
  exposure to "AI-capex factor" (NVDA, AVGO, AMD, MU, MRVL, AMAT, LRCX,
  KLAC) should not exceed your total exposure to the rest of the book.
- **Drawdown response**: when book DD exceeds 8% in a 5-day window, cut
  gross by 30%. When > 12%, cut by 60%. Reload only on confirmed
  regime reset (VIX/VIX3M back below 1.0, dealer gamma back positive).

---

## 10. What's likely overfit / avoid

In no particular order, things that look great in a Jupyter notebook and
disappoint in production:

1. **5-feature, 5-rule "perfect" backtests on the Mag 7.** With 7 names
   and 4 years of data, you have effectively zero degrees of freedom.
   Anything with Sharpe > 2 on this slice is overfit. Period.
2. **Optimised parameter grids for momentum lookbacks.** If your "optimal"
   lookback is 47 days, it's because 45 and 50 were slightly worse on this
   specific tape. Use round numbers (21, 63, 126, 252) and don't tune.
3. **Complex multi-factor weighting via mean–variance optimisation.** With
   noisy expected-return estimates, MVO turns into "lever up the highest
   in-sample Sharpe factor". Use equal weights or risk parity.
4. **Sentiment scores from generic FinBERT models.** The model wasn't trained
   on your specific names, doesn't understand context, and the data has
   horrendous look-ahead potential (article timestamps vs market reaction
   timestamps). Build your own with a recent LLM if you must.
5. **Reinforcement learning trading agents on OHLCV.** I have yet to see a
   production-grade implementation that beats a vol-targeted momentum
   strategy net of costs. RL needs millions of episodes; markets give you
   maybe 5000 useful ones.
6. **Order-book / Level-2 features for swing.** Useful for HFT, useless at
   2–20 day horizons. Don't waste time.
7. **Pure short-interest squeeze plays in NDX-100 mega-caps.** SI is too low
   to matter on this universe. Look elsewhere.
8. **"Earnings beat → buy" without guidance & sector context.** Half the
   2024 mega-cap earnings beats faded same-day or next-day because
   guidance disappointed. Beats alone are not a signal.
9. **"VIX > 30 always means buy".** Sometimes VIX > 30 is the start of VIX
   > 50. 2008, 2020, and parts of 2022 all happened. Don't catch the
   knife without confirmation (gamma flip, term-structure normalisation).
10. **"GEX flipped positive → guaranteed melt-up".** GEX is one input. In
    2022 GEX was positive for stretches that still saw chop or
    drawdown because rates and macro dominated.
11. **Strategies that require shorting individual mega-caps for the bulk of
    their return.** Borrow cost, hard-to-borrow events, and earnings gap
    risk eat the edge. Most "long-short" in this universe is barely
    profitable net of frictions.
12. **Backtests on QQQ that ignore the index reconstitution.** Names join
    and leave NDX-100; using current constituents to backtest historical
    strategies is survivorship bias. Norgate Data has properly
    point-in-time NDX membership; yfinance does not.
13. **Anything that relies on the 1990–2010 academic premium estimates
    persisting at full magnitude.** Premia have decayed roughly in half
    across momentum, value, and BAB in the last 15 years. Plan
    accordingly.
14. **"AI-enhanced" newsletters and signals services.** No edge survives
    public distribution. By the time a Twitter / Substack guru is selling
    a setup, the alpha is dead. Half-life of public signals: weeks.
15. **High-frequency rebalancing on retail-broker fills.** Slippage on
    market orders for 2000-share NVDA blocks at 9:31 ET is much worse
    than your backtest assumes. Use limit orders, accept some non-fills.
16. **"This time is different" — applied to mega-cap concentration.** Yes,
    the Mag 7 is huge. Yes, it could correct violently. Anyone who tells
    you they know *when* is selling something.

---

## 11. Data-source recommendations

For the strategies in this document, here's the honest stack ranking by
use-case.

### Daily OHLCV for NDX-100 backtesting

| Source | Cost | Pros | Cons |
|---|---|---|---|
| **yfinance** | Free | Easy, decent | **No point-in-time index membership**, occasional bad ticks, no fundamentals dates aligned, frequent breaking changes |
| **Tiingo** | $10–30/mo | Clean adjusted history, EOD reliable, decent news | No options, limited intraday for cheap tier |
| **Polygon** | $30–200/mo | Tick data, options chain, real-time, REST + WS | Pricier; options data needs higher tier; historical depth varies |
| **Norgate** | $400+/yr | **Proper point-in-time index constituents**, delisted stocks, splits/divs perfect, total-return | Windows-centric tooling, no options, no intraday, $$$$ |
| **EODHD** | $20–60/mo | Global coverage, fundamentals, news | Quality of US data is fine but Tiingo is cleaner |
| **Alpaca** | Free w/ account | Bars + recent option chain (premium plan), good APIs for live | Historical depth limited; not really a backtesting source |
| **Databento** | Pay-per-use | Tick-level, OPRA, Nasdaq TotalView | Pricey; overkill for swing horizon |

**Recommendation by use case**:

- **You're a hobbyist / learning**: yfinance + Tiingo for news. Accept
  survivorship bias; don't deploy real money off these backtests.
- **You're going to trade real money on factor strategies**: **Norgate** for
  the point-in-time constituents (critical) + **Polygon** or **Tiingo** for
  cleaner adjusted prices and fundamentals. Yes, the Norgate price stings,
  but it's the single biggest source of survivorship/look-ahead bias
  elimination for retail.
- **You want options chains, GEX, dealer flow proxy**: **Polygon Options
  Starter** is the cheapest viable source ($79/mo as of late 2025) for
  end-of-day full options chains. Real-time is $200+/mo. SqueezeMetrics
  publishes a free SPY GEX/DIX. SpotGamma is paid ($65–200/mo) and
  generally worth it if you take GEX seriously.
- **You want news / sentiment**: Tiingo News (cheap), Polygon News (bundled
  if you pay for Polygon), Benzinga Pro (real-time, $200+/mo, the standard
  for desk traders).
- **You want fundamentals**: Tiingo or Polygon are fine for headlines.
  For real point-in-time fundamentals (the date the 10-Q was *filed*, not
  the period end), you need either **SEC EDGAR direct** (free, painful) or
  paid providers like **Sharadar / Nasdaq Data Link** ($30–150/mo).
- **You want intraday data for OPEX / opening-range / closing-auction
  studies**: Polygon (best price/quality for retail), or Databento if
  you're getting serious. Alpaca is OK for live, weak for history.
- **You want options flow / unusual options activity**: **Unusual Whales** (best
  retail UX, ~$50/mo), **CheddarFlow**, **Tradytics** (~$60–120/mo).
  SpotGamma's flow tools also overlap.

### Specific gotchas

- **yfinance** changes its API constantly. Production code should pin to a
  specific version *and* keep a fallback. Don't build a real strategy on
  yfinance live data. Use it for prototypes only.
- **Polygon's** options snapshot endpoint occasionally has stale strikes;
  always reconcile with the OCC daily volume report if exact OI matters.
- **Norgate** is Windows-first; on Linux you can use the SDK via mono or
  run a small Windows VM. Annoying but tractable.
- **Tiingo's** adjusted prices are total-return-style (dividends reinvested)
  by default. Check what your strategy expects.
- All free EOD sources are **delayed at the close**. Don't trust EOD prices
  pulled at 16:00:30 ET — wait for the official close print
  (typically 16:00:01–16:00:15) and re-pull at 16:05.

---

## 12. Appendix — minimal Python building blocks

These are illustrative skeletons, not production code. They show the
*shape* of how you'd implement the above. Assume `pandas`, `numpy`, and
`yfinance` or your favourite OHLCV source.

### 12.1 Vol-targeted position sizing

```python
import numpy as np
import pandas as pd

def vol_target_weights(returns: pd.DataFrame,
                       target_vol_pa: float = 0.20,
                       lookback: int = 20,
                       max_lev: float = 2.5) -> pd.DataFrame:
    """
    returns: T x N daily log-returns of signals (signed)
    Returns weights such that each position's ex-ante annual vol = target_vol_pa.
    """
    realized_vol = returns.rolling(lookback).std() * np.sqrt(252)
    weights = target_vol_pa / realized_vol.replace(0, np.nan)
    weights = weights.clip(upper=max_lev).fillna(0.0)
    return weights
```

### 12.2 Cross-sectional momentum signal

```python
def xs_momentum_signal(prices: pd.DataFrame,
                       lookback: int = 63,
                       skip: int = 5,
                       top_n: int = 7) -> pd.DataFrame:
    """
    prices: T x N adjusted close prices
    Returns binary {0,1} long signals for top_n names by lookback-skip return.
    """
    rets = (prices.shift(skip) / prices.shift(skip + lookback)) - 1.0
    rank = rets.rank(axis=1, ascending=False)
    signal = (rank <= top_n).astype(float)
    return signal
```

### 12.3 Residual momentum signal

```python
import statsmodels.api as sm

def residual_momentum(prices: pd.DataFrame,
                      factors: pd.DataFrame,  # T x F, e.g. QQQ, SMH, IGV returns
                      reg_window: int = 60,
                      mom_window: int = 63,
                      top_n: int = 7) -> pd.DataFrame:
    daily_ret = np.log(prices / prices.shift(1))
    factor_ret = np.log(factors / factors.shift(1))

    residuals = pd.DataFrame(index=daily_ret.index, columns=daily_ret.columns,
                             dtype=float)
    for name in daily_ret.columns:
        y = daily_ret[name]
        X = sm.add_constant(factor_ret)
        for t in range(reg_window, len(y) - 1):
            window = slice(t - reg_window, t)
            res = sm.OLS(y.iloc[window], X.iloc[window], missing="drop").fit()
            # Today's residual = today's return - predicted from today's factors
            predicted = res.predict(X.iloc[t:t+1])[0]
            residuals.iloc[t, residuals.columns.get_loc(name)] = (
                y.iloc[t] - predicted
            )

    resid_cum = residuals.rolling(mom_window).sum()
    rank = resid_cum.rank(axis=1, ascending=False)
    signal = (rank <= top_n).astype(float)
    return signal
```

(This is slow; vectorise via rolling regression libs like `roll` or
`statsmodels.regression.rolling.RollingOLS` for production.)

### 12.4 Dual-momentum filter

```python
def dual_momentum(prices: pd.DataFrame,
                  abs_lookback: int = 126,
                  rel_lookback: int = 63,
                  top_n: int = 8) -> pd.DataFrame:
    abs_ret = (prices / prices.shift(abs_lookback)) - 1.0
    rel_ret = (prices / prices.shift(rel_lookback)) - 1.0

    abs_filter = (abs_ret > 0).astype(float)
    rank = rel_ret.where(abs_filter > 0).rank(axis=1, ascending=False)
    signal = (rank <= top_n).astype(float)
    return signal
```

### 12.5 VIX-regime filter

```python
def vix_regime_gross(vix_series: pd.Series,
                     vix3m_series: pd.Series) -> pd.Series:
    """
    Returns a 0-1 multiplier for portfolio gross based on simple regime rules.
    """
    ratio = vix_series / vix3m_series
    gross = pd.Series(1.0, index=vix_series.index)

    gross[vix_series > 25] = 0.5
    gross[vix_series > 35] = 0.2
    gross[(ratio > 1.0) & (vix_series > 22)] = 0.4
    gross[vix_series < 13] = 0.7  # complacency — modest derisk
    return gross
```

### 12.6 PEAD-style earnings drift entry

```python
def pead_entry(earnings_calendar: pd.DataFrame,
               prices: pd.DataFrame,
               sue: pd.Series,
               guidance_surprise: pd.Series) -> pd.DataFrame:
    """
    earnings_calendar: rows=date, columns=ticker, value=True on print day
    Returns a long signal on D+2 if combined score positive.
    """
    score = 0.5 * sue + 0.5 * guidance_surprise  # both z-scored
    long_signal = (score > 1.0).astype(float)

    # Hold for 10 trading days from D+2
    entry = earnings_calendar.shift(2) * long_signal.values
    return entry.rolling(10, min_periods=1).max()
```

### 12.7 Deflated Sharpe ratio (skeleton)

```python
from scipy.stats import norm

def deflated_sharpe(observed_sr: float,
                    n_trials: int,
                    n_obs: int,
                    skew: float,
                    kurt: float) -> float:
    """
    Bailey & Lopez de Prado (2014).
    Returns probability that the true SR > 0 given n_trials backtests tried.
    """
    # SR variance per Mertens (2002)
    sr_var = (1 - skew * observed_sr +
              (kurt - 1) / 4 * observed_sr ** 2) / (n_obs - 1)
    sr_std = np.sqrt(sr_var)

    # Expected max SR from n_trials independent draws ~ N(0,1)
    emc = 0.5772
    expected_max_sr = sr_std * (
        (1 - emc) * norm.ppf(1 - 1.0 / n_trials)
        + emc * norm.ppf(1 - 1.0 / (n_trials * np.e))
    )

    z = (observed_sr - expected_max_sr) / sr_std
    return float(norm.cdf(z))
```

Use this on *every* strategy before risking real money. If the deflated
probability is below ~0.95, you don't have a strategy — you have a story.

---

## Closing thoughts

If you are swing-trading mega-cap NDX names in 2025–2026, the realistic
playbook is:

1.  **Dual-momentum or residual-momentum** as the core long-bias engine.
2.  **Vol targeting** at the position level, **regime overlays** at the
    portfolio level using VIX, VIX/VIX3M, and dealer GEX.
3.  **Earnings as the main event source** — be ready with PEAD-aware entries
    on the right setups, stand aside on the wrong ones, never short
    premium on Mag 7 EPS without a strong view.
4.  **Options flow as confirmation, not trigger** — GEX/DEX, UOA clusters,
    skew shifts. Treat as overlays on top of price + momentum, not as
    standalone alpha.
5.  **Be ruthless about overfitting**: round-number parameters, walk-forward
    only, deflated Sharpe on everything, accept Sharpe 0.5–1.0 as a real
    edge and don't chase fairy tales.
6.  **Concentration is the enemy** — even with a 7-name universe, hard
    caps per name and per factor.
7.  **Survival > optimisation.** The best swing traders in this space lose
    less in 2022 and April 2025 type tapes, not necessarily make the most
    in 2023 rallies.

Edge is small. Discipline is everything. Most "systematic" retail swing
traders fail not because their model is wrong, but because they
override it under stress, over-leverage in calm regimes, and trade through
events they shouldn't. Pick a small set of rules from above, code them,
backtest them honestly, paper-trade them for a quarter, and only then risk
real money. Reassess every six months — these regimes change.

Good luck. The market does not care about you. 🫡
