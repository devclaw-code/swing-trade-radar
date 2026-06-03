# Swing Trade Radar

NASDAQ-100 mega-cap tech **swing-trade research desk** — daily signal suggestions with detailed reasoning.

**Status:** Phase 2 in progress. See [PHASE2_PLAN.md](./PHASE2_PLAN.md) and [research/00-INDEX.md](./research/00-INDEX.md).

> ⚠️ **Educational only. Not financial advice.**
> **This project does NOT execute trades.** It does not connect to any broker, place orders, or
> manage real or paper money. It is a read-only research tool that publishes daily verdicts and
> the reasoning behind them. Any decision to act on a suggestion is yours alone.

## What it does

Each trading day, after the US close, the engine scans the NDX-100 mega-cap basket and produces
a **verdict per ticker**: `BUY`, `WATCH`, `AVOID`, or `NO_SETUP`. Every verdict comes with:

- The primary setup that fired (e.g. "Connors RSI(2) Mean Reversion")
- Suggested entry / stop / target / R:R / max hold (informational only — not orders)
- Position-size *hint* for a hypothetical $25k account at 1% risk
- A structured **why** block: weighted evidence, what would invalidate the setup, counter-arguments, doc references
- A historical base rate: *"on this ticker, this exact setup has occurred N times over 10 years; win rate X%; avg R = Y"*
- Current market regime context (SPY/QQQ above 200-SMA, VIX, term structure)

The user reads, decides, and (if they want) places trades themselves elsewhere. The site never touches their money.

**Two horizons.** Alongside the long-term **Core Swing** verdicts (~30-day trend holds), a
**Tactical Swings** book scans for short-term **1–5 day** setups — *3-Day RSI Exhaustion* and
*Inside Day Breakout* (regime-gated on `Price > 200 SMA`). Risk levels use a **dynamic ATR model**
(`stop = entry − 1.5×ATR(14)`, targets at min **2.0 R:R**). Toggle Core / Tactical in the dashboard
header; the API exposes tactical cards at `GET /api/tactical`.

## What it does NOT do

- ❌ Connect to brokers, exchanges, or trading APIs
- ❌ Place, modify, or cancel orders — paper or live
- ❌ Track a real or simulated portfolio / PnL
- ❌ Recommend leverage, options, or short selling (Phase 3+)
- ❌ Provide intraday signals (EOD only, runs once per trading day)
- ❌ Use ML/LLM-based predictions (Phase 3+, only after rule-based has 6mo track record)

## Stack

- **Backend:** Python 3.12 + FastAPI + APScheduler + SQLite + yfinance + pandas-ta
- **Frontend:** Next.js 16 + TypeScript strict + Tailwind v4 + shadcn/ui + Biome
- **Strategies (5 locked, from research shortlist):**
  - S1 — 50/200 SMA + regime filter (trend)
  - S2 — Clenow time-series momentum
  - S3 — Connors RSI(2) mean reversion (regime-gated)
  - S4 — Minervini VCP scorer (volatility contraction breakout)
  - S5 — PEAD (post-earnings drift)
- **Risk profile per verdict:** 🟢 LOW / 🟡 MEDIUM / 🔴 HIGH
- **Backtesting:** walk-forward + deflated Sharpe (Bailey & Lopez de Prado) — strategies must clear DSR ≥ 1.0 before going live

See [research/00-INDEX.md](./research/00-INDEX.md) for the underlying research dossier (~10,500 lines across 8 docs).

## Quick start

```bash
# backend
cd backend && uv venv && uv sync && uv run python -m swing_trader.main

# frontend
cd frontend && pnpm i && pnpm dev
```

## Run with Docker

```bash
docker compose up --build
# frontend: http://localhost:8080
# backend:  http://localhost:8000
```

The backend SQLite DB persists to `./backend/var/` on the host.

## Configuration

Copy `backend/.env.example` to `backend/.env` and fill in keys as needed. **All keys are optional** — the app runs without them and degrades gracefully (calendars fail-open, yfinance fallbacks for prices/earnings).

| Env var | Purpose | Free key |
|---|---|---|
| `ALPHA_VANTAGE_API_KEY` | Price + earnings-calendar fallback | [get](https://www.alphavantage.co/support/#api-key) |
| `FRED_API_KEY` | Macro release dates (CPI, NFP, FOMC) | [get](https://fredaccount.stlouisfed.org/apikeys) |
| `FINNHUB_API_KEY` | Primary earnings calendar (60 req/min free) | [get](https://finnhub.io/register) |

Calendar/scheduler knobs (`MACRO_BLACKOUT_HOURS`, `EARNINGS_EXIT_HOURS`, `CALENDAR_REFRESH_HOUR_UTC`, etc.) have sane defaults — see `backend/.env.example` for the full list. The `refresh_calendars` job runs daily at 06:00 UTC; the price refresh runs once per trading day after the US close.

## Disclaimer

This is an educational research project. Verdicts are **suggestions for study**, not investment advice.
The authors take no responsibility for trading decisions made on the basis of this tool's output.
Past base rates do not predict future performance. **Do your own research.**

## License

MIT
