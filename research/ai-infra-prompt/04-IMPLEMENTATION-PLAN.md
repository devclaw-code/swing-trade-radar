# 04 — Implementation Plan: AI-Infra Prompt → Code

Tracker for executing the punch list from `02-CODE-AUDIT.md` and data plumbing from `03-MACRO-AND-UNIVERSE.md`.

Order of execution agreed with Aditya 2026-06-02: **(a) plan → (c) data plumbing → (b) macro-event gate**.

## Workstreams

### W1 — Calendar data plumbing (this sprint, in progress)
Foundation. Nothing else can land until this exists.

- [x] W1.1 Add `FRED_API_KEY`, `FINNHUB_API_KEY` to `config.Settings` (no-op if unset)
- [x] W1.2 Add `Event` SQLAlchemy model + migration (`kind`, `symbol`, `release`, `scheduled_at`, `confirmed`, `source`, `fetched_at`)
- [x] W1.3 `data/macro_calendar.py` — FRED `releases/dates` + FOMC ICS hybrid; pure-fn `fetch_next_14d() -> list[EventRow]`
- [x] W1.4 `data/earnings_calendar.py` — Finnhub primary, AlphaVantage `EARNINGS_CALENDAR` middle fallback, yfinance per-ticker last resort. Function: `fetch_earnings_next_14d(tickers) -> list[EventRow]`
- [x] W1.5 `engine/blackout.py` — `is_blackout(ticker, side, now) -> str | None`. Pure read against `events` table; no external IO
- [x] W1.6 Scheduler: new daily `refresh_calendars` job at 06:00 UTC; idempotent upsert
- [x] W1.7 Add `httpx` retry helper + `icalendar` dep
- [x] W1.8 Tests: macro fixture, earnings fixture, blackout window edge cases (T-48h±1m), fail-open path
- [ ] W1.9 README env-var docs + `.env.example`

### W2 — Macro-event gate (after W1)
The synthesizer rule that consumes W1.

- [ ] W2.1 `Verdict` schema: `pre_earnings_exit_by: date | None`, `macro_blackout: MacroBlock | None`
- [ ] W2.2 `engine/verdict.synthesize_verdict` — call `is_blackout`; demote BUY → WATCH if macro within 48h; clamp `max_hold_days` if earnings within hold window
- [ ] W2.3 `WhyBlock.what_could_invalidate` — append macro/earnings exit reason
- [ ] W2.4 Tests: BUY suppression on CPI-eve, WATCH demotion, hold-clamp on earnings T-3, fail-open when calendar stale

### W3 — Risk geometry hardening (independent, ship anytime)
Code-audit punch list section A — see `02-CODE-AUDIT.md` §6A.

- [ ] W3.1 `engine/risk_levels.py` (`atr_stop`, `min_rr_target`, `PCT_FALLBACK`)
- [ ] W3.2 Replace inline ATR-stops in v2 strategies (S1, S2, S3)
- [ ] W3.3 Wrap structure stops with ATR floor in S4, sr_breakout, macd_trend, volume_trend
- [ ] W3.4 Hard `verdict_min_rr=2.5` discard in `_verdict_kind`
- [ ] W3.5 Tests incl. AAOI-class high-vol fixture

### W4 — RSI(14) > 75 / StochRSI overbought reject
- [ ] W4.1 Add StochRSI to `indicators.enrich()`
- [ ] W4.2 Synthesizer guard: BUY→WATCH if `rsi14 > 75` or `stochrsi_k pinned ≥ 99 (3-bar)`

### W5 — Negative-beta hedge surfacing
Audit §6B. Depends on hedge-basket empirical verification first.

- [ ] W5.1 Verification script: 3y rolling-corr-to-QQQ for {DG, KR, GLD, SHV, CME, FXY, XLP, SIXU}; ship rule = full-sample ρ ≤ 0.20 AND p25(60d ρ) < 0
- [ ] W5.2 `RegimeContext.qqq_rsi14`, `hedge_recommended`
- [ ] W5.3 `engine/hedge.py` selector
- [ ] W5.4 Surface `hedge_candidate` on run-summary when `qqq_rsi14 > 70 and qqq_above_200sma`
- [ ] W5.5 Frontend ticket (separate)

### W6 — AI-infra capex sector tag (overlay)
After W2/W3. Dossier reference: research/05 §17.2 (Oct–Nov capex window).

- [ ] W6.1 `config/sector_tags.yaml` with capex-chain tickers within current NDX-100 basket (NVDA, AVGO, AMD, MU, intel-equip names that are in basket)
- [ ] W6.2 Detect Oct–Nov capex window; add small conviction multiplier to verdicts whose ticker carries the tag
- [ ] W6.3 A/B backtest with multiplier on/off; require ΔSharpe 95% CI ≥ 0 and t-stat > 2.0

### W7 — Backtest validation
- [ ] W7.1 Walk-forward (6mo train / 1mo test) 2014–2024 on locked basket
- [ ] W7.2 Deflated-Sharpe ≥ 1.0 maintained vs current S1–S5 baseline
- [ ] W7.3 ΔMaxDD must not regress
- [ ] W7.4 Report at `research/ai-infra-prompt/05-BACKTEST-RESULTS.md`

## Out of scope (parked)

- ❌ Adding small-caps (AXTI, AEHR, AAOI) to the universe — separate Phase-3 conversation; sizing model assumes mega-cap liquidity.
- ❌ Ascending Triangle / Bull Flag pattern recognition — heuristic-heavy, not worth the multiple-testing budget today.
- ❌ "Positions to flatten today" view — needs a positions table that doesn't exist; PEAD doesn't justify it alone.

## Risk / no-regret check

- W1 is purely additive, no behavior change until W2 reads `events`. Safe.
- W3 changes stop geometry on existing strategies — needs the test bundle before merge.
- W6 multiplier is gated on its own A/B test; default off until DSR validates it.
- All work behind feature flags where reasonable so we can roll forward without re-deploying.
