# Swing Trade Radar

NASDAQ-100 big-tech swing trade signal engine + dashboard + backtesting.

**Status:** Architecture phase. See [ARCHITECTURE.md](./ARCHITECTURE.md).

> ⚠️ Educational only. Not financial advice. Paper-trade everything.

## Stack

- **Backend:** Python 3.12 + FastAPI + APScheduler + SQLite + yfinance + pandas-ta
- **Frontend:** Next.js 16 + TypeScript + Tailwind v4 + Biome
- **Indicators:** 6 swing strategies (MA cross, RSI mean reversion, Bollinger squeeze, MACD+trend, S/R breakout, volume trend)
- **Risk classification:** 🟢 LOW / 🟡 MEDIUM / 🔴 HIGH per signal
- **Backtesting:** walk-forward, R-multiple metrics

## Quick start

_Coming in Phase 2._

```bash
# backend
cd backend && uv venv && uv sync && uv run python -m swing_trader.main

# frontend
cd frontend && pnpm i && pnpm dev
```

## License

MIT
