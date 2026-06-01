# 07 — The Skeptical Perspective on Swing Trading Mega-Cap US Tech

> *"It is difficult to get a man to understand something, when his salary depends on his not understanding it."* — Upton Sinclair
>
> *"The four most dangerous words in investing are: 'this time it's different.'"* — John Templeton
>
> *"In theory, theory and practice are the same. In practice, they are not."* — attributed to Yogi Berra (and to Einstein, and to everyone else)

This document is the loyal opposition inside our own project. Its job is to make the strongest possible case **against** what we are about to build: an end-of-day technical swing trading engine focused on mega-cap NASDAQ-100 names (AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA, AVGO, and friends).

Everything that follows is grounded in the academic and empirical literature. We name the papers, the years, the authors, and the specific findings. If we ship anything, it must clear these objections — or we must be explicit that we have chosen to ignore them, and why.

---

## 1. Efficient Markets on Mega-Caps: The Hardest Game in Equities

### 1.1 The Fama trilogy

The intellectual core of the skeptical case begins with three papers by Eugene Fama:

- **Fama, Eugene F. (1970). "Efficient Capital Markets: A Review of Theory and Empirical Work." *Journal of Finance*, 25(2), 383–417.**
  This is the foundational taxonomy: *weak-form* (prices reflect all past price information), *semi-strong* (prices reflect all public information), and *strong-form* (prices reflect all information, public and private) efficiency. The empirical evidence Fama surveyed in 1970 already pointed to weak-form efficiency in liquid US equities. End-of-day technical analysis lives or dies inside the weak-form claim, because it uses nothing but past prices and volumes. If weak-form efficiency holds even approximately on the most-watched names in the world, the prior probability that a vanilla EOD technical edge survives net of costs is small.

- **Fama, Eugene F. (1991). "Efficient Capital Markets: II." *Journal of Finance*, 46(5), 1575–1617.**
  Twenty-one years later, Fama updated the survey. Predictability is real at long horizons (dividend yields, term spread, default spread predict returns) but short-horizon return predictability from past prices alone is weak, inconsistent across samples, and frequently disappears once trading costs are included. The candor of this paper is what matters: Fama does not claim markets are perfect; he claims the deviations are small, noisy, and hard to monetize.

- **Fama, Eugene F. (2014). "Two Pillars of Asset Pricing." *American Economic Review*, 104(6), 1467–1485.** (His Nobel lecture.)
  The 2014 lecture concedes that there are anomalies (size, value, momentum, profitability, investment) but frames them as risk factors rather than as exploitable inefficiencies for typical investors. Crucially, Fama emphasizes the *joint hypothesis problem*: a test of market efficiency is always a joint test of efficiency plus a model of expected returns. You cannot reject efficiency without a model, and the models themselves are contested.

### 1.2 Cochrane and the discount-rate revolution

- **Cochrane, John H. (2011). "Presidential Address: Discount Rates." *Journal of Finance*, 66(4), 1047–1108.**
  Cochrane's central observation: time-variation in expected returns (discount rates), not time-variation in expected cash flows, drives almost all of the variance in price-dividend and price-earnings ratios. What looks like a "trend" or "momentum" pattern in a chart is, to a first approximation, the market re-pricing risk premia in response to information flow you cannot see in the candles. The signal that an EOD technician believes they are detecting in price is, under Cochrane's framework, usually the *output* of a discount-rate move that has already occurred and already been priced. You are reading the receipt, not getting in on the order.

### 1.3 Why mega-cap tech is the hardest sub-universe

Even if you believe small-cap or micro-cap markets are inefficient — and the evidence there is genuinely stronger — the case for inefficiency in **AAPL, MSFT, NVDA, GOOGL, AMZN, META** is uniquely weak:

1. **Coverage density.** Every sell-side bank has 5–20 analysts on these names. Every macro fund, every quant fund, every long-only fundamental fund, and every retail forum has an opinion. The marginal informed trader arrives in milliseconds.
2. **Liquidity.** AAPL's average daily dollar volume is in the tens of billions. NVDA's is comparable. Spreads are routinely 1 cent on a $150+ stock. This is the regime where HFT market-makers earn the spread and any persistent technical pattern is the first thing to be arbitraged.
3. **Options depth.** The options markets on these names are among the most liquid in the world. If a directional edge existed at the daily horizon, options market-makers would price it into skew and term structure within a session.
4. **Index inclusion.** These names are the top weights in SPY, QQQ, VTI, IWB, MTUM, and dozens of sector and thematic ETFs. They are the most-rebalanced, most-flow-driven stocks on earth. Technical patterns get demolished by mechanical rebalancing flows that have nothing to do with chart structure.
5. **Earnings concentration.** Roughly 8 days a year per name are earnings-driven discontinuities. A non-trivial fraction of annual return variance is concentrated in those overnight gaps, which are precisely where EOD systems are blindest.

**The honest prior:** If you cannot beat a simple buy-and-hold of QQQ net of costs over a 10-year out-of-sample window on these specific tickers using EOD technicals, you have not found an edge. You have found a curve fit. Fama (1970, 1991, 2014) and Cochrane (2011) together set a very high bar, and mega-cap tech is the worst possible place to attempt the climb.

### 1.4 The joint-hypothesis trap, applied to us

Suppose our engine produces a Sharpe of 1.2 in backtest on AAPL+MSFT+NVDA from 2014–2024. We will be tempted to say: *"the market is inefficient in these names."* But under Fama's joint hypothesis, the right statement is: *"either the market is inefficient in these names, OR our model of expected returns is wrong, OR we have overfit, OR we got lucky, OR all of the above."* The default assumption — the prior we should hold until shown overwhelming evidence to the contrary — is the last three.

---

## 2. Edge Decay: The Graveyard of Once-Famous Signals

A central pillar of the skeptical case is that the signals retail traders are taught (MA crossovers, RSI(2), Turtle breakouts, calendar effects) **worked at some point, were published, became famous, and then decayed**. The mechanism is not mysterious. Once a pattern is widely known, capital rushes in, and the pattern either disappears or inverts.

### 2.1 The decisive empirical paper

- **McLean, R. David, and Jeffrey Pontiff (2016). "Does Academic Research Destroy Stock Return Predictability?" *Journal of Finance*, 71(1), 5–32.**

  McLean and Pontiff hand-collected **97 predictor variables** from the published academic literature and re-tested each one in three regimes: (a) in-sample, as originally published; (b) out-of-sample but pre-publication; (c) post-publication. Their findings are devastating for naive faith in published signals:

  - **Out-of-sample decay:** Returns to predictors decay by about **26%** out-of-sample relative to in-sample.
  - **Post-publication decay:** Returns decay by an additional **~32% on top of that**, so post-publication a typical anomaly retains only about half of its original strength.
  - **The most arbitraged decay the most.** Predictors based on more liquid, larger stocks decay faster post-publication than those in small, illiquid corners. This is precisely the regime mega-cap tech swing trading lives in.

  The implication: any classical technical signal that was profitable in the 1990s or early 2000s and is now in every textbook, every YouTube tutorial, and every TradingView indicator library should be assumed *materially weaker* on mega-cap tech in the 2020s than it was when discovered.

### 2.2 The factor zoo and the t-stat hurdle

- **Harvey, Campbell R., Yan Liu, and Heqing Zhu (2016). "...and the Cross-Section of Expected Returns." *Review of Financial Studies*, 29(1), 5–68.**

  Harvey, Liu, and Zhu catalogued **316 published factors** purporting to explain the cross-section of equity returns. Their central methodological argument: because researchers have collectively run thousands of tests over decades, the conventional t-statistic threshold of 2.0 is wildly insufficient. After adjusting for multiple testing (using Bonferroni, Holm, and Benjamini-Hochberg-Yekutieli style corrections), they recommend a t-statistic threshold of **roughly 3.0 or higher** for any newly proposed factor to be taken seriously.

  Translated to backtesting technical strategies: if you tested 100 parameter combinations on RSI, MACD, MA crossovers, breakout lengths, and ATR multipliers, the single best one almost certainly clears t > 2.0 by luck alone. Harvey-Liu-Zhu says: raise the bar. Most "edges" you find are noise.

### 2.3 Signal-by-signal autopsy

#### Moving-average crossovers
The classic 50/200 "golden cross" and 10/20 short-horizon crossovers were the staple of Richard Donchian and the early trend-following era. Brock, Lakonishok, and LeBaron (1992, "Simple Technical Trading Rules and the Stochastic Properties of Stock Returns," *Journal of Finance*, 47(5), 1731–1764) found statistically significant abnormal returns to MA rules on the Dow from 1897–1986. But:

- **Sullivan, Timmermann, and White (1999). "Data-Snooping, Technical Trading Rule Performance, and the Bootstrap." *Journal of Finance*, 54(5), 1647–1691.** Re-examined the Brock et al. results using a bootstrap reality-check (Halbert White's procedure) on a universe of ~7,800 trading rules. They concluded that once you adjust for the data-snooping bias inherent in selecting the best-performing rule from a large family, **the post-1986 out-of-sample performance of MA crossovers is statistically indistinguishable from zero, and economically negative after costs.**
- Post-2010, multiple replication studies on US large-caps find the 50/200 cross delivers roughly buy-and-hold returns minus turnover costs. It is, at best, a volatility-reducer; it is not an alpha source.

#### RSI(2) and the Connors playbook
Larry Connors and Cesar Alvarez popularized RSI(2) in *Short Term Trading Strategies That Work* (2008). Buy SPY when RSI(2) < 5, sell when it closes above the 5-day MA. The backtest from ~1993–2008 looked spectacular: high win rate, smooth equity curve, modest drawdowns.

- **Post-2010 reality:** Every retail blog and Quantopian notebook reproduced this strategy. Multiple independent walk-forward tests (see Quantpedia's tracking, and the work of Cesar Alvarez himself on alvarezquanttrading.com, who has openly acknowledged decay) show the edge collapsed after 2010. The 2011 mid-year was the inflection point. By 2015 the strategy's alpha on SPY was negative net of costs. On single mega-cap tech names it is worse: high false-positive rate during persistent uptrends (NVDA 2023–2024 would have triggered "oversold buys" that were caught knives during pullbacks within a parabolic move, but the offsetting wins during chop have diminished).
- Mechanism of decay: short-term mean reversion in US large-caps was partly a microstructure phenomenon (specialist inventory rebalancing, decimalization aftermath) that was arbitraged away by stat-arb desks and HFT once it became common knowledge.

#### Turtle Trading (Dennis & Eckhardt, 1983)
The Turtle rules — 20-day Donchian breakout entry, 10-day Donchian exit, 2N stop, pyramid in N units — were extraordinarily profitable for Richard Dennis's protégés in the 1980s on commodity futures. Curtis Faith's *Way of the Turtle* (2007) is the canonical reference.

- **Post-2000 decay on futures:** Multiple CTAs and academic replications (e.g., the work of AQR's Asness, Moskowitz, Pedersen on "Time Series Momentum," *Journal of Financial Economics*, 104(2), 2012, 228–250) show trend-following remains real on diversified futures portfolios, but with Sharpe ratios that have **compressed from ~1.0+ in the 1980s–90s to ~0.3–0.5 in the 2010s.**
- **On single US equities:** The Turtle approach was never designed for single stocks. Breakouts on individual mega-cap tech names suffer from headline whipsaw, earnings gaps, and index-rebalancing flows that have nothing to do with persistent supply-demand imbalance in a commodity contract. The win rate on naive 20-day breakouts in QQQ constituents from 2015–2024 is in the 30–35% range with R-multiples that no longer compensate for the false signals once costs are included.

#### Calendar anomalies
- **Turn-of-the-month effect** (Ariel 1987, *Journal of Finance*): documented strong returns in the last few and first few trading days of each month. Multiple post-2010 studies (e.g., McConnell and Xu, 2008 update; subsequent work in *Journal of Banking & Finance*) show the effect has weakened by roughly half on US large-caps, and is statistically marginal post-2015.
- **January effect** (Rozeff and Kinney 1976, *Journal of Financial Economics*): the small-cap January premium. Post-2000, this is almost entirely gone in liquid large-caps. Haugen and Jorion (1996) documented early decay; subsequent work confirms.
- **Halloween / Sell in May** (Bouman and Jacobsen 2002, *American Economic Review*): the seasonal pattern persists in some markets but is statistically fragile post-2010 in US equities and especially in tech, which has had several strong summers (2020, 2023, 2024).
- **Friday-Monday effects, holiday effects, FOMC drift** (Cieslak, Morse, Vissing-Jorgensen 2019, "Stock Returns Over the FOMC Cycle," *Journal of Finance*): some macro-calendar effects survive, but they are narrow, regime-dependent, and largely unavailable to a daily-bar EOD swing system on individual names.

### 2.4 The meta-lesson

Every single one of these signals **worked in the sample where it was discovered**. Every single one **decayed after publication**. McLean-Pontiff predicted this should happen, and it did. The base-rate forecast for any new chart pattern, indicator combination, or "system" we cook up is: *it will decay too, and probably faster, because we are operating in the most-arbitraged sub-universe of the most-arbitraged equity market on earth.*

---

## 3. Multiple Testing, Backtest Overfitting, and the Deflated Sharpe Ratio

If Section 2 explains why known signals decay, Section 3 explains why **unknown signals you discover via backtest search are almost always illusions in the first place.**

### 3.1 The López de Prado / Bailey program

Marcos López de Prado (formerly AQR, Cornell, now ADIA Lab) and David H. Bailey (Lawrence Berkeley) have done the most rigorous work on backtest overfitting in the past decade. The relevant papers:

- **Bailey, David H., and Marcos López de Prado (2014). "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality." *Journal of Portfolio Management*, 40(5), 94–107.**

  Core insight: the observed Sharpe ratio of "the best" of N tried strategies is upward-biased. The bias grows with N (number of trials), with the variance of trial Sharpes, and with the non-normality (skew, kurtosis) of returns. The **Deflated Sharpe Ratio (DSR)** corrects for this and asks: *given that I tried N strategies, what is the probability that the observed best Sharpe exceeds a benchmark of zero true skill?*

  Worked intuition: if you test 100 strategies whose true Sharpe is exactly 0, the *expected maximum* observed Sharpe is roughly **0.6 to 1.0** on a 5-year sample, purely from luck. To claim real skill at conventional significance, your observed best needs to clear roughly **1.5 to 2.0** *after* deflation. Most retail backtests claiming "Sharpe 1.8" have done no such adjustment.

- **Bailey, David H., Jonathan Borwein, Marcos López de Prado, and Qiji Jim Zhu (2014). "Pseudo-Mathematics and Financial Charlatanism: The Effects of Backtest Overfitting on Out-of-Sample Performance." *Notices of the American Mathematical Society*, 61(5), 458–471.**

  The headline finding: with only **5 years of daily data**, an analyst running just **45 trials** can produce a backtest with Sharpe = 1.0 even when the true Sharpe is **0**. With 100 trials, you can easily produce a Sharpe of 1.5+. The paper is brutal: the authors argue most published trading strategies, and the overwhelming majority of retail-marketed "systems," are pseudo-mathematical artifacts of in-sample search.

- **Bailey, David H., and Marcos López de Prado (2014). "The Probability of Backtest Overfitting." Available on SSRN; later formalized in *Journal of Computational Finance*, 20(4), 2017, 39–69, as "The Probability of Backtest Overfitting" by Bailey, Borwein, López de Prado, and Zhu.**

  Introduces **PBO** — the Probability of Backtest Overfitting — computed via combinatorially symmetric cross-validation (CSCV). The procedure: split your backtest into S sub-samples, evaluate all strategy variants on every combination of (S/2) sub-samples as "training" and the complement as "testing," and measure how often the in-sample best is below median out-of-sample. A well-designed strategy should have PBO < 0.5; many retail systems score PBO > 0.7, meaning the in-sample winner is *more likely than not* to underperform the median strategy out-of-sample.

- **Bailey, David H., and Marcos López de Prado (2012). "The Sharpe Ratio Efficient Frontier." *Journal of Risk*, 15(2), 13–44.**

  Introduces **Minimum Track Record Length (MinTRL)**: the number of observations required to conclude with a given confidence that an observed Sharpe ratio exceeds a benchmark. For a strategy whose true Sharpe is 1.0 vs a benchmark of 0.5, with normally distributed returns, you need roughly **2–3 years of daily data** to clear 95% confidence. For Sharpe 0.5 vs 0, you need **5+ years**. Most retail backtests on 2–3 years of in-sample data are statistically incapable of distinguishing a true edge from noise even *before* multiple-testing adjustments.

### 3.2 The "1.5× backtest Sharpe → 0.5× live Sharpe" rule of thumb

This rule, popular among practitioners and consistent with the literature above, is not a theorem but it is a useful Bayesian prior. Sources for the spirit of it include:

- López de Prado, *Advances in Financial Machine Learning* (Wiley, 2018), Chapters 11–14 on backtesting and overfitting.
- AQR working papers by Cliff Asness and colleagues warning that live performance of factor strategies typically realizes at 40–60% of paper backtest Sharpe.
- Andrew Lo's discussions in *Adaptive Markets* (Princeton, 2017) on the half-life of strategies.

The pragmatic translation: if your honest backtest (no peeking, no in-sample optimization beyond a single walk-forward window, transaction costs included) shows Sharpe = 1.5, **plan your business as if live Sharpe will be 0.5.** If your backtest shows Sharpe = 0.8, plan for break-even after costs. If your backtest shows Sharpe = 0.3, do not deploy — you have nothing.

**Apply this to mega-cap tech swing trading:** A buy-and-hold of QQQ from 2010–2024 produced Sharpe in the range of 0.9–1.1. To justify the time, complexity, and stress of a swing trading engine, our **live** Sharpe needs to clear ~1.0 net of costs, which means our **honest backtest** needs to clear ~2.0 net of costs, which means our **raw in-sample best** (before deflation) probably needs to clear ~2.5–3.0. The probability that a single human, on commodity hardware, with publicly available indicators, hits that bar on the most-arbitraged stocks on earth is small.

### 3.3 The combinatorial explosion

Quick sanity check on how easy it is to silently run thousands of trials:

- 5 indicators × 10 parameter values each × 3 entry rules × 3 exit rules × 4 position-sizing schemes × 5 universes = **9,000 trials.**
- Run this overnight on a laptop. Pick the best. Sharpe = 2.4. Equity curve is gorgeous.
- Deflated Sharpe ratio: probably 0.0–0.3. Probability of backtest overfitting: > 0.8. Expected live performance: break-even at best, more likely a slow bleed.

The honest backtest discipline is: **fix the strategy before looking at the data, run it once, and accept the result.** Almost nobody does this. We won't either, unless we put hard guardrails in the engine itself.

---

## 4. Survivorship Bias in the Trading Literature

The trading-book canon is a museum of winners. The losers do not get book deals.

### 4.1 The Market Wizards problem

Jack Schwager's *Market Wizards* (1989), *The New Market Wizards* (1992), *Stock Market Wizards* (2001), and *Hedge Fund Market Wizards* (2012) are excellent journalism and terrible base-rate evidence. Schwager interviewed traders who, by the time of interview, had compiled extraordinary track records. He did not — *could not* — interview the thousands of equally hard-working, equally intelligent traders who blew up, gave up, or quietly underperformed.

If 10,000 traders each flip a coin every year for 10 years, roughly 10 will go 10-for-10. Those 10 will write books. The 9,990 will not. This is not a slander against the Wizards (many of them are clearly skilled); it is a statement about what you can and cannot infer from reading their books. **Reading *Market Wizards* and concluding "trading works" is the same statistical error as reading lottery-winner memoirs and concluding "lottery tickets are a good investment."**

### 4.2 Famously public calls that flopped

Public, time-stamped, repeatedly-wrong calls from people who were widely regarded as smart:

- **John Hussman (Hussman Strategic Growth Fund, HSGFX).** Hussman is a PhD economist, intellectually serious, and a prolific writer. He turned permanently bearish on US equities around 2009–2010 on valuation grounds (Shiller PE, market-cap/GDP, "Hussman Margin-Adjusted P/E"). His weekly commentaries have, for over a decade, predicted imminent crashes of 50–65%. HSGFX's actual track record from 2010 through 2024 is one of the worst among diversified US equity funds — substantial losses against a backdrop of one of the greatest bull markets in history. The intellectual framework is rigorous; the trades have been catastrophic. **Being right about valuation in the long run is not the same as being right about price in the medium run, and the medium run can outlast your fund.**
- **Robert Prechter (Elliott Wave International).** Has called major tops repeatedly since the late 1980s. Spectacular early call on the 1987 crash; near-continuous bearishness afterward through the entire 1990s, 2000s, and 2010s bull markets. Elliott Wave's flexibility (count revisions) is exactly the kind of unfalsifiability that López de Prado warns about.
- **Marc Faber, Nouriel Roubini, Peter Schiff** — perennial bears who were correct once (Schiff and Roubini on the GFC) and have been wrong on US equity direction for most of the subsequent 15+ years. Stopped-clock problem.
- **Meredith Whitney's 2010 muni-bond apocalypse call** on *60 Minutes* — predicted "hundreds of billions" in muni defaults within 12 months. Actual defaults were a tiny fraction of that. Career-defining call, completely wrong on magnitude and timing.
- **Bill Ackman's Herbalife short** — public, leveraged, intellectually argued, ultimately a multi-year capitulation at a loss reported in the hundreds of millions.
- **The "Death Cross" media cycle** — every time the S&P 500 50-day crosses below the 200-day, financial media writes "Death Cross signals coming crash." The historical post-Death-Cross return distribution on the S&P 500 is essentially indistinguishable from the unconditional distribution. The signal makes headlines because it sounds scary, not because it works.

The point is not that any individual was a fool. The point is: **public, articulate, well-credentialed people have been spectacularly wrong, in writing, for decades, in ways that retail readers tend to forget when the next confident-sounding call comes along.**

### 4.3 The absent literature

Where are the books titled:

- *How I Blew Up My Account: A Decade of RSI(2) on QQQ*
- *Confessions of a Failed Day Trader: 1997–2003*
- *I Studied Technical Analysis for 15 Years and Made $0*
- *My Beautiful Backtest That Lost Me Everything*

These books do not exist, or sell vanishingly few copies. The *base rate* of trading success is hidden because the failures do not publish.

Survivorship bias also infects:

- **Strategy backtests on current index constituents.** Backtesting "QQQ stocks" on today's QQQ constituents is cheating: you have implicitly selected the survivors. Real backtests must use point-in-time index membership (which most retail platforms do not provide cleanly).
- **Mutual fund performance studies.** Dead funds disappear from databases. Surviving fund performance overstates the average.
- **Hedge fund databases** (TASS, HFR, etc.) — well-documented upward bias of 2–4% per year from survivorship + backfill bias. See Malkiel & Saha (2005), "Hedge Funds: Risk and Return," *Financial Analysts Journal*.

### 4.4 What an honest curriculum would look like

It would read failure memoirs before *Market Wizards*. It would assign Barber-Odean before Pristine. It would teach the Deflated Sharpe Ratio before MACD. It does not exist because nobody wants to buy it.

---

## 5. Transaction Cost Math: Where Sharpe-1.5 Backtests Die

This is the section that matters most for engineering. Costs are not a footnote. **Costs are the variable that decides whether the strategy is real.**

### 5.1 The worked example

**Setup:**
- Account size: **$25,000** (Pattern Day Trader threshold; below this in the US, day-trading is restricted to 3 round-trips per 5 business days in a margin account).
- Symbol: **NVDA** at **$140**.
- 14-day ATR: **$5.00** (a reasonable mid-2024-ish figure; ATR has been higher during runs).
- Risk per trade: **1%** of account = **$250**.
- Stop distance: **1 ATR = $5.00** below entry.
- Position size: $250 risk / $5 stop = **50 shares**.
- Notional exposure: 50 × $140 = **$7,000** (28% of account in a single name — already concerning from a concentration standpoint, but typical of swing-trading sizing).

**Costs of a round trip (in and out):**

| Component | Per share | Per round-trip (50 sh) | As % of $250 R |
|---|---|---|---|
| Bid-ask spread (1¢ each side, paid by aggressing) | $0.01 in + $0.01 out = $0.02 | $1.00 | 0.4% |
| Slippage @ 0.05 ATR per fill ($0.25 each side) | $0.25 + $0.25 = $0.50 | $25.00 | 10.0% |
| Commission (typical US retail, zero-comm broker) | $0 | $0.00 | 0.0% |
| SEC fee (sell side, ~$22.90 per $1M, late 2024 rate) | ~$0.0001 | ~$0.005 | 0.0% |
| FINRA TAF (sell side, $0.000166/share, capped) | $0.000166 | ~$0.008 | 0.0% |
| Borrow cost (if short, varies; assume long) | — | — | — |
| **Total round-trip cost** | | **~$26** | **~10.4%** |

**So just to break even on a single trade, you need to make back ~10% of your risk unit (R) in pure cost.**

### 5.2 What this does to expectancy

Suppose your raw (cost-free) edge is:

- Win rate: 50%
- Average win: 1.5R
- Average loss: 1.0R
- Raw expectancy per trade: 0.5 × 1.5R − 0.5 × 1.0R = **+0.25R**

Apply costs:

- Net expectancy per trade: 0.25R − 0.10R = **+0.15R**

Costs have eaten **40% of your edge** before you've made a single mistake. And the 5¢ slippage assumption is **optimistic** for a 50-share market order on NVDA — fine — but **the moment ATR expands to $8 in a vol regime**, your stop widens, your position shrinks to 31 shares, but your slippage also widens proportionally and the cost share of R stays roughly constant. There is no scale escape at this account size.

### 5.3 What this does to Sharpe

Convert per-trade expectancy to annualized Sharpe under simplifying assumptions:

- 100 trades per year (≈ 2 per week, realistic for a daily-bar swing system across a small universe).
- Per-trade std dev of returns ≈ 1.2R (typical for an asymmetric system).
- Account-level per-trade return ≈ expectancy_R × 1% (because R = 1% of account).

**Pre-cost case:**
- Mean annual return ≈ 100 × 0.25R × 1% = **25% per year.**
- Std dev annual ≈ √100 × 1.2R × 1% = **12% per year.**
- Sharpe (rf = 0 for simplicity) ≈ **2.08.** *(This is your gorgeous backtest.)*

**Post-cost case (just spread + slippage, no other slippage sources):**
- Mean annual return ≈ 100 × 0.15R × 1% = **15% per year.**
- Std dev annual ≈ ~same, **12%.**
- Sharpe ≈ **1.25.**

Now layer in **realistic** additional frictions that backtests almost always miss:

- **Order-routing slippage on stops:** when a stop triggers in a fast-moving market, the actual fill is often 0.1–0.3 ATR worse than the stop price. Add ~$0.30/share = $15/round-trip = 6% of R on losing trades.
- **Overnight gaps against you:** swing systems hold overnight. On a 50-share NVDA position, a 2% adverse gap = $140 = **56% of R**, vaporizing 5+ trades' worth of expectancy in one open.
- **Borrow fees on shorts:** if the system shorts NVDA, hard-to-borrow fees during squeezes can hit 5–50% annualized on the short notional, dwarfing the directional edge.
- **Tax drag:** short-term capital gains in the US tax all gains at ordinary income rates (up to 37% federal + state). A swing system with 100 round-trips/year is by definition short-term. **Tax-adjusted Sharpe in a taxable account is materially worse than reported pre-tax Sharpe.** Pre-tax Sharpe 1.25 might be after-tax Sharpe ~0.8 for a high-bracket trader.
- **Behavioral/execution lapses:** missed signals, fat fingers, hesitation on entries during drawdowns — empirically, real human execution underperforms theoretical execution by 0.1–0.5R per trade on average (see Barber-Odean 2000 and subsequent retail studies).

**Realistic post-everything Sharpe: ~0.6–0.8** on what backtested as Sharpe 2.0. This is precisely the "1.5× backtest → 0.5× live" rule of thumb from López de Prado / AQR.

### 5.4 The brutal corollary

**To produce a live Sharpe of 1.0 on mega-cap tech swing trading, you need a backtest Sharpe of approximately 2.5–3.0 net of modeled costs.** Almost nobody achieves this honestly. The ones who claim to, on retail forums, have not done the multiple-testing math (Section 3) and have not modeled costs at the level above.

### 5.5 Why size doesn't save you

A common retort: "fine, but with $250k I can absorb costs better."

Partially true. Per-trade slippage as a % of R does shrink as you size up, because the bid-ask spread is roughly fixed in cents while your R grows. But:

- At $250k, you're now sometimes moving the market on entry/exit, *adding* to slippage on the marginal share.
- Position concentration becomes worse, not better — a 1% R trade now requires a $7k risk unit which on a $5 ATR is 1,400 shares, a $196k notional position, **78% of the account in one name.** Risk management says diversify; diversification means more positions, which means more cost events, not fewer.
- Tax drag scales linearly with profit; it does not improve with size.

The cost wall is not a function of being small. It is a function of trading too often relative to the size of your edge.

---

## 6. Behavioral Evidence: What Actually Happens to Retail Traders

The academic literature on retail trading outcomes is one of the most consistent bodies of evidence in finance. It is also one of the most ignored.

### 6.1 The Barber-Odean canon

- **Barber, Brad M., and Terrance Odean (2000). "Trading Is Hazardous to Your Wealth: The Common Stock Investment Performance of Individual Investors." *Journal of Finance*, 55(2), 773–806.**

  Sample: 66,465 households at a large US discount broker, 1991–1996. Findings:
  - The average household earned a gross annual return roughly equal to the market.
  - **The average household earned a net return ~1.5% below the market per year** due to trading costs.
  - The most active 20% of households (turnover > 250% annually) **underperformed by ~6.5% per year net of costs.**
  - The least active 20% nearly matched the market.
  - The relationship between turnover and net return was monotonically negative.

  The Barber-Odean 2000 conclusion is the title of their paper. It is not metaphor.

- **Barber, Brad M., and Terrance Odean (2001). "Boys Will Be Boys: Gender, Overconfidence, and Common Stock Investment." *Quarterly Journal of Economics*, 116(1), 261–292.**

  Same dataset, sliced by gender. Findings:
  - Men trade **45% more** than women.
  - Men's net returns are **~1.4 percentage points lower** per year as a result.
  - The differential is even larger for single men vs single women (67% more trading, ~2.3 pp lower net return).
  - Behavioral mechanism: overconfidence. Men systematically overestimate the precision of their information and the value of their trading skill.

  Caveat: the dataset is from a pre-zero-commission era, so the absolute cost magnitudes have shrunk. But the **relative ranking** — more trading = worse net outcomes — has been replicated in every subsequent study.

- **Barber, Brad M., Yi-Tsung Lee, Yu-Jane Liu, and Terrance Odean (2014). "The Cross-Section of Speculator Skill: Evidence from Day Trading." *Journal of Financial Markets*, 18, 1–24.**

  Sample: complete day-trading records from the Taiwan Stock Exchange, 1992–2006 — essentially the entire population of Taiwanese day traders. Findings:
  - **Less than 1% of day traders are able to predictably and reliably earn positive abnormal returns net of fees.**
  - Even among the top 500 day traders (out of hundreds of thousands), gross alpha is positive but small.
  - The vast majority of day traders lose money consistently year after year.
  - Heavy day traders as a group lose substantial sums; the wealth transfer is from individuals to institutions and to the exchange.

- **Barber, Brad M., and Terrance Odean (2013). "The Behavior of Individual Investors." In *Handbook of the Economics of Finance*, Vol. 2B, Chapter 22.**

  Survey of the literature. Summary of stylized facts that have replicated globally:
  1. Individual investors underperform standard benchmarks.
  2. They trade too much.
  3. They sell winners and hold losers (the disposition effect, Shefrin and Statman 1985).
  4. They are heavily influenced by attention (news, big movers).
  5. They underdiversify.
  6. They chase past performance.

  Every one of these failure modes is *exacerbated* by an EOD swing trading workflow on mega-cap tech, which is exactly the news-driven, attention-driven, undiversified, recently-performant set of stocks.

### 6.2 The "Do Day Traders Rationally Learn About Their Ability?" question

- **Barber, Brad M., Yi-Tsung Lee, Yu-Jane Liu, Terrance Odean, and Ke Zhang (2020). "Learning Fast or Slow?" *Review of Asset Pricing Studies*, 10(1), 61–93.** And the broader research stream beginning with **De Long, Shleifer, Summers, Vishny (1990), Odean (1998), and the explicit "Do Day Traders Rationally Learn?" question raised in Linnainmaa (2011), "Why Do (Some) Households Trade So Much?" *Review of Financial Studies*, 24(5), 1630–1666, and Mahani and Bernhardt (2007).**

  The empirical answer is approximately: **no, most don't learn fast enough.** Some learn — the small minority that survives. The median day trader keeps trading despite a losing record, drawing the wrong inferences from random wins, and exits the market only when their capital is depleted. Survivorship in the day-trading population is driven as much by capital exhaustion as by rational Bayesian updating.

### 6.3 The Brazilian CVM study

- **Chague, Fernando, Bruno Giovannetti, and Rodrigo De-Losso (2020). "Day Trading for a Living?" Working paper, University of São Paulo. (Commissioned in part by the Brazilian Comissão de Valores Mobiliários, the CVM, the Brazilian SEC.)**

  Sample: all Brazilian retail day traders who began trading equity futures between 2013 and 2015, followed for at least 300 days. Findings:
  - **97% of day traders who persisted for more than 300 days lost money.**
  - Only **0.4%** earned more than the Brazilian minimum wage on a per-day basis.
  - Only **0.1%** earned more than the salary of a bank teller.
  - The longer they traded, the more they lost on average — no evidence of learning at the population level.
  - The few profitable traders did not show persistence beyond what chance would predict.

  This study is particularly important because (a) it uses a complete population, not a self-selected sample, and (b) the CVM commissioned it specifically to evaluate the marketing claims of day-trading "educators." The CVM subsequently issued investor warnings.

### 6.4 FINRA and SEC data

- **FINRA's ongoing risk monitor reports and the SEC's 2020 report on Robinhood, the 2021 GameStop episode reviews, and academic work on commission-free trading platforms** (e.g., Barber, Huang, Odean, Schwarz 2022, "Attention-Induced Trading and Returns: Evidence from Robinhood Users," *Journal of Finance*) show:
  - Commission-free platforms increased turnover dramatically without improving outcomes.
  - "Top traded on Robinhood" lists exhibit reliable underperformance over subsequent weeks (the Robinhood herd effect).
  - Options trading by retail accelerated post-2020; the literature is still catching up but early evidence shows retail option traders lose at rates comparable to or worse than retail equity day traders.

- **The North American Securities Administrators Association (NASAA) and various state regulators** have repeatedly documented that day-trading firms historically were required (under SEC and state guidance) to disclose to prospective customers that the *majority* of day traders lose money. The disclosure language exists because the statistics are that bad.

### 6.5 What this means for our project

We are building a tool that lowers the friction of EOD swing trading. The literature unambiguously predicts that lowering friction without raising skill makes outcomes **worse**, not better. The base rate for retail traders attempting active strategies on equities is in the range of **70–97% losing money over multi-year horizons**, depending on the study and the holding-period definition.

The intellectually honest framings for our engine are:
1. **A learning sandbox** with explicit warnings, paper-trading by default, and small live size caps.
2. **A research tool** for backtest hygiene, walk-forward analysis, and statistical testing — not a "signal generator" for live deployment.
3. **A small-allocation supplement** (≤5–10% of total portfolio) for someone whose core wealth is in indexed, diversified, low-cost, tax-efficient holdings.

What it should **not** be: a "make money swing trading NVDA" turnkey product. The literature is too clear, the cost math is too unforgiving, and the regulatory disclosures exist for a reason.

---

## 7. Concentration Risk Right Now (2024–2025)

The case against mega-cap tech swing trading is sharpened by the current market structure, not just by the long-run statistics.

### 7.1 The Magnificent 7 problem

As of late 2024 / early 2025:
- The "Magnificent 7" (AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA) collectively represent **roughly 30–35% of the S&P 500** by market cap. The exact figure moves with prices; in mid-2024 it crossed 33% on multiple trading days.
- In the **NASDAQ-100 / QQQ**, the Mag 7 weight has been **roughly 45–55%** depending on the month and on whether you count by raw cap-weight or post-rebalance weight. NVDA alone has been 7–9%, MSFT 8–9%, AAPL 8–9% at various points.
- **Market breadth** by various measures (% of S&P 500 stocks outperforming the index, advance-decline divergences, equal-weight vs cap-weight spread) has been at or near multi-decade extremes. The 2023 advance was famously the **narrowest broad-index rally since 1973–74**, with the equal-weight S&P 500 underperforming the cap-weighted S&P 500 by one of the largest annual margins on record.

This matters for technical swing trading because:
- A "diversified" portfolio of QQQ-name swing trades is in fact a **concentrated bet on AI capex, US dollar strength, and a handful of supply chains** (TSMC, ASML, SK Hynix, the hyperscaler capex cycle).
- Correlations spike in drawdowns: when NVDA sells off on an AI-capex rethink, MSFT, GOOGL, META, and AMZN sell off together. A "5-name portfolio" is not 5 bets; it is 1 bet on 5 tickers.
- Position-level risk management (1% per trade) understates portfolio risk when the names co-move at 0.7–0.9 correlation during stress.

### 7.2 The Nifty Fifty parallel (1972–74)

The "Nifty Fifty" — IBM, Xerox, Polaroid, Avon, Disney, McDonald's, Coca-Cola, etc. — were the unquestioned mega-cap quality compounders of the late 1960s and early 1970s. They traded at P/E ratios of 40–90, justified by the narrative of perpetual high-quality growth.

**1972 to late 1974:**
- The S&P 500 fell roughly **48% peak-to-trough.**
- The Nifty Fifty as a group fell roughly **60–70%.**
- Individual names: Polaroid −91%, Avon −86%, Xerox −71%. Even the "highest quality" names — IBM, Disney, McDonald's — drew down 40–60%.

It took the broader Nifty Fifty group **roughly a decade** to recover in nominal terms; in real terms (CPI-adjusted), recovery took into the late 1980s.

The structural parallels to today are not perfect, but they are uncomfortable:
- Narrow leadership at extreme valuations relative to history.
- A coherent narrative (then: "one-decision stocks"; now: "AI capex supercycle") that justifies paying any price.
- Index concentration that mechanically funnels passive flows into the same names.
- High operating margins assumed to persist indefinitely.

### 7.3 The dot-com parallel (2000–02)

NDX peaked in March 2000 and bottomed in October 2002. Peak-to-trough drawdowns:
- **NASDAQ Composite: −78%.**
- **NDX/QQQ: ~−83%.**
- Individual mega-caps of the era:
  - **Cisco (CSCO): −89%** peak-to-trough; **never reclaimed its March 2000 high in nominal terms even by 2024.**
  - **Intel (INTC): −82%** peak-to-trough; only briefly reclaimed the 2000 high in 2020–21 before falling again.
  - **Microsoft (MSFT): −65%** peak-to-trough; took **15 years** to reclaim its 2000 high.
  - **Oracle (ORCL): −84%** peak-to-trough; took over a decade to recover.
  - **Sun Microsystems: ~−96%**, eventually acquired by Oracle.
  - **JDS Uniphase, Nortel, Lucent:** effectively zero.

Key lesson: **the largest, most-loved, most-essential companies of one cycle are not protected from drawdowns of 60–95%.** Microsoft in 2000 was as central to the world as it is in 2024. It still lost two-thirds of its value and took 15 years to recover.

For a swing trader running long-biased technical strategies, the relevant question is not "will mega-cap tech crash 80%?" — nobody knows. The relevant question is: **does our engine include hard rules to avoid being long-and-leveraged into a Mag 7 cliff that resembles 2000–02, even slightly?** If the answer is "no, the engine just keeps trading the signal," we have built a 2002-style account-incineration machine.

### 7.4 The reflexivity problem

George Soros's reflexivity framework, applied to the current regime: passive flows → mega-cap outperformance → more passive flows into mega-cap-heavy indices → more mega-cap outperformance → narrative reinforcement → ... until something breaks the loop (a recession, an AI-capex revaluation, a regulatory action, a geopolitical shock affecting Taiwan, an antitrust ruling). When the loop breaks, it breaks for *all* the names at once, because they are held by the same passive vehicles in the same proportions.

Swing technicals do not anticipate reflexivity unwinds. They follow trends and revert pullbacks. They are systematically wrong-footed at regime breaks.

---

## 8. Passive Flows Eat Alpha: The Inelastic Markets Hypothesis

The most important macro-microstructure paper of the past five years for our question:

- **Gabaix, Xavier, and Ralph S. J. Koijen (2022). "In Search of the Origins of Financial Fluctuations: The Inelastic Markets Hypothesis." NBER Working Paper No. 28967 (originally circulated 2021; revised 2022).**

  Central empirical finding: **a $1 inflow into the US equity market raises aggregate market value by roughly $5.** The aggregate demand curve for equities is *not* nearly flat (as classical theory assumes); it is steeply downward-sloping. Equity prices are far more sensitive to flows than to fundamentals at high frequencies.

  Mechanism: a large fraction of asset ownership (passive funds, target-date funds, pensions with fixed equity allocations, foreign reserve managers) is **mechanically inelastic** — they buy when they receive inflows and sell when they receive outflows, largely regardless of price. The marginal price-setter is a small subset of active capital, and that subset is itself constrained (mandate limits, risk budgets).

### 8.1 What this means for technical signals on mega-cap tech

1. **The "signal" in price is increasingly a flow signal, not a fundamental signal.** When SPY receives a $2bn inflow on a Monday, the top weights — AAPL, MSFT, NVDA, AMZN, GOOGL, META — receive proportional buying that has nothing to do with chart structure. A breakout on NVDA could be flow-driven (and reversible the next day on outflow), not information-driven.

2. **Mean-reversion and trend signals interact unpredictably with flow regimes.** During periods of strong inflows, momentum is amplified mechanically — your trend strategy looks like a genius. During regime shifts (outflow days, quarter-end rebalancing, ETF creation/redemption imbalances), short-term reversion strategies misfire because the "oversold" reading is a flow event, not a sentiment event.

3. **Index-rebalancing events are pure noise to a technical model and pure signal to anyone who knows the rebalance.** NDX annual rebalance, NDX "special rebalance" (as happened in July 2023 to address Mag 7 concentration), S&P 500 quarterly rebalances, Russell reconstitution — all create mechanical flows in mega-caps that swamp normal technical patterns for days around the event.

4. **Concentration of passive ownership makes the names more index-sensitive and less idiosyncratic.** Koijen's later work and follow-ups (e.g., Koijen and Yogo's demand-system asset pricing program) show that names with higher passive ownership exhibit lower idiosyncratic volatility relative to factor exposures, and price discovery becomes more dependent on flow events.

### 8.2 The structural decay argument

Combine Gabaix-Koijen with McLean-Pontiff: not only do published technical signals decay because traders arbitrage them, they decay **faster** in highly-indexed names because the marginal price-setter is less and less an "active trader reading charts" and more and more a "passive vehicle responding to flows." The information content of a daily bar on AAPL is increasingly *about flows*, not about discounted future cash flows or about the behavior of informed traders. Technical signals were developed in markets dominated by active investors. They are being deployed in markets dominated by passive vehicles. The mismatch matters.

### 8.3 Related literature worth knowing

- **Koijen, Ralph S. J., and Motohiro Yogo (2019). "A Demand System Approach to Asset Pricing." *Journal of Political Economy*, 127(4), 1475–1515.** The methodological foundation for thinking about asset prices as the intersection of heterogeneous-investor demand systems.
- **Ben-David, Itzhak, Francesco Franzoni, and Rabih Moussawi (2018). "Do ETFs Increase Volatility?" *Journal of Finance*, 73(6), 2471–2535.** Evidence that ETF ownership increases stock-level volatility, particularly during liquidity events.
- **Pavlova, Anna, and Taisiya Sikorskaya (2023). "Benchmarking Intensity." *Review of Financial Studies*, 36(3), 859–903.** Documents the rise of benchmarking-driven flows and their price impact.

The cumulative picture: mega-cap tech is now a flow-dominated regime where classical technical analysis was designed for a fundamentals-dominated regime. This is a category mismatch, not just a difficulty.

---

## 9. Realistic Alternatives: What an Honest Advisor Would Suggest

If we strip away the desire to "actively trade" and focus on **net-of-cost, net-of-tax, risk-adjusted wealth accumulation**, the menu looks like this. None of these alternatives are exciting. All of them are evidence-based.

### 9.1 Evidence-based passive

- **Total US market: VTI (Vanguard Total Stock Market ETF)** — 0.03% expense ratio, ~3,700 holdings, captures the entire investable US equity market. The Bogle-Sharpe arithmetic argument (Sharpe 1991, "The Arithmetic of Active Management," *Financial Analysts Journal*) guarantees that the average active dollar must underperform the average passive dollar net of costs. Decades of SPIVA reports (S&P Dow Jones Indices' twice-yearly active-vs-index reports) confirm: over 15-year horizons, **80–90% of active US equity managers underperform their benchmarks** net of fees, with the gap widening at longer horizons.
- **Global diversification: VT (Vanguard Total World), or a VTI/VXUS combination.** Home-country bias is a documented behavioral mistake (French-Poterba 1991, "Investor Diversification and International Equity Markets," *AER P&P*). A globally diversified equity sleeve reduces the concentration risk discussed in Section 7.
- **Bonds and stable allocation: BND, VGIT, or short-duration treasuries** for the non-equity portion of the portfolio, sized to risk tolerance, not to return chasing.

### 9.2 Factor and momentum tilts (if you must)

- **MTUM (iShares MSCI USA Momentum Factor ETF)** — captures the cross-sectional momentum premium (Jegadeesh and Titman 1993, "Returns to Buying Winners and Selling Losers," *Journal of Finance*; Asness, Moskowitz, Pedersen 2013, "Value and Momentum Everywhere," *Journal of Finance*) in a low-cost, mechanical, rules-based wrapper. Expense ratio ~0.15%. **The momentum premium is real and has survived out-of-sample replication globally**, but it suffers severe drawdowns during reversals (e.g., March-April 2009, January 2016, March 2020). Using MTUM as a small overlay captures the academic premium without the daily turnover and self-inflicted execution mistakes of running it yourself on individual names.
- **QMOM (Alpha Architect U.S. Quantitative Momentum ETF)** — a more concentrated, higher-conviction momentum implementation. Higher expense ratio (~0.29%) and higher turnover, but a "purer" momentum factor exposure for those who want it.
- **VLUE, AVUV** — value and small-cap value factor exposures, well-supported by Fama-French and subsequent literature. Not relevant to mega-cap tech but relevant to portfolio construction around any tech-heavy core.

### 9.3 Low-volatility / defensive equity

- **SPLV (Invesco S&P 500 Low Volatility ETF), USMV (iShares MSCI USA Min Vol Factor ETF).** Capture the low-volatility anomaly (Frazzini and Pedersen 2014, "Betting Against Beta," *Journal of Financial Economics*) in a wrapper. Over long horizons these have delivered market-like returns with materially lower drawdowns. The anomaly may be partially crowded after 2015 but the diversification benefit remains.

### 9.4 Trend-following / managed futures

- **DBMF (iMGP DBi Managed Futures Strategy ETF), KMLM (KraneShares Mount Lucas Managed Futures Index Strategy ETF), CTA, RSST.** These ETFs implement diversified, multi-asset, time-series-momentum strategies on futures contracts across equities, rates, currencies, and commodities. They exhibit low to negative correlation with equities, particularly during equity drawdowns (2022 was a famous validation year for the category). Expense ratios are higher (0.85–1.0%) but the diversification and drawdown-mitigation benefits during sustained equity bear markets are real and documented (see AQR's "A Century of Evidence on Trend-Following Investing," Hurst, Ooi, Pedersen 2017, *Journal of Portfolio Management*).

**Crucially, these ETFs capture the trend-following premium with institutional execution and proper diversification across dozens of contracts.** A retail attempt to replicate trend-following on a handful of US tech stocks captures none of the diversification benefit (the very thing that makes trend-following work as a strategy class) and all of the execution drag.

### 9.5 When small swing-trading allocations *are* defensible

There is a legitimate, evidence-respecting place for an EOD swing trading sleeve. It looks like this:

1. **Position sizing: ≤ 5–10% of total net worth in the active sleeve.** The remaining 90%+ in evidence-based passive (Sections 9.1–9.4).
2. **Purpose: learning, not income.** The expected value of the sleeve is approximately zero or negative net of costs and time. The justification is intellectual engagement, skill development, and the option value of *possibly* discovering and verifying a real edge — not a planned income stream.
3. **Hard caps:** maximum drawdown the trader is willing to accept on the sleeve before forced shutdown (e.g., −25% triggers a 6-month timeout). Maximum monthly trade count. Maximum single-position exposure.
4. **Paper trade first, for at least 6 months on the live system**, comparing paper results to backtest results to detect implementation drift.
5. **Honest accounting:** include all costs, all taxes, all opportunity cost of time, and benchmark against the cost-free alternative of putting the same capital in MTUM or QQQ.
6. **Pre-registered strategy:** the strategy parameters are written down and committed to git **before** seeing the out-of-sample performance, and not retroactively tweaked after deployment.
7. **A pre-committed quit rule:** "if after N months of live trading my Sharpe is below X, I shut the sleeve down and reallocate to passive." Without a quit rule, you are in the Brazilian-CVM 97%-lose-money cohort by default.

If we cannot enforce these constraints in our engine — by default, with the user having to actively turn off the guardrails to do anything dangerous — then we are building a product that the literature predicts will harm its users.

---

## 10. Anti-Patterns To Never Ship In Our Engine

Concrete, non-negotiable engineering rules. These should be encoded as defaults and as hard limits that require explicit, multi-step opt-out to bypass.

### 10.1 Research / backtest discipline

1. **No parameter optimization without walk-forward analysis.** Any "best parameters" must come from a walk-forward / nested cross-validation procedure with disjoint in-sample and out-of-sample windows. Single-pass grid search reporting the best in-sample result is banned.
2. **No more than 10 strategy variants from a single research session.** If a user wants to test more, they must do so in separate, time-stamped research notebooks with explicit DSR/PBO computation, not by silently expanding the grid.
3. **Mandatory Deflated Sharpe Ratio computation** for any backtest summary screen. If N trials > 1, the DSR must be displayed alongside the raw Sharpe, with a warning if DSR p-value > 0.05.
4. **Mandatory PBO (Probability of Backtest Overfitting) computation** via CSCV for any strategy promoted to "live candidate." Hard refuse to enable live trading on a strategy with PBO > 0.5.
5. **Point-in-time index membership.** Backtests on "QQQ stocks" must use the actual constituent list as of each historical date, not today's list. Survivorship bias is not optional to address.
6. **Transaction costs modeled by default at realistic levels.** Default spread = 1¢ + 0.05 ATR slippage per side. No zero-cost backtests, ever. Users may *raise* costs for stress tests; they may not lower the defaults.
7. **No look-ahead bias.** Strict bar-close semantics. Signals fire on bar close T; orders execute at open T+1 with modeled slippage. No "executes at close T" cheating.
8. **No infinite tweaking.** Each strategy gets a maximum of 3 revision cycles after seeing out-of-sample results before it is killed. Beyond that, the analyst is overfitting to OOS, which is just in-sample with extra steps.

### 10.2 Execution / risk discipline

9. **Risk per trade default ≤ 1%** of account equity. Hard ceiling at 2% with multi-step confirmation. No "5% YOLO" presets.
10. **No leverage by default.** Margin must be explicitly enabled per-session with an acknowledgment of the increased risk. Default account configuration assumes cash equity.
11. **No overnight earnings exposure unhedged.** If a position is open into an earnings announcement, the engine must either (a) auto-close before the announcement, (b) require an explicit confirmation that the user accepts the gap risk, or (c) require an options hedge. Default = auto-close.
12. **Hard portfolio-level concentration caps.** Maximum 20% of equity in any single name. Maximum 40% in any single sector (so a portfolio of NVDA + AMD + AVGO + MU cannot exceed 40% combined). Maximum 60% in any single factor exposure (long momentum, long beta, etc.) as estimated from rolling regressions.
13. **Daily loss limit / kill switch.** Default: account drawdown of 5% in a single day triggers automatic disable of new entries for 24 hours. Account drawdown of 15% from high-water-mark triggers a 7-day timeout requiring manual re-enable.
14. **No martingale or grid sizing.** No averaging down past the original stop. No "add to losers" logic in any form.
15. **No undocumented order types.** Every order placed by the engine must correspond to a logged, reviewable strategy decision with a citable rule. No "scalp" overrides outside the strategy framework.

### 10.3 Statistical / reporting honesty

16. **All performance reports must include:** gross return, net return after modeled costs, after-tax return assuming ordinary-income treatment, Sharpe, Sortino, Calmar, max drawdown, drawdown duration, number of trades, average trade duration, hit rate, average R, and **DSR + PBO**.
17. **All performance reports must compare to passive benchmarks** — at minimum, buy-and-hold of the underlying basket (e.g., equal-weight QQQ for a QQQ-name strategy) and buy-and-hold of the cap-weighted benchmark (QQQ itself, MTUM if momentum-tilted). If the strategy does not beat both, the report must say so prominently, not bury it.
18. **No "since inception" returns that include pre-deployment paper-trading.** Live and paper must be reported separately. Paper performance must be marked clearly as paper.
19. **No equity curves without underlying trade logs.** Every chart must be drillable to the trade list it summarizes.
20. **No "annualized" returns from samples shorter than 1 year.** Annualizing a 3-month return is misleading and triggers exactly the cognitive errors that lead to over-deployment.

### 10.4 Universe and signal discipline

21. **No more than 10–15 symbols in the active universe by default.** Expanding the universe linearly increases multiple-testing exposure and degrades signal quality through attention dilution.
22. **No exotic indicators by default.** Default indicator set is conservative: 20/50/200 SMA, 14-period RSI, 20-period Donchian, 14-period ATR, MACD(12,26,9). Adding novel indicators requires explicit user action and triggers stricter DSR thresholds.
23. **No machine learning models by default.** Any ML-based signal must come with a regularization disclosure, an OOS performance window of at least 2 years, and PBO < 0.3. No black-box "AI signals" hidden in the strategy library.
24. **No high-frequency signal updates.** EOD swing means EOD. Intraday signal recalculation is banned by default; users wanting intraday must explicitly graduate to a separate intraday module with its own risk and cost rules.

### 10.5 User-facing honesty

25. **First-run disclosure screen** that includes: the Barber-Odean 2000 statistic (most traders underperform the market), the Brazilian CVM 2020 statistic (97% of day traders lose money), the McLean-Pontiff decay finding, and the 1.5× backtest → 0.5× live rule of thumb. Acknowledgment required before any live trading.
26. **Default mode = paper trading.** Live mode requires explicit, time-delayed (24-hour cooldown) activation per strategy.
27. **Periodic reality checks.** Quarterly automated email/notification comparing actual live performance to (a) the backtest, (b) the paper-trade record, (c) buy-and-hold of the benchmark. Persistent underperformance vs benchmark triggers a "consider reallocating to passive" recommendation.
28. **No leaderboards, no social features, no "copy this trader" by default.** The Robinhood literature (Barber-Huang-Odean-Schwarz 2022) shows attention-driven trading destroys returns. We will not engineer the same failure mode.

---

## What We Should Believe vs What We Should Doubt

| What we should believe | What we should doubt |
|---|---|
| Mega-cap US tech equity markets are close to weak-form efficient most of the time (Fama 1970, 1991, 2014). | That EOD technical analysis reliably extracts alpha from AAPL/MSFT/NVDA net of costs. |
| Time-varying discount rates explain most price variation, not technical patterns (Cochrane 2011). | That a chart pattern is "the market telling you" anything beyond a flow event. |
| Published predictors decay ~26% out-of-sample and another ~32% post-publication (McLean & Pontiff 2016). | That MA crossovers, RSI(2), Turtle breakouts, or calendar anomalies retain pre-2010 strength on mega-cap tech. |
| The honest t-stat hurdle for new factors is ~3.0 after multiple-testing adjustments (Harvey, Liu, Zhu 2016). | Any backtest result with raw t-stat 2.0–2.5 from a parameter grid search. |
| Observed backtest Sharpe is upward-biased; DSR and PBO are mandatory checks (Bailey & López de Prado 2014, 2017). | A reported Sharpe of 1.8 from a 5-year backtest with no DSR or PBO computation. |
| Live performance typically realizes at ~30–60% of honest backtest Sharpe. | Any business plan that assumes backtest = live performance. |
| Transaction costs eat ~10% of R per round-trip at retail scale on mega-cap tech (worked example, Section 5). | Any backtest run with zero or trivial costs. |
| Most retail traders underperform; ~70–97% lose money over multi-year horizons (Barber-Odean, Chague et al., Taiwan study). | Any anecdotal "I made 80% this year" claim as evidence of a repeatable edge. |
| Concentration in Mag 7 is at extremes comparable to Nifty Fifty 1972 and dot-com 2000. | That "this time is different" because of AI/secular trends. |
| Passive flows now dominate marginal price-setting; inelasticity multiplier ≈ 5× (Gabaix & Koijen 2022). | That technical signals designed for active-investor markets still apply to flow-dominated markets. |
| Buy-and-hold of broad index ETFs is the default that >80% of active managers fail to beat over 15-year horizons (SPIVA). | Any strategy that does not compare itself to buy-and-hold of the relevant benchmark. |
| Trend-following and momentum premia are real but best captured via diversified, low-cost ETFs (MTUM, DBMF, KMLM). | Retail replication of these premia on a small handful of US tech tickers. |
| Pre-registered strategies, walk-forward analysis, and quit rules separate disciplined research from gambling. | Strategies that get "tweaked" after seeing live results. |
| Small (<10% of portfolio) swing-trading sleeves can be defensible as learning tools. | Any framing of swing trading as a primary income strategy or retirement vehicle. |

---

## Engine Red Flags — Hard Rules

If our engine does any of these, we have failed our users and our own intellectual honesty.

- ❌ **No backtest may be reported without modeled transaction costs (≥ 1¢ spread + 0.05 ATR slippage per side).**
- ❌ **No strategy may go live without walk-forward out-of-sample validation across ≥ 3 disjoint windows.**
- ❌ **No strategy may go live with PBO > 0.5 or DSR p-value > 0.05.**
- ❌ **No leverage enabled by default. No margin without explicit per-session opt-in.**
- ❌ **No risk-per-trade default above 1%. Hard ceiling at 2% with confirmation.**
- ❌ **No more than 20% of equity in a single name, ever, without bypassing a hard guard.**
- ❌ **No overnight earnings exposure without auto-close or explicit acknowledged-risk override.**
- ❌ **No parameter grid search above 10 variants without mandatory DSR/PBO recomputation and warning.**
- ❌ **No "best parameters" reported from in-sample data alone.**
- ❌ **No backtest using current index constituents instead of point-in-time membership.**
- ❌ **No equity curve display without underlying trade log access.**
- ❌ **No live trading by default — paper trading first, with a 24-hour cooldown to enable live per strategy.**
- ❌ **No daily drawdown > 5% without an automatic 24-hour cooldown.**
- ❌ **No drawdown > 15% from high-water-mark without a 7-day mandatory timeout.**
- ❌ **No martingale, no averaging down past stop, no "add to losers."**
- ❌ **No undisclosed strategy modifications post-deployment.**
- ❌ **No leaderboards, copy-trading, or attention-amplifying social features.**
- ❌ **No marketing language that implies expected positive returns without referencing the base-rate retail failure literature.**
- ❌ **No suppression of underperformance vs benchmark in periodic reports.**
- ❌ **No use of pre-deployment paper-trading results commingled with live results in performance summaries.**

---

## Appendix A — Extended Notes on the Cited Literature

This appendix expands the citations with the specific findings, methodologies, and limitations that matter for our engineering decisions. It exists so that future contributors to this codebase do not have to re-derive the skeptical case from scratch every time a new strategy idea is proposed.

### A.1 Fama (1970) in detail

The 1970 paper defines:
- **Weak-form efficiency:** the information set is past prices and returns.
- **Semi-strong-form efficiency:** the information set is all public information.
- **Strong-form efficiency:** the information set is all information including private.

Fama surveyed:
- **Serial correlation studies** (Kendall 1953, Fama 1965 "The Behavior of Stock Market Prices") showing that daily and weekly return autocorrelations on US large-caps were small (typically |ρ| < 0.05) and not consistently exploitable after costs.
- **Runs tests** confirming returns are close to but not exactly random walks.
- **Filter rules** (Alexander 1961, 1964): the granddaddy of technical-rule backtesting. Alexander initially claimed profitable filter rules; Fama and Blume (1966, "Filter Rules and Stock Market Trading," *Journal of Business*) showed that once realistic transaction costs and dividends were included, the rules produced returns below buy-and-hold for nearly all filter sizes.
- **Event studies** (Fama, Fisher, Jensen, Roll 1969 — the original event-study methodology paper) showing rapid price adjustment to stock splits.

The 1970 paper's pessimistic take on the exploitability of weak-form patterns has been the consensus among financial economists for over half a century, with periodic mild updates (the momentum literature being the most important exception).

### A.2 Fama (1991) in detail

The 1991 update reorganized the framework around what is being tested:
- "Tests of return predictability" (replacing weak-form),
- "Event studies" (replacing semi-strong),
- "Tests of private information" (replacing strong-form).

Key updated findings circa 1991:
- Long-horizon (3–5 year) return predictability from dividend yields, default spreads, and term spreads is real and economically meaningful — but operates at horizons no swing trader can use.
- Short-horizon return autocorrelations in individual stocks are slightly negative (mild reversal) and in indices are slightly positive (mild momentum), but the economic magnitudes are typically too small to overcome trading costs.
- The size effect (Banz 1981) was already showing signs of decay post-1980.
- The value effect (Basu 1977, Rosenberg-Reid-Lanstein 1985) was robust but interpretable as a risk premium.

The 1991 paper is, in many ways, more nuanced than the 1970 paper. Fama explicitly concedes anomalies; the empirical landscape is messier than the original elegant statement. But the core message — *don't expect to beat the market by reading charts on liquid US stocks* — stands.

### A.3 Fama (2014) in detail

The Nobel Lecture acknowledges:
- The Fama-French five-factor model (Fama-French 2015) with market, size, value, profitability, and investment as risk factors explains a large fraction of the cross-section of returns.
- Momentum (Jegadeesh-Titman 1993) is a persistent embarrassment to the three-factor model: it has positive risk-adjusted returns that don't fit clean risk-factor stories.
- The joint-hypothesis problem means efficiency can never be cleanly rejected; we can only reject specific equilibrium asset-pricing models.

For swing traders, the Nobel lecture is humbling in a specific way: even *Fama* acknowledges momentum is an anomaly. But the academically clean way to capture momentum is via diversified cross-sectional factor portfolios with monthly or quarterly rebalancing (the Asness/AQR program), not via daily-bar technicals on six tickers.

### A.4 Cochrane (2011) Discount Rates in detail

Cochrane's Presidential Address makes three central claims:
1. **Variance decomposition:** virtually all variance in price/dividend or price/earnings ratios is attributable to variation in expected returns (discount rates), not to variation in expected cash flows.
2. **All risk premia are now understood to be time-varying** — equity, bonds, FX, real estate, credit. The "expected return" is a moving target driven by economic conditions, intermediary balance sheets, and sentiment.
3. **The next 50 years of asset pricing research are about understanding *why* discount rates vary** (intermediary capital, habit formation, long-run risks, rare disasters, behavioral mechanisms), not about finding new return predictors.

The implication for technical analysis is subtle but profound. A trend in price typically reflects a *change in the discount rate the market is applying to a stock's cash flows*. By the time the trend is visible on the daily chart, the discount-rate move has already happened. A trend-following technical strategy is, at best, betting on momentum in discount-rate updates — and that is precisely the cross-sectional momentum literature, which is best captured via diversified factor ETFs, not single-name swing trades.

### A.5 McLean & Pontiff (2016) in granular detail

Methodology:
- Identified 97 cross-sectional return predictors from the published academic literature (e.g., accruals, asset growth, momentum sub-variants, profitability proxies).
- For each predictor, defined three samples:
  - **Original sample:** the exact data window of the original paper.
  - **Out-of-sample, pre-publication:** the gap between the end of the original sample and the date of publication (or earliest working-paper circulation).
  - **Post-publication:** the period after publication.
- Built long-short portfolios on each predictor and tracked monthly returns.

Findings:
- Mean predictor return: ~58 bps/month in-sample.
- Mean predictor return out-of-sample, pre-publication: ~43 bps/month (a 26% decline, suggesting in-sample overfitting / data-mining bias accounts for some of the original effect).
- Mean predictor return post-publication: ~29 bps/month (an additional ~32% decline relative to pre-publication out-of-sample, suggesting active arbitrage by post-publication market participants).
- **Predictors with characteristics that make them easier to arbitrage** (large-cap, liquid, lower idiosyncratic risk) decay faster — exactly the regime that AAPL/MSFT/NVDA inhabit.
- Cross-predictor correlation in post-publication returns increases, suggesting arbitrageurs are deploying multi-factor strategies that link previously independent anomalies.

For a 2025 swing trader on mega-cap tech, the predictable interpretation: any "edge" published in a 2008 book or a 2012 quantitative finance paper should be assumed to have decayed by ~50% on these specific names. If your backtest doesn't show that decay, your backtest is broken (most likely: leaks, look-ahead, or implicit survivorship).

### A.6 Harvey, Liu, Zhu (2016) in granular detail

Methodology:
- Catalogued 316 factors from 313 papers in top finance journals (JF, JFE, RFS) from 1967 to 2014.
- Applied multiple-testing corrections appropriate to the publication process (sequential testing, peer-review filtering for high t-stats).
- Recommended t-stat thresholds:
  - **Bonferroni:** t > 4.9 for the most recent factors (very conservative).
  - **Holm:** t > 3.78.
  - **Benjamini-Hochberg-Yekutieli (FDR control):** t > 3.39.
  - A reasonable practitioner threshold: **t > 3.0** for new factors.

Key implications:
- The conventional t > 2.0 threshold yields a false-discovery rate so high that most published factors are likely Type I errors.
- The "factor zoo" is mostly noise after correction.
- Factors that survive higher t-stat thresholds and survive McLean-Pontiff style post-publication tests (e.g., classical Fama-French factors, cross-sectional momentum) are a small minority of the published literature.

For our backtest infrastructure: every grid search is implicitly running hundreds of statistical tests. The reported t-statistic of the best variant must be deflated by the search size. This is what Bailey & López de Prado formalize.

### A.7 Bailey & López de Prado (2014, 2017) — the DSR and PBO machinery

The **Deflated Sharpe Ratio** intuition:

The expected maximum of N i.i.d. trial Sharpes (under null hypothesis of zero true skill) is approximately:

```
E[max SR] ≈ sqrt(2 * log(N)) * sigma_SR
```

where sigma_SR is the cross-trial standard deviation of Sharpe ratios. For N = 100 trials and sigma_SR = 0.5 (typical for technical-rule grid searches), this gives E[max SR] ≈ 1.5 purely from luck.

The **Probability of Backtest Overfitting (PBO)** via Combinatorially Symmetric Cross-Validation (CSCV):
1. Divide your full backtest period into S equal sub-samples (S even).
2. Form all (S choose S/2) combinations of "in-sample" sub-samples.
3. For each combination: rank the N strategies in-sample, find the in-sample best; check its rank in the out-of-sample (complementary) sub-samples.
4. PBO = the fraction of combinations where the in-sample best ranks below the median out-of-sample.

A robust strategy should yield PBO close to 0. A pure curve-fit yields PBO close to 1. Our engine should refuse to deploy strategies with PBO > 0.5.

**Minimum Track Record Length (MinTRL):** for typical equity-like return distributions, distinguishing Sharpe = 1.0 from Sharpe = 0 at 95% confidence requires approximately **2–3 years** of daily data. Distinguishing Sharpe = 1.5 from Sharpe = 1.0 (i.e., showing your strategy beats QQQ buy-and-hold) requires **5–7 years**. Most retail backtests have insufficient data to support the claims being made.

### A.8 Barber-Odean canon — global replication

The Barber-Odean findings have been replicated in:
- **Sweden** (Calvet, Campbell, Sodini 2007, 2009): retail underperformance, undiversification, disposition effect all confirmed.
- **Finland** (Grinblatt-Keloharju series, 2000–2009): same patterns.
- **China** (Feng-Seasholes 2005, Chen-Kim-Nofsinger-Rui 2007): retail underperformance and the disposition effect even more pronounced.
- **Germany, Netherlands, France**: smaller-sample studies, same direction.

The Barber-Odean findings are among the most robust facts in empirical finance. They are not American quirks. They are universal patterns of retail trader behavior.

### A.9 Chague-De-Losso-Giovannetti (2020) — methodological notes

The Brazilian study is particularly hard to dismiss because:
- **Complete population**, not a sample. Every retail futures day trader registered between 2013 and 2015.
- **Long observation window**: at least 300 days per trader.
- **All costs included**: explicit fees, taxes, and slippage embedded in observed P&L.
- **Independent verification**: data sourced from B3 (the Brazilian exchange) under CVM regulatory authority.

The 97% loss rate is robust to definitional choices about "day trader" (different lookback windows, different minimum trade counts). The minority that profits is small, and there is no evidence of skill persistence — profitable months are statistically indistinguishable from random.

### A.10 Gabaix-Koijen (2022) — mechanism and implications

The Inelastic Markets Hypothesis empirical strategy:
- Identify exogenous flow shocks (e.g., reserve manager rebalancing, pension fund target-date adjustments).
- Measure the price impact of these shocks on aggregate equity prices.
- Estimate the **macro elasticity of demand** for equities.

Estimated multiplier: $1 inflow → ~$5 increase in aggregate market value. This is roughly **two orders of magnitude larger** than the multiplier implied by classical efficient-market theory (which predicts an elasticity close to flat — flows shouldn't move prices much because informed arbitrageurs absorb them).

Mechanism:
- A large share of equity ownership is mandate-constrained (passive index funds, target-date glide paths, foreign reserve managers, insurance company general accounts).
- These holders are *price-inelastic* — they buy when they receive inflows, sell when they receive outflows, regardless of price levels.
- The marginal price-setter is a small fraction of "active" capital, and that capital is itself constrained (risk budgets, VaR limits, drawdown stops).
- Equity prices therefore respond to flows by a much larger multiplier than fundamentals would predict.

Direct implications for mega-cap tech:
- These names are the **top holdings of essentially every passive vehicle**. They are the most flow-sensitive stocks in the US market.
- A technical pattern on NVDA is increasingly a flow pattern, not an information pattern.
- Index-rebalancing events (NDX special rebalance July 2023, S&P 500 quarterly rebalances, Russell reconstitution) create predictable mechanical flows that swamp technical signals around the event window.

For our engine, this means **flow-aware features (e.g., distance from index rebalance dates, ETF creation/redemption imbalance proxies) may be more informative than classical technical indicators** — but we are not building a flow-trading system; we are building a technical-analysis system, and we should be honest that the underlying signal is degrading as the market structure shifts.

---

## Appendix B — A More Realistic Cost Worksheet

Section 5 used a simplified cost model. Here is a more realistic accounting that the engine should default to.

### B.1 Per-trade cost components

For each round-trip on a US-listed equity at retail scale:

1. **Quoted spread** (NBBO bid-ask):
   - AAPL, MSFT: typically 1¢ on $200+ stock (~0.5 bps).
   - NVDA: typically 1–2¢ on $140 stock (~0.7–1.4 bps).
   - TSLA: typically 1–3¢ on $200–250 stock (~0.4–1.5 bps), wider during vol.
   - Smaller QQQ constituents: 1–5¢ depending on price and time of day.
   - **Cost paid by aggressing orders**: half-spread on entry + half-spread on exit ≈ full spread per round-trip.

2. **Effective spread (vs midpoint at order arrival):**
   Typically 0.8–1.2× the quoted spread for retail-sized marketable orders, because of brief midpoint moves between order arrival and execution.

3. **Market-impact slippage on size:**
   For orders < 0.1% of average daily volume, impact is negligible (< 1 bp). For 50–500 share orders on mega-cap tech, this is the regime.
   For orders > 0.5% of ADV, square-root impact models (Almgren-Chriss style) predict impact of several bps to tens of bps.

4. **Time-of-day slippage:**
   Spreads widen and effective costs increase at the open (9:30–9:45 ET) and around closing auction (15:55–16:00 ET). If our engine sends MOO/LOO orders, we should model auction slippage explicitly.

5. **Slippage on stop-loss execution:**
   Stops in fast markets execute meaningfully worse than the stop price. Typical adverse slippage: 0.1–0.3 ATR. On a 1-ATR stop, this is 10–30% of R on losing trades.

6. **Overnight and weekend gap risk:**
   For a swing system holding overnight: every position is exposed to overnight gap risk that cannot be mitigated by a daytime stop. Empirically, single-name overnight gaps of 2–5% occur regularly on news; gaps of 10%+ occur multiple times per year on earnings or major news.

7. **Earnings gap risk:**
   On 4 earnings days per year per name, the absolute overnight gap averages roughly 5–8% on mega-cap tech, with frequent outliers of 10–20%+. Holding into earnings is effectively selling an at-the-money straddle for free.

8. **Commissions:**
   At zero-commission brokers (Robinhood, Schwab, Fidelity, IBKR Lite), commissions are nominally $0. But:
   - **Payment for order flow (PFOF):** zero-commission brokers route orders to wholesale market-makers (Citadel, Virtu) who execute against their own books. The execution quality is typically within 1–2 bps of NBBO midpoint, but the *whole reason PFOF is profitable for wholesalers* is that retail orders are slightly worse-priced than they would be at midpoint. This is a hidden cost embedded in the spread.
   - **IBKR Pro and other pro tiers:** commissions of ~0.5¢/share, with explicit routing. Often produces better fills net of commissions than PFOF venues.

9. **Regulatory fees (sell side only):**
   - SEC Section 31 fee: $27.80 per $1M of sell-side principal (as of late 2024; updated annually).
   - FINRA TAF (Trading Activity Fee): $0.000166/share, capped at $8.30 per trade.
   - Negligible per-trade for retail but should be modeled.

10. **Borrow costs (short side):**
    Mega-cap tech is typically easy-to-borrow at GC rates (low single-digit basis points per day). But during squeezes or special situations (e.g., index inclusion/exclusion events), borrow rates can spike to 5–50% annualized for hard-to-borrow names.

11. **Taxes (most ignored, most impactful):**
    - **Short-term capital gains** (positions held ≤ 1 year) taxed at federal ordinary-income rates: 10–37% depending on bracket, plus 3.8% NIIT for high earners, plus state income tax (0–13.3% in California).
    - A swing system holding positions for days to weeks generates **100% short-term gains**.
    - For a top-bracket California trader: combined STCG rate ≈ 50%+.
    - **The same dollar of pre-tax gain produces ~50¢ of after-tax wealth** for a high-bracket trader. The buy-and-hold alternative (LTCG at 15–23.8% federal) is dramatically more tax-efficient.
    - **Wash-sale rules** further complicate loss harvesting in active trading.

### B.2 Worked example, extended

Same setup as Section 5: $25k account, NVDA at $140, ATR $5, 1% risk, 50-share position, 1-ATR stop.

| Cost component | Per round-trip | As % of R ($250) |
|---|---|---|
| Quoted spread (1¢ × 2 sides × 50 sh) | $1.00 | 0.4% |
| Effective spread premium (~25%) | $0.25 | 0.1% |
| Slippage on entry (0.05 ATR) | $12.50 | 5.0% |
| Slippage on exit at limit/MOC | $5.00 | 2.0% |
| Slippage on stop-loss (0.2 ATR, on losing trades, weighted 50%) | $12.50 | 5.0% |
| Commission (zero-comm broker) | $0.00 | 0.0% |
| Hidden PFOF spread leakage (~0.5 bps notional × 2) | $0.70 | 0.3% |
| SEC + FINRA fees (sell side) | $0.02 | <0.1% |
| **Subtotal direct costs** | **~$32** | **~12.8%** |
| Tax drag on gains (assuming +0.15R net pre-tax, 50% STCG rate) | $18.75 | 7.5% (on wins) |
| Overnight gap "tail tax" (rare but large) | probabilistic | 1–3% |

**Realistic round-trip cost: ~13–16% of R**, with additional tax drag on gains.

Recompute the expectancy:
- Raw expectancy: +0.25R per trade.
- Net of direct costs: +0.25R − 0.13R = **+0.12R per trade**.
- Net of tax on the gains portion: ≈ **+0.06–0.08R per trade**.

Sharpe recomputation at 100 trades/year:
- Mean annual return: ~6–8% (post-cost, post-tax).
- Std dev: ~12%.
- **After-tax Sharpe: ~0.5–0.7.**

Compare to the alternative: hold QQQ. ~10-year trailing Sharpe ~1.0 (gross), ~0.85 (after-tax for buy-and-hold). The swing strategy needs to **clear 0.85 after-tax** to add value, which means **gross Sharpe before tax of ~1.2**, which means **backtest Sharpe (with the 0.5× discount) of ~2.4**.

This is hard. Most strategies don't clear it.

### B.3 Why the engine must default to these costs

If we let users (or ourselves) run "frictionless" backtests, we will inevitably:
1. Be excited about strategies that have no real edge.
2. Deploy them.
3. Lose money in line with the literature predictions.

The cost defaults are the **single most important guardrail** against the cognitive trap of pretty backtests. They are non-negotiable.

---

## Appendix C — Strategy-Class Decay Notes

A working catalog of strategy classes and what we know about their post-2010 viability on mega-cap US tech specifically.

### C.1 Cross-sectional momentum (winner-minus-loser portfolios)
- **Status:** Real, but compressed.
- **Original evidence:** Jegadeesh-Titman 1993.
- **Post-2000 decay:** Significant. The 12-month minus 1-month momentum factor on US large-caps has a post-2000 Sharpe roughly half its pre-2000 level. The 2009 momentum crash and the 2016 reversal are vivid examples of left-tail behavior.
- **Implication:** If we want momentum exposure, MTUM/QMOM ETFs are dominant. A daily-bar single-name implementation will not capture the diversified factor premium.

### C.2 Time-series momentum / trend-following on single stocks
- **Status:** Marginal-to-negative on US large-caps after costs.
- **Original evidence:** Moskowitz-Ooi-Pedersen 2012 (futures, not single stocks).
- **Post-2010 decay:** On single US large-caps, multi-month trend-following has produced returns close to buy-and-hold minus turnover costs. The diversification benefit that makes trend-following work on diversified futures portfolios is absent in a 5–10 name tech universe.
- **Implication:** DBMF/KMLM for the trend-following premium; do not attempt single-stock trend on mega-cap tech as a primary strategy.

### C.3 Short-term mean reversion (RSI(2), 3-day pullback, etc.)
- **Status:** Decayed sharply post-2010, especially post-2015.
- **Original evidence:** Connors-Alvarez 2008, plus academic literature on short-term reversal (Jegadeesh 1990, Lehmann 1990, Lo-MacKinlay 1990).
- **Mechanism of original effect:** Microstructure inventory-rebalancing by specialists/market-makers in pre-decimalization and early post-decimalization markets.
- **Post-2010 decay:** HFT and stat-arb desks have arbitraged most of the effect. On SPY/QQQ, the post-2015 net-of-cost Sharpe of canonical RSI(2) rules is approximately zero. On individual mega-cap tech, it's worse — these names have strong trending behavior that makes "buy oversold" a recipe for catching knives.
- **Implication:** Do not include short-term mean reversion as a default strategy without explicit warning about post-2010 decay.

### C.4 Breakout strategies (Donchian, Turtle-style)
- **Status:** Marginal on single equities; better-validated on diversified futures.
- **Issue on mega-cap tech:** False breakouts are common around earnings, around index rebalance dates, around macro events. Single-name implementations suffer from headline whipsaw.
- **Implication:** If included, must be paired with strong filters (volatility regime, market regime, earnings blackout windows) and tested with full multiple-testing discipline.

### C.5 Volatility-based mean reversion (Bollinger band fades, etc.)
- **Status:** Mixed; depends heavily on regime.
- **Issue:** Works in choppy markets, fails in trending markets. Mega-cap tech has had multiple year-long trends (2017, 2020 H2, 2023, 2024) where volatility-based reversion strategies got run over.
- **Implication:** Regime-conditional logic is required; without it, these strategies are coin-flips at best.

### C.6 Pattern-based (head-and-shoulders, triangles, flags)
- **Status:** Negligible academic support; high subjective interpretation.
- **Original evidence:** Lo-Mamaysky-Wang (2000), "Foundations of Technical Analysis," *Journal of Finance*, used kernel regression to objectively identify patterns. Found *some* statistical content in certain patterns on US individual stocks 1962–1996, with effect sizes too small to overcome costs.
- **Post-2000 evidence:** Follow-up studies have not replicated even the modest findings on post-2000 large-caps.
- **Implication:** Do not include subjective pattern-recognition rules. If included for educational purposes, label as such.

### C.7 Earnings-event strategies (PEAD, drift, surprise-based)
- **Status:** Real anomaly (post-earnings announcement drift, Bernard-Thomas 1989, 1990), decayed but not gone.
- **Issue:** Operating in this space requires fundamental data (earnings surprise vs. consensus) and is not pure EOD technicals. Also, the holding period is days-to-weeks post-announcement, with significant volatility.
- **Implication:** Out of scope for a pure technical engine; could be a future extension with proper data integration.

### C.8 Calendar/seasonal strategies
- **Status:** Mostly decayed in US large-caps post-2010.
- **Implication:** Do not rely on calendar effects as primary signals. Note them as context only.

### C.9 Sentiment / news / alternative-data strategies
- **Status:** Active research area; institutional advantage is real.
- **Issue:** Retail does not have access to the data sources (tick-level news feeds, satellite imagery, credit-card transaction panels, etc.) that drive institutional sentiment alpha.
- **Implication:** Out of scope for our engine. Do not pretend retail sentiment scraping competes with institutional alt-data.

---

## Appendix D — A Pre-Mortem

Imagine it is 12 months after we ship the engine. Things have gone badly. What does the post-mortem say?

### D.1 The most likely failure mode

We shipped an engine that backtested beautifully. Users deployed it with real money. After 9–12 months of live trading, the average user's account is down 15–30% net of taxes, vs a benchmark QQQ return that was up or flat. We discover, on retrospective analysis:

1. The strategies that backtested at Sharpe 1.8 are running at live Sharpe 0.3.
2. The cost model in the backtester understated real-world slippage by 30–50%.
3. Users overrode the risk-per-trade default, the leverage default, and the earnings-blackout default, individually or collectively.
4. The DSR / PBO warnings were dismissed as "stats jargon" and not enforced as hard refusals.
5. Drawdowns triggered behavioral overrides (revenge trading, parameter tweaking, universe expansion).
6. The paper-trading discipline collapsed within weeks of deployment.

This is the predictable failure mode. The Barber-Odean / Brazilian-CVM / Taiwan-day-trader literature is the post-mortem of this exact story, written in advance, in three different countries, over thirty years.

### D.2 The second most likely failure mode

We shipped a too-conservative engine with so many guardrails that users in our target audience found it unusable, switched to TradingView / ThinkOrSwim / a competitor's tool, and lost money there instead. We failed to provide the value (skill development, statistical discipline) we believed our guardrails would enable.

This is also bad — but it is *less bad* than the first failure mode, because at least we did not amplify the harm.

### D.3 The hope-case

Users trade in paper for 3–6 months, see that their strategies don't perform as well as the backtest, internalize the discipline, reallocate the bulk of their capital to passive vehicles, and use the engine as a small (5–10%) learning sandbox where they continuously refine their understanding of statistical edges. A small minority discover an actual edge through rigorous walk-forward research, deploy it with disciplined risk management, and outperform passive by a modest margin (1–3% annualized) for several years.

This is the best realistic outcome. We should design for this, not for the marketing-deck outcome of "make money trading mega-cap tech."

---

## Appendix E — Citations List

For ease of reference, the canonical citations that underpin this document.

**Efficient Markets and Asset Pricing**
- Fama, Eugene F. (1970). "Efficient Capital Markets: A Review of Theory and Empirical Work." *Journal of Finance*, 25(2), 383–417.
- Fama, Eugene F. (1991). "Efficient Capital Markets: II." *Journal of Finance*, 46(5), 1575–1617.
- Fama, Eugene F. (2014). "Two Pillars of Asset Pricing." *American Economic Review*, 104(6), 1467–1485.
- Fama, Eugene F., and Kenneth R. French (2015). "A Five-Factor Asset Pricing Model." *Journal of Financial Economics*, 116(1), 1–22.
- Cochrane, John H. (2011). "Presidential Address: Discount Rates." *Journal of Finance*, 66(4), 1047–1108.

**Anomaly Decay and Multiple Testing**
- McLean, R. David, and Jeffrey Pontiff (2016). "Does Academic Research Destroy Stock Return Predictability?" *Journal of Finance*, 71(1), 5–32.
- Harvey, Campbell R., Yan Liu, and Heqing Zhu (2016). "...and the Cross-Section of Expected Returns." *Review of Financial Studies*, 29(1), 5–68.
- Sullivan, Ryan, Allan Timmermann, and Halbert White (1999). "Data-Snooping, Technical Trading Rule Performance, and the Bootstrap." *Journal of Finance*, 54(5), 1647–1691.
- Brock, William, Josef Lakonishok, and Blake LeBaron (1992). "Simple Technical Trading Rules and the Stochastic Properties of Stock Returns." *Journal of Finance*, 47(5), 1731–1764.

**Backtest Overfitting**
- Bailey, David H., and Marcos López de Prado (2012). "The Sharpe Ratio Efficient Frontier." *Journal of Risk*, 15(2), 13–44.
- Bailey, David H., and Marcos López de Prado (2014). "The Deflated Sharpe Ratio." *Journal of Portfolio Management*, 40(5), 94–107.
- Bailey, Borwein, López de Prado, Zhu (2014). "Pseudo-Mathematics and Financial Charlatanism." *Notices of the AMS*, 61(5), 458–471.
- Bailey, Borwein, López de Prado, Zhu (2017). "The Probability of Backtest Overfitting." *Journal of Computational Finance*, 20(4), 39–69.
- López de Prado, Marcos (2018). *Advances in Financial Machine Learning*. Wiley.

**Momentum and Factors**
- Jegadeesh & Titman (1993). "Returns to Buying Winners and Selling Losers." *Journal of Finance*, 48(1), 65–91.
- Asness, Moskowitz, Pedersen (2013). "Value and Momentum Everywhere." *Journal of Finance*, 68(3), 929–985.
- Moskowitz, Ooi, Pedersen (2012). "Time Series Momentum." *Journal of Financial Economics*, 104(2), 228–250.
- Frazzini & Pedersen (2014). "Betting Against Beta." *Journal of Financial Economics*, 111(1), 1–25.
- Hurst, Ooi, Pedersen (2017). "A Century of Evidence on Trend-Following Investing." *Journal of Portfolio Management*, 44(1), 15–29.

**Retail Trader Behavior**
- Barber & Odean (2000). "Trading Is Hazardous to Your Wealth." *Journal of Finance*, 55(2), 773–806.
- Barber & Odean (2001). "Boys Will Be Boys." *Quarterly Journal of Economics*, 116(1), 261–292.
- Barber, Lee, Liu, Odean (2014). "The Cross-Section of Speculator Skill." *Journal of Financial Markets*, 18, 1–24.
- Barber & Odean (2013). "The Behavior of Individual Investors." In *Handbook of the Economics of Finance*.
- Barber, Huang, Odean, Schwarz (2022). "Attention-Induced Trading and Returns." *Journal of Finance*, 77(6), 3141–3190.
- Chague, De-Losso, Giovannetti (2020). "Day Trading for a Living?" Working paper.
- Linnainmaa (2011). "Why Do (Some) Households Trade So Much?" *Review of Financial Studies*, 24(5), 1630–1666.
- Odean (1998). "Are Investors Reluctant to Realize Their Losses?" *Journal of Finance*, 53(5), 1775–1798.
- Shefrin & Statman (1985). "The Disposition to Sell Winners Too Early and Ride Losers Too Long." *Journal of Finance*, 40(3), 777–790.

**Market Structure and Flows**
- Gabaix & Koijen (2022). "In Search of the Origins of Financial Fluctuations: The Inelastic Markets Hypothesis." NBER WP 28967.
- Koijen & Yogo (2019). "A Demand System Approach to Asset Pricing." *Journal of Political Economy*, 127(4), 1475–1515.
- Ben-David, Franzoni, Moussawi (2018). "Do ETFs Increase Volatility?" *Journal of Finance*, 73(6), 2471–2535.
- Pavlova & Sikorskaya (2023). "Benchmarking Intensity." *Review of Financial Studies*, 36(3), 859–903.

**Other Foundational Work**
- Sharpe (1991). "The Arithmetic of Active Management." *Financial Analysts Journal*, 47(1), 7–9.
- Lo, Mamaysky, Wang (2000). "Foundations of Technical Analysis." *Journal of Finance*, 55(4), 1705–1765.
- Bernard & Thomas (1989). "Post-Earnings-Announcement Drift." *Journal of Accounting Research*, 27, 1–36.
- Malkiel & Saha (2005). "Hedge Funds: Risk and Return." *Financial Analysts Journal*, 61(6), 80–88.
- Lo (2017). *Adaptive Markets*. Princeton University Press.
- Faith (2007). *Way of the Turtle*. McGraw-Hill.
- Connors & Alvarez (2008). *Short Term Trading Strategies That Work*.
- Schwager (1989). *Market Wizards*.

---

## Appendix F — Drawdown Catalogue: Mega-Cap Tech, 2000–2024

A reference table of the largest drawdowns experienced by the current Mag 7 and selected predecessors. The point is not to predict the next drawdown but to anchor risk expectations.

### F.1 Drawdowns by name

**AAPL (post-IPO history)**
- 1985–1997: extended multi-year drawdowns up to ~80% from peaks.
- 2000–2003: dot-com era, ~80% drawdown from late-1999 highs to 2003 lows (pre-iPod).
- 2008–2009: ~60% drawdown during GFC.
- 2012–2013: ~45% drawdown post-Steve Jobs era / post-iPhone 5 peak.
- 2018–2019: ~38% drawdown on China/iPhone demand concerns.
- 2020 (Mar): ~30% drawdown over ~5 weeks (Covid).
- 2022: ~31% drawdown peak-to-trough.

**MSFT**
- 2000–2002: ~65% drawdown.
- 2008–2009: ~50% drawdown.
- 2022: ~38% drawdown.
- Time to recover 2000 peak (in price terms): ~15 years (mid-2016).

**GOOGL (post-IPO 2004)**
- 2008–2009: ~65% drawdown.
- 2022: ~45% drawdown.
- 2024 Q3: ~25% drawdown on regulatory and AI-competition concerns.

**AMZN**
- 1999–2001: ~95% drawdown peak-to-trough (the most famous dot-com survival).
- 2008–2009: ~65% drawdown.
- 2018–2019: ~35% drawdown.
- 2021–2022: ~55% drawdown peak-to-trough.

**META (post-IPO 2012)**
- 2012–2013: ~55% drawdown shortly post-IPO.
- 2018 (July–Dec): ~45% drawdown on Cambridge Analytica + earnings concerns (largest single-day market-cap loss in history at the time).
- 2021–2022: ~77% drawdown peak-to-trough on Reality Labs spending + ad headwinds.

**NVDA**
- 2001–2002: ~90% drawdown.
- 2008–2009: ~85% drawdown.
- 2018–2019 (Oct–Dec): ~56% drawdown on crypto unwind + datacenter pause.
- 2021–2022: ~66% drawdown peak-to-trough.
- Multiple intra-year 15–25% drawdowns during the 2023–2024 AI-capex bull run.

**TSLA**
- 2020 H2 → 2021 H1: ~36% drawdown after the parabolic late-2020 move.
- 2021–2023: ~75% drawdown peak-to-trough.
- Multiple 20–40% intra-year drawdowns since IPO.

**Predecessor mega-caps (cautionary tales)**
- **Cisco (CSCO):** ~89% drawdown 2000–2002. **Never reclaimed the 2000 nominal high** as of 2024 — a 24-year underwater period for what was, in 2000, the most valuable company in the world.
- **Intel (INTC):** ~82% drawdown 2000–2002. Briefly reclaimed in 2020–2021; fell sharply again in 2022–2024.
- **Oracle (ORCL):** ~84% drawdown 2000–2002. Took over a decade to recover.
- **EMC (now part of Dell):** ~95% drawdown 2000–2002.
- **Sun Microsystems:** ~96% drawdown; eventually acquired by Oracle in 2010.
- **Lucent, Nortel, JDS Uniphase:** effectively zero.

### F.2 Implications for swing trading risk management

- **Single-name drawdowns of 30–80% are normal**, even for the highest-quality mega-cap tech names, over multi-year windows.
- **A swing strategy long-only on these names will participate in their drawdowns** unless its trend/regime filters explicitly de-risk during cyclical downturns — and even then, regime filters lag and tend to keep you long into the first 10–20% of a major correction.
- **The "buy the dip" reflex on mega-cap tech worked spectacularly from 2009–2021 and from 2023–2024.** It failed spectacularly in 2000–2002 and in 2022. Strategies that backtest only on the favorable regime are dangerously selection-biased.
- **Position sizing must account for the realized historical drawdown distribution**, not the post-2009 sub-sample. A 1% R sizing assumes diversification will smooth single-name volatility, but in a concentrated 5–10 name mega-cap-tech portfolio, correlations spike to 0.7–0.9 in drawdowns and the diversification benefit disappears precisely when you need it.

### F.3 The CAGR illusion

An easy mistake when designing strategies: backtesting on a sample that contains the 2009–2021 bull market and reporting the CAGR. QQQ CAGR over that window was roughly **20% annualized**, with low realized volatility relative to history. Any reasonable long-only strategy on mega-cap tech in that window would have produced a beautiful equity curve. None of that is evidence of strategy skill; it is evidence of regime favorability. The honest backtest must include 2000–2002, 2008–2009, 2018 Q4, 2022 — the full bear-market and choppy-regime sample — to have any predictive value for the next decade.

---

## Appendix G — Behavioral Failure Modes Specific to Swing Trading

Beyond the cognitive biases catalogued in the Barber-Odean canon, swing trading on mega-cap tech triggers a specific suite of behavioral failure modes that the engine must defend against.

### G.1 The asymmetric attention problem

Mega-cap tech names dominate financial media. AAPL earnings, NVDA earnings, TSLA tweets, META antitrust headlines — these events generate dramatically more retail attention than equivalent events at smaller companies. The literature (Barber-Odean 2008, "All That Glitters," *Review of Financial Studies*) shows attention-driven trading systematically underperforms because retail buys at peaks of attention (which coincide with peaks of price). Building a swing engine on the names that generate the most attention is building on top of a known cognitive trap.

### G.2 The anchor-to-recent-highs problem

Swing traders systematically anchor to recent highs and set targets relative to them ("NVDA was $140 last month, it'll get back there"). The behavioral finance literature on anchoring (Tversky-Kahneman 1974, *Science*) and the disposition effect (Shefrin-Statman 1985) predicts this leads to holding losers too long and exiting winners too early — the precise opposite of the trend-following discipline that mega-cap tech requires.

### G.3 The narrative-update problem

Mega-cap tech narratives (AI capex, antitrust, regulatory) shift rapidly and dramatically. Swing traders who entered on "NVDA AI tailwind" in January find themselves in June rationalizing the same position under "NVDA gross margins peaking but multiple still has room." Narrative-rationalized position holding is one of the most common ways disciplined risk management is silently abandoned.

### G.4 The peer-comparison problem

Mega-cap tech trading is socially visible. WallStreetBets, Twitter/X, Discord groups, financial TikTok. Other people's winning trades are highly visible; their losing trades are invisible (selection bias by the participants). The base rate is distorted upward, and the trader compares themselves to a non-representative sample, leading to over-aggressive sizing and over-frequent trading.

### G.5 The "this time my conviction is higher" problem

Every losing trade was, at entry, high-conviction. The trader does not learn from losses by lowering conviction; they learn by retroactively constructing reasons why *this* loss was special and *next time* the high-conviction setup will work. This is the precise behavioral pattern that the Brazilian-CVM 97%-lose-money cohort exhibits.

### G.6 Engine defenses

The engine cannot fix human psychology, but it can implement frictions that slow down the worst expressions of it:

- **Cooldown periods after losses:** after a 3-loss streak, require a 24-hour cooldown before new entries.
- **Mandatory position-size reduction during drawdown:** if account is in a 10%+ drawdown from high-water-mark, automatically reduce risk-per-trade by 50% for the next 20 trades.
- **No "convicted trades" override:** the engine should not allow users to size up beyond default risk per trade based on subjective conviction. Conviction is correlated with overconfidence, not with edge.
- **Mandatory journaling on overrides:** every time a user overrides a default, prompt for a written justification. This adds friction and creates a reviewable audit trail.
- **Periodic behavioral audit reports:** quarterly summary of override frequency, drawdown-period behavior, deviation from pre-registered strategy parameters. Surface these proactively.

---

## Appendix H — The Specific Case Against Each Mega-Cap as a Swing Target

A per-name accounting of why each of the Magnificent 7 is a particularly difficult swing-trading target. Not to discourage all interest — to be honest about the specific friction each name presents.

### H.1 AAPL
- **Tightest spreads, highest liquidity, deepest options market** of any single stock on earth. The marginal informed trader arrives in microseconds.
- **Quarterly earnings + iPhone launches + China data** create roughly 12–16 high-volatility event days per year, scattered throughout the calendar. Earnings-blackout rules exclude a meaningful fraction of all trading days.
- **Index weight of ~7%** in S&P 500, ~9% in QQQ means it is the single most-flow-driven stock. Technical signals are dominated by flow events.
- **Long-term trend:** 20%+ annualized for over a decade. "Buy and hold" has crushed any active swing strategy.

### H.2 MSFT
- Similar liquidity and coverage profile to AAPL.
- **Cloud business (Azure) creates non-iPhone-style discontinuities** around hyperscaler capex commentary, OpenAI-related news, and Copilot adoption metrics.
- **Multiple compression risk:** trades at premium valuation that depends on continued AI-monetization narrative. Multiple unwind risk is asymmetric.

### H.3 GOOGL
- **Antitrust overhang** (search monopoly ruling, Chrome divestiture risk) creates idiosyncratic discontinuous risk that no technical signal will anticipate.
- **AI competition narrative** (Gemini vs ChatGPT vs Claude) creates persistent narrative volatility that produces false technical signals.
- **Two share classes (GOOG vs GOOGL)** with negligible price difference but different voting rights — not a swing-trading issue but a footnote.

### H.4 AMZN
- **AWS vs retail mix** creates earnings volatility that technical signals can't model.
- **Margin sensitivity** to capex cycles, fulfillment costs, and AWS pricing pressure.
- **Historical drawdown profile is worse than other Mag 7** (95% in 2000–2001, 65% in 2008, 55% in 2022).

### H.5 META
- **Most volatile of the Mag 7 by realized vol**, partly due to advertising-revenue sensitivity.
- **Reality Labs / metaverse spending creates persistent overhang** — occasional capex headlines can drive 10–20% single-day moves.
- **Regulatory risk** (EU DMA, US antitrust, child-safety legislation) creates discontinuous downside risk.
- **Single-day 26% drop in Feb 2022** is the largest single-day market-cap loss in US history at the time, on an earnings miss. Swing traders long into earnings were destroyed; swing traders following a momentum signal had a 26% gap against them.

### H.6 NVDA
- **Highest realized vol in the Mag 7** during 2023–2024 AI bull run.
- **Concentration in hyperscaler customer base** (Microsoft, Google, Meta, Amazon, Oracle account for the majority of datacenter revenue). Customer concentration is hidden tail risk.
- **China export-control risk** creates discontinuous downside that no technical signal anticipates.
- **Crypto-cycle exposure** (datacenter GPUs used in crypto mining) caused the 2018 H2 56% drawdown.
- **AI-capex revaluation risk:** if hyperscalers cut capex by 20%, NVDA's earnings estimates collapse and the multiple compresses simultaneously. Asymmetric downside.

### H.7 TSLA
- **Most narrative-driven name** in the universe. Elon Musk tweets, Robotaxi unveils, FSD versions, and political affiliations all drive 5–20% single-day moves.
- **Margin compression** as competition intensifies (BYD, legacy autos, Chinese EV ecosystem).
- **Valuation sensitivity to non-auto narratives** (robotaxi, Optimus, energy storage, Dojo) creates multiple-expansion and multiple-compression cycles that swamp technical signals.
- **Realized volatility** historically 50–80% annualized, dwarfing other Mag 7 names. Sizing on a fixed % risk basis means TSLA dominates portfolio P&L variability.

### H.8 The aggregate point

Each of these names individually presents specific reasons why a generic EOD technical swing strategy will struggle. A portfolio of all of them does *not* diversify these risks away, because:
- They co-move at 0.6–0.8 correlation in normal regimes and 0.8–0.95 in stress regimes.
- They share common risk factors (AI capex, US dollar, hyperscaler cycles, regulatory backdrop).
- A "5-name diversified mega-cap tech swing portfolio" is in practice a 1-factor bet wearing a costume.

---

## Appendix I — The Honest Sales Pitch (a thought experiment)

If we were forced to write the marketing copy for our engine in a way that complied with the spirit of the academic literature and the regulatory disclosure requirements, it would read something like this:

---

> **Swing Trade Radar: Honest Edition**
>
> An end-of-day technical swing trading engine for US mega-cap tech equities. Built for traders who want to learn, experiment, and rigorously test their own strategies under realistic conditions.
>
> **What you should know before you start:**
>
> - The majority of retail active traders underperform a simple buy-and-hold of a low-cost index fund (Barber & Odean 2000, *Journal of Finance*; SPIVA Reports). For day traders specifically, the loss rate is approximately 97% over multi-year horizons (Chague, De-Losso, Giovannetti 2020).
> - Most published technical-trading edges have decayed substantially since their original discovery (McLean & Pontiff 2016, *Journal of Finance*). The signals you can read about in a book are weaker today than when they were first documented.
> - Backtest performance systematically overstates live performance. A common practitioner adjustment is to expect live results at approximately one-third of backtest results, primarily due to overfitting, transaction costs, and behavioral execution gaps (Bailey & López de Prado 2014).
> - The stocks our engine focuses on (AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA) are the most-analyzed, most-traded, most-arbitraged stocks in the world. The probability of finding a durable EOD technical edge on these specific names is lower than on smaller, less-followed stocks.
> - Transaction costs (spread, slippage, taxes) typically consume 10–16% of risk-per-trade for a retail account at $25k–$100k scale. This is a meaningful headwind that the engine models honestly.
>
> **What this engine is good for:**
>
> - Learning how technical strategies actually perform under realistic conditions.
> - Developing statistical discipline (walk-forward analysis, deflated Sharpe ratios, overfitting probability).
> - Running a small (≤5–10% of portfolio) experimental sleeve alongside a passive core.
> - Building intuition for risk management, position sizing, and drawdown psychology.
>
> **What this engine is not for:**
>
> - Replacing income.
> - Funding retirement.
> - Building wealth as a primary strategy.
> - Competing with institutional execution and data.
>
> **The default alternative we recommend:** Hold a globally diversified, low-cost index fund portfolio (e.g., VTI + VXUS, or VT) for 90%+ of your equity allocation. Add factor tilts (MTUM, AVUV, USMV) if you have a thesis. Add managed-futures exposure (DBMF, KMLM) if you want crisis-period diversification. Use this engine for the active 5–10% sleeve, if at all.

---

We will not ship that exact copy. But the engine's behavior, defaults, and disclosures should be consistent with the spirit of it. If we ship marketing that promises "consistent profits trading mega-cap tech with our proprietary signals," we have lied to our users and the post-mortem (Appendix D.1) will write itself.

---

## Closing Word

We are about to build a tool whose entire purpose lies in tension with the most robust empirical findings in finance. That is not, in itself, a reason not to build it. There are legitimate reasons — research, learning, the small probability of discovering or implementing a real edge, the broader value of building software that *forces* statistical discipline on people who would otherwise trade without it.

But we owe it to ourselves and our users to build the engine with the skeptics' findings **encoded as defaults**, not as warnings that disappear after the first dismissal. Fama, Cochrane, McLean, Pontiff, Harvey, Liu, Zhu, Bailey, López de Prado, Barber, Odean, Chague, Gabaix, and Koijen do not get a vote at our planning meetings. But their evidence does, because if we ignore it we are building, with our own hands, the next chapter in the literature on how retail investors lose money trading mega-cap stocks they could have just held.

Build it. But build it as if the skeptics were watching. They are.
