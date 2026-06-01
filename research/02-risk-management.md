# Risk Management, Position Sizing & Safety Rules for Swing Trading Mega-Cap US Tech

*Research dossier #02 — Swing Trade Radar*
*Scope: NASDAQ-100 mega-caps (AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA, AVGO, etc.). Holding horizon: 2–20 trading days. Account size assumption: $10k–$500k retail margin account.*

> **Thesis of this document.** Swing traders blow up for three reasons, in order of frequency: (1) oversizing relative to stop distance, (2) refusing to honor the stop once it triggers, (3) running too many correlated positions and calling it diversification. Setup selection is a rounding error compared to those three. This report builds the rule-set that fixes each.

---

## Table of Contents

1. [Foundations: Why Risk Management Is the Entire Game](#1-foundations)
2. [The R-Multiple & Expectancy Framework (Van Tharp)](#2-r-multiple)
3. [Position Sizing Models — Theory + Worked Examples](#3-position-sizing)
   - 3.1 Fixed-Dollar
   - 3.2 Fixed-Fractional (% of equity)
   - 3.3 Fixed-Risk % (the 1% rule)
   - 3.4 Volatility-Based / ATR (Van Tharp & Turtles)
   - 3.5 Kelly Criterion & Fractional Kelly
   - 3.6 Ralph Vince's Optimal f
   - 3.7 Equal-Risk Contribution
   - 3.8 Comparison Table
4. [Stop-Loss Methodologies](#4-stop-loss)
5. [Risk:Reward & Asymmetric Payoffs](#5-rr)
6. [Portfolio-Level Risk: Heat, Concentration, Correlation](#6-portfolio)
7. [Drawdown Mathematics](#7-drawdown)
8. [Regime Filters: When To Be In Cash](#8-regime)
9. [Common Causes of Ruin](#9-ruin)
10. [Real-World Blow-Up Case Studies](#10-blowups)
11. [Psychology & Behavioral Biases](#11-psychology)
12. [Taxes, PDT & Mechanical Frictions](#12-taxes)
13. [Safety Checklist — The Non-Negotiables](#13-checklist)
14. [References](#14-refs)

---

<a id="1-foundations"></a>
## 1. Foundations: Why Risk Management Is the Entire Game

Brad Barber and Terrance Odean's landmark 1999/2000 *Journal of Finance* paper *"Trading Is Hazardous to Your Wealth"* studied 66,465 retail accounts at a discount broker between 1991–1996. Headline finding: the most active 20% of retail traders earned an annualized **net return of 11.4% vs. 17.9% for a buy-and-hold benchmark** — underperforming by ~6.5% per year, almost exactly the size of their transaction costs and bad timing. [^1] Tax-adjusted, the gap widens further.

That paper is the empirical bedrock of every risk-management book worth reading: **the average active trader doesn't lose because their picks are bad; they lose because position sizing, transaction costs, taxes, and behavioral leaks compound against them.** Risk management is the lever that converts a marginally positive edge into a survivable equity curve.

Van Tharp put it most bluntly in *Trade Your Way to Financial Freedom*: **"Position sizing is the part of your trading system that tells you how much."** Most amateurs spend 95% of their effort on entries (which contribute maybe 10% of long-run results) and 5% on sizing and exits (which contribute 90%). [^2]

### The three layers of swing-trade risk

| Layer | Question | Tools |
|---|---|---|
| **Trade-level** | How much do I lose if THIS trade fails? | Stop placement, share count |
| **Portfolio-level** | How much do I lose if ALL my open trades fail at once? | Max heat, correlation, sector caps |
| **Account-level** | How much can I lose before I must stop trading? | Monthly drawdown limit, regime filter, circuit breakers |

Every section below maps to one of these three layers. Miss any one of them and you've left a hole the market will eventually find.

---

<a id="2-r-multiple"></a>
## 2. The R-Multiple & Expectancy Framework (Van Tharp)

### 2.1 What is R?

**R = Initial Risk per trade**, denominated in dollars. It's the distance from your entry to your stop, multiplied by share count, plus commissions/slippage.

> *Example.* Buy 100 NVDA at $500. Stop at $485. R = (500 − 485) × 100 = **$1,500**.

Every trade outcome is then expressed as a multiple of R:

- Stopped out at planned stop → **−1R**
- Exit at $530 → +30 × 100 = $3,000 = **+2R**
- Gap-down stop at $475 → −25 × 100 = $2,500 = **−1.67R** (slippage = bad luck, but still measured)

Why this matters: **R normalizes trades across instruments and account sizes**, so you can evaluate a strategy independently of position size or notional. A 100-trade backtest spitting out a string of R-multiples is a system's true fingerprint. [^3] [^4]

### 2.2 Expectancy

Van Tharp's expectancy formula:

```
Expectancy (in R) = (Win% × Avg Win in R) − (Loss% × Avg Loss in R)
```

A system with 40% win rate, average winner +2.5R, average loser −1R:

```
E = (0.40 × 2.5) − (0.60 × 1.0) = 1.00 − 0.60 = +0.40R per trade
```

That means **every trade is worth, on average, 0.4 × $1,500 = $600 to your account.** Take 100 trades a year, you make $60,000 in *gross* expectancy on a $150,000 account, before drawdowns chew at the geometry.

Tharp also introduced **System Quality Number (SQN)**:

```
SQN = (Mean R / StdDev R) × sqrt(N)
```

with the rule-of-thumb scoring: 1.6–1.9 = below average, 2.0–2.4 = average, 2.5–2.9 = good, 3.0–5.0 = excellent, > 5.0 = holy grail (usually means small sample or overfit). [^3]

### 2.3 The minimum acceptable expectancy

For swing trading with 0.25–1.0% round-trip costs (commission + slippage + spread) and ~20% short-term tax drag if profitable, a system needs:

- **E ≥ +0.3R after costs** to be worth running on real money
- **R-multiples consistent across regimes** (i.e., don't average a +5R 2020-tech-bubble outlier with -0.2R during chop)

---

<a id="3-position-sizing"></a>
## 3. Position Sizing Models — Theory + Worked Examples

### Common scenario (used throughout)

> **Account: $50,000.**
> **Setup: Long NVDA on a Volatility Contraction Pattern (VCP) breakout.**
> **Entry: $500.00.**
> **14-day ATR: $12.50.**
> **Chart-based stop (below pivot): $485.00 → stop distance = $15 (3%).**
> **Max risk tolerated per trade: 1% of equity = $500.**

We will run this through every model and compare results.

---

### 3.1 Fixed-Dollar Sizing

**Rule:** Always trade the same dollar notional, e.g., $10,000 per position regardless of stop distance.

> Position size = $10,000 / $500 = **20 shares.**
> Risk = 20 × $15 = **$300 (0.6% of account).**

**Pros:** Dead simple. Works for ultra-stable accounts.
**Cons:** Risk varies wildly with volatility. A tight-stop trade risks $100; a wide-stop trade risks $700. Loses the benefit of normalized R.
**Verdict:** Beginner crutch. Don't use after month one.

---

### 3.2 Fixed-Fractional (Percent of Equity)

**Rule:** Each position = X% of current equity (e.g., 20% per trade → max 5 positions).

> Position size = 20% × $50,000 = $10,000 → 20 NVDA shares.
> Risk per trade = 20 × $15 = **$300 (0.6%).**

This is what most retail traders accidentally do ("I put $10k in each name"). Position size grows with the account — that's the *fractional* part — but **risk per trade still depends on stop distance**, which can vary 3× across setups.

**Pros:** Scales with account, easy to mental-math.
**Cons:** Same flaw as fixed-dollar: doesn't normalize R.
**Verdict:** OK as a **maximum cap** on notional ("never let one position exceed 25% of equity") but a bad primary sizing rule.

---

### 3.3 Fixed-Risk Percent (The 1% / 2% Rule)

**Rule:** Risk a fixed % of equity per trade, with share count adjusting to keep dollar-risk constant.

```
Shares = (Account × Risk%) / (Entry − Stop)
```

> Shares = ($50,000 × 1%) / ($500 − $485) = $500 / $15 = **33 shares.**
> Position notional = 33 × $500 = $16,500 (33% of account).
> Max loss if stopped = **$500 (exactly 1%).**

Alexander Elder's **2% rule** (in *Trading for a Living* and *Come Into My Trading Room*) is the canonical retail norm. He recommends **2% as the absolute maximum per trade**, with 1% being healthier and 0.5% being what professionals use on large accounts. [^5] In *The New Trading for a Living* he writes: *"In trading a large account, I use the 6% Rule but tighten the 2% Rule to well under 1%."* [^5]

#### Why 1% is the swing trader's sweet spot

With a 50% win rate strategy (typical for swing breakouts):

| Risk per trade | Risk of 20% drawdown (100 trades) | Risk of ruin (50% DD) |
|---|---|---|
| 0.5% | < 0.1% | virtually 0 |
| 1.0% | ~3% | < 0.1% |
| 2.0% | ~25% | ~2% |
| 5.0% | ~85% | ~30% |
| 10.0% | ~99% | ~75% |

(Computed via Monte Carlo simulation assuming +1R wins, −1R losses, 50% win rate. The pattern is well known and reproduced in many backtest studies. [^6])

**Recommendation for mega-cap tech swings: 0.5%–1.0% per trade**, never above 1.5% even on A+ setups. Mark Minervini, two-time U.S. Investing Champion, advocates dynamic sizing where the **dollar risk is fixed and share count flexes** — exactly this model. [^7] [^8]

---

### 3.4 Volatility-Based / ATR Sizing (Van Tharp + Turtles)

The Average True Range (ATR), introduced by **J. Welles Wilder Jr. in *New Concepts in Technical Trading Systems* (1978)**, measures recent volatility as the average of:

```
TR = max(High − Low, |High − PrevClose|, |Low − PrevClose|)
ATR(14) = Wilder's smoothed average of TR over 14 periods
```

[^9] [^10]

#### The Turtle "N" / Unit formula (Richard Dennis & William Eckhardt, codified by Curtis Faith)

The Turtles called ATR(20) "N" and sized every position so that **a 1N move equaled 1% of equity** ("Unit"): [^11] [^12]

```
Unit = (1% × Account) / (N × Dollars per Point)
```

For stocks (1 share = $1 per $1 move):

```
Unit shares = (Account × 0.01) / N
```

> **NVDA Unit example:**
> Unit = ($50,000 × 0.01) / $12.50 = **40 shares.**
> Stop = entry − 2N = $500 − $25 = $475.
> Risk if stopped = 40 × $25 = **$1,000 (2%).**

The Turtles paired this with a **2N stop** — meaning planned −1R loss was 2% of equity per Unit. They could pyramid up to **4 Units per market** = 8% max risk per market, and capped total open risk at 12% per direction. [^12]

#### Van Tharp's volatility-position-sizing model

Tharp uses a stop = K × ATR and shares = Risk$ / (K × ATR). With K=2 and 1% risk:

> Shares = ($50,000 × 1%) / (2 × $12.50) = $500 / $25 = **20 shares.**
> Stop = $500 − $25 = $475.
> Risk = 20 × $25 = **$500 (exactly 1%).**

#### Why this is the gold standard for swing trading

- **Stops are placed where the *market* says noise lives, not where you wish it to be.** A tight chart stop on volatile NVDA will get whipsawed; a 2-ATR stop respects the asset's heartbeat.
- **Position size auto-adjusts to vol.** When NVDA's ATR doubles during earnings season, your share count halves automatically. Same dollar-risk, less gap exposure.
- **Backtested results from the Turtles, Andreas Clenow's *Following the Trend*, and Van Tharp's *Definitive Guide to Position Sizing* all converge** on volatility-normalized sizing as Sharpe-superior to fixed-fractional. [^13]

**Verdict:** Default sizing model for mega-cap tech swing trading.

---

### 3.5 Kelly Criterion & Fractional Kelly

J.L. Kelly Jr. (1956) derived the bet size that maximizes the long-run **geometric** growth rate of a bankroll:

```
f* = (bp − q) / b      where  b = win/loss payoff ratio
                                p = win probability
                                q = 1 − p
```

For a swing system with 50% win rate and 2:1 payoff:

```
f* = (2 × 0.5 − 0.5) / 2 = 0.5 / 2 = 0.25 → bet 25% of equity per trade
```

That sounds insane — and it is, for trading. Kelly is derived assuming you **know the true probabilities**. In trading you estimate them from a finite, regime-dependent backtest, and overestimating edge by even 10% pushes you past full Kelly into the **"overbetting cliff"** where geometric growth turns negative. [^14]

#### Fractional Kelly

Industry practice: bet **¼ to ½ of full Kelly**. Even Ed Thorp, who introduced Kelly to investing, used roughly half-Kelly at Princeton Newport. [^15] A 2024 SSRN paper by Wójtowicz & Serwa applied fractional Kelly (Optimal-f with fractional adjustment) to Polish equity strategies and confirmed risk-adjusted returns improve dramatically vs. full Kelly while still beating fixed-fractional benchmarks. [^16]

> **Half-Kelly NVDA example** (assuming 50% win, 2R:1R):
> f = 0.5 × 0.25 = 12.5% of equity = $6,250 risk per trade
> That's 12.5× the 1% rule. Mathematically optimal *if your edge estimate is perfect.* In practice, **don't.**

**Verdict:** Use Kelly as an *upper bound* and a *sanity check*: if your "optimal" 1% rule sizing is way below ¼-Kelly, you've got room. If it's above ¼-Kelly, you're overbetting your estimated edge.

---

### 3.6 Ralph Vince's Optimal f

Vince's *Portfolio Management Formulas* (1990) generalizes Kelly to trading where wins and losses aren't binary. Optimal f maximizes the **Terminal Wealth Relative (TWR)** over a sequence of historical R-multiples:

```
TWR = ∏ (1 + f × (−Trade_i / WorstLoss))
maximize TWR over f ∈ (0, 1)
```

[^17] [^18]

Same caveat as Kelly: full Optimal f produces wild drawdowns (often 80%+). Vince himself advocates **diluted f** for practical use. QuantPedia's analysis concludes: *"Going over the real underlying Kelly/optimal f is catastrophic. Stay well under whatever you estimate."* [^15]

**Verdict for swing traders:** Read it, understand it, never trade at full f. Use ¼-Kelly or 1%-risk instead.

---

### 3.7 Equal-Risk Contribution (ERC)

Borrowed from institutional portfolio construction. Each position contributes the same expected portfolio-level risk (volatility, not dollar-stop). For correlated mega-cap tech:

```
Position_i weight = (1 / σ_i) × covariance adjustment
```

For a 5-stock NDX-100 swing portfolio (AAPL, MSFT, NVDA, GOOGL, META), ERC sizing automatically downweights the highest-vol names (NVDA, TSLA) and upweights lower-vol (MSFT, GOOGL). This is essentially **what ATR sizing does in single-stock terms, extended to a multi-position portfolio.**

**Verdict:** Useful overlay if running 5+ concurrent positions. Implement as an *adjustment* to your ATR sizing, not a replacement.

---

### 3.8 Comparison Table

| Model | Formula (1-line) | NVDA shares (our example) | Sharpe impact¹ | Complexity | Best for |
|---|---|---|---|---|---|
| Fixed Dollar | Notional/Price | 20 | Low | ★ | Bond ladders, not stocks |
| Fixed Fractional | %Equity/Price | 20 | Low | ★ | Cap on notional only |
| **Fixed Risk %** | (Eq×R%)/(E−S) | **33** | Medium-High | ★★ | **Mandatory baseline** |
| **ATR / Volatility** | (Eq×R%)/(k×ATR) | **20** | **Highest²** | ★★★ | **Default for swing tech** |
| Kelly | (bp−q)/b × Equity | ~165 (full) / ~40 (¼) | High if edge is real, ruinous if not | ★★★ | Theoretical upper bound |
| Optimal f | argmax TWR over hist R | varies wildly | High but extreme DD | ★★★★ | Quant systems only |
| ERC | Vol-weighted basket | per stock | High at portfolio level | ★★★★ | Multi-position overlays |

¹ Sharpe impact from Tharp/Vince simulations and Clenow's *Following the Trend* (2012) backtests.
² Vol-based sizing improves Sharpe by ~0.15–0.30 vs. fixed-fractional in trend-following backtests over 1990–2020. [^13]

**Practitioner stack (recommended):**
1. **Primary:** ATR-based with 1% risk per trade and k=2.
2. **Cap:** Notional ≤ 20% of equity per position (Fixed-Fractional ceiling).
3. **Sanity check:** Make sure size ≤ ¼-Kelly given your estimated edge.

---

<a id="4-stop-loss"></a>
## 4. Stop-Loss Methodologies

### 4.1 Why stops must be defined BEFORE entry

If you can't write down your stop before clicking buy, you don't have a trade — you have a hope. Tharp's *Definitive Guide* opens with this: **"You can't calculate risk without a stop."** A position with no stop has undefined R, which means undefined position size, which means undefined expectancy. [^19]

### 4.2 Stop types

#### A. Chart-Based (Structural) Stops

Place stop just below recent swing low / pivot / consolidation base. Mark Minervini's VCP setups use:

- **Initial stop**: just under the breakout pivot (the high of the final volatility contraction)
- **Maximum tolerable**: **7–8% below entry, never more**. In volatile environments Minervini tightens to 5–6%. [^8] [^20]

> NVDA breakout at $500, pivot low at $485 → stop $485 (3%). Good.
> If pivot is $460 (8%), Minervini would skip the trade or take half-size.

**Pros:** Aligned with market structure. If price breaks the structure, your thesis is dead.
**Cons:** Stop distance varies; tight stops in calm markets get whipsawed.

#### B. ATR Multiple Stops

- **1.5×ATR** — aggressive, for tight VCP-style entries
- **2.0×ATR** — balanced, Tharp/Turtle standard
- **3.0×ATR** — wide, for trend-following on weekly charts (Chandelier-style)

> NVDA at $500, ATR=$12.50 → 2-ATR stop at $475.

#### C. Percent Stops

Used by Minervini (7–8%), William O'Neil/CANSLIM (7–8% hard rule), and Stan Weinstein (stage analysis). Simple but ignores volatility — a 7% stop on AAPL (low vol) is way wider than market noise; a 7% stop on TSLA (high vol) gets hit on a quiet day. **Prefer ATR.**

#### D. Time Stops

If thesis hasn't played out in N bars, exit regardless of P/L. Common for swing: **5–10 day time stop**. A breakout that hasn't moved up 5 days after pivot break is a failed breakout, even if it hasn't hit your price stop.

#### E. Trailing Stops

**Chandelier Exit** (Chuck LeBeau, late 1990s, popularized via *Beyond Technical Analysis*): [^21] [^22]

```
Long Chandelier = Highest High (last N bars) − (k × ATR)
```

Standard: N=22 (one month of bars), k=3. Hangs from the recent peak like a chandelier. Trails up as new highs are made, never moves down.

> If NVDA rallies from $500 to $540 over 3 weeks with ATR=$15, Chandelier = $540 − 3×$15 = $495.
> Locks in $5/share above entry while letting the trend breathe.

**Parabolic SAR** (Wilder again, 1978): accelerating dot-stop that tightens as the move extends. Good for catching the parabolic phase of a momentum move; bad in chop because acceleration factor closes you out on first pullback.

**Moving-average trail:** common variants are 10-EMA (Minervini's aggressive trail on parabolic Stage-2 movers), 21-EMA (standard swing trail), and 50-SMA (Stan Weinstein's stage-2 trail).

#### F. Break-even / Scaling Stops

Once trade reaches +1R, move stop to entry (break-even). At +2R, trail to +1R (locked profit). At +3R, switch to Chandelier or 21-EMA trail. This **converts uncertain R-multiples into a floor-of-zero risk profile** for the rest of the move.

### 4.3 Stop-execution mechanics (critical)

- **Use stop-limits, not stop-markets, on mega-cap tech**. Liquidity is deep enough that limit slippage is minor; market stops during halts (earnings, news) can fill 5–15% below your stop.
- **Mental stops are not stops.** If it's not in the broker, it doesn't exist.
- **Pre-market / after-hours don't execute regular stops.** Use GTC or know your broker's extended-hours rules.
- **Earnings → flatten or hedge.** No stop survives a 15% AH gap. See §9.

---

<a id="5-rr"></a>
## 5. Risk:Reward & Asymmetric Payoffs

### 5.1 Minimum R:R for swing setups

Empirically, mega-cap tech swing trades have win rates of **40–55%**. To produce positive expectancy at 45% win rate:

```
E = 0.45 × W − 0.55 × 1 ≥ 0  →  W ≥ 1.22R
```

That's the **breakeven** R:R. To actually make money after costs and slippage, target:

- **Minimum 2:1 reward:risk** on any planned entry
- **Preferred 3:1** for breakout setups
- **5:1+** acceptable only if you size down (low-probability, high-asymmetry — e.g., earnings runup)

### 5.2 Asymmetric payoff design

The Turtle/Tharp insight: **a small number of trades make all the money.** In Curtis Faith's Turtle results, fewer than 10% of trades produced over 100% of the profit. This means:

- **Cut losers fast** (−1R always, no exceptions)
- **Let winners run via trailing stop** (some will go +10R, +20R)
- **Never cap upside with a fixed take-profit** unless your backtest shows mean-reversion is your edge

Asymmetric R-distribution example for a healthy swing system:

| R-bucket | % of trades |
|---|---|
| −1R | 45% |
| −0.5R (cut early, partial) | 5% |
| 0 to +1R | 20% |
| +1R to +2R | 15% |
| +2R to +5R | 10% |
| +5R to +20R | 5% |

Expectancy on that distribution ≈ **+0.55R per trade**. The right tail does all the work.

### 5.3 Scaling out

Two-step exit common in swing trading:
1. Sell **50%** at +1R (locks in breakeven on the position).
2. Trail remaining 50% with 21-EMA or 2.5-ATR chandelier.

This trades a bit of expectancy for a much smoother equity curve and powerful psychological reinforcement (you "always" make money on winners, easier to take −1R losses).

---

<a id="6-portfolio"></a>
## 6. Portfolio-Level Risk: Heat, Concentration, Correlation

### 6.1 Max Heat (Total Open Risk)

"**Heat**" = sum of dollar-risk across all open positions if every stop hits today.

Limits:
- **Per Elder's 6% rule:** total open risk ≤ 6% of equity at all times. [^23]
- **Turtle rule:** 12% max per direction (long/short), 24% gross, but they were trading uncorrelated futures.
- **Swing-tech recommendation:** **5–6% max heat** because mega-cap tech correlations spike to 0.8+ in selloffs.

> Example: $50k account, 1% per trade, max heat 6% = max **6 concurrent positions**.

### 6.2 The 6% Monthly Drawdown Stop (Elder)

From *Come Into My Trading Room*: **"Never lose more than 6% of your capital in any one month."** Calculation:

1. At month-end, mark your equity baseline.
2. Sum realized losses + open position risk = month-to-date risk.
3. If that hits 6% of month-start equity, **stop opening new trades** until next month, or scale out existing positions to bring risk under 6%. [^23]

This is the single most important account-level circuit breaker in retail trading.

### 6.3 Concentration & Sector Caps

NDX-100 is **53% information technology + 17% communications + 14% consumer disc** — already concentrated. Add Apple + Microsoft + Nvidia + Google + Amazon + Meta = ~45% of the index. Your "diversified 5-stock tech swing portfolio" is essentially one trade with a 5-stock skin.

Hard caps:
- **No more than 25% notional in any one stock**
- **No more than 50% notional in any one GICS sub-industry** (e.g., semiconductors: NVDA + AVGO + AMD together ≤ 50%)
- **No more than 75% gross long exposure** unless market is in confirmed Stage-2 uptrend (see regime filter, §8)

### 6.4 Correlation & Beta

Mega-cap tech intra-correlations (rolling 60-day, 2020–2024):
- AAPL ↔ MSFT: ~0.70
- NVDA ↔ AVGO: ~0.75
- META ↔ GOOGL: ~0.65
- All vs. QQQ: ~0.80–0.95

During VIX spikes (>30), every name converges to **~0.95 correlation with QQQ**. Translation: **your 5 long positions are 1 position when you most need diversification**.

Practical rules:
- Treat NDX-tech longs as a single basket. Track **basket beta** (sum of weighted betas).
- Cap basket beta-adjusted exposure at **1.0× account** in normal regimes, **0.5×** in elevated VIX (>25).
- Hedge with QQQ puts or short SQQQ/long SH if running >100% gross and VIX rising.

### 6.5 Pyramiding (Adding to Winners)

The Turtles added 1 Unit every ½N favorable move, up to 4 Units. For swing tech:

- Add only to **winners that have moved ≥ +1R** in your favor.
- New add gets its own stop, sized to take total position risk back to your max-per-name limit.
- **Never average down on a loser.** Period. See §9.

---

<a id="7-drawdown"></a>
## 7. Drawdown Mathematics

### 7.1 Time to recover from a drawdown

A drawdown of D% requires a gain of `D / (1 − D)` to recover:

| Drawdown | Required gain to recover | Years at +15% CAGR |
|---|---|---|
| 5% | 5.3% | 0.36 yr |
| 10% | 11.1% | 0.75 yr |
| 20% | 25.0% | 1.6 yr |
| 30% | 42.9% | 2.5 yr |
| 40% | 66.7% | 3.6 yr |
| 50% | 100.0% | 5.0 yr |
| 75% | 300.0% | 9.9 yr |
| 90% | 900.0% | 16.5 yr |

**A 50% drawdown takes 5 years to recover at a +15% CAGR. A 75% drawdown takes a decade.** This is why max-drawdown control trumps maximum return.

### 7.2 Probability of consecutive losses

For an independent-trial system with win rate p, probability of n consecutive losses in a row is `(1−p)^n`. Expected longest streak in N trades ≈ `log(N) / log(1/(1−p))`.

| Win rate | P(5 losses in row) | P(7 in row) | P(10 in row) | Expected longest in 100 trades |
|---|---|---|---|---|
| 60% | 1.0% | 0.16% | 0.01% | ~4 |
| 50% | 3.1% | 0.78% | 0.10% | ~6 |
| 45% | 5.0% | 1.5% | 0.25% | ~7 |
| 40% | 7.8% | 2.8% | 0.60% | ~9 |
| 33% | 13.5% | 6.1% | 1.8% | ~11 |

**For a 45% win-rate breakout system, expect to lose 7 in a row at some point in any 100-trade run.** That's a 7% drawdown at 1% risk per trade. **If that breaks your psychology, you're sized too big.** [^24] [^25]

### 7.3 Risk-of-ruin formula

Approximation (Kelly framework):

```
ROR ≈ ((1 − Edge) / (1 + Edge))^(Capital / RiskPerTrade)
```

For Edge = 0.10 (10% statistical advantage), risk = 1% of capital → ROR ≈ 1.6×10⁻⁸. Effectively zero.
Same edge at 5% risk per trade → ROR ≈ 13%. **Five times the risk → 8 million times more likely to blow up.**

### 7.4 Drawdown circuit breakers (the layered defense)

| Trigger | Action |
|---|---|
| −2R day | Stop trading for the rest of the day |
| −3R in a week | Cut position size by 50% next week |
| −6% in a month (Elder) | Halt new entries until month rolls |
| −10% from equity high | Halve risk %, force full strategy review |
| −15% from equity high | Hard stop — go to cash, no trading 30 days |
| −20% from equity high | Quit. The strategy is broken or the regime is. |

Turtles cut Unit size by 20% for every 10% drawdown. [^26]

---

<a id="8-regime"></a>
## 8. Regime Filters: When To Be In Cash

### 8.1 The 200-day filter

Meb Faber's classic 2007 paper *A Quantitative Approach to Tactical Asset Allocation* showed that simply being long when S&P > 10-month SMA (≈ 200-day) and in cash otherwise cut drawdowns from −51% to −20% over 1973–2005 while matching returns. [^27]

**Hard rule for swing-tech longs:**
- **QQQ above 200-day SMA** → swing system enabled, full risk
- **QQQ within ±2% of 200-day** → caution zone, halve size or take only A+ setups
- **QQQ below 200-day SMA** → no new swing longs; existing positions on tight trail; consider short setups

### 8.2 Market breadth

Mark Minervini's market timing emphasizes:
- **% of NDX-100 stocks above their 50-day SMA** > 55% = healthy
- **% above 200-day** > 60% = bull regime
- **New 52-week highs > new 52-week lows** = leadership intact

When breadth deteriorates (high-flying index masked by 5 mega-caps doing all the work), reduce swing exposure even if QQQ is still above 200d. The 2021–2022 setup was a textbook example: index made new highs while breadth crumbled for months before the top.

### 8.3 VIX thresholds

| VIX | Regime | Action |
|---|---|---|
| < 12 | Complacency, low vol | Normal sizing, watch for vol expansion |
| 12–20 | Normal | Normal sizing |
| 20–30 | Elevated | Halve new-position size, widen stops to 2.5–3 ATR |
| 30–40 | Stress | Long entries only on best setups, size /3 |
| > 40 | Panic/crash | No new longs. Cash. Consider short or hedged trades only |

### 8.4 Multi-factor regime checklist

Before opening any swing long, all four should ideally be true:

1. ✅ QQQ above 200-day SMA, sloping up
2. ✅ QQQ above 50-day SMA
3. ✅ VIX < 25 and not spiking 20% over its 10-day average
4. ✅ Market breadth healthy (>50% NDX above 50-day)

3-of-4 = take only A+ setups at ½ size. ≤2-of-4 = no new longs.

---

<a id="9-ruin"></a>
## 9. Common Causes of Ruin

### 9.1 Averaging Down

**"Adding to a loser to lower your cost basis."** Sounds prudent. Actually doubles or triples your dollar risk on a position your thesis has *already been wrong about*. The math:

> Buy 100 NVDA at $500, stop $485 → risk $1,500.
> NVDA drops to $470, you "add 100 more to average down to $485, will sell at $490 for breakeven."
> Now 200 shares with no stop, risk = 200 × ($470 − next support, say $440) = **$6,000.**
> A second 6% drop = $9,400 loss = nearly 20% of a $50k account on one position.

Every major blow-up story includes this move. **Rule: never add to a loser. If your thesis changes, exit and re-enter sized properly.**

### 9.2 Oversizing

The single most common ruin cause. Trader makes 5 winning trades in a row, feels invincible, doubles size on the 6th. The 6th is a −1R loser at the new size = a −5% drawdown that should have been −2%. Three of those in a month and you're at −15% from a position the strategy said was a normal loss.

Fix: **size is a constant**, not a function of confidence. Increase risk-% only after **+25% account gain and at most by 0.25%** (e.g., 1% → 1.25%).

### 9.3 Ignoring Stops

Stop hits at $485. Trader thinks "it'll bounce, I'll give it room to $480." It doesn't bounce, goes to $470. New "stop" at $465. By the time he capitulates at $440 it's a −4R loss on what should have been −1R. **One ignored stop can erase 30 disciplined trades of expectancy.**

Fix: stop is in the broker before entry. Bracket orders, OCO orders, hard stops. If you can't trust yourself, you must trust the platform.

### 9.4 Earnings Blowups

Mega-cap tech routinely gaps 5–15% on earnings. Recent magnitude examples:
- META Feb 2022: −26% AH gap
- NFLX Apr 2022: −35% next-day gap
- NVDA Aug 2023: +6% beat
- META Apr 2024: −15% on capex guidance
- ASML Oct 2024: −16% on bookings miss

**No stop survives those.** Rules:
- **Default: be flat through earnings.** Close the position the day before.
- **If holding through earnings** (because you have a thesis): size at **¼ normal**, accept the gap as your stop.
- **Never hold a leveraged or full-size position through earnings.**

Calendar awareness: pin earnings dates in your trade journal. Most blow-ups happen because the trader didn't know earnings were tomorrow.

### 9.5 Gap Risk (non-earnings)

Overnight gaps from macro events, geopolitics, regulatory news, M&A announcements. Mitigations:
- Smaller overnight position sizes than intraday
- Avoid holding ahead of FOMC, CPI, jobs reports if size is significant
- Diversify across ≥3 names so a single-name gap is < 2R
- Use long-dated OTM puts as cheap tail insurance during high-event weeks

### 9.6 Leverage Misuse

Cash account margin: 2:1. Pattern day trader: 4:1 intraday, 2:1 overnight. Portfolio margin (>$125k): 6:1+. Plus options/futures embedded leverage.

The trap: leverage doesn't change your edge, only your variance. A 1% risk rule on 4× leverage is a **4% effective risk rule**. ROR explodes. Most blowups in retail futures/forex are 50:1 or 100:1 leverage producing 5% account swings on 5-pip moves.

**Mega-cap tech swing rule:** maximum 1.5× gross exposure outside confirmed bull regime. Even then, never let any single position exceed unleveraged max-per-name.

### 9.7 Strategy Drift

Trader starts as a swing trader on daily charts, holding 5–10 days. After a losing week, switches to 15-min charts and starts day-trading. Or starts trading penny stocks "for the action." Or adds options to "leverage the conviction." **All three are the same disease**: changing strategy because of recent P/L, not because the strategy is broken.

Fix: strategy reviews are **quarterly**, based on **at least 50 trades**, not daily based on the last 3.

---

<a id="10-blowups"></a>
## 10. Real-World Blow-Up Case Studies

### 10.1 Long-Term Capital Management (1998)

**The setup:** Founded 1994 by John Meriwether with Nobel laureates Myron Scholes and Robert Merton on the board. Initial capital $1.25B grew to ~$5B equity. Strategy: fixed-income relative-value arbitrage exploiting tiny spread inefficiencies. [^28] [^29]

**The leverage:** ~25:1 on-balance-sheet, but **over 250:1 including off-balance-sheet derivatives**. Notional positions exceeded $1.25 trillion. [^28]

**The rule broken:** Position size relative to liquidity. Their trades were so large that **they** were the market in those spreads. When Russia defaulted in August 1998 and spreads widened violently against them, they couldn't unwind without moving prices further against themselves.

**The cost:** $4.6B lost in four months, NY Fed–organized $3.6B bailout, full dissolution by 2000.

**Swing trader takeaway:** Don't let position size become so large that *you* are the marginal seller into your stop. For mega-cap tech this is essentially impossible at retail scale, but the principle extends to thinly-traded options or microcaps you might "spice up" your portfolio with. **Liquidity is risk capacity.**

### 10.2 Archegos / Bill Hwang (2021)

**The setup:** Family office of Tiger Asia alumnus Bill Hwang. ~$10B of equity in early 2021. Used **total return swaps with multiple prime brokers (Credit Suisse, Nomura, Morgan Stanley, Goldman, UBS)** so each broker only saw their slice of the exposure. [^30] [^31] [^32]

**The leverage and concentration:** Estimated 5:1 leverage on a portfolio concentrated in just ~10 names (ViacomCBS, Discovery, Baidu, Tencent Music, Vipshop, GSX). Total notional ~$100B+. ViacomCBS alone was a ~$20B position.

**The trigger:** ViacomCBS announced a $3B secondary offering March 22, 2021. The stock fell 23% in two days. Margin calls from prime brokers couldn't be met. Brokers force-liquidated.

**The cost:** Hwang's $20B+ family-office equity wiped out in a single week. Credit Suisse lost $5.5B (a key factor in its eventual collapse). Nomura lost $2.9B. Hwang convicted of fraud and sentenced to 18 years in 2024.

**Rules broken:**
- **Concentration:** ~5 stocks made up most of the book. No diversification.
- **Leverage:** 5:1 on volatile, single-name equity is extreme.
- **Opacity:** Hiding exposure across brokers meant no single counterparty risk-managed him. As a retail trader, your equivalent is hiding losses from yourself by not journaling — same dynamic.
- **No exit plan:** When ViacomCBS broke, there was no pre-defined stop. He held into the avalanche.

**Swing trader takeaway:** This is the **textbook lesson on concentration + leverage + no stops**. Even with $20B of equity and access to the smartest counterparties on the planet, you blow up in 4 days if you violate the basics.

### 10.3 JPMorgan "London Whale" (2012)

**The setup:** Bruno Iksil, trader in JPM's Chief Investment Office, built a $157B notional synthetic credit derivatives position. Originally a hedge, it morphed into a directional bet.

**The cost:** ~$6.2B loss; CIO leadership fired; major regulatory action.

**Rule broken:** **Position grew so large the hedge fund community front-ran the unwind.** Same liquidity problem as LTCM. Plus: internal risk metrics were quietly re-parameterized to keep showing acceptable VaR while real risk exploded.

**Retail analog:** Moving your stop down "just this once" is the retail version of re-parameterizing your risk model. Every time you do it, you're telling the market your real risk tolerance is higher than your stated one. Eventually the market tests it.

### 10.4 Retail Blowups: r/WallStreetBets era (2020–2024)

**The pattern:** Public posts of multi-million-dollar loss porn on options spreads, leveraged LEAPS, or 0DTE bets. Common setups:

- **All-in single-stock LEAPS** (call options) on AMC, GME, BBBY post-meme-rally — option premiums went to zero as IV crushed even when stocks held.
- **Naked short calls on TSLA / NVDA** that got run over during squeezes (one infamous WSB post: $9M loss on short NVDA calls in 2023).
- **0DTE put-selling for "income"** until a single −2% SPY day produced 50–100× the average daily premium in losses.
- **YOLO into earnings options**: 90% of these end at zero. The 10% that win produce screenshots that recruit the next 1,000 victims.

**Rules broken (consistent across cases):**
1. **No position sizing** — "all in" or "60% of net worth" is standard.
2. **No stops** — options without stops + leverage = digital option on bankruptcy.
3. **Concentration in one name and one expiry** — no diversification.
4. **Survivorship-biased role models** — the Roaring Kitty $50k → $50M arc is statistically a lottery winner, not a repeatable strategy. [^33]

### 10.5 Keith Gill / "Roaring Kitty" (2021 & 2024) — nuanced version

Worth a separate note because he's idolized. Gill turned ~$53k into ~$50M during the January 2021 GME squeeze via LEAPS + shares. [^33] In 2024 he posted another massive position. The lesson is **not** "concentrated bets work." The lessons are:

- He had **deep fundamental conviction** documented for over a year on YouTube/Reddit before the squeeze.
- His initial $53k bet was **money he could lose entirely** without ruin.
- The squeeze was a one-in-a-million confluence of short interest >100%, retail coordination, and broker-payment-for-order-flow plumbing. **Not repeatable.**
- The thousands of WSB users who copied him *after* the squeeze peaked lost everything when GME mean-reverted from $483 to $40.

**Survivorship bias** is the most expensive cognitive trap in trading.

### 10.6 Lessons cross-checked

| Blowup | Leverage | Concentration | No stops | Liquidity mismatch | Behavioral |
|---|---|---|---|---|---|
| LTCM | ✓✓✓ | ✓✓ | ✓ | ✓✓✓ | Overconfidence (Nobel hubris) |
| Archegos | ✓✓✓ | ✓✓✓ | ✓✓ | ✓✓ | Opacity, no risk officer |
| London Whale | ✓✓ | ✓✓ | ✓ | ✓✓✓ | Re-parameterizing risk to fit P/L |
| WSB YOLOs | ✓✓✓ | ✓✓✓ | ✓✓✓ | sometimes | Tribal/dopamine |

Every one of them violated **at least three** of: stop discipline, position sizing, concentration limits, leverage caps. **You can survive breaking one rule. You cannot survive breaking three at once.**

---

<a id="11-psychology"></a>
## 11. Psychology & Behavioral Biases

Trading systems fail because traders fail. Risk-management rules are the firewall against your own brain. Key biases, sourced to behavioral-finance literature:

### 11.1 Loss Aversion (Kahneman & Tversky, 1979)

Losses feel ~2× as painful as equivalent gains feel good. Consequence: you take profits too early on winners and refuse to cut losers. This **inverts the asymmetric R-distribution** your system needs to work — small wins, large losses — exactly the opposite of profitable swing trading.

**Defense:** Mechanical exits. Take partial profits at +1R automatically. Stops in the broker, not the head.

### 11.2 The Disposition Effect (Shefrin & Statman, 1985; Odean, 1998)

Terrance Odean's 1998 *Journal of Finance* paper analyzed 10,000 retail accounts and found investors are **~1.5× more likely to realize a gain than a loss of similar magnitude**. The winners they sold subsequently outperformed the losers they kept by ~3.4% over the next year. [^34] [^35]

**Defense:** R-multiple journaling. Track winners cut early as "missed R." When the average missed-R exceeds 0.5R, you have a disposition problem; force yourself to use a trail stop on every winner.

### 11.3 Overconfidence (Odean, 1998; Barber & Odean, 2001)

Barber & Odean's "Boys Will Be Boys" study found men trade 45% more than women, and underperform by 1.4% annually as a direct result. Overconfidence after winning streaks → over-trading and oversizing. [^36] [^1]

**Defense:** Position size is locked to a rule, not to confidence. Increases require equity milestones, not feelings.

### 11.4 Recency Bias

Last 5 trades feel more representative than last 100. Three losses in a row → strategy must be broken → tinker / switch. Three wins → invincible → oversize.

**Defense:** Required minimum sample (50 trades) before any strategy change. Rolling 50-trade expectancy is the only signal that matters.

### 11.5 Revenge Trading / Tilt

Borrowed from poker. After a painful loss, the brain reframes the next trade as "the one that fixes it" rather than an independent positive-EV bet. Stake goes up, criteria loosen, stops get ignored.

Brett Steenbarger (clinical psychologist who works with prop traders) frames it as a **physiological state** more than a thinking problem: heart rate up, prefrontal cortex offline. The trade isn't a trade; it's a fight response.

**Defense:** Hard rule — **after −2R in a day, no more trades that day. Walk away.** No exceptions. Physiologically, you need 30+ minutes away from the screen to reset. This is the single most violated rule in retail trading.

### 11.6 Confirmation Bias

You bought NVDA → you find bullish takes on NVDA. Bearish data gets explained away. Stop levels get rationalized away.

**Defense:** Pre-commit your invalidation criteria *in writing*, before entry. "I'm wrong if NVDA closes below $485 on volume > 50M, OR if QQQ closes below 200-DMA, OR if 21-EMA breaks." Then if-then. No re-reading.

### 11.7 Sunk Cost Fallacy

"I've held this for 3 weeks, I'm not going to bail now." Time and effort sunk into a position have **zero predictive value** for its future. The market doesn't know or care about your cost basis. Only forward-looking expectancy matters.

**Defense:** Daily mental reset: "If I had no position, would I open this trade today at this price with this stop?" If no → close it.

### 11.8 FOMO / Chase Bias

A stock you missed runs 15%. You buy the breakout extension instead of waiting for a base. Risk:reward is awful because the stop has to go far back to the prior base.

**Defense:** Pre-defined entry criteria (pivot, base length, volume profile). If today's price doesn't match, the trade doesn't exist. There is always another setup tomorrow.

### 11.9 The Self-Attribution Bias

Wins are skill; losses are bad luck or rigged markets. This is what makes losing streaks so dangerous: instead of triggering a review, they trigger external blame. The disposition-effect literature consistently links it to overconfidence. [^37]

**Defense:** Journal both. Forced post-mortems on every loss AND every win, with the question "was it the setup, or was it luck?" If you can't tell, sample size is too small.

---

<a id="12-taxes"></a>
## 12. Taxes, PDT & Mechanical Frictions

### 12.1 Short-Term Capital Gains (US)

Holdings ≤ 1 year are taxed as **ordinary income** (10–37% federal + state). For a typical high-earning active trader in California: marginal rate can hit **52%**. That's a brutal drag.

Implication: a swing strategy with +20% pre-tax CAGR delivers ~10% after-tax in a high bracket. **Net of taxes, buy-and-hold of QQQ at long-term cap gains (15–20%) starts to look very competitive.** Make sure your edge is large enough to clear this hurdle.

### 12.2 Wash Sale Rule (IRC §1091)

Sell at a loss → buy "substantially identical" security within **30 days before or 30 days after** → loss is **disallowed for current-year tax purposes** (added to basis of replacement). [^38] [^39]

Active swing traders triggering many wash sales can find at year-end that **realized losses they thought offset gains are deferred to next year**, resulting in a bigger tax bill than expected.

Avoidance:
- Don't re-enter the same ticker within 30 days of taking a loss, OR
- Track wash-sale adjustments meticulously (broker 1099-B reports them but errors are common), OR
- Elect **Trader Tax Status (TTS) + Section 475(f) mark-to-market** if you qualify — eliminates wash sales but converts everything to ordinary income and recognized at year-end. Requires CPA. [^39]

### 12.3 Pattern Day Trader (PDT) Rule

FINRA Rule 4210: **4+ day trades** (open and close same security same day) **in 5 business days** in a margin account → flagged as Pattern Day Trader → **must maintain $25,000 minimum equity** or account gets restricted to closing transactions only. [^40]

For pure swing traders (holding overnight), PDT rarely triggers. But:
- A failed breakout you cut same day = 1 day trade.
- Earnings-day exit after morning gap-up = day trade if you opened that morning.

If account < $25k, watch this carefully. Cash accounts don't have PDT but have T+1 settlement delays that limit turnover.

### 12.4 Frictions & "Phantom" Costs

Per round-trip:
- **Commission**: $0 at most US retail brokers post-2019
- **SEC + TAF fees**: $0.0008 + $0.0002 per share roughly
- **Spread**: 1–2 cents on mega-cap tech (negligible per share, real on tight-margin strategies)
- **Slippage on stops**: 5–20 bps in normal vol, 50–200 bps during news/halts
- **Tax drag** (covered above): can be 20–30% of pretax returns

Total realistic friction for swing tech: **~0.2–0.5% per round trip + 25% tax drag**. Build this into expectancy assumptions or your "positive E system" actually loses money.

---

<a id="13-checklist"></a>
## 13. Safety Checklist — The Non-Negotiables

Ranked by what kills accounts first. **Rules 1–5 are non-negotiable; breaking any of them is a strategy failure.** Rules 6–15 are best-practice; breaking them costs you Sharpe.

### Tier 1: Survival Rules (NEVER break)

1. **Stop is defined before entry and lives in the broker.** No mental stops. No "I'll watch it." If you can't enter the stop, you can't enter the trade.
2. **Risk per trade ≤ 1% of account equity** (0.5% if account > $250k, 1% baseline, **never above 1.5%**).
3. **Never average down on a loser.** If thesis breaks, exit. Re-enter at a new sized position if setup re-validates.
4. **Flat through earnings, unless taking ¼ size as a calculated thesis bet.** No full-size positions through scheduled binary events.
5. **Max heat (sum of open risk) ≤ 6% of equity.** Cap simultaneous positions accordingly.

### Tier 2: Account-Level Circuit Breakers

6. **Monthly drawdown limit: 6%.** Hit it → stop opening new trades that month, scale out to reduce risk.
7. **After −2R in a day → no more trades that day.** Tilt prevention.
8. **After −10% from equity high → halve position sizing**, full strategy review before resuming full size.
9. **After −15% from equity high → 30-day cooling-off** in cash. Strategy is broken or regime is wrong; don't try to gut it out.

### Tier 3: Regime & Concentration

10. **QQQ below 200-day SMA → no new swing longs.** Existing positions on tight trail.
11. **VIX > 30 → halve all new position sizes**, widen stops to 2.5–3 ATR, take only A+ setups.
12. **Max 25% notional in any one stock; max 50% in any single sub-industry** (semis, mega-cap platforms).
13. **Treat NDX tech basket as one position when correlation > 0.7.** Cap basket beta-adjusted exposure at 1.0× in normal regime, 0.5× in elevated VIX.

### Tier 4: Process Discipline

14. **Journal every trade with entry, stop, target, R-multiple result, and a 1-line "why."** Review weekly. No journal = no improvement.
15. **Strategy changes require ≥ 50 trades of evidence and a written hypothesis.** No tinkering based on the last 5 trades.

### Quick pre-trade checklist (paste above the order screen)

- [ ] Setup matches written criteria (VCP / pullback / etc.)
- [ ] QQQ above 200-day **and** 50-day SMA
- [ ] VIX < 25 (or ½ size if 25–30, no trade if > 30)
- [ ] Earnings date > 5 trading days away
- [ ] Stop level identified (chart-based or 2-ATR)
- [ ] R:R ≥ 2:1 (preferably 3:1)
- [ ] Position size calculated by ATR formula, risk = 1% of equity
- [ ] Adding this trade keeps total heat ≤ 6%
- [ ] Notional ≤ 25% of equity, sector ≤ 50%
- [ ] Stop entered in broker as a bracket/OCO order
- [ ] Trade logged in journal **before** order goes in

If any box is unchecked, the trade doesn't happen.

---

<a id="14-refs"></a>
## 14. References

[^1]: Barber, B. M., & Odean, T. (2000). "Trading Is Hazardous to Your Wealth: The Common Stock Investment Performance of Individual Investors." *Journal of Finance*, 55(2), 773–806. PDF: https://faculty.haas.berkeley.edu/odean/papers/returns/individual_investor_performance_final.pdf · SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=219228

[^2]: Tharp, V. K. (2007). *Trade Your Way to Financial Freedom* (2nd ed.). McGraw-Hill. Position sizing as the "how much" component: https://vantharpinstitute.com/van-tharp-teaches-position-sizing-strategies-and-risk-management/

[^3]: Tharp, V. K. *Definitive Guide to Position Sizing Strategies*. Van Tharp Institute. Summary PDF: https://wiki.rschooltoday.com/filedownload.ashx/Resources/596/871/aN1ER6/Van%20Tharp%20Position%20Sizing%20Definitive.pdf

[^4]: Trademetria. "What Are R-Multiples? The Key Metric Every Trader Should Know." https://trademetria.com/blog/what-are-r-multiples-the-key-metric-every-trader-should-know/

[^5]: Elder, A. (2014). *The New Trading for a Living*. Wiley. PDF reference: http://file.hstatic.net/1000205346/file/alexander_elder_-_the_new_trading_for_a_living__2014_.pdf

[^6]: Discussion of % risk per trade and ruin probabilities: Portfolio123 community thread on Elder's 2%/6% rules. https://community.portfolio123.com/t/position-sizing-and-risk-management-the-2-rule-and-6-rule/23478

[^7]: Minervini, M. (2013). *Trade Like a Stock Market Wizard*. McGraw-Hill. Strategy summary: https://www.chartmill.com/documentation/stock-screener/fundamental-analysis-investing-strategies/464-Mark-Minervini-Strategy-Think-and-Trade-Like-a-Champion-Part-1

[^8]: QuantStrategy.io. "SEPA Strategy Explained: Mastering Trend Following with Mark Minervini's Techniques." https://quantstrategy.io/blog/sepa-strategy-explained-mastering-trend-following-with-mark/

[^9]: Wilder, J. W. (1978). *New Concepts in Technical Trading Systems*. Trend Research. ATR formula reference: https://www.investopedia.com/terms/a/atr.asp

[^10]: LuxAlgo. "Average True Range: Dynamic Stop Loss Levels." https://www.luxalgo.com/blog/average-true-range-dynamic-stop-loss-levels/

[^11]: Faith, C. M. (2007). *Way of the Turtle*. McGraw-Hill. Summary: https://traderlion.com/trading-books/way-of-the-turtle-by-curtis-faith/

[^12]: "The Original Turtle Trading Rules" (Dennis/Eckhardt, public release c. 2003). PDF: https://oxfordstrat.com/coasdfASD32/uploads/2016/01/turtle-rules.pdf

[^13]: Trading Momentum (Substack). "The Art and Science of Position Sizing: Lessons from Van Tharp and Tom Basso." https://tradingmomentum.substack.com/p/the-art-and-science-of-position-sizing

[^14]: Kelly, J. L. (1956). "A New Interpretation of Information Rate." *Bell System Technical Journal*, 35, 917–926. Practical discussion: https://quantpedia.com/beware-of-excessive-leverage-introduction-to-kelly-and-optimal-f/

[^15]: QuantPedia. "Beware of Excessive Leverage – Introduction to Kelly and Optimal F." https://quantpedia.com/beware-of-excessive-leverage-introduction-to-kelly-and-optimal-f/

[^16]: Wójtowicz, M., & Serwa, D. (2024). "Application of Fractional Kelly Criterion to Enhance Profits in Emerging Markets." SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5027918

[^17]: Vince, R. (1990). *Portfolio Management Formulas*. Wiley. Optimal f overview: https://www.quantifiedstrategies.com/optimal-f-money-management/

[^18]: ProRealCode forum discussion of Optimal f implementation: https://www.prorealcode.com/topic/ralph-vinces-optimal-f-positioning-sizing/

[^19]: Tharp on stops and risk calculation, cited in nexusfi.com discussion: https://nexusfi.com/a/risk-management/volatility-based-position-sizing

[^20]: Picture Perfect Portfolios. "How To Invest Like Mark Minervini." https://pictureperfectportfolios.com/how-to-invest-like-mark-minervini-momentum-trading-champion/

[^21]: LeBeau, C., & Lucas, D. (1992). *Technical Traders Guide to Computer Analysis of the Futures Markets* — origin of Chandelier Exit. Modern reference: https://corporatefinanceinstitute.com/resources/equities/chandelier-exit/

[^22]: TrendSpider Learning Center. "Anchored Chandelier Stop." https://trendspider.com/learning-center/anchored-chandelier-stop/

[^23]: Incredible Charts (Colin Twiggs). "Alexander Elder's 6 Percent Rule." https://www.incrediblecharts.com/trading/6_percent_rule.php

[^24]: JournalPlus. "Consecutive Losses: Managing Losing Streaks." https://journalplus.co/learn/glossary/consecutive-losses

[^25]: EdgeFlo. "Losing Streak: Why 5 Losses Don't Mean Your Strategy Is Broken." https://www.edgeflo.com/blog/losing-streak-trading

[^26]: TurtleTrader.com. "Drawdown Recovery: How the Turtle Traders Managed Losses." https://www.turtletrader.com/recovery/

[^27]: Faber, M. (2007). "A Quantitative Approach to Tactical Asset Allocation." *Journal of Wealth Management*. SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=962461 (regime-switching using 10-month SMA) — see also https://graniteshares.com/research/the-200-moving-average-strategy-explained/

[^28]: Federal Reserve History. "Near Failure of Long-Term Capital Management." https://www.federalreservehistory.org/essays/ltcm-near-failure

[^29]: US Treasury / President's Working Group on Financial Markets (1999). "Hedge Funds, Leverage, and the Lessons of Long-Term Capital Management." PDF: https://home.treasury.gov/system/files/236/hedgfund.pdf · CFTC mirror: https://www.cftc.gov/sites/default/files/tm/tmhedgefundreport.htm · Retrospective: https://clsbluesky.law.columbia.edu/2018/09/10/a-retrospective-on-the-demise-of-long-term-capital-management/

[^30]: ESMA (2022). "TRV Risk Analysis — Leverage and derivatives: the case of Archegos." https://www.esma.europa.eu/sites/default/files/library/esma50-165-2096_leverage_and_derivatives_the_case_of_archegos.pdf

[^31]: TS Imagine. "Prime Brokerage Risk After Archegos — Four Years On." https://tsimagine.com/insights/protecting-prime-four-years-on-have-we-learnt-the-lessons-of-archegos-or-could-history-repeat-itself/

[^32]: VAR Capital. "Understanding the Archegos Collapse: 3 Key Takeaways." https://www.varcapital.com/understanding-the-archegos-collapse-3-key-takeaways-from-var-capital/

[^33]: WSJ. "Keith Gill Drove the GameStop Reddit Mania." https://www.wsj.com/finance/stocks/keith-gill-drove-the-gamestop-reddit-mania-he-talked-to-the-journal-11611931696

[^34]: Odean, T. (1998). "Are Investors Reluctant to Realize Their Losses?" *Journal of Finance*, 53(5), 1775–1798. PDF: https://faculty.haas.berkeley.edu/odean/papers%20current%20versions/areinvestorsreluctant.pdf

[^35]: An, L., et al. (2024). "Disposed to Be Overconfident." NYU working paper PDF: https://as.nyu.edu/content/dam/nyu-as/econ/documents/Odean%20Paper.pdf

[^36]: Barber, B. M., & Odean, T. (2001). "Boys Will Be Boys: Gender, Overconfidence, and Common Stock Investment." *Quarterly Journal of Economics*. Google Scholar profile with citations: https://scholar.google.com/citations?user=ubzu7jQAAAAJ&hl=en

[^37]: Ploner, M. (2023). "When the disposition effect proves to be rational: Experimental evidence." PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC9996105/

[^38]: COG CPA. "Wash Sale Rule Basics for Active Traders and Fund Accountants." https://www.cogcpa.com/wash-sale-rule-basics-for-active-traders-and-fund-accountants/

[^39]: Centerpoint Securities. "Day Trading Rules That Every Trader Should Be Aware Of." https://centerpointsecurities.com/day-trading-rules/

[^40]: Charles Schwab. "Day Traders: Beware the Pattern Day Trader Rule." https://www.schwab.com/learn/story/introduction-to-pattern-day-trader-rules

### Additional reading

- Investopedia. "Average True Range (ATR)." https://www.investopedia.com/terms/a/atr.asp
- Investopedia. "Position Sizing." https://www.investopedia.com/terms/p/positionsizing.asp
- Zerodha Varsity. "Stock Trading Position Sizing: 3 Methods for Risk Control." https://zerodha.com/varsity/chapter/position-sizing-active-traders-part-3/
- Incredible Charts. "ATR Trailing Stops." https://www.incrediblecharts.com/indicators/atr_average_true_range_trailing_stops.php
- proRSI. "Entry, Exit, Trailing Stop Mastery — PSAR, Chandelier Exit, Trendline Strategy." https://prorsi.com/blog/entry,-exit,-trailing-stop-mastery-%F0%9F%93%88-cmt-level-1-tools-psar,-chandelier-exit,-trendline-strategy
- Enlightened Stock Trading. "Chandelier Exit Explained." https://enlightenedstocktrading.com/chandelier-exit/
- Trading Setups Review. "How to Manage Gap Risk in Swing Trading." https://www.tradingsetupsreview.com/manage-gap-risk-swing-trading/
- TradeAlgo. "Day Trading Psychology: How to Master Discipline, Emotions, and Mental Performance." https://www.tradealgo.com/trading-guides/day-trading/day-trading-psychology-how-to-master-discipline-emotions-and-mental-performance
- Alchemy Markets. "Turtle Trading Complete Guide." https://alchemymarkets.com/education/strategies/turtle-trading-guide/
- TradeThatSwing. "How Much Stock to Buy — Position Sizing." https://tradethatswing.com/how-much-stock-to-buy-how-to-position-size-when-swing-trading-stocks/

---

*End of dossier #02. Cross-reference with dossier #01 (setup selection) and forthcoming #03 (execution & journaling tooling). The setup gets you in; the rules above keep you alive long enough for the setup's edge to compound.*
