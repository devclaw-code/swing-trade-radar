# 04 — Backtesting Methodology & Pitfalls for Swing-Trading US Equities

> Scope: Validate signals before deploying capital. Swing horizon ≈ 2–20 trading days, US equities (large/mid + selectively small caps), long-biased with optional shorts. This is the "trust but verify" doctrine: every number a backtest spits out is guilty until proven innocent.
>
> Primary sources synthesised: Lopez de Prado — *Advances in Financial Machine Learning* (2018) and *Machine Learning for Asset Managers* (2020); Bailey, Borwein, Lopez de Prado & Zhu — PBO (2014/2015), Deflated Sharpe (2014); Pardo — *The Evaluation and Optimization of Trading Strategies* (2008); Tomasini & Jaekle — *Trading Systems* (2009); Aronson — *Evidence-Based Technical Analysis* (2006); Chan — *Quantitative Trading*, *Algorithmic Trading*, *Machine Trading*; White (2000) Reality Check; Hansen (2005) SPA; Almgren–Chriss (2000) execution cost; Harvey & Liu (2015) "...and the cross-section of expected returns".

---

## 0. TL;DR — The Hard Truths

1. **A backtest is a hypothesis, not evidence.** It is evidence only after walk-forward, multiple-testing correction, paper trading, and a sample of live fills.
2. **Most published edges don't survive transaction costs.** Aronson, after testing 6,402 TA rules on the S&P, found *none* with statistically significant alpha after data-snooping correction.
3. **If your in-sample Sharpe > 2.5 on a swing strategy, suspect overfitting first, genius second.** Real liquid-market swing edges are typically **0.5–1.5 Sharpe net of costs** at retail size.
4. **The IS→OOS Sharpe haircut is real and measured.** Bailey & Lopez de Prado find that with N>50 trials, the *expected* OOS Sharpe of the "best" backtest is **negative** even when the true Sharpe of every strategy is zero.
5. **Look-ahead is the silent killer.** Most of it hides in: fundamental data without point-in-time stamps, indicator computation that includes the bar you're entering on, fill prices that "know" the future, and survivorship-cleaned universes.
6. **yfinance is fine for prototyping, dangerous for production research.** No delisted tickers, occasional missing splits, unreliable adjusted close, no point-in-time fundamentals, rate limits + silent gaps.
7. **For swing strategies specifically:** the dominant frictions are *spread + slippage at the open/close*, *gap risk*, and *short-borrow cost*. Commissions at IBKR/Alpaca tiers are essentially noise.

---

## Table of Contents

1. Backtest architecture: vectorized vs event-driven
2. Data quality and bias sources
3. Validation techniques (train/test, WFO, CPCV, MC)
4. Overfitting detection (PBO, DSR, sensitivity)
5. Realistic frictions (commissions, fees, slippage, borrow)
6. Performance metrics — what to trust and what lies
7. Tooling comparison (vectorbt, backtesting.py, bt, zipline-reloaded, backtrader, nautilus_trader, QC Lean, pyfolio, quantstats)
8. Statistical significance (sample size, t-stat, Reality Check, SPA)
9. Live-vs-backtest gap diagnostics
10. **The Backtest Trust Checklist** (use before believing any number)
11. Appendix: reference implementations & pseudocode

---

## 1. Backtest Architecture: Vectorized vs Event-Driven

### 1.1 Two paradigms

**Vectorized** (pandas/numpy/numba/jax). Compute signals, positions, returns as array operations across the whole history at once. No simulated clock, no order objects.

```python
# canonical vectorized pattern
signals  = (close > close.rolling(50).mean())        # bool matrix [T x N]
position = signals.astype(int).shift(1)              # T+1 entry, no look-ahead
returns  = position * close.pct_change()             # PnL series
equity   = (1 + returns - costs(position)).cumprod()
```

**Event-driven** (backtrader, zipline, nautilus, QC Lean, hand-rolled). Replay bar-by-bar (or tick-by-tick). Strategy callback receives one bar, may submit orders that fill on the *next* bar's data. Order book, portfolio, broker, and strategy are distinct objects.

```python
# canonical event-driven pattern
class Strat(bt.Strategy):
    def next(self):                                  # called once per bar
        if not self.position and self.sma50[0] < self.close[0]:
            self.buy(size=self.calc_size())
```

### 1.2 Trade-offs at swing timeframe

| Dimension                        | Vectorized                                    | Event-driven                                       |
|----------------------------------|-----------------------------------------------|----------------------------------------------------|
| Speed                            | 10–1000× faster (numba/numpy SIMD)            | Slow (Python loop, object allocations)             |
| Multi-asset/parameter sweeps     | Trivial; broadcast across [T × N × P]         | Painful; one process per run or threading hacks    |
| Order types / fill realism       | Approximated (assume next-open fill, etc.)    | Native (limit, stop, OCO, partial fills)           |
| Look-ahead foot-guns             | High — `.shift()` discipline required         | Low — clock guarantees causality                   |
| Path-dependent logic (trailing stops, ATR resize, partial scale-out) | Awkward, often wrong | Natural |
| Portfolio constraints (max gross, sector caps, margin) | Hand-rolled | Built-in framework support |
| Live deployment reuse            | Different code path (research vs live)        | Same `next()` logic feeds live broker              |
| Debuggability                    | Hard — bug = silent numeric drift             | Easy — step through bars                           |

### 1.3 Recommendation for swing-trade-radar

**Two-stage pipeline**:

1. **Vectorized "sieve"** (vectorbt or hand-rolled numpy) — sweep thousands of parameter combos / universes / lookbacks to *identify candidate edges*. Use deliberately conservative cost assumptions.
2. **Event-driven "confirmation"** (backtrader or zipline-reloaded or QC Lean) — re-run survivors with realistic order types, slippage models, T+1 settlement, and portfolio constraints. This is the number you actually trust.

If you skip stage 2 you will deploy strategies whose backtest Sharpe leaks 30–60% from path-dependence and order-fill simplifications.

### 1.4 The "next-bar fill" rule (vectorized non-negotiable)

For daily swing on OHLC bars: **decisions made using bar *t* data must fill at bar *t+1* open (or worse)**. Encode it once:

```python
# decision uses today's close → execute tomorrow's open
entry_price = open_.shift(-1)                   # forward shift = realistic
position    = signal.shift(1)                   # backward shift to align PnL
```

A surprising number of "amazing" backtests are people accidentally filling at the same close they computed the signal from.

---

## 2. Data Quality and Bias Sources

### 2.1 Survivorship bias

**What it is.** Your historical universe contains only tickers that *exist today*. Enron, Lehman, WCOM, Bear Stearns, Wirecard, every dot-com flameout, every reverse-merger penny stock that went to zero — *gone*. So is every ticker that got rolled into an acquisition at a discount.

**Effect size.** Empirically estimated at **+1% to +4% annualised return inflation** for broad US equity universes over 10+ year windows; far worse for momentum and small-cap strategies (Price Action Lab found 2–6% CAGR inflation on momentum rotational systems vs current-S&P-500 backtests). For a strategy with 8% true CAGR, survivorship-biased backtests can show 12–14%.

**Symptoms in backtest output.**
- "Buy worst-performing stock in universe and hold" shows positive returns (it shouldn't).
- Equal-weight universe portfolio beats market index by an absurd margin.
- All strategies look good.

**Fix.**
- Use a vendor that ships *delisted* tickers with their full price history including the terminal drop.
- For index-tracking strategies, you need **historical index constituents** (which tickers were in the SPX on date *t*?), not the current membership.

### 2.2 Data vendor reality check

| Vendor              | Delisted incl.       | PIT fundamentals | Historical constituents | Cost      | Adjustments | Notes |
|---------------------|----------------------|------------------|-------------------------|-----------|-------------|-------|
| **yfinance** (Yahoo)| ❌ no                | ❌ no            | ❌ no                   | free      | OK-ish      | Silent gaps; sporadic split errors (#1531); rate limits; "Adj Close" semantics shifting (`auto_adjust=True` now default). Fine for prototyping, **never** for production research. |
| **Tiingo**          | ⚠️ delisted only from ~2015 | partial    | ❌                      | $10–30/mo | good        | EOD focus; cheap; OK for recent-history backtests. |
| **Polygon.io**      | ✅ since 2003        | ⚠️ via SEC filings | ⚠️ limited            | $30–200/mo| good        | Tick + agg; popular with retail quants; fundamentals are SEC scrape, not PIT-stamped natively. |
| **EOD Historical Data** | ✅              | ✅ PIT           | partial                 | ~$20/mo   | good        | Great price/value ratio; index constituents via separate API. |
| **Norgate Data**    | ✅ canonical         | partial          | ✅ full PIT membership for SPX/NDX/R3000/TSX… | $40–75/mo | gold-standard | The retail/prosumer standard for *survivorship-bias-free US equities*. Index members on each historical date. AmiBroker/Python plugins. |
| **Algoseek**        | ✅                   | ✅               | ✅                      | $$$$      | gold        | Tick + nbbo + corp actions; institutional pricing. |
| **CRSP**            | ✅ canonical         | n/a              | ✅                      | academic license | gold | Gold-standard for academic research; usually inaccessible to retail. |
| **Sharadar (Quandl/Nasdaq)** | ✅          | ✅ PIT           | ✅                      | ~$50/mo   | good        | Excellent PIT fundamentals (SF1) + delisted. |
| **Compustat PIT**   | ✅                   | ✅ canonical     | ✅                      | $$$$$     | gold        | Industry standard for institutional research. |

**Concrete recommendation for this project**: **Norgate Data Premium** (US Equities) for prices + index membership, **Sharadar SF1** or **EOD Historical** for PIT fundamentals if your signals need them. Total ≈ $90/mo. yfinance only for live quote polling and ad-hoc exploration.

### 2.3 Look-ahead bias — the catalogue

1. **Same-bar fill**: Compute signal on bar *t* close, fill at bar *t* close. You can't actually do that; you knew the close before it printed.
2. **Lookback that includes the current bar**: `df.rolling(20).mean()` *includes* the current row. For a *signal* generated at *t*'s close intended to act at *t+1*, that's OK. For a *signal computed mid-bar*, it's a leak.
3. **Future-anchored normalization**: z-scoring with `df.mean()` and `df.std()` over the *entire history* before training/test split. Use expanding/rolling stats only.
4. **Restated fundamentals**: Companies *amend* earnings months later. The number you can see today for 2018 Q1 EPS is the *restated* one. The number an investor could see in May 2018 was different. Use point-in-time vintages.
5. **Index reconstitution after-the-fact**: Filtering universe to "S&P 500 stocks" using current membership. Every name in the modern SPX *got there by going up*. Use historical membership.
6. **Symbol changes / ticker reuse**: AAPL today wasn't necessarily AAPL in 2003 (it's the same company, but ticker collisions exist in other names). Always join on stable identifiers (CIK, PERMNO, FIGI).
7. **Calendar effects**: Earnings dates, ex-div dates, splits — if you signal on price *before* recording the corporate-action adjustment, your "anomalous return" is just the corp action.
8. **VWAP / day's high-low**: Using day's H/L for an entry/exit decision generated mid-day requires intraday data; on daily bars you can only "know" H/L *after* close.
9. **Snooping the test window for feature design**: Choosing 14-period RSI because "it worked best on 2015–2023". You've leaked through your own brain.

### 2.4 Split / dividend adjustment correctness

There are three valid price series:
- **Raw (unadjusted)**: what actually printed on the tape that day.
- **Split-adjusted**: only split-adjusted, dividends untouched.
- **Total-return adjusted ("Adjusted Close")**: split + dividend reinvested.

**Rules of thumb:**
- Compute *signals* on **split-adjusted** prices (technical indicators must not jump on a 2-for-1).
- Compute *returns / PnL* on **total-return adjusted** prices, OR on split-adjusted prices with explicit dividend cashflow injected on ex-div date.
- Compute *position sizing in shares* using **raw** prices on the date of execution (you trade in real-world share counts at real-world prices).
- Compute *volume filters* using **split-adjusted volume** (so a 2-for-1 doesn't show a fake volume surge).

yfinance gotcha: `auto_adjust=True` overwrites `Open/High/Low/Close` with split+dividend adjusted values and drops `Adj Close`. If you later want raw, you need to re-pull with `auto_adjust=False`. Mixing the two within one DataFrame is a common bug class.

Yahoo specific bug (yfinance #1531 and others): occasionally a split is recorded but the historical OHLC is not back-adjusted, producing a fake 50% gap. yfinance has a `repair=True` flag; use it, but spot-check.

### 2.5 Point-in-time fundamentals

If your signal uses earnings, book value, debt ratios, analyst estimates — you *must* use the vintage that was knowable on signal date. Default Compustat / SimFin / yfinance fundamentals are *restated*. A PIT vendor (Sharadar SF1, Compustat PIT, S&P Capital IQ PIT, Wharton's WRDS PIT layer) stamps each datum with `known_on_date` and `report_period`. Join on `known_on_date <= signal_date`.

### 2.6 Free-data gotchas summary

- **Stale data on weekends/holidays**: yfinance returns the last available bar with today's date in some edge cases.
- **Missing bars**: Free sources silently skip halt days; your indicator's "20-day" window becomes "20 *available* days", which is a different statistic.
- **Timezone confusion**: `Date` index may be naive but represent ET; aligning across instruments with different exchanges breaks. Standardise to UTC + explicit session calendar (`exchange_calendars`).
- **Rate limits**: Yahoo throttles aggressively in 2024+. A 5,000-ticker backtest will hit ban. Cache locally to Parquet.

---

## 3. Validation Techniques

### 3.1 The hierarchy (weak → strong)

1. **In-sample fit** — useless. Tells you nothing about generalisation.
2. **Single train/test split** — minimal; one OOS observation.
3. **Time-series k-fold (rolling)** — better; respects causality.
4. **Walk-forward optimization (WFO)** — industry standard for systematic trading.
5. **Combinatorial Purged Cross-Validation (CPCV)** — Lopez de Prado's recommended approach; produces multiple OOS paths from limited data.
6. **WFO + CPCV + bootstrap of trade returns + Monte Carlo path shuffles** — the full belt-and-suspenders.

### 3.2 Train/test split

```python
split = int(len(df) * 0.7)
train, test = df.iloc[:split], df.iloc[split:]
```

Problems: one OOS window means one realisation of the regime, and the test set is contiguous so a single bull/bear period drives the result. Don't ship anything based on this alone.

### 3.3 Time-series k-fold (no shuffle)

`sklearn.model_selection.TimeSeriesSplit` produces expanding-train / fixed-test folds. Better, but the *labels* (forward returns) inside each fold overlap if the holding period is > 1 bar — see §3.5.

### 3.4 Walk-Forward Optimization (Pardo)

The canonical procedure for *parameter-bearing* strategies:

```
              IS_1      OOS_1
             [────────][──]
                   IS_2      OOS_2
                  [────────][──]
                        IS_3      OOS_3
                       [────────][──]
```

For each step:
1. Optimize parameters on IS window (objective: e.g. Sharpe, Calmar, profit factor — pick **one** and never change it).
2. Apply *frozen* params to next OOS window. Record OOS performance.
3. Roll forward by `step` bars.
4. Concatenate all OOS segments → "walk-forward equity curve".

**Two flavors.**
- **Anchored (expanding)**: IS start is fixed; IS grows each step. Good when regime is stable / data is short.
- **Rolling (sliding)**: IS window is fixed length; both ends slide. Good when regime drifts.

**Pardo's WFE (Walk-Forward Efficiency)** = (annualised OOS return) / (annualised IS return). Target: **≥ 0.5**. Below 0.3 = strategy is overfit garbage. Above 1.0 = OOS happens to be in a tailwind regime; don't celebrate.

**Sizing of windows for swing trading**: typical IS = 2–5 years, OOS = 3–12 months, step = 3–6 months. Aim for **≥ 10 OOS segments** so you have a distribution.

```python
def walk_forward(prices, param_grid, train_yrs=3, test_mos=6, step_mos=3,
                 objective=lambda eq: sharpe(eq.pct_change())):
    results = []
    t0 = prices.index[0]
    while t0 + pd.DateOffset(years=train_yrs, months=test_mos) < prices.index[-1]:
        is_end = t0 + pd.DateOffset(years=train_yrs)
        oos_end = is_end + pd.DateOffset(months=test_mos)
        is_data  = prices[t0:is_end]
        oos_data = prices[is_end:oos_end]
        best = max(param_grid,
                   key=lambda p: objective(backtest(is_data, p).equity))
        oos_eq = backtest(oos_data, best).equity
        results.append({"window": (is_end, oos_end),
                        "params": best,
                        "oos_sharpe": sharpe(oos_eq.pct_change())})
        t0 += pd.DateOffset(months=step_mos)
    return results
```

**Anti-pattern**: peeking at OOS results and re-tuning the *strategy structure* (not just params) — that turns OOS into IS. WFO works only if the search space (the param grid + objective) is fixed before you look at OOS.

### 3.5 Purged & Embargoed K-Fold (Lopez de Prado)

Problem: if your label is "5-day forward return at *t*", then training observations at *t* and validation observations at *t+1*, *t+2*, ..., *t+5* **share information** (their forward-return windows overlap). Standard k-fold leaks future into past via label overlap.

**Purge**: drop training observations whose forward-return window overlaps with the test window.
**Embargo**: drop training observations *immediately after* the test window equal in length to the label horizon (prevents leakage in the reverse direction via slow-decaying features).

```python
# pseudo (mlfinlab provides this)
def purged_kfold(X, t1, n_splits=5, embargo_pct=0.01):
    # t1[i] = end timestamp of label for observation i
    indices = np.arange(len(X))
    for test_idx in np.array_split(indices, n_splits):
        test_t1 = t1.iloc[test_idx]
        train_idx = indices[
            (t1 < test_t1.min()) |       # ends before test starts
            (t1.index > test_t1.max() + embargo)  # starts after embargo
        ]
        yield train_idx, test_idx
```

`mlfinlab` (and its OSS forks since the license tightened) implement `PurgedKFold` and `CombinatorialPurgedKFold` directly.

### 3.6 Combinatorial Purged Cross-Validation (CPCV)

**Why**: WFO produces *one* equity path. With one path you cannot estimate the *variance* of OOS performance. CPCV solves this by generating many alternate OOS paths from the same data.

**Procedure** (Lopez de Prado, *AFML* ch. 12):
1. Split data into **N** groups (e.g., N=10) of contiguous time.
2. Choose **k** of those N as the test set (e.g., k=2 → C(10,2) = 45 combinations).
3. For each combination: train on N−k groups (with purge+embargo), test on the k held-out groups.
4. Each *group* appears in (N−1 choose k−1) test sets → many recombinations.
5. Stitch test predictions into **φ = C(N,k) · k / N** distinct OOS paths (e.g., N=10, k=2 → 9 paths).
6. Compute Sharpe (or any metric) on *each* path. You now have a distribution.

**Use case**: feed the distribution of path-Sharpes into PBO and DSR (§4). CPCV is *the* defence against picking the one lucky walk-forward path.

**Computational cost**: trains the model C(N,k) times. For an ML model that's expensive. For a rule-based swing strategy with cheap evaluation, run it; the variance estimate is worth it.

### 3.7 Bootstrap of trade returns

Treat your closed-trade R-multiples (or per-trade returns) as a sample from an unknown distribution. Resample with replacement to estimate:
- Confidence interval for CAGR
- Confidence interval for Sharpe
- Distribution of max drawdown

```python
def bootstrap_metric(trade_returns, metric, n=10_000, ci=0.95):
    sims = np.array([metric(np.random.choice(trade_returns,
                                             size=len(trade_returns),
                                             replace=True))
                     for _ in range(n)])
    lo, hi = np.quantile(sims, [(1-ci)/2, 1-(1-ci)/2])
    return sims.mean(), (lo, hi)
```

**Caveat**: this destroys autocorrelation. For metrics where the *order* of trades matters (max drawdown, longest losing streak) use **block bootstrap** (resample contiguous blocks).

### 3.8 Monte Carlo path shuffling

Two flavours, *very* different:
- **Trade-order MC**: shuffle the order of closed trades, recompute equity curve. Estimates the range of MaxDD/Calmar consistent with your trade distribution. **Useful** for assessing whether your worst drawdown is "expected" or unlucky.
- **Bar-return MC** (synthetic price paths): bootstrap daily returns, run strategy on synthetic series. **Mostly useless** for path-dependent strategies — synthetic series have no support/resistance, no earnings, no regimes; trend-following will look terrible on bootstrapped IID returns even if it's a real edge. Use only as a null-hypothesis sanity check.

### 3.9 Regime-stratified evaluation

Don't just report aggregate metrics. Slice OOS performance by:
- **Bull / bear / chop** (e.g., SPY 200-DMA regime; VIX percentile)
- **Year** (table of yearly returns; spot the one year carrying the whole CAGR)
- **Sector** (if multi-asset; one sector carrying alpha = concentration risk)
- **Earnings vs. non-earnings days** (some "edges" are just earnings-jump leakage)

If your strategy works *only* in 2009 + 2020 (vol regime spikes), that's not a strategy, that's an option-like payoff on a single factor.

---

## 4. Overfitting Detection

### 4.1 The selection-bias problem in plain English

Run 1,000 backtests with random parameters. By chance alone ≈ 25 will have apparent Sharpe > 2.0 even if true Sharpe = 0. Pick the best; it is *guaranteed* to overstate true performance. The amount of overstatement is **selection bias**, and it grows with the number of trials.

This is the core insight behind PBO and DSR.

### 4.2 Probability of Backtest Overfitting (PBO)

Bailey, Borwein, Lopez de Prado & Zhu (2014). PBO estimates the probability that the strategy *selected as best* in-sample will *underperform the median* of all candidates out-of-sample.

**Algorithm (Combinatorially Symmetric Cross-Validation, CSCV):**
1. Build the **performance matrix** `M` of shape [T × N]: T = time chunks, N = strategy variants.
2. Choose even `S` (number of submatrix chunks; e.g., S=16). Split M's rows into S equal blocks.
3. For every possible way to split S blocks into two halves J and J' (C(S, S/2) combinations):
   - Best strategy on J: `n* = argmax_n Sharpe(M_J[:, n])`.
   - Its rank on J': `r = relative_rank_among_N(M_{J'}[:, n*])`.
   - Logit: `λ = log(r / (1 − r))`.
4. **PBO = fraction of splits with λ ≤ 0** (i.e., the IS-best variant ranks at-or-below-median OOS).

**Interpretation**:
- PBO ≈ 0 → strategy selection is *informative*; the in-sample best really is good.
- PBO ≈ 0.5 → strategy selection is *uninformative*; you might as well pick at random.
- PBO > 0.5 → selection is *anti-informative* (the IS-best variant is *more likely* to underperform OOS than a random pick).

Implementation: `mlfinlab.backtest_statistics.bet_sizing.probability_of_backtest_overfitting`, or roll your own — it's < 50 lines.

```python
def pbo(M, S=16):
    # M: DataFrame rows=time chunks, cols=strategy variants
    chunks = np.array_split(np.arange(len(M)), S)
    splits = list(itertools.combinations(range(S), S // 2))
    lambdas = []
    for J in splits:
        Jp = [s for s in range(S) if s not in J]
        idx_J  = np.concatenate([chunks[i] for i in J])
        idx_Jp = np.concatenate([chunks[i] for i in Jp])
        sr_is  = M.iloc[idx_J].apply(sharpe)
        sr_oos = M.iloc[idx_Jp].apply(sharpe)
        n_star = sr_is.idxmax()
        rank = (sr_oos.rank(pct=True))[n_star]
        rank = np.clip(rank, 1e-6, 1 - 1e-6)
        lambdas.append(np.log(rank / (1 - rank)))
    return np.mean(np.array(lambdas) <= 0), np.array(lambdas)
```

### 4.3 Deflated Sharpe Ratio (DSR)

Bailey & Lopez de Prado (2014). The DSR adjusts the Sharpe for: (a) selection bias from multiple trials, (b) non-normal returns (skew/kurt), (c) sample length.

**Step 1 — Probabilistic Sharpe Ratio (PSR)**:
PSR(SR*) = probability that the *true* Sharpe exceeds a benchmark SR*, given an observed Sharpe of `SR̂`, skew γ₃, kurtosis γ₄, and sample length T:

```
PSR(SR*) = Φ( ( (SR̂ − SR*) · √(T − 1) )
              / √( 1 − γ₃·SR̂ + ((γ₄ − 1)/4) · SR̂² ) )
```

**Step 2 — Expected maximum Sharpe under the null** (from extreme-value theory across N independent trials):

```
E[max SR | null] ≈ √V · ( (1 − γ_E) · Φ⁻¹(1 − 1/N) + γ_E · Φ⁻¹(1 − 1/(N·e)) )
```

where V is variance of trial Sharpes and γ_E ≈ 0.5772 (Euler-Mascheroni).

**Step 3 — DSR**: DSR = PSR(SR* = E[max SR | null]).

DSR > 0.95 ⇒ statistically significant at 5% after multiple-testing correction. DSR < 0.5 ⇒ your strategy is indistinguishable from a lucky pick.

**Library**: implementations on GitHub (search `deflated-sharpe-ratio`); also in `mlfinlab`, `pyfolio`-fork (`quantrocket-pyfolio`), and Quantdare's blog has a clean reference Python.

**Concrete example**: SR̂ = 1.5, T = 252×3 = 756 daily obs, skew = −0.5, kurt = 5, N = 100 trials with variance of trial-Sharpes = 0.25 → DSR ≈ 0.45. You think you have a great strategy; you don't.

### 4.4 Minimum track record length (Bailey/LdP)

How long must paper-trading run before you reject "luck = SR_benchmark"?

```
MinTRL = 1 + (1 − γ₃·SR̂ + ((γ₄ − 1)/4) · SR̂²) · ( Φ⁻¹(α) / (SR̂ − SR*) )²
```

For SR̂ = 1.5, SR* = 1.0, α = 0.95, normal returns → MinTRL ≈ 24 months of daily data. That's the lower bound; in practice plan **for ≥ 12 months of live/paper before declaring victory** on a swing strategy.

### 4.5 Parameter sensitivity heatmaps

Pick the top 2 most-impactful parameters; sweep both; render a heatmap of (e.g.) walk-forward Sharpe. Look for:

- **Plateau** of high-Sharpe cells = robust edge.
- **Single pixel** of high-Sharpe surrounded by garbage = curve-fit; deploy and watch it die.
- **Diagonal ridge** = parameters are *coupled* (e.g., entry threshold and stop are really one degree of freedom).
- **High variance row-to-row** = strategy is brittle.

Quantitative rule of thumb (Pardo): pick parameters from the *centre* of a plateau, not the global maximum. Sacrifice 10–20% of IS Sharpe for OOS stability.

### 4.6 IS/OOS degradation thresholds

Tomasini & Jaekle's *Trading Systems* rule: a strategy is acceptable if:
- WFE ≥ 0.5 (OOS keeps half the IS edge)
- OOS profit factor ≥ 1.3
- OOS max DD ≤ 1.5× IS max DD
- OOS trade count ≥ 30 per WF segment

Lopez de Prado's stricter rule: aim for PBO < 0.5 *and* DSR > 0.95. If both fail, do not deploy.

### 4.7 The Harvey–Liu haircut

Harvey & Liu (2015) propose: if you've tested **N** strategies, multiply your reported t-stat hurdle by a multiple-testing factor. A rough proxy: a strategy needs |t| > **3.0** (vs. the usual 2.0) to be credible if you've explored "a few dozen" variants. Above that, use the formal Bonferroni / Holm / BHY adjustments.

---

## 5. Realistic Frictions

### 5.1 Commissions and exchange/regulatory fees

US equities, 2024–2025 typical retail:
- **IBKR Pro Fixed**: $0.005/share, min $1, max 1% of trade value.
- **IBKR Pro Tiered**: $0.0035/share + exchange/clearing/SEC fees (often nets cheaper at scale).
- **Alpaca, Robinhood, Schwab, Fidelity**: $0 commission (PFOF-funded).
- **SEC Section 31 fee (sells only)**: ~$27.80 per $1M notional (rate updates yearly). Tiny but non-zero.
- **FINRA TAF (sells only)**: $0.000166/share, max $8.30/trade.
- **NSCC pass-through, OCC, exchange route fees**: pennies; matter only HFT.

For a $10k swing position (one side), all-in costs at IBKR Tiered ≈ $0.50–1.50. At "zero commission" brokers the cost is hidden in execution quality (PFOF spreads), usually 1–3 bps worse than IBKR — for daily swing this still rounds to a few dollars per trade and is **dominated by spread+slippage**.

**Don't get cute**: model commissions as either flat `$ / trade` or `$0.005 × shares` for fixed, and call it a day. Get the order of magnitude right.

### 5.2 Slippage models

In ascending realism order:

**1. Fixed bps** (`slippage = price × bps × 1e-4`). Default 5–10 bps for liquid large-caps, 20–50 bps for small-caps. Simple, conservative, fine for first-pass.

**2. Half-spread + impact**:
```
slip = 0.5 · spread + k · σ · sqrt(participation_rate)
```
where `participation_rate = order_size / ADV`. The square-root market impact (Almgren et al. 2005) is the institutional standard:
```
impact_bps ≈ Y · σ_daily · (Q / V)^0.5    # Y ≈ 0.1 – 0.2 empirically
```
where Q is order size in shares, V is daily volume.

**3. ATR-based** (good for swing): assume worst fill is some fraction of average true range.
```python
slip = 0.10 * atr14   # 10% of 14-day ATR per round-trip
```
This naturally penalises strategies that trade volatile names.

**4. Volume participation cap with VWAP-tilt**: limit fills to ≤ P% of bar volume (P = 1–10% depending on aggression). For the portion that fills, mark-to VWAP + a participation-impact term. Required for any strategy touching small-cap or <$5M ADV names.

**5. Bid-ask at open/close**:
- Opening auction: spread is wide (often 2–3× intraday avg) and price is *uncertain*. Modelling opening fills at OPEN price is optimistic by 5–20 bps for liquid names, far more for thin names.
- Closing auction: spread tightens, but MOC orders compete with everyone else's MOC. Closing fills are usually *better* than opening fills but worse than mid-day.

**Pragmatic stack for swing-trade-radar**:
- Liquid (ADV > $50M, e.g., SPX members): half-spread (5 bps) + small impact (3 bps) = **8 bps round-trip**.
- Mid-liquid ($5–50M ADV): **15–25 bps round-trip**.
- Illiquid (<$5M): exclude from universe or apply **50–100 bps + volume cap**. Probably exclude.

### 5.3 Borrow costs (shorts only)

If your strategy shorts:
- **General Collateral (GC) borrow rate**: 0.25–1.5% annualised for easy-to-borrow large/mid caps. Treat as a continuous drag.
- **Hard-to-borrow (HTB)**: can be 5%–100%+ annualised. BYND, GME, AMC, recent IPO meme names. Often the names that look most attractive to short are the most expensive.
- **Recall risk**: lender can recall the share; you're forced to cover. Common around earnings or special dividends.

Backtest implementation:
```python
# borrow cost per day on a short position
daily_borrow_drag = -short_notional * borrow_rate_annual / 360
```

For unknown historical borrow rates: **assume 1% for shorts on universe-filtered names, exclude pre-IPO-12mo and meme tickers, and add a +50 bps "uncertainty" cushion** to short-side returns.

Vendors with historical borrow rates: Interactive Brokers' API (limited history), S3 Partners (institutional, $$$), Markit Securities Finance (institutional).

### 5.4 Other frictions to model (or explicitly assume away)

- **Pattern Day Trader rule**: 4 day-trades in 5 days → $25k min equity. Doesn't bite swing typically.
- **T+1 settlement** (US equities since May 2024): unsettled cash from a sell *cannot* be used for an unrelated buy until T+1 in a cash account. In margin accounts this is fine. For cash-account backtests, model it.
- **Locate fee for shorts**: $1–10 flat per HTB locate, daily. Small but non-zero.
- **Wash sale tax interactions**: ignore in the backtest, address at portfolio level.
- **Position-size capping due to 5% order-flow limits** (if you ever scale).
- **Halt/circuit-breaker days**: SPY halts didn't fill; do you model that? Usually no, but record in trade log.

### 5.5 Funding & financing for leveraged longs (margin)

If your backtest uses leverage:
```
overnight_financing = -borrowed_cash * (broker_call_rate + spread)
```
IBKR margin rate ≈ FedFunds + 1.5% for retail tiers. At 5% FFR + 1.5% = **6.5% annualised** on borrowed dollars. A 2x-long strategy with average gross leverage 1.5x pays ~3.25% drag per year on the borrowed half — that's *huge* and often missing from naive backtests.

---

## 6. Performance Metrics — What to Trust, What Lies

### 6.1 Return metrics

- **CAGR** (compound annual growth rate). Honest about compounding. **Lies** when path is short or has fat tails — a single 100% year on a 3-year sample fakes a 26% CAGR.
- **AnnualVol** (σ_daily × √252). Assumes IID returns; understates risk if returns are autocorrelated (most swing strategies are).
- **Total return** — meaningless without a window comparison.

### 6.2 Risk-adjusted ratios

**Sharpe** = (μ_excess) / σ. **Lies** when:
- Returns are non-Normal (most strategies — selling premium, mean-reversion, momentum all have skew/kurt).
- Returns are autocorrelated (Sharpe is inflated by `√(1 + 2·Σρ_k)`).
- Sample is short (T < 3 yrs daily ≈ T < 750).
- Strategy selection bias is present (the multiple-trials problem).

→ Always report **Probabilistic Sharpe** and **Deflated Sharpe** alongside.

**Sortino** = μ / σ_downside. Better for asymmetric strategies. Same selection-bias caveats. Lies less than Sharpe for option-selling-like payoffs, lies more for "smooth" mean-reverters.

**Calmar** = CAGR / |MaxDD|. Tomasini & Jaekle's favoured metric for trend-following. **Lies** when sample is short — MaxDD is the most sample-size-sensitive statistic in finance; it strictly increases (in expectation) with sample length.

**MAR** ratio = CAGR_since_inception / |MaxDD_since_inception|. Same as Calmar but anchored to inception, not a rolling window. Common in CTA evaluation.

**Ulcer Index** = √( mean( drawdown_pct² ) ) over the period. Penalises *depth × duration* of drawdowns, smoother than MaxDD. **Ulcer Performance Index (UPI)** = (CAGR − rf) / Ulcer Index — Calmar's better-behaved cousin.

```python
def ulcer_index(equity):
    dd = (equity / equity.cummax() - 1) * 100
    return np.sqrt((dd ** 2).mean())
```

### 6.3 Trade-level metrics

- **Profit factor** = Σ(wins) / Σ(|losses|). > 1.5 is encouraging; > 3 on > 100 trades is suspicious.
- **Win rate** — almost meaningless on its own. A 90%-win mean-reverter with tail blowup losses can be -EV.
- **Expectancy (R-multiple)** = win_rate · avg_win_R − loss_rate · avg_loss_R, expressed in units of "R" (initial risk per trade). Van Tharp's framing. > 0.3R is a real edge.
- **Average trade**, **median trade**, **largest win/loss** — read them as a row to spot single-trade dominance.
- **Trade count** — see §8 for required minima.

### 6.4 The "lies" hall of fame

1. **Sharpe ratio in isolation.** Without skew, kurt, autocorrelation, and N(trials) context, useless.
2. **Calmar without sample-length disclosure.** A 5-year backtest *cannot* have observed your true MaxDD.
3. **CAGR with no DD.** Anyone reporting just CAGR is selling something.
4. **Profit factor on < 30 trades.** Single-digit trade counts produce wild PF numbers.
5. **Sharpe on monthly returns.** Aggregation hides intramonth drawdowns; reduces apparent volatility. Always report daily.
6. **In-sample Sharpe.** Already covered. Worth saying twice.
7. **"Equity curve since launch"** of a real fund without showing the strategies they killed. Survivorship bias on your own strategy lab.

### 6.5 Metrics to *always* report together

For any candidate strategy:

```
- Sample period (start, end, n_days)
- CAGR (net of all costs)
- AnnVol
- Sharpe, Sortino, Calmar, UPI
- MaxDD, MaxDD duration (days), Ulcer
- Skew, Kurt of daily returns
- N_trades, win_rate, avg_R, profit_factor
- Expectancy in R
- WFE (walk-forward efficiency)
- PBO, DSR
- Turnover (annual)
- Avg holding period
- % time in market
- Worst calendar month / year
- Top 5 days' contribution to total return  (alpha concentration check)
```

---

## 7. Tools — Concrete Comparison

### 7.1 Vectorized

**vectorbt** (and vectorbtpro):
- Numba-accelerated; sweeps millions of param combos in seconds.
- Excellent multi-asset / multi-param tensor operations.
- Built-in drawdown, trade analysis, signal-generator helpers.
- Steep API; non-trivial to model partial fills, trailing logic, T+1 settlement.
- Best for: **research stage**, signal discovery, param sweeps, sensitivity analysis.
- Pro version ($$$) adds many features; OSS version is enough for swing research.

**backtesting.py**:
- Tiny, opinionated, single-asset, vectorized-ish.
- Excellent built-in interactive Bokeh plot.
- API is clean (subclass `Strategy`, implement `init/next`).
- Multi-asset = hand-rolled outer loop.
- Best for: **single-strategy validation, prototyping, teaching**.

**bt** (PMP):
- Composable strategy "trees" (allocation, rebalance, weighting algos).
- Strong for monthly/weekly rebalancing portfolios (asset allocation, risk parity).
- Less natural for entry/exit signal strategies.

### 7.2 Event-driven

**backtrader**:
- Mature, huge community, tons of indicators.
- Unmaintained since ~2023 (last release 2023-04); still works, but no future fixes.
- Realistic broker simulation (limit/stop/OCO/bracket, partial fills, margin).
- Slow (pure Python); 5–10 years of daily bars × few hundred symbols ≈ minutes.
- Best for: **single-strategy realistic event-driven runs after research narrows**.

**zipline-reloaded** (Stefan Jansen's fork of Quantopian's Zipline):
- The canonical Quantopian engine, alive again.
- Strong pipeline API (cross-sectional factor research).
- Tied to Quandl/Sharadar/Bundles data ingestion.
- Calendar-aware (uses `exchange_calendars`), survivorship-aware via bundles.
- Best for: **factor / cross-sectional strategies on a fixed universe**.

**QuantConnect LEAN** (Python/C#):
- Production-grade event-driven engine; same code research → cloud backtest → paper → live.
- Built-in survivorship-bias-free US data (Algoseek-sourced) on QC cloud.
- Realistic fills, multiple brokers (IB, Alpaca, TD, Tradier), options/futures/crypto.
- Local LEAN engine is free (Docker); cloud sub for data is paid.
- Heavy framework; learning curve real.
- Best for: **the strategy you actually intend to deploy**.

**nautilus_trader**:
- Modern (2023+), Rust core, Python API, low-latency.
- Tick-level realism; built for HFT and intraday.
- Overkill for daily swing; revisit if/when intraday strategies enter scope.

### 7.3 Analytics layer (pairs with any backtester)

**pyfolio** (Quantopian, dead but Stefan Jansen maintains `pyfolio-reloaded`):
- Tear sheet: returns, rolling Sharpe, drawdown table, regime conditional, factor exposures (Fama-French via `empyrical`).
- Pairs naturally with zipline.

**quantstats**:
- Modern tear sheet generator (HTML/PDF reports), broader metric coverage than pyfolio.
- One-liner `quantstats.reports.html(returns)` produces a shareable report.
- Use for **any backtest**, regardless of engine.

**empyrical** (or `empyrical-reloaded`):
- Pure metric library (Sharpe, Sortino, alpha, beta, etc.). Underlies pyfolio.

### 7.4 Recommended stack for this project

| Stage              | Tool                           | Why                                           |
|--------------------|--------------------------------|-----------------------------------------------|
| Signal exploration | **vectorbt** + duckdb/Parquet  | Fast param sweeps, fast iteration             |
| Cross-section / factor research | **zipline-reloaded** | Pipeline API + survivorship-clean bundles |
| Realistic execution validation | **backtrader** or **QC LEAN local** | Event-driven fills, costs |
| Statistical validation | hand-rolled CPCV + DSR + PBO + mlfinlab-fork | Lopez de Prado discipline |
| Reporting | **quantstats** | One-call shareable HTML reports |
| Live + paper | **QC LEAN cloud** or **Alpaca + custom shim** | Same code path as backtest ideally |

---

## 8. Statistical Significance

### 8.1 Sample size: how many trades?

Heuristic table (assumes IID trade returns, which is optimistic):

| Edge (avg R per trade) | Trades for 95% conf | Trades for 99% conf |
|------------------------|---------------------|---------------------|
| 0.05 R (tiny)          | ~1,600              | ~2,700              |
| 0.10 R                 | ~400                | ~680                |
| 0.20 R                 | ~100                | ~170                |
| 0.30 R (strong)        | ~45                 | ~75                 |

Derivation: required N ≈ (z_α · σ_R / μ_R)². For typical σ_R ≈ 1.0 (R-multiple stdev), μ_R = 0.2 → N = (1.96 / 0.2)² ≈ 96.

**Practical floor**: **≥ 100 trades** before any claim, **≥ 300** before you bet meaningful capital. Swing strategies generate 20–80 trades/year per name; portfolio of 20 names easily clears 300/year.

### 8.2 t-stat on returns

```
t = (μ_excess_daily / σ_daily) · √T = Sharpe_daily · √T
```

For annualised Sharpe of 1.0 on 3 years of daily data: t ≈ 1.0 · √3 ≈ 1.73 → **not** significant at 5%. You need Sharpe ≈ 1.2 over 3 years just to clear |t| > 2.

With multiple testing (N strategies tried), the Harvey-Liu-style adjusted hurdle pushes to **|t| > 3** for any single strategy to be credible.

### 8.3 White's Reality Check (RC)

For *k* candidate strategies whose returns are jointly evaluated. Null: best strategy's mean return ≤ 0.
1. Compute observed test statistic `V̄ = max_k √T · μ̂_k`.
2. Stationary-bootstrap the joint return matrix (preserves cross-strategy correlation).
3. For each bootstrap b: compute `V̄_b = max_k √T · (μ̂_k_b − μ̂_k)` (centered).
4. p-value = fraction of `V̄_b ≥ V̄`.

If p < 0.05, the best strategy beats the null *after correcting for the entire search*. Aronson applied this to 6,402 TA rules; none survived after RC. Sobering.

### 8.4 Hansen's SPA Test

Refinement of RC. RC is *conservative* because it includes obviously-bad strategies in the comparison. Hansen's SPA upweights strategies that are plausibly good, gives sharper p-values. Same bootstrap, modified test stat. Implementation: `pysnoop` (limited), `arch` package has stationary bootstrap; assemble manually. R package `ttrTests` has both.

### 8.5 Bonferroni / Holm / Benjamini-Hochberg

For "I tried N strategies and want to declare a few significant":
- **Bonferroni**: divide α by N. Very conservative.
- **Holm**: stepdown, less conservative.
- **BHY (FDR)**: controls *false discovery rate* (proportion of false positives among declared positives). Harvey, Liu & Zhu (2016) recommend BHY for factor research.

### 8.6 Block bootstrap for autocorrelated returns

Politis & Romano (1994) stationary bootstrap: sample blocks of geometric-mean length L (where L ≈ longest meaningful autocorrelation, e.g., 10–20 days for swing). Use this everywhere you'd use IID bootstrap on time series.

---

## 9. Live vs Backtest Gap — Diagnostic Catalogue

Empirically, retail strategies that backtest at Sharpe 2.0 deliver **Sharpe 0.5–0.8 live**, on average. Why:

### 9.1 Data-side gaps

1. **Survivorship bias** (§2.1) — kills 1–4% CAGR on long-bias.
2. **Look-ahead bias** (§2.3) — invisible until live; the gap can be *all* of your edge.
3. **PIT vs restated fundamentals** — if you use them, ~0.5–2% CAGR overstated.
4. **Index reconstitution** — momentum/rotation strategies: 1–3% overstated.
5. **Adjusted-close mismatch** — silently distorts level-based indicators.
6. **Stale prices on low-volume names** — your "fill at close" was at a price no one would actually give you.

### 9.2 Cost-side gaps

7. **Optimistic slippage** — 5 bps assumed, 20 bps reality on mid-caps.
8. **Open/close auction pricing** — assuming OPEN = printable open misses 5–15 bps of true cost.
9. **Borrow on shorts** — unmodeled, kills 1–10% CAGR on short-heavy strategies.
10. **Margin financing** — unmodeled, kills 1–3% CAGR on leveraged longs.
11. **Slippage scaling with size** — backtest sized at $10k, live at $1M: nonlinear impact.

### 9.3 Strategy-side gaps

12. **Overfitting** (§4) — by far the most common.
13. **Regime change** — backtest ends 2021, live starts 2022, momentum dies.
14. **Capacity** — edge exists at $100k, evaporates at $10M.
15. **Adverse selection** — when you can get a fill, it's because someone better-informed is willing to take the other side.
16. **Crowded factor** — the published anomaly has been arbed; OOS = post-2010 = dead.
17. **Hard-to-fill thin names** — backtest assumes you got the full size; live you got 30%.

### 9.4 Execution-side gaps

18. **Latency** — minute-bar strategy missing the open print by 30s costs 2–10 bps.
19. **Order rejection / partial fills** — backtest assumes 100% fill; reality is 60–95% depending on aggression.
20. **Halt / circuit breaker** — exits blocked when most needed.
21. **Outage** — broker/data outage during a critical moment (rare but devastating).

### 9.5 Behavioural

22. **Manual override** — you turned the bot off during the dip. Killed your edge.
23. **Position-size cheat** — went heavier on the "obvious winner". Killed Sharpe.

### 9.6 The diagnostic playbook (gap > 1 Sharpe)

When live falls short by > 1 Sharpe vs backtest:
1. Recompute backtest using only data available *as-of* live start date (no future fundamentals).
2. Recompute with conservative slippage (×3 vs original).
3. Recompute with delayed fills (next-bar OPEN if original was CLOSE).
4. Diff trade list IDs: live vs backtest. Where do they differ? Skipped trades = signal lag; different sizes = liquidity cap; missing trades = data discrepancy.
5. Trade-by-trade alpha decomposition: for each live trade, compare realised vs backtest-modelled PnL. Sum the differences.
6. Re-run backtest with live-observed slippage per trade. Does the gap close?

---

## 10. The Backtest Trust Checklist

Before believing *any* backtest number — your own or someone else's — verify every item. If you cannot tick it, mark down the headline Sharpe by the implied haircut.

### Data integrity
- [ ] Delisted tickers are present in the universe for the entire backtest window.
- [ ] Index membership is point-in-time (not "current SPX backfilled").
- [ ] Splits applied correctly (spot-check 3 known historical splits; AAPL Aug-2020, TSLA Aug-2020, NVDA Jun-2024).
- [ ] Dividend handling explicit (total-return for PnL, split-adj for signals, raw for sizing).
- [ ] Fundamentals are PIT-stamped (if used).
- [ ] No "Adjusted Close" leaked into signal computations alongside raw OHLC.
- [ ] Timezone normalised; session calendar matches exchange.
- [ ] Bars per ticker per year ≈ 252 (no silent missing days).

### Look-ahead
- [ ] Signal computed at time *t* uses **only** information available at *t*'s close (or earlier).
- [ ] Fill price for a *t*-decision is at *t+1*'s open (or worse, e.g., open + slippage).
- [ ] Rolling normalisations are expanding or rolling-prior-only, never full-sample.
- [ ] No `.fillna(method='bfill')` (back-fill = look-ahead).
- [ ] Indicator warmup period is excluded from PnL (no signals fire on partial-data bars).
- [ ] Earnings/news features stamped with `released_at` not `report_period`.

### Validation
- [ ] OOS test ran *after* all parameter choices were frozen.
- [ ] Walk-forward analysis with ≥ 10 OOS segments.
- [ ] WFE ≥ 0.5.
- [ ] CPCV-derived distribution of path Sharpes available (not just one).
- [ ] PBO computed and < 0.5.
- [ ] DSR computed and > 0.95.
- [ ] Parameter sensitivity heatmap shows plateau, not pixel.

### Costs
- [ ] Commission model documented and matches target broker.
- [ ] SEC/FINRA fees included on sells.
- [ ] Slippage model documented: at least half-spread + size-impact.
- [ ] Slippage stressed (×2, ×3) — strategy still profitable.
- [ ] Borrow cost applied to shorts (≥ 1% annualised baseline).
- [ ] Margin financing applied if leverage > 1.0.
- [ ] Open/close auction premium modeled (or trades shifted to mid-day VWAP).

### Statistics
- [ ] Trade count ≥ 100 in OOS.
- [ ] Daily Sharpe reported (not monthly).
- [ ] Probabilistic Sharpe > 0.95 (or equivalent t-stat > 2).
- [ ] Skewness and kurtosis disclosed.
- [ ] Top-5-days contribution < 30% of total PnL.
- [ ] At least one full bear market in sample (2008, 2020, 2022).
- [ ] Yearly return table — no single year carrying the strategy.

### Reality
- [ ] Strategy code is run live in **paper mode** for ≥ 3 months *before* go-live.
- [ ] Paper trade list reconciles to backtest signal list (same dates, same tickers, fill prices within slippage envelope).
- [ ] Live go-live capital is ≤ 25% of intended size for the first month.
- [ ] Pre-defined kill switch (DD threshold, Sharpe degradation threshold) documented.

### Sanity-check null tests (run these even if everything else passes)
- [ ] Replace signal with random uniform → backtest returns ≈ 0 after costs.
- [ ] Shuffle signal timestamps → returns collapse to noise.
- [ ] Invert signal (long↔short) → equity curve roughly inverts (if not, asymmetric data issue).
- [ ] Reduce universe to 10 random names → results degrade gracefully (if they *improve*, you're cherry-picking).

> **Rule of thumb**: every unchecked box ≈ 0.2–0.5 Sharpe of expected live haircut. Six unchecked = your "Sharpe 2.0" is probably a Sharpe 0.5–1.0 in real money.

---

## 11. Appendix — Reference Snippets

### 11.1 Vectorized backtest skeleton (no look-ahead)

```python
import numpy as np, pandas as pd

def vbacktest(close: pd.DataFrame,                  # [T x N] adj-close
              open_: pd.DataFrame,                  # [T x N] adj-open
              entries: pd.DataFrame,                # [T x N] bool
              exits:   pd.DataFrame,                # [T x N] bool
              cost_bps: float = 8.0):
    # Decision at close of t → fill at open of t+1
    fill = open_.shift(-1)
    # Position state derived from entries/exits
    pos = np.zeros_like(close.values)
    in_trade = np.zeros(close.shape[1], dtype=bool)
    for t in range(len(close) - 1):
        new_entry = entries.values[t] & ~in_trade
        new_exit  = exits.values[t]  &  in_trade
        in_trade  = (in_trade | new_entry) & ~new_exit
        pos[t + 1] = in_trade.astype(float)            # held during t+1
    pos = pd.DataFrame(pos, index=close.index, columns=close.columns)
    # Trade-level cost: cost applied on position changes
    turnover = pos.diff().abs().fillna(0)
    fills = fill.where(turnover > 0)
    # Per-bar return uses adjusted close-to-close while in position
    bar_ret = close.pct_change().fillna(0)
    gross   = pos * bar_ret
    costs   = turnover * cost_bps * 1e-4
    net     = gross - costs
    equity  = (1 + net.sum(axis=1) / pos.sum(axis=1).clip(lower=1)).cumprod()
    return equity, pos, net
```

### 11.2 Walk-forward harness

```python
def walk_forward(prices, search_space, train_yrs=3, test_mos=6, step_mos=3,
                 objective=lambda eq: sharpe(eq.pct_change().dropna())):
    out, t0 = [], prices.index[0]
    while t0 + pd.DateOffset(years=train_yrs, months=test_mos) <= prices.index[-1]:
        is_end  = t0 + pd.DateOffset(years=train_yrs)
        oos_end = is_end + pd.DateOffset(months=test_mos)
        best = max(search_space,
                   key=lambda p: objective(run(prices[t0:is_end], p).equity))
        oos = run(prices[is_end:oos_end], best).equity
        out.append({"is_end": is_end, "oos_end": oos_end,
                    "params": best, "oos_sharpe": objective(oos),
                    "oos_eq": oos})
        t0 += pd.DateOffset(months=step_mos)
    return pd.DataFrame(out)

def wfe(results):  # walk-forward efficiency
    return results["oos_sharpe"].mean() / results["is_sharpe"].mean()
```

### 11.3 Deflated Sharpe (minimal)

```python
from scipy.stats import norm

def psr(sr_hat, sr_star, T, skew, kurt):
    num = (sr_hat - sr_star) * np.sqrt(T - 1)
    den = np.sqrt(1 - skew * sr_hat + (kurt - 1) / 4 * sr_hat**2)
    return norm.cdf(num / den)

def expected_max_sr(n_trials, var_sr_trials):
    gamma_e = 0.5772156649
    z1 = norm.ppf(1 - 1.0 / n_trials)
    z2 = norm.ppf(1 - 1.0 / (n_trials * np.e))
    return np.sqrt(var_sr_trials) * ((1 - gamma_e) * z1 + gamma_e * z2)

def deflated_sharpe(sr_hat, T, skew, kurt, n_trials, var_sr_trials):
    sr_star = expected_max_sr(n_trials, var_sr_trials)
    return psr(sr_hat, sr_star, T, skew, kurt)
```

### 11.4 PBO via CSCV (minimal)

```python
import itertools
def pbo(M: pd.DataFrame, S: int = 16):
    chunks = np.array_split(np.arange(len(M)), S)
    lambdas = []
    for J in itertools.combinations(range(S), S // 2):
        Jp = [s for s in range(S) if s not in J]
        idx_J  = np.concatenate([chunks[i] for i in J])
        idx_Jp = np.concatenate([chunks[i] for i in Jp])
        sr_is  = M.iloc[idx_J ].apply(sharpe)
        sr_oos = M.iloc[idx_Jp].apply(sharpe)
        n_star = sr_is.idxmax()
        r = sr_oos.rank(pct=True)[n_star]
        r = np.clip(r, 1e-6, 1 - 1e-6)
        lambdas.append(np.log(r / (1 - r)))
    return float(np.mean(np.array(lambdas) <= 0))
```

### 11.5 Slippage helpers

```python
def slip_half_spread(price, bps=5):
    return price * bps * 1e-4

def slip_sqrt_impact(price, qty, adv, sigma_daily, Y=0.15):
    # Almgren et al. 2005 sqrt-impact
    return price * Y * sigma_daily * np.sqrt(qty / max(adv, 1))

def slip_atr(atr, k=0.10):
    return k * atr

def total_slip(price, qty, adv, sigma_daily, spread_bps=5, atr=None):
    s = slip_half_spread(price, spread_bps) + slip_sqrt_impact(price, qty, adv, sigma_daily)
    if atr is not None:
        s = max(s, 0.5 * slip_atr(atr))   # ATR floor
    return s
```

### 11.6 Block bootstrap of trade returns

```python
def block_bootstrap(returns, block_len=20, n_boot=10_000):
    n = len(returns)
    out = np.empty(n_boot)
    for i in range(n_boot):
        idx = []
        while len(idx) < n:
            start = np.random.randint(0, n - block_len)
            idx.extend(range(start, start + block_len))
        idx = idx[:n]
        out[i] = sharpe(returns[idx])
    return out
```

### 11.7 PBO/DSR pipeline integration

```python
# After running e.g. 200 parameter variants over 5 years daily:
M = pd.DataFrame({f"v{i}": v.daily_returns for i, v in enumerate(variants)})

pbo_score = pbo(M)
print(f"PBO = {pbo_score:.2%}  (target < 50%)")

best = M.mean().idxmax()
sr   = sharpe(M[best])
skew = M[best].skew()
kurt = M[best].kurt()
var_sr = M.apply(sharpe).var()

dsr = deflated_sharpe(sr, len(M), skew, kurt,
                      n_trials=M.shape[1], var_sr_trials=var_sr)
print(f"Best variant Sharpe={sr:.2f}  DSR={dsr:.2%}  (target > 95%)")
```

### 11.8 Null tests

```python
def null_test_random_signal(price, n=100):
    sharpes = []
    for _ in range(n):
        sig = pd.DataFrame(
            np.random.rand(*price.shape) > 0.97,        # ~3% entry prob
            index=price.index, columns=price.columns)
        eq, *_ = vbacktest(price, price, sig, sig.shift(5).fillna(False))
        sharpes.append(sharpe(eq.pct_change().dropna()))
    return np.mean(sharpes), np.std(sharpes)

def null_test_shuffle_signal(price, signal, n=100):
    sharpes = []
    base_signal = signal.values.copy()
    for _ in range(n):
        s = base_signal.copy()
        np.random.shuffle(s)
        sig_s = pd.DataFrame(s, index=signal.index, columns=signal.columns)
        eq, *_ = vbacktest(price, price, sig_s, sig_s.shift(5).fillna(False))
        sharpes.append(sharpe(eq.pct_change().dropna()))
    return np.mean(sharpes), np.std(sharpes)
```

If real-signal Sharpe is not in the **upper 5%** of the random-signal Sharpe distribution, the "edge" is noise.

---

## 12. Reading List (in priority order)

1. **Lopez de Prado — *Advances in Financial Machine Learning* (2018)** — chapters 7, 11, 12, 14, 15, 16. The bible.
2. **Bailey, Borwein, Lopez de Prado & Zhu — "The Probability of Backtest Overfitting"** (JFinData 2017 / SSRN 2326253).
3. **Bailey & Lopez de Prado — "The Deflated Sharpe Ratio"** (J. Portfolio Mgmt 2014 / SSRN 2460551).
4. **Pardo — *The Evaluation and Optimization of Trading Strategies* (2008)** — WFO canon.
5. **Tomasini & Jaekle — *Trading Systems* (2009)** — robustness, MC of trade order.
6. **Aronson — *Evidence-Based Technical Analysis* (2006)** — Reality Check applied to 6,402 rules; humbling.
7. **Chan — *Quantitative Trading* (2009), *Algorithmic Trading* (2013)** — practical pitfall walk-throughs.
8. **Harvey, Liu & Zhu — "...and the Cross-Section of Expected Returns" (2016)** — t-stat haircut for factor zoo.
9. **White (2000)** — Reality Check original paper.
10. **Hansen (2005)** — SPA test.
11. **Almgren, Thum, Hauptmann & Li (2005)** — "Direct Estimation of Equity Market Impact" — slippage modeling.
12. **Politis & Romano (1994)** — stationary bootstrap.

---

## 13. Final word

A backtest is the *easy* part. Anyone can produce a 2.0 Sharpe with enough degrees of freedom. The hard part is the discipline of:

- **freezing your search space** before looking at OOS,
- **counting your trials honestly** when you apply DSR,
- **modelling costs you'd rather pretend don't exist**,
- **paper-trading for 3+ months** before deploying real capital,
- and **killing strategies that decay** with the same speed you launched them.

Most retail "algo trading" doesn't fail at the math; it fails at the discipline. This document is the discipline.

---

## 14. Deep-Dive Addenda

### 14.1 Bar resolution: daily vs intraday for swing

Swing strategies *can* be evaluated on daily OHLC bars, but **entry/exit timing assumptions are first-order**:

| Bar resolution | Pros | Cons | When to use |
|----------------|------|------|-------------|
| Daily OHLC      | Free / cheap data; fast backtests; least overfit-prone | Fills approximated; can't model stop-loss intrabar accurately; gap risk invisible until next bar | First-pass research; signal generation |
| 1-hour          | Captures intraday momentum / mean-reversion; reasonable data cost | More bars → more parameters → more overfit risk | Confirming intraday entries |
| 5-min / 1-min   | Realistic stop-loss / TP fills | Storage cost; survivorship of intraday data; clock-sync issues | Final validation of execution model |
| Tick / L1 NBBO  | True bid/ask, true fills | $$$$; only needed for sub-minute strategies | Not needed for swing |

**The intrabar stop problem.** A daily-bar backtest that sets stops based on intraday low has a hidden look-ahead: you don't know in advance whether the low printed before or after the high. If your strategy is "enter on open, stop at −2%, target at +4%", on a day where both stop and target prices traded, *you don't know which hit first*. The honest assumption is **always assume the worst-case ordering** (stop first), or **simulate at intraday resolution**.

```python
# Conservative intrabar stop assumption from daily bars
def intrabar_outcome(o, h, l, c, entry, stop, target):
    if l <= stop and h >= target:
        return ('stop', stop)              # pessimistic: stop hit first
    if l <= stop:
        return ('stop', stop)
    if h >= target:
        return ('target', target)
    return ('eod', c)
```

### 14.2 Gap risk and overnight exposure

Swing strategies hold overnight, exposing capital to:

- **Earnings gaps**: 5–30% moves are routine. A stop at −2% does not protect you; the gap fills past the stop.
- **News gaps**: M&A, FDA, guidance pre-announcements.
- **Sector rotation gaps**: Sunday-night macro news cascades.

Backtest treatment:
- Model gap-down fills at the **gap-open price**, not the stop price. This is the difference between a paper Sharpe of 1.5 and a real one of 0.6 for breakout strategies that overweight earnings winners.
- For "avoid earnings" filters: use a **PIT earnings calendar** (Wall Street Horizon, Estimize, Zacks). Skip holding through next-N-day earnings windows.
- Sensitivity test: re-run with the **worst N=5 gap days** removed. If the strategy collapses, you were paid for tail-risk you didn't model.

### 14.3 Capacity analysis

A Sharpe-2 strategy at $10k is often a Sharpe-0 strategy at $10M because *your own trading moves the price*. To estimate capacity:

1. For each historical fill, compute participation rate `qty / ADV_at_date`.
2. Apply Almgren sqrt-impact at *target* capital level (vs backtest level).
3. Recompute strategy returns net of expanded impact.
4. Find the capital level at which net Sharpe drops by 0.5 — that's your conservative capacity.

```python
def capacity_curve(trades, capital_levels):
    # trades: DataFrame with [date, ticker, qty_at_test_capital, price, adv, sigma]
    out = []
    for K in capital_levels:
        scale = K / TEST_CAPITAL
        impact_bps = []
        for _, t in trades.iterrows():
            q = t.qty_at_test_capital * scale
            ip = 0.15 * t.sigma * np.sqrt(q / max(t.adv, 1)) * 1e4  # bps
            impact_bps.append(ip)
        avg_impact = np.mean(impact_bps)
        out.append({"capital": K, "avg_impact_bps": avg_impact,
                    "approx_sharpe": base_sharpe - avg_impact / 100})
    return pd.DataFrame(out)
```

For swing on SPX-only universe, retail capacity often goes to **$5–50M** before degrading. For Russell 2000 mean-reversion: **$500k–5M**. For thinly-traded names: **$50–500k**. Know your number.

### 14.4 ML-specific backtesting traps

If signals are produced by ML models (xgboost, RF, neural nets), additional landmines:

1. **Label leakage**: Triple-barrier labels (Lopez de Prado) embed future PT/SL touches → a feature accidentally correlated with the bar at which the barrier fires leaks. Use **purged k-fold** during model training, not just evaluation.
2. **Feature scaling across split**: `StandardScaler.fit(X)` on the *whole* dataset before splitting = leak. `fit_transform(X_train)` only, then `transform(X_test)`.
3. **Hyperparameter tuning on the same OOS**: every Bayesian-opt iteration *snoops* the validation set. Use nested CV (inner CV for HP tuning, outer CPCV for performance estimate).
4. **Feature importance instability**: features that look important under one CV split aren't under another. Use **Mean Decrease Accuracy (MDA)** with permutation under purged CV; report stability.
5. **Class-imbalance**: most swing signals fire infrequently → 95% "no trade" labels. Subsample or use class weights, but do it inside the training split only.
6. **The triple-barrier `t1` field is critical** for purging. If you set the vertical barrier at +5 days, every observation has a 5-day forward dependency. Train/test boundaries must respect that.
7. **"Walk-forward retraining"**: retraining the model every WF step is realistic but expensive. Document the frequency; sensitivity to retrain frequency is itself a parameter.
8. **Random seed cherry-picking**: Run the same training pipeline with 20 different seeds. Report mean & std of OOS Sharpe. If std > 0.3, your model is fitting noise.

### 14.5 Cross-sectional vs time-series strategies

**Time-series strategy** (long if price > MA, short otherwise): per-asset signal, evaluated independently. Validation focus: regime stability over time.

**Cross-sectional strategy** (long top-decile momentum, short bottom-decile): relative ranking across universe at each date. Validation focus:
- **Universe definition is part of the strategy.** Backtest with the same universe filter your live system will use (e.g., "top 500 by ADV as of date t").
- **Re-rank costs.** Daily re-ranking with full rebalancing = enormous turnover. Add a hysteresis band (don't trade if rank moves < threshold).
- **Sector-neutral vs naive long-short.** A "momentum" long-short that's secretly 80% long-tech-short-energy is a sector bet, not a momentum bet. Decompose with Fama-French + sector factors via `pyfolio.factor_analysis` or `alphalens`.
- **Alphalens** is the canonical tool for cross-sectional signal evaluation: IC (Information Coefficient) by lag, by sector, by quantile; turnover; cumulative returns by quantile. Use it before backtesting a portfolio strategy.

### 14.6 Dividend / corporate-action edge cases

- **Special dividends** (one-time): standard adj-close handles them, but if the dividend is large (> 5% of price), some vendors mis-classify it as a split. Spot-check.
- **Spin-offs**: parent + spin-off must both be in your data, on the right date, with the right cost-basis split. yfinance regularly mishandles these (e.g., GE Healthcare 2023, Kellanova/WK Kellogg 2023).
- **M&A cash deals**: target ticker stops trading mid-deal; treat as "forced sell at deal price" on close-of-deal date.
- **M&A stock deals**: target shares convert to acquirer shares at the ratio. Survivor-bias-free data handles this; yfinance does not.
- **Reverse splits** (1-for-N): often a delisting precursor. Many backtests fail to detect that the same ticker has effectively become a different security (e.g., post-RS sub-$1 → sub-$0.50 dynamics).
- **Bankruptcy emergence with new ticker**: e.g., HTZGQ → HTZ. Linking pre/post is essential for fundamental strategies.

### 14.7 Calendar / session edge cases

- **Half-days** (day after Thanksgiving, Christmas Eve): 1pm ET close. MOC orders behave differently.
- **Holidays**: NYSE closures differ slightly from CBOE / OTC. Use `exchange_calendars.get_calendar('XNYS')`.
- **Daylight savings**: cron-based intraday systems break twice a year.
- **Pre/post-market**: 4am–9:30am, 4pm–8pm ET. Wider spreads, lower liquidity. Many backtests treat "open price" as 9:30am NBBO midpoint, but RTH-only fills assume official open auction print. Be specific.

### 14.8 The "data scientist" failure mode

A common path to a fake Sharpe:
1. Pull yfinance data, current S&P 500 constituents.
2. Engineer 50 features (MA, RSI, MACD, BBands, volume ratios, sector dummies).
3. Train xgboost with default-ish hyperparams.
4. 70/30 train/test split, random order.
5. Sharpe = 3.2! 🎉

Everything is wrong here:
- Survivorship bias (current SPX). +2% CAGR fake.
- Random shuffle of test split → label leakage across overlapping forward returns. +1.5 Sharpe fake.
- yfinance adj-close used both for features and PnL → adj-close feature leaks the future dividend. +0.5 Sharpe fake.
- No costs. Subtract 0.3 Sharpe.
- 50 features × `param search` → multiple testing inflation. DSR ≈ 0.2.
- True Sharpe: probably **negative**.

If you've ever seen this pipeline produce a "3.2 Sharpe model," you have *not* discovered alpha. You've discovered the path of least research resistance.

### 14.9 Worked example: a meaningful Sharpe budget

For a long-only US swing strategy, here's a realistic per-stage haircut budget:

| Stage                                | Optimistic SR | Realistic SR | Notes                                    |
|--------------------------------------|---------------|--------------|------------------------------------------|
| Idealised vector backtest, no costs  | 2.5           | 2.5          | Where stories begin                      |
| Survivorship-bias correction         | 2.5 → 2.2     | −0.3         | Norgate or Sharadar                      |
| Realistic slippage (15 bps/side)     | 2.2 → 1.8     | −0.4         | half-spread + impact                     |
| Realistic commissions                | 1.8 → 1.75    | −0.05        | IBKR Tiered scale                        |
| Open-fill premium                    | 1.75 → 1.6    | −0.15        | Open auction not benign                  |
| Walk-forward selection penalty       | 1.6 → 1.2     | −0.4         | Single best param loses to plateau mean  |
| Multiple-testing deflation (N≈50)    | 1.2 → 0.95    | −0.25        | DSR-driven                               |
| Regime / OOS degradation             | 0.95 → 0.75   | −0.2         | First year live is usually worst         |
| **Live, after 12 months**            | **2.5**       | **0.75**     | The honest delivered number              |

If the *honest* expectation is 0.75 Sharpe — is that worth doing? Compared to buy-and-hold SPY (~0.5 long-run Sharpe), **yes**, if uncorrelated. Compared to T-bills (Sharpe ≈ 0 by definition above rf), **only marginally**. This is why edge accumulation through *uncorrelated* strategies matters more than any single strategy's Sharpe.

### 14.10 Backtest reproducibility hygiene

- Lock data snapshot date. Re-running on "latest yfinance" tomorrow won't reproduce today's numbers.
- Pin library versions in `requirements.txt` / `pyproject.toml`. vectorbt and pandas behaviour drifts.
- Seed all RNGs (`numpy`, `random`, `torch`).
- Persist intermediate artifacts: signal matrix, trade list, equity curve. Diff before/after any change.
- One backtest = one Git commit hash + one data snapshot hash. Both go in the report header.
- Treat backtests as you would treat scientific experiments — replicable, version-controlled, with explicit hypotheses and pre-registered analysis plans.

### 14.11 Pre-registering your strategy

Borrowed from clinical trials. Before running the final OOS evaluation:

1. Freeze the *exact* code (commit hash).
2. Freeze the *exact* universe and date range.
3. Freeze the *exact* metric and the threshold required for go-live.
4. Write it down in a dated markdown file in the repo.
5. Run. The result is the result. No re-tuning.

If you skip this, your OOS is just a longer IS.

### 14.12 Production monitoring (post-deploy)

A backtest's validity *decays* once live. Monitor:

- **Rolling 30-day live Sharpe** vs backtest's rolling 30-day Sharpe distribution. Live falling below the 5th percentile of backtest rolling distribution → investigate.
- **Trade-level slippage drift**: avg realised slip / backtest assumed slip. If > 1.5 sustained, costs assumption is broken.
- **Hit-rate drift**: % winning trades, compared to backtest. Drop > 10pp → signal decay.
- **Position-correlation creep**: if names cluster (sector, factor) more than backtest, capital is concentrated. Risk-manage down.
- **Kill-switch**: pre-define DD (e.g., −12% from HWM) at which the strategy is paused for review. Document and *honor it*.

---

## 15. Glossary

- **ADV** — Average Daily Volume (shares or $).
- **Adj Close** — Total-return adjusted close (splits + dividends).
- **AFML** — *Advances in Financial Machine Learning* (Lopez de Prado, 2018).
- **BHY** — Benjamini-Hochberg-Yekutieli; false-discovery-rate procedure.
- **CAGR** — Compound Annual Growth Rate.
- **CPCV** — Combinatorial Purged Cross-Validation.
- **CSCV** — Combinatorially Symmetric Cross-Validation (the PBO machinery).
- **DSR** — Deflated Sharpe Ratio.
- **FDR** — False Discovery Rate.
- **HTB** — Hard-to-Borrow.
- **IC** — Information Coefficient (cross-sectional rank correlation of signal to forward return).
- **IS / OOS** — In-Sample / Out-Of-Sample.
- **MAR** — Managed Account Reports ratio (CAGR / MaxDD, inception-anchored).
- **MinTRL** — Minimum Track Record Length.
- **NBBO** — National Best Bid and Offer.
- **PBO** — Probability of Backtest Overfitting.
- **PIT** — Point-In-Time.
- **PSR** — Probabilistic Sharpe Ratio.
- **RC** — Reality Check (White, 2000).
- **R-multiple** — trade PnL expressed in units of initial risk.
- **SPA** — Superior Predictive Ability test (Hansen, 2005).
- **WFA / WFO** — Walk-Forward Analysis / Optimization.
- **WFE** — Walk-Forward Efficiency.

---

*End of file. Next: 05-execution-risk-management.md.*
