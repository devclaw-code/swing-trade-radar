# 06 — Implementation Stack for an Automated US-Equity Swing Trading Signal Engine

> **Scope.** This document is the *practical implementation* dossier for the Swing Trade Radar project.
> It deliberately avoids strategy theory (covered in earlier research notes) and focuses on
> **tooling, data, storage, execution, scheduling, observability, compliance, and deployment**.
> Target user: a solo retail swing trader, EOD-driven signals, single VPS, sub-$50/month
> infra budget, paper-first → optional live with hard human-in-the-loop.
>
> **Last refreshed.** Sources current through late 2025 / early 2026 (Polygon → Massive rebrand,
> ib_insync → ib_async fork, SEC PDT change, Databento US Equities GA, IEX Cloud RIP).
>
> **TL;DR (decision matrix lives at the bottom).** For a solo EOD swing trader on a tight budget:
>
> - **Data:** Tiingo ($10/mo) for primary EOD + fundamentals; **yfinance** as free fallback;
>   **Alpaca Free** for free realtime IEX snapshots if you need an intraday confirm.
> - **Broker / paper:** **Alpaca Paper** (free, full Trading API) → **Alpaca Live** or **Tradier** if you graduate.
> - **Indicators:** `pandas-ta` (pure-python, no compile pain) + `talib-binary` only if you need patterns.
> - **Backtest / research:** `vectorbt` (or `vectorbtpro` if you can spend) for cross-sectional EOD scans.
> - **Live signal engine:** Plain Python + `APScheduler` (no need for Prefect/Celery at this scale).
> - **Storage:** **DuckDB** + Parquet partitions for OHLCV history; **SQLite** for signals/trades/positions ledger.
> - **Calendar:** `pandas_market_calendars` (XNYS).
> - **Notify:** Telegram bot + Discord webhook + email (SES/Resend) — never auto-fire orders.
> - **Deploy:** Docker Compose on a $6–12 Hetzner / DigitalOcean VPS in `America/New_York` TZ.
>
> Full justification, alternatives, edge cases, and code-shaped patterns follow.

---

## Table of Contents

1. [Market data sources — deep comparison](#1-market-data-sources--deep-comparison)
2. [Broker APIs for execution](#2-broker-apis-for-execution)
3. [Python ecosystem stack](#3-python-ecosystem-stack)
4. [Storage architecture](#4-storage-architecture)
5. [Indicator computation pipeline](#5-indicator-computation-pipeline)
6. [Signal pipeline architecture](#6-signal-pipeline-architecture)
7. [Paper trading & performance tracking](#7-paper-trading--performance-tracking)
8. [Alerting & dashboard UX](#8-alerting--dashboard-ux)
9. [Compliance & safety rails](#9-compliance--safety-rails)
10. [Deployment](#10-deployment)
11. [Final recommended stack (decision matrix)](#11-final-recommended-stack-decision-matrix)
12. [Appendix — schema, env vars, smoke tests](#12-appendix)

---

## 1. Market data sources — deep comparison

For a *swing* engine (multi-day holding period, daily bars, optional 1h or 15m intraday
confirmation), you do not need a tick-level feed and you should not pay for one. Your real
requirements are:

- **Adjusted daily OHLCV** for the entire universe you scan (typically 2,000–8,000 US
  equities: S&P 1500 + Russell 2000 + a long-tail watchlist).
- **Survivorship-bias-free history** for honest backtests (the *single* most-cheated
  assumption in retail research).
- **Reliable corporate-action handling** (splits + cash dividends → adjusted close).
- **A liquid intraday snapshot** (latest price + bid/ask) at scan time, even if delayed.
- **Reasonable rate limits** for batch backfills of a few thousand symbols.
- **Long-term existence of the vendor** (IEX Cloud shutting down in Aug 2024 was a real
  wake-up call — never single-source critical infra).

Everything below is graded against those needs, not against "is it the fanciest tick feed."

### 1.1 yfinance (Yahoo, unofficial)

- **Cost:** Free.
- **Latency / coverage:** EOD adjusted bars for basically every US ticker, decades of history;
  intraday data is best-effort 1m/2m/5m/15m/30m/60m/90m/1h/1d, but 1m only goes back 7 days,
  2m–90m only 60 days. Real-time quote is ~15-min delayed.
- **Adjustments quality:** Splits and dividends are reflected in `Adj Close`. Generally good
  but occasional retroactive revisions and the odd missing split day; you will find weirdness
  in micro-caps and recently-delisted names.
- **Reliability:** This is the headline problem in 2025. Yahoo has been aggressively
  rate-limiting and IP-blocking the unofficial endpoints (`YFRateLimitError('Too Many
  Requests. Rate limited. Try after a while.')` is now a daily occurrence on GitHub issues
  and Stack Overflow). The 0.2.5x line of `yfinance` is essentially a cat-and-mouse game with
  Yahoo's anti-bot. There are no documented limits; expect a single IP to break around a few
  hundred symbols in tight loops.
- **Gotchas:**
  - `auto_adjust=True` (new default in 0.2.51+) means `Close` is already split- and
    dividend-adjusted and `Adj Close` is dropped. Pin the version *and* be explicit.
  - `MultiIndex` columns when you download >1 ticker. Don't trust positional access.
  - Pre/post-market bars sometimes leak into the 1d series.
  - `Ticker.history()` and `download()` use different code paths and occasionally disagree.
  - `repair=True` helps with bad ticks but slows things down dramatically.
- **Recommended use case:** Free fallback / disaster-recovery feed; one-off research; never a
  primary in a system you actually rely on. If you do build on it, cache aggressively to a
  local Parquet store so a Yahoo outage doesn't kill you.

### 1.2 Alpaca Market Data API

- **Cost:** Free tier with an Alpaca account (paper or live). "Algo Trader Plus" is $99/mo
  for full SIP realtime + options + crypto.
- **Coverage / latency:**
  - Free: **IEX-only** quotes (i.e., only trades that print on the IEX exchange).
    That's <3% of US consolidated volume — fine as a *price reference* but useless as a
    volume indicator for most names.
  - Paid: full SIP consolidated tape, sub-second WebSocket for trades/quotes/bars.
  - Historical: ~7 years of minute and daily bars on all US equities, free.
- **Rate limits:** Up to **10,000 API calls / minute** on paid; "200/min" on free is the
  conservative number repeatedly quoted in their forum and docs (it has been raised over
  time, but always design for 200/min on free).
- **Adjustments:** Bars endpoint accepts `adjustment=raw|split|dividend|all`. Decent quality;
  same source they use to execute against, which is a nice property.
- **Gotchas:** "Free realtime" misleads — it is IEX-only, not consolidated. Volume on free
  IEX bars is *much* lower than what you see on TradingView. For an EOD swing system that
  is acceptable for entry/exit prints but you should never compute relative volume from
  IEX-only bars.
- **Recommended use case:** If you are *already* using Alpaca for execution (paper or live),
  use their daily bars for free as a secondary source. Their consistency between data feed
  and execution side reduces backtest-vs-live drift.

### 1.3 Polygon.io (now rebranded **Massive**)

- **Cost (2025/26):** Free tier = 5 calls/min, EOD only, 2 years history — basically a demo.
  Paid stocks plans start around **$199/mo** for full historical + WebSocket; higher tiers
  for tick-level Trades/Quotes. This is well outside the sub-$50 budget.
- **Latency:** Sub-20ms realtime via WebSocket; flat-file S3 bucket for bulk historical.
- **Coverage:** Full SIP consolidated tape, all US equities, options, forex, crypto. 20+
  years of minute history on paid tiers.
- **Adjustments:** Reliable — has both adjusted and unadjusted endpoints. Maintains a
  splits/dividends history you can pull separately for your own adjustment logic.
- **Survivorship:** Polygon retains historical tickers after delisting (good), but verifying
  this for every name is an exercise.
- **Gotchas:**
  - Free tier rate limit (5/min) effectively rules out any backtest backfill.
  - Brand confusion: "Polygon.io" is now also marketed as "Massive" — same product, same docs,
    just don't get spooked when URLs change.
- **Recommended use case:** When you scale to multi-strategy / intraday and the $199/mo is
  small relative to AUM. Not for a sub-$50 hobbyist.

### 1.4 Tiingo

- **Cost:** **$10/mo** "Starter" (commercial use, ~1,800 EOD-quality tickers, news, IEX
  realtime); **$30/mo** "Power" lifts limits substantially. Free tier exists but is
  research-only license.
- **Coverage:** **30+ years of clean adjusted EOD** on US stocks + ETFs + mutual funds. The
  whole company is built around "good EOD data, not gold-plated tick." Tiingo also offers
  fundamentals (DAILY frequency for ~3,500 tickers), news API, crypto, forex.
- **Adjustments:** Probably the cleanest EOD adjustment quality at this price point.
  Maintains delisted tickers (survivorship-friendly) for the most-traded names.
- **Rate limits:** ~2,400 requests/hour on Starter — plenty for an EOD batch over 3k symbols
  if you parallelize with a small worker pool (`asyncio` + `aiohttp` works fine).
- **Gotchas:** Universe is curated, not exhaustive — you will not find every OTC tape or
  ADR. For "S&P 1500 + Russell 2000 + a handful of themes" it covers everything.
- **Recommended use case:** **Primary data source for a sub-$50 EOD swing engine.** This is
  the sweet spot.

### 1.5 EOD Historical Data (EODHD)

- **Cost:** **$19.99/mo** "All-In-One" gets you EOD + intraday + fundamentals + news for
  ~70+ exchanges worldwide; **$59.99/mo** for realtime.
- **Coverage:** Strongest *international* coverage in the budget tier. 30+ years of
  history. Bulk EOD download endpoints (one HTTP call → CSV of *every* US ticker for a day)
  — this is huge for batch backfills.
- **Adjustments:** Good. They expose both adjusted and unadjusted prices.
- **Rate limits:** 100,000 requests/day on the AIO plan; generous.
- **Gotchas:** Slightly worse EOD quality than Tiingo on US micro-caps in my experience and
  others' reports. The bulk-download endpoint is fantastic and underused.
- **Recommended use case:** Primary source if you trade non-US too, or if you specifically
  want the daily bulk-download workflow.

### 1.6 Finnhub

- **Cost:** Free tier is real (60 calls/min). Paid starts at **$9.99/mo** "Personal Use" and
  goes way up.
- **Coverage:** Decent EOD, but Finnhub's real strength is **fundamentals, earnings calendar,
  insider transactions, news, sentiment, alt-data**. WebSocket for realtime trades on paid.
- **Adjustments:** OK, not its strong suit; cross-check vs Tiingo if you care.
- **Gotchas:** The free tier is great for *catalysts* (earnings dates, IPOs, splits) but the
  EOD bars on free are limited in history (≤1 year for many endpoints).
- **Recommended use case:** **Catalyst / earnings overlay**, not primary OHLCV. Pair with
  Tiingo: Tiingo for prices, Finnhub free for "is earnings within the next 5 days?"

### 1.7 Alpha Vantage

- **Cost:** Free (5 calls/min, 500 calls/day) → $49.99–$249.99/mo for higher rates.
- **Coverage:** Wide (US + global EOD, intraday, FX, crypto, ~50 indicators built into the
  API itself).
- **Gotchas:** **Free tier is unusable for a scanner** — 5 calls/min × 1,440 min = 7,200/day
  but you're capped at 500. The 75-rpm tier is $50, edging your budget.
- **Recommended use case:** Quick experiments / single-ticker dashboards. Not a serious
  scanner backend.

### 1.8 Norgate Data

- **Cost:** **$30–$50/mo USD** for US stocks (Platinum tier is required for survivorship-free
  delisted history; cheaper tiers omit delisted names — which defeats the point).
- **Coverage:** US, AU, CA stocks + world futures. Decades of adjusted EOD. **Truly
  survivorship-bias-free** — they maintain *every* delisted ticker and the historical
  *constituents* of major indices (S&P 500 / S&P 1500 / Russell 1000-3000 / NASDAQ-100 /
  etc.) on every historical date. This is the killer feature for backtests of universe-based
  strategies ("rank top 10% of S&P 1500 by momentum each month").
- **Delivery:** Local SQLite-style data on disk via the Norgate Data Updater (NDU) Windows
  app + a Python package. On Linux you have to run NDU in Wine or on a Windows side-machine
  and sync.
- **Adjustments:** Gold-standard for backtests; they expose total-return-adjusted, capital-
  adjusted, and unadjusted.
- **Gotchas:** Windows-first. No realtime — strictly EOD updated after market close.
- **Recommended use case:** **The honest backtest layer.** If you're serious about avoiding
  survivorship bias, pay the $30 once for a research backfill, then run live signals off
  Tiingo/Alpaca/yfinance. Most retail systems quietly skip this and overestimate edge.

### 1.9 IEX Cloud — RIP

- **Status:** **Shut down August 31, 2024.** Acquired by Blue Sky Data. Migrating apps had a
  rough time. Mention only as a cautionary tale: **never single-source your data.** Your
  data adapter layer must support swapping vendors without rewriting strategy code.

### 1.10 Databento

- **Cost:** Usage-based ($/GB) or subscription. **US Equities Summary** (EQUS.SUMMARY — daily
  OHLCV across all RegNMS venues, delayed-basis 100% volume) is genuinely cheap on
  pay-as-you-go and they give **$125 of free credit on signup**. Their realtime SIP-class
  feeds start cheap-ish per dataset (~$50–$200/mo each).
- **Coverage:** Institutional. Direct feeds from CME, NYSE, NASDAQ, OPRA, etc. The cleanest,
  best-documented schemas in the industry (MBO, MBP-1, MBP-10, TBBO, trades, BBO-1s,
  BBO-1m, OHLCV-1s/1m/1h/1d).
- **Adjustments:** They emit *unadjusted* by design — you apply corporate actions yourself,
  which is the "correct" institutional approach.
- **Gotchas:** Schema is more involved (DBN binary format; use their `databento-python`
  client). Adjustment is on you. Pay-as-you-go bills can surprise.
- **Recommended use case:** When you outgrow Tiingo/Alpaca and want institutional-quality
  data without paying a Bloomberg terminal. The free $125 credit lets you backfill the
  EQUS.SUMMARY dataset for a full universe — worth doing on day one as a quality-control
  baseline against your primary feed.

### 1.11 Algoseek

- **Cost:** Enterprise. Quotes-on-request, four-figure minimums.
- **Coverage:** Decades of US tick + book data, options, futures. Used by funds.
- **Recommended use case:** Not for retail. Mentioned for completeness.

### 1.12 Honorable mentions

| Vendor | Niche | Note |
|---|---|---|
| **Twelve Data** | Multi-asset REST + WS, $0–$329 | 800 calls/day free, very clean docs, 99.95% SLA |
| **Financial Modeling Prep** | Fundamentals + SEC EDGAR | $19/mo entry, 30+ years of statements |
| **Marketstack** | Cheap EOD ($10/mo) | Limited history depth, OK as a second yfinance |
| **QuantConnect / LEAN** | Bundled data + backtester | $20+/mo; data tied to their cloud |
| **Quandl / Nasdaq Data Link** | Datasets marketplace | Sharadar fundamentals is the canonical pick |

### 1.13 Data layer design rules

Regardless of vendor:

1. **Wrap every vendor behind a single `DataAdapter` interface.** Methods: `get_daily(symbol,
   start, end)`, `get_intraday(symbol, tf, start, end)`, `get_snapshot(symbols)`,
   `get_corporate_actions(symbol)`, `get_universe(name, asof)`. Concrete classes
   `TiingoAdapter`, `AlpacaAdapter`, `YFinanceAdapter`, etc. Strategy code only sees the
   interface.
2. **Always cache locally.** Vendor outages are not "if," they're "when." A local DuckDB +
   Parquet cache means a Yahoo or Tiingo outage at 4:05pm doesn't kill the 4:30pm scan.
3. **Hash-version your adjustments.** Store a `(symbol, asof_date, adj_factor)` table so when
   a vendor revises splits, you can re-derive the affected window without nuking everything.
4. **Always backfill into both a primary and a secondary source.** Diff them weekly; alert on
   >0.5% close-price disagreement on liquid names.
5. **Survivorship-bias-free universe membership** must come from a vendor that retains
   delistings (Norgate, Polygon's tickers endpoint, Databento). Yahoo silently drops them.

---

## 2. Broker APIs for execution

For a swing engine you mostly need: place orders, cancel orders, query positions, query
account state, list filled orders by date. Anything more elaborate (algo VWAP, complex
exotics) is overkill at this scale.

### 2.1 Alpaca (paper + live)

- **What:** Commission-free US equities + options + crypto broker, built API-first.
- **Paper trading:** Excellent. Same endpoints, just a different base URL
  (`https://paper-api.alpaca.markets/v2` vs `…live…`). Identical schema for orders, fills,
  positions. Switching is one env var change.
- **Order types:** market, limit, stop, stop-limit, trailing-stop (single only), bracket
  (entry + take-profit + stop-loss), OCO (paired exits on an existing position), OTO
  (one-triggers-other). **Notable limitation:** trailing-stop is *not* yet supported as the
  stop-loss leg of a bracket/OCO. (Open feature request since 2020.) Workaround: enter with
  a bracket using fixed stop, then after partial profit, *replace* the stop with a
  trailing-stop standalone order.
- **TIF:** `day`, `gtc`, `opg` (market-on-open), `cls` (market-on-close), `ioc`, `fok`. For
  swing you want `day` for entries and `gtc` for resting stop/take-profit.
- **Rate limits:** 200 requests/min on free; 10,000/min on paid data plan. Very generous.
- **Auth:** API key + secret, header-based. No OAuth dance.
- **SDKs:** Official `alpaca-py` (current), `alpaca-trade-api-python` (legacy, archived).
  Always use `alpaca-py`.
- **Quirks:** Order updates arrive on the trading WebSocket (`/stream`); poll endpoints are
  also fine. After-hours `extended_hours=true` is supported for limit orders only.
- **Recommended use case:** **Default broker for a US-equity retail swing system.** Best
  paper-trading API in the industry. Lowest friction from research → paper → live.

### 2.2 Interactive Brokers (IBKR)

- **What:** The pro broker. Lowest commissions on margin/short-borrow, best routing,
  asset-class breadth (every exchange on earth, futures, options, FX, bonds).
- **APIs:**
  - **TWS / IB Gateway socket API** (the canonical one). Requires a desktop process — TWS or
    IB Gateway — to be running and authenticated. Painful in headless cloud.
  - **`ibapi`** — the official thin Python wrapper. Callback-driven, verbose.
  - **`ib_insync`** — the famous community wrapper. **Author Ewald de Wit passed away in
    early 2024** and the project is no longer maintained by him; the community
    `ib-api-reloaded/ib_async` fork is the active successor. Use `ib_async`. Pip name is
    `ib_async`.
  - **Client Portal Gateway (REST)** — newer, runs a Java gateway that exposes REST + WS.
    Auth via web SSO every ~24h, which is annoying for unattended bots.
- **Order types:** Everything. Brackets, OCAs (one-cancels-all, more flexible than OCO),
  trailing stops including as bracket leg, conditional orders, adaptive algo, VWAP, TWAP.
- **Paper trading:** "Paper account" in TWS — solid but has occasional fill weirdness vs
  live, especially MOC orders.
- **Rate limits:** ~50 messages/sec; market-data subscriptions are metered (you pay per
  exchange per month for live data; ~$10/mo for NYSE non-pro).
- **Gotchas:**
  - TWS / Gateway auto-logout daily unless you use `IBC` (IB Controller) to keep it logged
    in. Plan on running `ibc-gradle`/`IBC` in your Docker compose.
  - Conid (contract id) vs symbol — IBKR identifies instruments by conid; cache it.
  - Pacing violations on historical data requests if you backfill aggressively.
- **Recommended use case:** When commissions or routing actually matter (large size, shorts,
  options); when you need non-US markets; when you want pro-grade order types. For pure US
  long swing trades under $50k AUM, the operational tax of IBKR isn't worth it vs Alpaca.

### 2.3 Tradier

- **What:** Self-clearing broker; API-first, especially strong on options.
- **API:** REST + WebSocket. Three environments: Sandbox (paper, free), Brokerage (live),
  Market Data (data only).
- **Order types:** Equity & multi-leg options; **OCO, OTO, OTOCO** all supported natively —
  the OTOCO is what people call "bracket." Limit, stop, stop-limit, market. **Trailing
  stops** also supported.
- **Rate limits:** Documented per endpoint family. ~120 req/min for the trading endpoints,
  ~60/min for non-realtime market data, higher for streaming. Plenty for EOD.
- **Pricing:** $0 commission on stocks; $0.35/contract options. Market-data subscription
  required for streaming ($10/mo).
- **Paper:** Sandbox is functional but feels less polished than Alpaca's.
- **Recommended use case:** Strong alternative to Alpaca when you also want options. Cleaner
  multi-leg options API than Alpaca historically. Good for a "swing + occasional spread"
  setup.

### 2.4 TradeStation

- **What:** Brokerage + platform; REST + streaming API.
- **API:** OAuth2, fairly modern. Order types include brackets and OCO. Historical data is
  included.
- **Gotchas:** Approval process for API access is slower than Alpaca; commission structure
  is more "old broker" (per-trade and per-share options).
- **Recommended use case:** If you already use TradeStation's charting and want the same
  account programmatic. Otherwise Alpaca or Tradier are easier to onboard.

### 2.5 Robinhood (unofficial)

- **What:** No official public API. `robin_stocks` and `pyrh` are community libraries that
  reverse-engineer the mobile API.
- **Risk:** **You can and will get your account locked / closed for API trading.** This is
  documented repeatedly on GitHub issues. Robinhood's ToS prohibits unattended programmatic
  access.
- **Recommended use case:** **Don't.** If your goal is automation, switch broker. The
  account-ban risk dwarfs any UX benefit.

### 2.6 Charles Schwab (post-TDA)

- **What:** Schwab finished the TDA acquisition; **TDA's Developer API was sunset in May
  2024**. The successor is the Schwab Trader API (individual + commercial).
- **Auth:** OAuth2 with a refresh-token dance every 7 days. Painful but doable; community
  libraries handle the loop.
- **Coverage:** Full Schwab brokerage — equities, options, mutual funds. Streamer API for
  realtime quotes.
- **Order types:** Single, OCO, OTO, OTOCO (bracket), trailing stop, conditional. Good
  breadth.
- **Pricing:** API is free with a Schwab brokerage account (no monthly platform fee).
- **Gotchas:**
  - Individual developer onboarding takes days; app must be approved.
  - 7-day refresh token forces a re-auth ceremony you must automate or be reminded of.
  - Streamer protocol is its own JSON dialect, not standard SSE/WebSocket semantics.
- **Recommended use case:** If you already have a Schwab account, this is a real option for
  US-equity automation. Otherwise Alpaca onboards in minutes vs Schwab's days.

### 2.7 Comparison matrix

| Broker | Paper API | Best order type | Stocks comm | Options comm | Rate limit | Auth | Onboarding | Best for |
|---|---|---|---|---|---|---|---|---|
| Alpaca | ★★★★★ | Bracket/OCO/OTO | $0 | $0 | 200–10k/min | API key | Minutes | Default retail automation |
| IBKR | ★★★★ | OCA/Adaptive/Bracket | $0.0035/sh* | $0.65/ct* | 50/s | TWS login | Days | Pros, non-US, options |
| Tradier | ★★★ | OTOCO/OCO | $0 | $0.35/ct | 120/min | OAuth | Days | Options-heavy swing |
| TradeStation | ★★★ | OCO/Bracket | $0–$5 | $0.50–$0.60 | Modest | OAuth | Days | Existing TS users |
| Schwab | ★★★ | OCO/OTOCO | $0 | $0.65/ct | Modest | OAuth+refresh | Days | Existing Schwab users |
| Robinhood | ✗ (unofficial) | Limited | $0 | $0 | n/a | Reverse-eng | Hostile | Don't |

*IBKR "Pro" pricing; "Lite" is commission-free but worse routing.*

### 2.8 Execution design rules

1. **Mirror your `DataAdapter` with a `BrokerAdapter`.** Methods: `submit_order(symbol,
   qty, side, type, tif, limit_price=None, stop_price=None, bracket=None)`,
   `cancel(order_id)`, `replace(order_id, ...)`, `list_orders(status, since)`,
   `list_positions()`, `get_account()`. Live and paper differ only by environment URL.
2. **Idempotency keys.** Use `client_order_id` on every submit — set it to a deterministic
   hash of `(signal_id, side, qty)`. If your scheduler retries after a network blip, the
   broker rejects the duplicate instead of doubling your position.
3. **Two-stage submit.** Compute orders → write them to a `pending_orders` table → display
   them in the dashboard → require a "✅ confirm" tap in Telegram or a dashboard button →
   then call `submit_order`. This is your last human checkpoint.
4. **Reconcile on every cycle.** At the start of every scheduled run, fetch positions and
   open orders from the broker and reconcile against your local DB. Drift → halt + alert.

---

## 3. Python ecosystem stack

### 3.1 Indicator libraries

| Library | What | Pros | Cons |
|---|---|---|---|
| **TA-Lib** | C library + Python bindings; 200+ indicators, candlestick patterns | Fast, battle-tested, the academic reference | C build hell on Linux (apt install `ta-lib0-dev` or use `talib-binary` prebuilt wheel). Mutable internal state on incremental updates. |
| **pandas-ta** | Pure-python on top of pandas | Trivial install (`pip install pandas-ta`), 130+ indicators, idiomatic `df.ta.rsi()` | Slower than TA-Lib; pandas dependency. Original repo was archived in 2024 → community fork `pandas-ta-classic` is the maintained one in 2025. |
| **ta** | Pure-python | Cleaner API than pandas-ta in places | Smaller indicator set |
| **finta** | Pure-python | OK | Maintenance has been quiet |
| **vectorbt's built-ins** | Numba-compiled | Vectorized across cross-sections; fastest in pure-python land | Tied to vectorbt's data model |
| **Custom NumPy** | Roll your own | Total control, perfect incremental updates | You will get EMA seeding wrong; don't unless you must |

**Recommendation:** Use **`pandas-ta-classic`** as the default. Add **`TA-Lib`** *only* for
candlestick pattern detection (CDLENGULFING etc.) and only if you actually use patterns.
Install via:

```bash
# Debian/Ubuntu
sudo apt-get install -y build-essential wget
wget https://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz && cd ta-lib && ./configure --prefix=/usr && make && sudo make install
pip install TA-Lib
# Or, easier:
pip install talib-binary
```

### 3.2 Backtesting frameworks

| Framework | Paradigm | Speed | Live-trading bridge | Best for |
|---|---|---|---|---|
| **vectorbt** (and `vectorbtpro`) | Vectorized, Numba | Fastest by far (1000× over event-driven on cross-sectional scans) | Indirect — you'd hand-roll | Multi-symbol scan strategies, parameter sweeps |
| **backtrader** | Event-driven, OOP | Slow but accurate | Built-in IBKR/Oanda live brokers (somewhat dated) | Single-asset complex logic, beginners |
| **zipline-reloaded** | Event-driven (Quantopian heritage) | Medium | None first-class | Bundled data + research notebooks |
| **nautilus_trader** | Event-driven, Rust core | Fast and accurate | First-class live with multiple venue integrations | Production multi-venue automation |
| **backtesting.py** | Event-driven, minimal | Fast for small | None | Quick one-off prototyping |
| **bt** | Tree-of-strategies | Medium | None | Portfolio-of-strategies allocation |
| **lean / QuantConnect** | Event-driven cloud | N/A | Built-in | If you want cloud-bundled data |

**Recommendation for swing:**

- Research / scans / parameter sweeps → **vectorbt** (free) or **vectorbtpro** (~$400/yr) if
  you can afford it; the pro version's portfolio sim is dramatically better.
- Production live engine → **don't reuse the backtest framework**. Build a thin event loop
  that calls the same strategy `compute_signals(df)` function the backtest does. This avoids
  the "I shipped my backtester to prod and it has subtle calendar bugs" failure mode.
- **nautilus_trader** is the right answer the day you outgrow homebrew. It is Rust-cored,
  production-grade, and supports backtest + live with the same code. Steeper learning curve.

### 3.3 Scheduling

| Tool | What | Fit for EOD swing |
|---|---|---|
| **cron** | OS scheduler | Fine for "run this script at 16:05 ET". Painful for cross-machine, retries, alerting. |
| **APScheduler** | In-process Python scheduler | **Sweet spot for a single-VPS swing bot.** Cron-like syntax in Python, supports timezones natively, persists jobs in SQLite if you want. |
| **systemd timers** | OS-level | Cleaner than cron; great for triggering the Python process if you don't want a long-running daemon. |
| **Celery** | Distributed task queue (Redis/RabbitMQ broker) | Overkill. Useful if you have a web app dispatching jobs to workers, not for a 5-jobs-a-day batch. |
| **Prefect** | Modern orchestrator, UI, retries, deps | Nice DX, but the Prefect Server/Cloud overhead is heavy for one bot. Worth it once you have ≥5 inter-dependent flows. |
| **Dagster** | Asset-centric orchestrator | Same story as Prefect — beautiful but heavy for one bot. |
| **Airflow** | The legacy orchestrator | Don't. Heavyweight, painful in containers, designed for data warehouses. |
| **Temporal** | Durable workflows | Overkill. |

**Recommendation:** Start with **APScheduler** inside a long-running `python -m engine.run`
process supervised by Docker. Move to **Prefect** if and only if you grow >5 flows or want a
nicer UI for run history.

### 3.4 Dashboard / API

- **FastAPI** for the backend API (positions, signals, PnL, controls). Built-in OpenAPI, async
  out of the box, perfect for a single-process bot exposing internal state.
- **Streamlit** is the lazy/fast option for an internal dashboard — one Python file → web UI.
  Use it for a "today's signals + portfolio + kill switch" page.
- **Next.js + shadcn/ui** if you want a real product UI (overkill for personal use, but if
  you're sharing with friends or planning to charge for it eventually, do it right).
- **NiceGUI** is a nicer-than-Streamlit single-file alternative if you want reactive UI in
  pure Python.

### 3.5 Other utilities

- **`requests`** + **`tenacity`** for retries with exponential backoff on every HTTP call.
- **`httpx`** + **`anyio`** if you want async.
- **`pydantic`** v2 for typed config, env, and DB schemas.
- **`structlog`** for JSON logs; ship to a file + a Loki/Logtail/Better Stack if you want.
- **`rich`** for nice CLI output in the manual ops scripts.
- **`typer`** for the CLI entry points (backfill, scan, paper-trade, replay, etc.).
- **`uv`** for fast dependency management (replaces pip + venv; 10–100× faster).
- **`ruff`** + **`black`** + **`mypy --strict`** for hygiene.
- **`pytest`** + **`pytest-asyncio`** for tests; **`hypothesis`** for property tests on
  indicator math.

---

## 4. Storage architecture

### 4.1 What you actually need to store

| Domain | Volume (rough) | Read pattern | Write pattern |
|---|---|---|---|
| Daily OHLCV history | ~5k symbols × ~10y × 252 = ~13M rows | Bulk read at scan time (whole columns of recent N) | Append-only daily; occasional revisions for splits |
| Intraday 1m bars (optional) | ~5k × ~390 × 60d = ~117M rows | Selective read (last few days of one symbol) | Append daily |
| Indicator cache | Same shape as bars | Read at scan time | Recompute trailing window |
| Universe membership (S&P 500 history, etc.) | ~10k events | Read once per backtest | Rare write |
| Corporate actions | ~50k events | Read on rebuild | Append nightly |
| Signals | ~10–100/day | Read for dashboard, audit | Append per scan |
| Orders / fills | ~10–100/day | Read for reconciliation | Append per submit/fill |
| Positions | tens of rows | Read every cycle | Update per fill |
| Equity curve / metrics | one row per day | Read for dashboard | Append nightly |

### 4.2 Engine choices

| Engine | Strength | Weakness | Use for |
|---|---|---|---|
| **SQLite** | Zero ops, in-file, ACID, fast on a single writer | Single-writer; not great for analytic scans on M+ rows | **Operational tables**: signals, orders, fills, positions, equity curve, audit log |
| **DuckDB** | Columnar OLAP, reads Parquet directly, no server, blistering fast on aggregates | Concurrency story is "one writer, many readers" | **Analytic queries** over OHLCV history (`SELECT symbol, AVG(close) FROM bars WHERE date > …`) |
| **Parquet** (partitioned) | Compressed columnar files, language-agnostic, infinite scale, S3-friendly | No transactions, need a query engine on top | **OHLCV history bulk store** — one Parquet file per symbol or per (year, month) partition |
| **Postgres** | The default. Full SQL, concurrency, indexes, JSON, extensions | Sized for OLTP; bar history queries are not its strength | Only if you need multi-process concurrency or a web app sharing the DB |
| **TimescaleDB** | Postgres + hypertables for time series | All the Postgres ops overhead | If you commit to Postgres and want time-series ergonomics for free |
| **QuestDB** | SIMD-native column store, ILP ingest, sub-ms queries | Operational footprint, schema rigidity | Only if you genuinely capture ticks |
| **InfluxDB** | Time series specialist | Schema flux 1→2→3, costly cloud | Skip for trading; better for ops monitoring |
| **ClickHouse** | Industrial columnar | Operational overhead | When you become a fund |

### 4.3 Recommended layered storage

```
data/
├── bars/
│   ├── daily/
│   │   └── symbol={SYMBOL}/year={YYYY}/data.parquet      # primary OHLCV history
│   └── intraday_1m/
│       └── symbol={SYMBOL}/year={YYYY}/month={MM}/data.parquet
├── corporate_actions/
│   └── data.parquet
├── universe/
│   ├── sp500_history.parquet
│   ├── russell2000_history.parquet
│   └── delisted.parquet
├── indicators/
│   └── set={INDICATOR_SET_HASH}/symbol={SYMBOL}.parquet  # cacheable / regenerable
└── catalog.duckdb                                         # views over the above
state/
└── ops.sqlite                                             # signals, orders, fills, positions
```

**Why this split:**

- Bars + indicators are *append-only, analytic, regeneratable* → Parquet + DuckDB.
- Operational state is *small, transactional, mutated* → SQLite.
- DuckDB has first-class Parquet readers, so a query like

  ```sql
  CREATE VIEW bars_daily AS
    SELECT * FROM read_parquet('data/bars/daily/**/*.parquet', hive_partitioning=1);
  ```

  lets you treat the directory tree as one table without ETL.
- Backups: `data/` is restorable from vendor (tolerate hours of downtime). `state/` is
  precious — back it up every 15 min (litestream → S3 is perfect for SQLite).

### 4.4 Suggested schemas

**`ops.sqlite` (SQLite):**

```sql
CREATE TABLE signals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    asof_date       TEXT    NOT NULL,         -- ISO date the signal was computed for
    generated_at    TEXT    NOT NULL,         -- ISO timestamp
    strategy        TEXT    NOT NULL,
    symbol          TEXT    NOT NULL,
    side            TEXT    CHECK(side IN ('long','short')) NOT NULL,
    entry_price     REAL    NOT NULL,         -- intended entry (e.g. next-day open)
    stop_price      REAL    NOT NULL,
    target_price    REAL,
    risk_pct        REAL    NOT NULL,         -- % equity at risk
    confidence      REAL,                     -- model score 0..1
    rationale_json  TEXT    NOT NULL,         -- indicator snapshot for audit
    status          TEXT    CHECK(status IN ('emitted','acked','rejected','filled','expired'))
                            NOT NULL DEFAULT 'emitted',
    client_order_id TEXT    UNIQUE
);
CREATE INDEX ix_signals_asof ON signals(asof_date, strategy);
CREATE INDEX ix_signals_symbol_status ON signals(symbol, status);

CREATE TABLE orders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id       INTEGER REFERENCES signals(id),
    broker          TEXT    NOT NULL,        -- 'alpaca-paper', 'alpaca-live', etc
    client_order_id TEXT    UNIQUE NOT NULL,
    broker_order_id TEXT,
    symbol          TEXT    NOT NULL,
    side            TEXT    NOT NULL,
    qty             INTEGER NOT NULL,
    order_type      TEXT    NOT NULL,
    limit_price     REAL,
    stop_price      REAL,
    tif             TEXT    NOT NULL,
    submitted_at    TEXT    NOT NULL,
    status          TEXT    NOT NULL,
    raw_json        TEXT    NOT NULL
);

CREATE TABLE fills (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        INTEGER REFERENCES orders(id),
    fill_time       TEXT    NOT NULL,
    qty             INTEGER NOT NULL,
    price           REAL    NOT NULL,
    commission      REAL    NOT NULL DEFAULT 0
);

CREATE TABLE positions (
    symbol          TEXT    PRIMARY KEY,
    qty             INTEGER NOT NULL,
    avg_price       REAL    NOT NULL,
    opened_at       TEXT    NOT NULL,
    last_signal_id  INTEGER REFERENCES signals(id),
    stop_order_id   INTEGER REFERENCES orders(id),
    target_order_id INTEGER REFERENCES orders(id)
);

CREATE TABLE equity_curve (
    date            TEXT    PRIMARY KEY,
    equity          REAL    NOT NULL,
    cash            REAL    NOT NULL,
    gross_exposure  REAL    NOT NULL,
    net_exposure    REAL    NOT NULL,
    open_positions  INTEGER NOT NULL,
    pnl_day         REAL    NOT NULL,
    pnl_unrealized  REAL    NOT NULL,
    high_water_mark REAL    NOT NULL
);

CREATE TABLE audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT NOT NULL,
    actor       TEXT NOT NULL,        -- 'scheduler', 'human:adi', 'broker_ws'
    event       TEXT NOT NULL,
    payload     TEXT NOT NULL         -- JSON
);
```

**Parquet `bars/daily`:**

```
symbol     STRING       (partition)
year       INT16        (partition)
date       DATE
open       DOUBLE
high       DOUBLE
low        DOUBLE
close      DOUBLE
adj_close  DOUBLE
volume     BIGINT
vwap       DOUBLE       -- optional, if vendor provides
source     STRING       -- vendor that wrote this row
ingested_at TIMESTAMP
```

---

## 5. Indicator computation pipeline

### 5.1 The naive approach (don't)

```python
for symbol in universe:                # 5,000 symbols
    df = load_bars(symbol)             # 2,500 rows each
    df['rsi14'] = ta.rsi(df.close, 14) # recompute everything
    df['sma200'] = ta.sma(df.close, 200)
    ...
```

This is 5,000 file opens, 5,000 full-history recomputes, every day. 30+ minutes for nothing.

### 5.2 Incremental + cached

**Pattern:**

1. **Stable indicator set hash.** Hash the indicator spec (`{'rsi':[14], 'sma':[20,50,200],
   'atr':[14], 'adx':[14]}`) → `set_id`. Store cached values under
   `indicators/set=SET_ID/symbol=SYM.parquet`.
2. **On daily run:** load cached indicators, check `max(date)`, append only new bar(s) and
   recompute the indicators *only for the tail window* needed to make them numerically
   stable (e.g., for SMA200 you need 200 prior bars; for EMA you need ~3× span to converge).
3. **Vectorize across symbols.** With vectorbt:

   ```python
   import vectorbt as vbt
   close = pd.DataFrame({s: load_close(s) for s in universe})  # T × N
   rsi = vbt.RSI.run(close, window=14).rsi                     # T × N
   ```

   One Numba-compiled pass over a 2500 × 5000 matrix is ≈100× faster than per-symbol loops.

4. **Parallelize the I/O.** Loading 5,000 Parquet files is I/O-bound — use a thread pool
   (`concurrent.futures.ThreadPoolExecutor(max_workers=32)`). DuckDB's single
   `read_parquet('**/*.parquet')` does this for you internally even better.

### 5.3 Corporate actions mid-history

The classic foot-gun. If `AAPL` splits 4:1 on date `D`, your raw bars need adjusting back
through history *or* your indicator math breaks across the split.

**Two clean strategies:**

1. **Adjusted-only storage.** Always store *split- and dividend-adjusted close*. Re-adjust
   the entire history whenever a new split or dividend lands. Simple to reason about; bad if
   you also need unadjusted (e.g., for "true" dollar-volume).
2. **Unadjusted storage + adjustment factor table.** Store raw bars, plus a per-(symbol,
   date) `adj_factor`. Indicator computation pulls `close * adj_factor_at_asof_date /
   adj_factor_at_each_bar`. This is what Norgate and Databento expect. More work, but
   lossless and lets you backtest *as you would have seen prices on the day*.

**Either way:** when a corporate action is detected, *invalidate the indicator cache for
that symbol* (delete or version-bump). The signal pipeline should treat indicator-cache
freshness as an explicit input, not assume it.

### 5.4 Parallelization across symbols

For an EOD batch on a 4-core VPS:

- **vectorbt path:** single process, vectorized across symbols, ~30s for full S&P 1500
  with a dozen indicators.
- **per-symbol path:** `multiprocessing.Pool(processes=4)` with each worker handling
  ~1/4 of the universe. ~2–5 minutes.
- Don't use `asyncio` here — indicator math is CPU-bound, not I/O.

---

## 6. Signal pipeline architecture

### 6.1 The canonical flow

```
       ┌────────────────────────────────────────────────────────────┐
       │ 16:05 ET (after RTH close, after consolidated tape settles)│
       └─────────────────────────────┬──────────────────────────────┘
                                     │
                       ┌─────────────▼────────────┐
                       │ 1. is_trading_day(today) │  pandas_market_calendars
                       └─────────────┬────────────┘
                                     │
                       ┌─────────────▼────────────┐
                       │ 2. fetch + upsert bars   │  DataAdapter (Tiingo primary)
                       │    for universe(asof)    │  diff vs secondary (Alpaca)
                       └─────────────┬────────────┘
                                     │
                       ┌─────────────▼────────────┐
                       │ 3. compute indicators    │  vectorized, cached
                       └─────────────┬────────────┘
                                     │
                       ┌─────────────▼────────────┐
                       │ 4. run strategy rules    │  pure function: df → candidates
                       └─────────────┬────────────┘
                                     │
                       ┌─────────────▼────────────┐
                       │ 5. risk filter           │  position-sizing, sector caps,
                       │                          │  open-position overlap, kill switch
                       └─────────────┬────────────┘
                                     │
                       ┌─────────────▼────────────┐
                       │ 6. persist signals       │  ops.sqlite
                       └─────────────┬────────────┘
                                     │
                       ┌─────────────▼────────────┐
                       │ 7. notify (Telegram +    │  with one-tap "✅ paper-fire"
                       │    Discord + dashboard)  │  button
                       └─────────────┬────────────┘
                                     │
                       ┌─────────────▼────────────┐
                       │ 8. AT NEXT OPEN: submit  │  bracket orders via BrokerAdapter
                       │    confirmed signals     │  with client_order_id idempotency
                       └─────────────┬────────────┘
                                     │
                       ┌─────────────▼────────────┐
                       │ 9. WS listener updates   │  fills, partials, rejections
                       │    orders/fills/positions│
                       └──────────────────────────┘
```

### 6.2 Idempotency and audit

- **Idempotent steps.** Every step is keyed by `(asof_date, strategy_version)`. Re-running
  the whole pipeline for today must produce the same `signals` table (assuming data hasn't
  changed). Achieved by `INSERT OR IGNORE` keyed on `(asof_date, strategy, symbol)`.
- **Strategy version.** Bake a `STRATEGY_VERSION` constant into every signal row. When you
  change the rules, bump the version — old signals stay attributable to the old code.
- **Rationale JSON.** Every signal carries a JSON blob of the exact indicator values that
  triggered it (`{"rsi14": 28.4, "sma200_dist": -0.12, "atr14": 1.85, ...}`). Two purposes:
  (a) you can debug a stinker months later; (b) if you ever ML-rank signals, the rationale
  is your feature matrix.
- **Replay mode.** A CLI command `engine replay --date 2026-05-23` reruns the entire
  pipeline as-of that date (using bars known on that date — point-in-time correctness via
  Parquet `ingested_at` filtering). Lets you reproduce any past signal.

### 6.3 Strategy interface

```python
from typing import Protocol
import pandas as pd

class Strategy(Protocol):
    name: str
    version: str

    def required_history(self) -> int:
        """Min bars needed before this strategy emits anything."""

    def compute(self,
                bars: dict[str, pd.DataFrame],         # symbol -> OHLCV
                indicators: dict[str, pd.DataFrame],   # symbol -> indicator cols
                asof: pd.Timestamp,
                context: "MarketContext"               # regime, VIX, etc.
                ) -> list["SignalCandidate"]:
        """Pure function. No side effects, no I/O."""
```

The pure-function shape is what lets you reuse the *same* `compute` in vectorbt research and
the live engine. **The strategy never knows whether it's in research or live.**

---

## 7. Paper trading & performance tracking

### 7.1 Paper modes

There are three "paper" levels and you want all three:

1. **Backtest paper.** vectorbt sim on historical data. Tells you in-sample / out-of-sample
   expectancy. Suffers from look-ahead and survivorship if you're not careful.
2. **Forward paper-from-signals.** Run the live signal pipeline daily, persist signals,
   simulate fills *yourself* using next-day OHL (open for entry, intraday high/low for
   stop/target). No broker round-trip; pure logic test.
3. **Broker paper.** Submit real orders to Alpaca Paper. Now you also test the broker
   adapter, idempotency, partial fills, OCA leg cancels, and your reconciliation.

**Run #2 and #3 in parallel from day one.** When they disagree, you've found a bug.

### 7.2 What to log per signal lifecycle

For each `signal_id`, capture:

- The intended entry/stop/target prices at emission.
- The bracket order ids at submission.
- Every fill (price, qty, time, commission).
- The final exit reason (`stop`, `target`, `time`, `manual`, `signal_inverted`).
- Holding period.
- Realized PnL ($ and R-multiples — R = initial risk per share × shares).
- **Slippage vs intended:** `entry_fill_price - signal.entry_price` and similar for exit.
- **Drift vs backtest:** for the same signal generated in the offline backtest, compare its
  simulated PnL to the live (paper) PnL. The mean and stdev of this drift over 100+ signals
  is your "backtest honesty" metric. If drift is materially negative and persistent, your
  backtest is lying.

### 7.3 PnL attribution

Track at three layers:

- **Per signal.** R-multiple, slippage components, time-in-trade.
- **Per strategy.** When you run multiple strategies, attribute realized PnL by `strategy`
  column. Decompose into:
  - selection alpha (did you pick winners vs the universe?)
  - timing alpha (did your entry/exit beat naïve next-day open/close?)
  - friction (commissions + slippage)
- **Per portfolio.** Equity curve, max DD, Sharpe, Sortino, Calmar, longest losing streak.
  Use `quantstats` (free) to produce a nice HTML tear sheet weekly.

### 7.4 Drift detection

A simple, useful alert:

> If trailing-30-day live R-expectancy is below the trailing-30-day backtest R-expectancy by
> more than 1 standard deviation of the historical backtest run-to-run noise → flag for
> human review.

This catches both bugs (your live engine is doing the wrong thing) and regime shifts (the
strategy is just not working right now).

---

## 8. Alerting & dashboard UX

### 8.1 Channels

- **Telegram** — primary push. Bot DMs you the daily signal pack with an inline keyboard
  ("✅ paper fire", "🛑 skip", "🔍 show chart"). Best mobile UX.
- **Discord** — secondary, for richer formatting and a shared channel if you have a small
  group. Use embeds; not tables.
- **Email** — daily digest (post-close) and weekly tear sheet attached as HTML.
- **Browser dashboard** — internal-only, behind Tailscale / Cloudflare Access. Real UI for
  deeper inspection.

Never use SMS for signals — latency and per-message cost. Use SMS only for *paging* on
critical alerts ("KILL SWITCH TRIPPED").

### 8.2 What a useful swing dashboard shows

Top of page, always visible:

- **Account snapshot.** Equity, cash, gross / net exposure, # positions, day PnL,
  high-water-mark.
- **Risk status.** "OK" / "DEGRADED" / "HALTED" + reason. e.g., "HALTED — daily order cap
  reached".
- **Regime gauge.** Your market-context input(s). e.g., SPY > 200d? Y/N. VIX percentile.
  Breadth (% of S&P above 50d). Color: green/amber/red.

Today's setups panel:

- Ranked list of signal candidates with: symbol, side, entry, stop, target, R:R, position
  size, % equity at risk, strategy, score.
- Mini sparkline of last 60 days.
- One-tap actions: ✅ fire (paper), 🛑 skip, 🔗 chart (TradingView deep link).

Open positions panel:

- Symbol, side, entry, current, unrealized R, days held, stop, target, distance to each.

Watchlist scan panel:

- "Approaching" — symbols near triggering a signal (within 1 ATR of breakout etc.).

History panel:

- Closed trades table sortable by date / symbol / R / strategy.
- Equity curve + drawdown.

Ops panel:

- Last data refresh times by vendor.
- Scheduler heartbeat ("last EOD scan: 16:07 ET, success, 1,532 symbols, 4 signals").
- **Kill switch** (big red button) → sets `KILL=1`, broker adapter refuses any further
  submits, open orders are *not* auto-canceled (manual decision).

### 8.3 Tech for the dashboard

Cheap path: **Streamlit** in the same Docker compose, password-protected, exposed on a
random port behind Tailscale. ~200 lines of Python.

Nicer path: **FastAPI + Next.js + shadcn/ui + Tremor.so** for the charts. SSE for live
updates from the engine.

---

## 9. Compliance & safety rails

### 9.1 PDT rule (and the 2026 change)

- **Old rule (historical):** A margin account flagged as Pattern Day Trader (4+ day trades
  in 5 business days, >6% of activity) had to maintain ≥$25,000 equity.
- **2026 update:** The SEC has approved rule changes that effectively retire the PDT
  designation for many brokers; check your broker's specific policy before relying on it.
  Cash accounts were never subject to PDT.
- **For a *swing* engine** this is mostly moot — by definition you hold overnight. But if
  your strategy ever same-day-exits on a stop (rare but possible), you can accumulate day
  trades. **Solution:** in the risk filter, count day trades in the trailing 5 business days
  and refuse new opens that *could* trigger same-day exits, when you're at 3/5.

### 9.2 Hard caps in the risk filter

A `RiskGuard` class consults config + state and answers `(ok: bool, reason: str)`:

```python
@dataclass
class RiskLimits:
    max_positions: int = 10
    max_gross_exposure_pct: float = 1.00   # 100% of equity, no margin
    max_per_position_pct: float = 0.15     # 15% of equity per name
    max_per_sector_pct: float = 0.35       # 35% any one GICS sector
    max_risk_per_trade_pct: float = 0.0075 # 0.75% equity at risk per trade (stop-based)
    max_total_risk_open_pct: float = 0.04  # sum of risk on all open positions ≤ 4%
    max_orders_per_day: int = 20           # circuit breaker
    max_signals_per_day: int = 30
    halt_on_daily_loss_pct: float = 0.02   # if day PnL ≤ -2%, halt
    halt_on_dd_from_hwm_pct: float = 0.10  # if equity ≤ -10% from HWM, halt
    require_human_confirm: bool = True     # never auto-fire by default
```

### 9.3 Kill switches

Three layers:

1. **Manual kill** — dashboard button, Telegram `/kill` command, or `KILL=1` env var. Sets a
   sentinel file `state/KILL`. Broker adapter refuses `submit_order` while the file exists.
2. **Auto kill** — daily loss limit, drawdown-from-HWM limit, sudden data feed failure
   (>30min stale bars), broker auth failure.
3. **Watchdog** — separate process (cron every 5 min) checks the engine heartbeat file
   (`state/heartbeat`); if older than 15 min during RTH, alerts on all channels.

### 9.4 The "no auto-fire" pattern

Default config:

```yaml
trading:
  mode: paper            # paper | live
  auto_fire: false       # if false, signals are emitted but orders require human confirm
  confirm_channel: telegram
  confirm_timeout_minutes: 30   # if no confirm by then, signal expires
```

The engine emits the signal, posts to Telegram with inline buttons (`✅ Confirm` / `🛑 Skip`),
and waits. Confirmation flips the signal status to `acked` and queues the broker submit for
**next market open** (not immediately — swing entries are typically MOO or limit-at-open).

**Even in `auto_fire: true` mode**, keep a per-day order cap and a per-day notional cap as a
second layer of defense.

### 9.5 Environment separation

```bash
# .env.paper
ENV=paper
ALPACA_KEY=...
ALPACA_SECRET=...
ALPACA_BASE_URL=https://paper-api.alpaca.markets
DATA_PRIMARY=tiingo
NOTIFY_CHANNELS=telegram,discord
LIVE_TRADING_GUARD=disabled

# .env.live
ENV=live
ALPACA_KEY=...
ALPACA_SECRET=...
ALPACA_BASE_URL=https://api.alpaca.markets
DATA_PRIMARY=tiingo
NOTIFY_CHANNELS=telegram,email
LIVE_TRADING_GUARD=enabled    # the BrokerAdapter validates this on every submit
```

A simple boot-time assertion catches the worst foot-gun:

```python
if config.env == "live":
    assert "paper" not in config.broker.base_url, "paper URL in live env!"
    assert config.require_human_confirm or config.daily_notional_cap < equity * 0.05
```

### 9.6 Audit & change-control

- Every order submit, every signal emission, every config change → `audit_log` row.
- Git: tag every release; every live order's `client_order_id` includes the git short SHA
  (`swing-v1.4.0-a1b2c3d-20260601-AAPL-long`). When something blows up, the order id alone
  tells you what code did it.
- Config is in version control; the live engine refuses to start on a dirty working tree
  when `ENV=live`.

---

## 10. Deployment

### 10.1 VPS sizing

For an EOD swing engine covering ~2,000 symbols, indicators, signal generation, dashboard,
notifications:

| Resource | Need | Comfortable |
|---|---|---|
| vCPU | 1 | 2 |
| RAM | 1 GB | 2–4 GB |
| Disk | 10 GB (with 5y daily data) | 40–80 GB SSD (with 60d 1m intraday) |
| Bandwidth | 50 GB/mo | 500 GB/mo |

That's a **$6/mo Hetzner CX22** or a **$12/mo DigitalOcean Basic Droplet**. If you want
1-minute intraday on 5,000 symbols, go to 4 vCPU / 8 GB / 160 GB (~$24/mo).

**TZ:** set the host to `America/New_York`. Don't argue with the market.

### 10.2 Docker Compose

```yaml
services:
  engine:
    build: .
    env_file: .env.${ENV:-paper}
    volumes:
      - ./data:/app/data
      - ./state:/app/state
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-m", "engine.healthcheck"]
      interval: 60s
      timeout: 10s
      retries: 3

  dashboard:
    build:
      context: .
      dockerfile: Dockerfile.dashboard
    env_file: .env.${ENV:-paper}
    volumes:
      - ./data:/app/data:ro
      - ./state:/app/state:ro
    ports:
      - "127.0.0.1:8501:8501"   # bind localhost only; expose via Tailscale
    depends_on: [engine]
    restart: unless-stopped

  litestream:
    image: litestream/litestream:latest
    volumes:
      - ./state:/data
      - ./litestream.yml:/etc/litestream.yml
    command: replicate
    restart: unless-stopped
```

### 10.3 Scheduling alignment

Driven inside the `engine` process by APScheduler with a `pytz.timezone('America/New_York')`
on the trigger:

```python
sched = BlockingScheduler(timezone='America/New_York')

@sched.scheduled_job('cron', day_of_week='mon-fri', hour=9, minute=25)
def pre_open_reconcile(): ...                    # 5min before open

@sched.scheduled_job('cron', day_of_week='mon-fri', hour=9, minute=31)
def submit_confirmed_signals(): ...              # 1 min after open

@sched.scheduled_job('cron', day_of_week='mon-fri', hour=16, minute=5)
def post_close_data_refresh(): ...

@sched.scheduled_job('cron', day_of_week='mon-fri', hour=16, minute=15)
def eod_scan_and_signal(): ...

@sched.scheduled_job('cron', day_of_week='mon-fri', hour=16, minute=30)
def eod_notify(): ...

@sched.scheduled_job('cron', day_of_week='sat', hour=8, minute=0)
def weekly_tear_sheet(): ...
```

Use `pandas_market_calendars.get_calendar('XNYS')` to skip holidays and handle early
closes (the 1pm close days around Thanksgiving / Christmas / Independence Day eve). Wrap
every scheduled job with:

```python
def market_aware(job):
    @wraps(job)
    def wrapper(*a, **kw):
        cal = mcal.get_calendar('XNYS')
        today = pd.Timestamp.now(tz='America/New_York').normalize()
        sched_df = cal.schedule(start_date=today, end_date=today)
        if sched_df.empty:
            log.info("market closed today, skipping", job=job.__name__)
            return
        return job(*a, **kw)
    return wrapper
```

### 10.4 Observability

- **Logs** → JSON via `structlog` → `./logs/engine.log`. Optionally ship to Better Stack or
  Loki Cloud's free tier.
- **Metrics** → Prometheus textfile exporter writing `./metrics/*.prom`, scraped by a free
  Grafana Cloud instance. Track: bars_ingested_total, signals_emitted_total,
  orders_submitted_total, broker_errors_total, scheduler_job_duration_seconds,
  data_staleness_seconds.
- **Errors** → Sentry free tier; catches the unhandled exceptions you'll miss in logs.

### 10.5 Backups

- `state/ops.sqlite` → **Litestream → S3/B2** continuous replication. ~$0.50/mo for the
  storage.
- `data/` is rebuildable from vendor; just snapshot the universe + corporate actions
  weekly.
- Config + code → git, pushed to GitHub.

### 10.6 Cost summary (per month)

| Item | Cost |
|---|---|
| VPS (Hetzner CX22) | $6 |
| Tiingo Starter | $10 |
| Backups storage (B2) | $0.50 |
| Telegram bot | $0 |
| Discord webhook | $0 |
| Email (Resend free tier) | $0 |
| Sentry free tier | $0 |
| Tailscale free tier | $0 |
| Grafana Cloud free tier | $0 |
| **Total** | **~$16.50/mo** |

Well inside the $50 budget. Headroom for:

- Norgate $30/mo when you want survivorship-bias-free backtest history. Total $46.50.
- Or Databento pay-as-you-go (~$5–20/mo at swing-only volume).
- Or Alpaca Algo Trader Plus ($99/mo) if/when you need full SIP — that breaks the budget;
  upgrade only when AUM justifies.

---

## 11. Final recommended stack (decision matrix)

> **Target profile.** Solo retail swing trader. EOD signals (mostly daily, optional 1h
> confirm). Universe: S&P 1500 + Russell 2000 (~2,500 names). Holding period 2–20 days.
> Single VPS. Sub-$50/mo total. Paper-first; live only after 90+ days of clean forward paper
> performance with manual confirm.

### 11.1 The stack

| Layer | Pick | Why | Alternatives I'd swap in |
|---|---|---|---|
| **Primary data (EOD prices)** | **Tiingo Starter ($10/mo)** | Cleanest cheap EOD, 30y history, fundamentals, generous rate limits | EODHD ($20) if you want international + bulk-download endpoint |
| **Secondary data (cross-check + free realtime snap)** | **Alpaca Free** | Same vendor as exec, free IEX snapshots, decent 7y bars | Polygon if you ever pay $199 |
| **Survivorship-free history (research only)** | **Norgate Platinum ($30/mo, optional)** | The only retail-priced honest-backtest data | Databento US Equities Summary on-demand |
| **Free fallback / DR feed** | **yfinance** | $0, works for any ticker, brittle but ubiquitous | Twelve Data free (800/day) |
| **Earnings / catalysts overlay** | **Finnhub Free** | Earnings calendar + insiders for $0 | NASDAQ Data Link |
| **Broker (paper)** | **Alpaca Paper** | Best paper-trading API in the industry | Tradier Sandbox |
| **Broker (live, when ready)** | **Alpaca Live** | Same code path as paper, $0 commission | Tradier (if options too); IBKR (if shorting / pro features) |
| **Indicators** | **pandas-ta-classic** + **TA-Lib** for candle patterns | Easiest install, full coverage | vectorbt's built-ins (when in research) |
| **Backtest / research** | **vectorbt** (free) | 100× faster cross-sectional scans than event-driven; same `compute(df)` reusable live | vectorbtpro ($400/y); nautilus_trader when you outgrow |
| **Live engine** | **Plain Python + APScheduler** | Minimal moving parts, easy to reason about, tz-aware | nautilus_trader for production scale |
| **Storage — OHLCV history** | **Parquet (hive-partitioned) + DuckDB** views | Fastest analytic reads, regeneratable, S3-friendly | TimescaleDB only if you commit to Postgres |
| **Storage — operational state** | **SQLite + Litestream replication to B2** | Zero ops, ACID, continuous off-site backup | Postgres when you go multi-process |
| **Calendar** | **pandas_market_calendars** | Industry standard, XNYS + 50+ others | `holidays` + custom if you want minimal deps |
| **Dashboard** | **Streamlit** (single file) → upgrade to **FastAPI + Next.js** when sharing | Cheapest path to a real UI | NiceGUI / Dash |
| **Notifications** | **Telegram bot** (primary, inline buttons) + **Discord webhook** + **Resend** email | Free, mobile, interactive | Slack if you already live there |
| **Logs** | **structlog → file → Better Stack free** | Searchable, structured | Loki self-host |
| **Errors** | **Sentry free tier** | Catches what logs miss | GlitchTip self-host |
| **Metrics** | **Prometheus textfile → Grafana Cloud free** | Drawdown / staleness graphs | Plain SQLite + Streamlit charts |
| **Deploy** | **Docker Compose** on **Hetzner CX22 ($6/mo)** | Cheap, EU/US, reliable | DigitalOcean Basic; Fly.io |
| **Access** | **Tailscale** (free) | No exposed ports | Cloudflare Access |
| **Secrets** | `.env.${ENV}` + **age**-encrypted at rest in git | Simple, auditable | Doppler / 1Password CLI |
| **CI** | **GitHub Actions** (free for private repos at this scale) | Build, lint, test, push image | Drone self-host |

### 11.2 What you DO NOT need at this scale

- ❌ Polygon $199/mo — overkill for EOD; revisit at AUM > $100k.
- ❌ Postgres — SQLite + DuckDB beats it for this volume.
- ❌ Celery / Airflow / Prefect — APScheduler is enough.
- ❌ Redis — you don't have multi-process IPC needs yet.
- ❌ Kubernetes — Docker Compose is correct.
- ❌ A complex feature store / MLOps stack — your "features" are a few hundred indicator
  columns in Parquet.

### 11.3 90-day rollout plan

| Week | Milestone |
|---|---|
| 1 | Repo scaffolding, `DataAdapter` (Tiingo + yfinance + Alpaca), DuckDB/Parquet store, backfill 10 years for S&P 500 |
| 2 | Indicator engine with cache, vectorbt research notebook, first strategy `compute(df)` function |
| 3 | `BrokerAdapter` (Alpaca paper), idempotent submit, reconciliation, audit log |
| 4 | APScheduler, market-calendar wrapper, EOD scan + signal persistence |
| 5 | Telegram bot with inline confirm, Discord webhook, email digest |
| 6 | Streamlit dashboard, risk filter, kill switch, full Docker compose |
| 7 | Backtest the strategy honestly on Norgate / Databento; quantstats tear sheet |
| 8 | Forward paper for 4 weeks; nightly drift report; tune the strategy *without* refitting on the paper period |
| 9–12 | Continue forward paper; build a second strategy; only consider going live after 90 days of clean paper with positive expectancy *and* drift within tolerance |

### 11.4 The "go-live" checklist (read this before flipping `ENV=live`)

- [ ] 90+ days of forward paper with positive R-expectancy.
- [ ] Live-vs-backtest drift is ≤1σ negative.
- [ ] Kill switch tested (manual `/kill`, auto daily-loss, watchdog).
- [ ] All orders use `client_order_id` derived from `signal_id` + git SHA.
- [ ] Reconciliation runs at every scheduled tick and alerts on drift.
- [ ] `require_human_confirm: true` is the live default for the first 30 days.
- [ ] Litestream is replicating ops.sqlite to B2 and you've test-restored.
- [ ] Sentry is wired and you've intentionally raised a test error.
- [ ] Tailscale-only access to the dashboard.
- [ ] You have a written one-page playbook for "engine misbehaves at 9:45 AM" — who you
      call (yourself), how you halt (`/kill`), how you flatten (broker app directly), how
      you preserve evidence (`logs/`, `state/`).

If any box is unchecked, stay on paper.

---

## 12. Appendix

### 12.1 Env vars (canonical list)

```env
# environment
ENV=paper                                 # paper | live
TZ=America/New_York

# data
DATA_PRIMARY=tiingo                       # tiingo | eodhd | alpaca | yfinance
TIINGO_API_KEY=...
ALPACA_DATA_KEY=...
ALPACA_DATA_SECRET=...
DATA_CACHE_DIR=/app/data

# broker
BROKER=alpaca
ALPACA_KEY=...
ALPACA_SECRET=...
ALPACA_BASE_URL=https://paper-api.alpaca.markets   # paper or live URL
LIVE_TRADING_GUARD=disabled               # disabled | enabled (must match ENV)

# risk
MAX_POSITIONS=10
MAX_PER_POSITION_PCT=0.15
MAX_GROSS_EXPOSURE_PCT=1.00
MAX_RISK_PER_TRADE_PCT=0.0075
MAX_TOTAL_RISK_OPEN_PCT=0.04
MAX_ORDERS_PER_DAY=20
HALT_ON_DAILY_LOSS_PCT=0.02
HALT_ON_DD_FROM_HWM_PCT=0.10
REQUIRE_HUMAN_CONFIRM=true

# notifications
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
DISCORD_WEBHOOK_URL=...
RESEND_API_KEY=...
ALERT_EMAIL=you@example.com

# observability
SENTRY_DSN=...
LOG_LEVEL=INFO

# backup
B2_BUCKET=swing-radar-state
B2_KEY_ID=...
B2_APP_KEY=...
```

### 12.2 Smoke tests (run after every deploy)

```bash
# 1. Calendars
python -m engine.smoketest calendar           # asserts today's open/close == NYSE

# 2. Data adapters
python -m engine.smoketest data --symbol AAPL # both primary + secondary return same close

# 3. Indicators
python -m engine.smoketest indicators         # known fixture matches expected RSI/SMA values

# 4. Broker
python -m engine.smoketest broker             # places + cancels a $1 limit on a thin name (paper only)

# 5. Notifications
python -m engine.smoketest notify             # sends "smoketest ok" to all channels

# 6. Kill switch
python -m engine.smoketest kill               # creates KILL file, asserts broker refuses, removes
```

### 12.3 Reading list (vetted)

- **Alpaca docs:** https://docs.alpaca.markets/ — trading + market-data APIs are exemplary.
- **vectorbt docs:** https://vectorbt.dev/ — the patterns chapter is gold.
- **nautilus_trader docs:** https://nautilustrader.io/docs/ — when you outgrow homebrew.
- **ib_async (the maintained IBKR fork):** https://github.com/ib-api-reloaded/ib_async
- **pandas_market_calendars docs:** https://pandas-market-calendars.readthedocs.io/
- **QuantStart**: foundational articles on PIT data, survivorship, and event-driven design.
- **Robot Wealth**: pragmatic systems-trading content with code.
- **Ernie Chan, "Algorithmic Trading"**: classic, light on infra but heavy on bias awareness.
- **Marcos Lopez de Prado, "Advances in Financial Machine Learning"**: when you're ready to
  ML-rank signals.
- **Databento docs:** https://databento.com/docs/ — even if you don't pay them, the schema
  docs teach you institutional thinking.
- **DuckDB time-series patterns blog series**: how to structure Parquet hive partitions for
  fast analytic scans.

---

*End of 06-implementation-stack.md.*
