# Swing Trade Radar — Architecture

**Status:** Phase 1 design (superseded by [PHASE2_PLAN.md](./PHASE2_PLAN.md) for v2). Not fully implemented yet.
**Scope:** NASDAQ-100 big tech (20 tickers) swing-trade **signal advisor** + dashboard + backtesting. **Read-only — does not execute trades.**
**Disclaimer:** Educational project. Not financial advice. **The system does NOT connect to brokers, place orders, or manage any real or simulated portfolio.** Verdicts are suggestions for study; any trading decision is the user's own.

---

## 1. System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                          External Sources                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐    │
│  │   yfinance   │  │ Alpha Vantage│  │  RSS Feeds (news)        │    │
│  │  (OHLCV)     │  │  (fallback)  │  │  Yahoo / CNBC / MW       │    │
│  └──────┬───────┘  └──────┬───────┘  └────────────┬─────────────┘    │
└─────────┼─────────────────┼──────────────────────┼──────────────────┘
          │                 │                      │
          ▼                 ▼                      ▼
┌──────────────────────────────────────────────────────────────────────┐
│                  Backend (Python 3.12 + FastAPI)                     │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │            APScheduler (every 3h)                            │    │
│  └──────────────┬───────────────────────────────────────────────┘    │
│                 ▼                                                    │
│  ┌──────────────────────┐  ┌──────────────────────┐                  │
│  │  data/price_fetcher  │  │  data/news_scraper   │                  │
│  └──────────┬───────────┘  └──────────┬───────────┘                  │
│             │                         │                              │
│             ▼                         ▼                              │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │     SQLite (prices, news, signals, runs, backtests)          │    │
│  └──────────┬───────────────────────────────────────────────────┘    │
│             │                                                        │
│             ▼                                                        │
│  ┌──────────────────────┐  ┌──────────────────────┐                  │
│  │ engine/indicators    │  │ engine/backtester    │                  │
│  └──────────┬───────────┘  └──────────┬───────────┘                  │
│             ▼                         │                              │
│  ┌──────────────────────────────┐     │                              │
│  │  strategies/* (6 modules)    │     │                              │
│  └──────────┬───────────────────┘     │                              │
│             ▼                         ▼                              │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │   engine/signal_generator → engine/risk_classifier           │    │
│  └──────────┬───────────────────────────────────────────────────┘    │
│             ▼                                                        │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │   FastAPI REST + WebSocket (version pings)                   │    │
│  └──────────┬───────────────────────────────────────────────────┘    │
└─────────────┼────────────────────────────────────────────────────────┘
              │ JSON
              ▼
┌──────────────────────────────────────────────────────────────────────┐
│              Frontend (Next.js 16 App Router + TS)                   │
│                                                                      │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │ Header /    │ │ Filter Bar   │ │ Trade Cards  │ │ News Panel   │  │
│  │ Market Bar  │ │              │ │ Grid + Spark │ │              │  │
│  └─────────────┘ └──────────────┘ └──────────────┘ └──────────────┘  │
│                                                                      │
│  Polls /api/last-updated every 60s → invalidates SWR cache           │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Backend | **Python 3.12 + FastAPI** | Async, automatic OpenAPI, perfect for `pandas-ta`/`yfinance` ecosystem. |
| ORM / DB | **SQLAlchemy 2.0 + SQLite (WAL)** | Zero ops locally. Trivially swap to Postgres via DSN env var. |
| Scheduler | **APScheduler 3.x (BackgroundScheduler)** | In-process, no Redis/Celery needed for a single 3h job. |
| Price data | **yfinance** primary, **Alpha Vantage** fallback | yfinance is free + no key. AV used when yfinance ratelimits (Azure IPs sometimes blocked). |
| News | **feedparser** over RSS | No keys, simple. Reuters' public RSS is dead — using Yahoo Finance per-ticker RSS + CNBC + MarketWatch + Yahoo Finance Top Stories. |
| Indicators | **pandas-ta** | Pure Python, no TA-Lib C build. |
| Frontend | **Next.js 16 (App Router) + TS strict + Tailwind v4 + shadcn/ui** | Already the project default. App Router for server components on data fetching. |
| Data fetching (FE) | **SWR** | Built-in revalidation, fits the 60s poll pattern cleanly. |
| Charts | **Lightweight SVG sparklines (inline)** for cards; **lightweight-charts** by TradingView for detail view (later). |
| Linter | **Biome** (FE) + **ruff** (BE) | One tool per side. |
| Tests | **pytest** (BE) + **vitest** (FE) | Strategy logic + risk classifier well covered. |
| Container | **Dockerfile + docker-compose** | One `docker compose up` for the whole stack. |

**Trade-offs:**
- Monorepo (backend + frontend in one repo) → easier ops, single PR for cross-cutting changes.
- SQLite for dev → Postgres path: change DSN, run alembic migrations.
- No Celery/Redis → if we ever need >1 scheduled job class or horizontal scale, swap APScheduler for Celery Beat.

---

## 3. Data Pipeline

### 3.1 Price fetcher (`data/price_fetcher.py`)
1. For each ticker in `config.TICKERS`:
   - Query DB for latest `date` of cached OHLCV.
   - If stale or missing → fetch incremental window via yfinance (`period="6mo"` on first run, `period="5d"` on warm runs).
   - On yfinance error (HTTP 429 / empty df) → retry with Alpha Vantage TIME_SERIES_DAILY.
   - Upsert into `prices` table.
2. Always keep at least **250 trading days** per ticker (200 SMA + buffer).

### 3.2 News scraper (`data/news_scraper.py`)
1. Pull RSS from configured feeds (parallel via `httpx.AsyncClient`).
2. For each entry: parse title, summary, link, pubdate.
3. **Ticker tagging:** simple regex on `(title + summary)` against ticker symbols + company alias map (e.g. `Tesla|TSLA`, `Apple|AAPL`).
4. **Optional sentiment:** VADER (lexicon-based, no model download) — tags each headline `pos/neu/neg` with score. Lightweight, ~no perf cost.
5. Dedupe by URL hash. Upsert into `news` table with TTL of 7 days.

### 3.3 Indicator engine (`engine/indicators.py`)
Wraps pandas-ta with a single `compute(df) -> df` that adds columns:
- `ema9`, `ema21`, `sma50`, `sma200`
- `rsi14`
- `bb_upper`, `bb_mid`, `bb_lower`, `bb_bandwidth`
- `macd`, `macd_signal`, `macd_hist`
- `atr14`
- `vol_sma20`
- `pivot_high_20`, `pivot_low_20`

### 3.4 Strategy engine (`strategies/*.py`)
Each strategy implements `BaseStrategy`:
```python
class BaseStrategy(ABC):
    name: str
    @abstractmethod
    def generate(self, df: pd.DataFrame, ticker: str) -> list[Signal]: ...
```
Returns zero or more `Signal` dataclasses:
```python
@dataclass
class Signal:
    ticker: str
    strategy: str
    direction: Literal["LONG","SHORT"]
    entry: float
    target: float
    stop: float
    confirmations: list[str]   # human-readable
    confidence: float          # 0..1
    generated_at: datetime
    bar_date: date             # the bar this signal fired on
```

### 3.5 Signal generator (`engine/signal_generator.py`)
1. Loops all tickers × all 6 strategies.
2. Dedupe rule: if same `(ticker, direction)` fires on multiple strategies same day → keep the one with **highest confidence**, but merge `confirmations` list (boosts risk score below).
3. Persist to `signals` table; mark prior open signals for same `(ticker, strategy)` as `superseded`.

### 3.6 Risk classifier (`engine/risk_classifier.py`)
Score every signal:

| Metric | Source |
|---|---|
| `n_confirmations` | length of merged confirmations |
| `stop_pct` | `abs(entry - stop) / entry` |
| `rr_ratio` | `abs(target - entry) / abs(entry - stop)` |

Classification (per the prompt):
- 🟢 **LOW**: `n ≥ 3` AND `stop_pct < 0.03` AND `rr ≥ 2.5`
- 🟡 **MEDIUM**: `n ≥ 2` AND `0.03 ≤ stop_pct ≤ 0.06` AND `1.5 ≤ rr < 2.5`
- 🔴 **HIGH**: otherwise

Confidence score (% shown in UI) = weighted blend:
```
0.4 * normalized(n_confirmations, 1..4)
+ 0.3 * normalized(rr_ratio, 1..4)
+ 0.3 * (1 - stop_pct/0.08).clamp(0,1)
```

---

## 4. Strategy Engine (exact specs)

All strategies operate on **daily bars**, latest closed bar = `t`.

| # | Name | Entry (LONG version) | Exit | Stop |
|---|---|---|---|---|
| 1 | **MA Crossover** | `ema9[t-1] ≤ ema21[t-1]` AND `ema9[t] > ema21[t]` → enter at next open | opposite cross, or 8–12 bar timeout | bar low or `ema21 - 1*ATR` |
| 2 | **RSI Mean Reversion** | `rsi[t] < 35` AND `close > sma50` | `rsi crosses 50` | `entry - 2*ATR` |
| 3 | **Bollinger Squeeze + Breakout** | `bb_bandwidth[t-1] < sma20(bb_bandwidth)` AND `close[t] > bb_upper[t]` | `close ≤ bb_mid` | `bb_mid` |
| 4 | **MACD + Trend Filter** | `macd crosses signal up` AND `close > sma200` | `macd crosses signal down` or 10-day timeout | last 10-bar swing low |
| 5 | **S/R Breakout** | `close > rolling_max(high, 20)[t-1]` AND `volume > 1.5 * vol_sma20` | next pivot high (resistance) | `breakout_level * 0.99` |
| 6 | **Volume Trend Continuation** | `close > sma50 > sma200` AND pullback to within 1% of `ema20` on declining volume AND next bar bounce on `volume > vol_sma20` | `entry + 1.5*(entry-stop)` | pullback low |

SHORT variants are symmetric (swap conditions).

**Target rule (default):** if strategy doesn't define one explicitly, use `entry + 2 * (entry - stop)` for a 2R target.

---

## 4a. Tactical Swings module (1–5 day holds)

A second, short-term screener book that runs **alongside** the Core (30-day)
verdicts. Every verdict/card carries a `time_horizon` field (`"Core"` |
`"Tactical"`) plus a `volatility_atr` (latest daily ATR(14)) for
volatility-adjusted sizing and UI display.

**Code layout**
- `engine/atr.py` — standalone Wilder ATR(14) (`compute_atr14`), NaN/short-history safe.
- `engine/risk_levels.py::dynamic_atr_trade()` — the **Dynamic ATR Risk** model:
  `stop = entry - 1.5*ATR`, `take_profit` priced to **min 2.0 R:R** (replaces the
  old static 2.50 target). Degrades to a percent stop when ATR is missing.
- `strategies/tactical/` — `TacticalStrategy` base + one file per setup. Adding a
  new setup = one file + one line in `engine/tactical_engine.py`.
- `engine/tactical_engine.py` — universe scanner (`generate_tactical`), serves `/api/tactical`.

**Shared regime gate (all tactical setups):** `Price > SMA(200)`.

| ID | Setup | Entry | Stop | Exit / invalidation |
|---|---|---|---|---|
| `T1_rsi_exhaustion` | **3-Day RSI Exhaustion** | 3 consecutive lower closes AND `RSI(4) < 30` → market entry at close | `entry - 1.5*ATR` (dynamic) | first profitable close, or `RSI(4) > 55`; hard stop; max 5 days |
| `T2_inside_day_breakout` | **Inside Day Breakout** | inside day (`H<prevH` & `L>prevL`) AND `EMA(10)` rising → **buy-stop** at `inside_high + $0.10` | `inside_low - $0.05` (structural, ATR-floored at 1.5×ATR) | min 2.0 R:R target; no-fill if stop never tagged; max 5 days |

RSI(4) and EMA(10) are computed on-the-fly inside each setup (not part of the
shared `enrich()` pass). All setups wrap evaluation in `try/except` and return a
clean *not-fired* result on NaN/short-history/malformed bars.

**Expected hold (data-backed).** `max_hold_days` (5) is only the *timeout cap*.
`engine/tactical_holds.py` replays each setup's **exact** entry/exit rules across
~5y of history for the whole universe and reports the **median** realised hold
(`expected_hold_days`), cached 6h. Empirically: T1 ≈ **1 day** (mean-reversion
snaps back fast), T2 ≈ **2 days**. Cards surface both: `expected_hold` ("~1 days")
and `max_hold` ("≤ 5 trading days").

---

## 5. Backtesting

### 5.1 Engine (`engine/backtester.py`)
- Walk-forward, daily bars only.
- For each `(ticker, strategy)`: iterate bars, simulate signal → entry-at-next-open → exit on stop/target/timeout.
- Position sizing: **1 unit per signal**, no compounding (returns expressed in R-multiples to keep apples-to-apples).
- Slippage: 5 bps each side. Commission: 0 (Robinhood-style).
- Track per-trade: `entry_date, exit_date, exit_reason, return_R, return_pct, max_adverse_excursion, max_favorable_excursion`.

### 5.2 Metrics (per strategy per ticker, also aggregated)
- Total trades
- Win rate (%)
- Average R
- Profit factor (sum wins / |sum losses|)
- Max drawdown (in R)
- Sharpe (annualized, daily returns)
- Avg holding bars

### 5.3 Schedule
- Full backtest run: **manual** via `/api/backtest/run` (heavy) or CLI.
- Lookback: 2 years default, configurable.
- Results cached in `backtests` table; UI shows latest per strategy.

---

## 6. Scheduler

`scheduler.py`:
```python
scheduler.add_job(refresh_pipeline, IntervalTrigger(hours=3), id="refresh", max_instances=1, coalesce=True)
scheduler.add_job(refresh_pipeline, DateTrigger(run_date=now+5s), id="boot_refresh")  # first-run kick
```

`refresh_pipeline()`:
1. `fetch_prices()` — parallel via thread pool.
2. `scrape_news()` — parallel via asyncio.
3. `generate_signals()` — sequential per ticker, parallel across tickers (CPU-bound but light).
4. `classify_risk()`.
5. Insert row in `runs` table with `started_at`, `finished_at`, `n_signals`, `errors`.
6. Bump `version` in `meta` table (frontend polls this).

**Failure handling:** any stage failure logs the error, increments `runs.errors`, but the pipeline continues. Frontend banner shows "Last update had N errors — showing potentially stale data" if `errors > 0`.

---

## 7. Frontend Architecture

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx                # dark theme, header, footer disclaimer
│   │   ├── page.tsx                  # dashboard
│   │   └── api/                      # (none — talks directly to FastAPI)
│   ├── components/
│   │   ├── header/
│   │   │   ├── MarketBar.tsx         # S&P, NDX, VIX
│   │   │   └── LastUpdated.tsx       # countdown to next refresh
│   │   ├── filters/
│   │   │   └── FilterBar.tsx         # risk/strategy/direction/sort
│   │   ├── cards/
│   │   │   ├── TradeCard.tsx
│   │   │   ├── RiskBadge.tsx
│   │   │   └── Sparkline.tsx         # inline SVG, 20-day closes
│   │   ├── news/
│   │   │   └── NewsPanel.tsx
│   │   └── ui/                       # shadcn primitives
│   ├── lib/
│   │   ├── api.ts                    # fetch wrappers, types from OpenAPI
│   │   └── types.ts
│   └── hooks/
│       ├── useSignals.ts             # SWR
│       ├── useNews.ts
│       └── useRefreshPolling.ts      # 60s poll on /api/last-updated → mutate keys on version bump
```

**Auto-refresh:** `useRefreshPolling` polls `/api/last-updated`, compares `version`. On change → `mutate("/api/strategies")` + toast.

**Backend URL:** `NEXT_PUBLIC_API_BASE` env var (defaults to `http://localhost:8000`).

---

## 8. REST API

All under `/api`. JSON only.

| Method | Path | Description |
|---|---|---|
| GET | `/strategies` | All open signals. Query: `risk`, `strategy`, `direction`, `sort`. |
| GET | `/strategies/{ticker}` | All signals for one ticker (open + last 30d closed). |
| GET | `/news` | Latest 50 headlines. Query: `ticker`. |
| GET | `/last-updated` | `{ version: int, ts: iso8601, errors: int }` |
| GET | `/market-summary` | `{ sp500, ndx, vix, ts }` (also from yfinance: `^GSPC`, `^NDX`, `^VIX`) |
| GET | `/backtest/{strategy}` | Cached backtest metrics per ticker + aggregate. |
| POST | `/backtest/run` | Trigger full backtest (background task). |
| GET | `/tactical` | **Tactical Swings (1–5 day) cards.** On-demand universe scan. Query: `setup` (e.g. `T1_rsi_exhaustion`). Each card has `time_horizon:"Tactical"` + `volatility_atr`. |
| GET | `/health` | Liveness. |

**Example response — `GET /strategies`:**
```json
{
  "version": 142,
  "generated_at": "2026-05-26T23:30:00Z",
  "signals": [
    {
      "id": "uuid",
      "ticker": "NVDA",
      "company": "NVIDIA Corporation",
      "strategy": "ma_crossover",
      "direction": "LONG",
      "entry": 142.55,
      "target": 152.10,
      "stop": 138.20,
      "stop_pct": 0.0305,
      "rr_ratio": 2.20,
      "risk": "MEDIUM",
      "confidence": 0.72,
      "confirmations": [
        "EMA9 crossed above EMA21",
        "Price > SMA50",
        "Volume +18% above 20d avg"
      ],
      "sparkline": [141.2, 140.9, 141.7, /* ...18 more */],
      "news": [
        { "title": "NVIDIA beats Q1...", "url": "...", "sentiment": "pos", "ts": "..." }
      ],
      "generated_at": "2026-05-26T23:30:00Z"
    }
  ]
}
```

---

## 9. Database Schema (SQLite)

```sql
prices(ticker, date, open, high, low, close, volume, PRIMARY KEY(ticker, date))
news(id, url_hash UNIQUE, title, summary, source, published_at, tickers JSON, sentiment, sentiment_score)
signals(id, ticker, strategy, direction, entry, target, stop, stop_pct, rr_ratio,
        risk, confidence, confirmations JSON, generated_at, bar_date, status)
        -- status: open | superseded | closed_target | closed_stop | closed_timeout
runs(id, started_at, finished_at, n_signals, errors, log_summary)
meta(key, value)  -- holds version counter
backtests(id, strategy, ticker, period_start, period_end, n_trades, win_rate,
          avg_r, profit_factor, max_dd_r, sharpe, avg_hold_bars, ran_at)
```

Indices on `signals(ticker, status)`, `prices(ticker, date desc)`, `news(published_at desc)`.

---

## 10. Repo Layout

```
swing-trade-radar/
├── backend/
│   ├── pyproject.toml
│   ├── README.md
│   ├── src/swing_trader/
│   │   ├── main.py
│   │   ├── scheduler.py
│   │   ├── config.py
│   │   ├── data/{db,price_fetcher,news_scraper}.py
│   │   ├── strategies/{base,ma_crossover,rsi_mean_reversion,bollinger_squeeze,macd_trend,sr_breakout,volume_trend}.py
│   │   ├── engine/{indicators,signal_generator,risk_classifier,backtester}.py
│   │   └── api/routes.py
│   └── tests/
├── frontend/                          # Next.js (reused starter template)
│   └── src/...
├── docker-compose.yml
├── ARCHITECTURE.md                    # this file
├── README.md                          # quick start
└── .github/workflows/ci.yml           # ruff + pytest + biome + tsc + next build
```

---

## 11. Risk Classification Schema (recap)

| Risk | Confirmations | Stop % | R/R | Visual |
|---|---|---|---|---|
| 🟢 LOW | ≥ 3 | < 3% | ≥ 2.5 | green |
| 🟡 MEDIUM | 2 | 3–6% | 1.5–2.5 | amber |
| 🔴 HIGH | 1 or any threshold breached | > 6% or any | < 1.5 or any | red |

All three conditions must hold for LOW. MEDIUM is the AND of its three. Anything else → HIGH (explicitly so signals don't get over-promoted).

---

## 12. Implementation Phasing

| Phase | Deliverable | ETA effort |
|---|---|---|
| 2a | Backend skeleton: config, db, price_fetcher, indicators, 1 strategy (MA crossover), API for `/strategies` | 1 |
| 2b | Remaining 5 strategies + signal_generator + risk_classifier | 1 |
| 2c | News scraper + tagging + sentiment | 0.5 |
| 2d | Scheduler + runs/meta + `/last-updated` | 0.5 |
| 2e | Backtester + `/backtest` endpoints | 1 |
| 2f | Frontend: layout, MarketBar, FilterBar, TradeCard, sparkline | 1 |
| 2g | Frontend: NewsPanel + polling + toasts | 0.5 |
| 2h | CI, Dockerfile, README, polish | 0.5 |

(Numbers are loose "dev sessions", not days.)

---

## 13. Open Questions Resolved

| Q | A |
|---|---|
| Stack | Hybrid: Python BE + Next.js FE ✅ |
| Repo | `devclaw-code/swing-trade-radar` (public) ✅ |
| Backtesting | Yes ✅ |
| Real trading? | Assumed no — paper-trading + disclaimer. Confirm if wrong. |
| Reuters RSS | Dead; swapped to Yahoo Finance per-ticker + CNBC + MarketWatch + Yahoo Finance Top. |
| yfinance reliability | Alpha Vantage as fallback; user supplies free API key in `.env`. |

---

## 14. Non-Goals (v1)

- Real broker integration (Alpaca, IBKR) — out of scope, intentionally.
- Live tick data — daily bars only.
- Options strategies.
- Portfolio/position tracking.
- User accounts / auth — single-user local app.
- Mobile-native — responsive web only.

These are good v2 candidates if it proves out.
