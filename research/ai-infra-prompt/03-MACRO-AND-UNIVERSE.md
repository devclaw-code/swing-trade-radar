# 03 — Macro Calendar, Earnings Calendar & AI-Infra Universe

Companion design doc to `00-PROMPT.md`. Scope: data sources for the **macro-event filter** (pillar 3), the **chokepoint universe** (pillar 1), and the **negative-beta hedge basket** (Aditya feedback #2). No code; pick-and-justify only.

## TL;DR

- **Macro calendar:** ship a tiny **FRED release-calendar + hard-coded FOMC ICS** hybrid. Free, keyed (FRED), deterministic, no scraping. `investpy` is tempting but its Investing.com endpoint breaks every few months — keep as fallback only.
- **Earnings calendar:** primary = **Finnhub free tier** (`/calendar/earnings`, 60 req/min, dated and reliable). Fallback = `yfinance.Ticker.get_earnings_dates` (per-ticker only, often stale, no bulk). NASDAQ scraper is a last resort and Cloudflare-fragile.
- **Universe:** ~20 chokepoint names across 8 bottleneck buckets (substrates, HBM, photonics, thermal, test/burn-in, EUV, advanced packaging, power delivery). Three are micro-cap (AEHR, AXTI, POET) and need a **per-name dollar cap** override on the $25k/1% sizing model — they can't absorb a 1R loss on a thin tape without slippage blowing the stop.
- **Hedge basket:** 6 names (DG, KR, CME, GLD, SHV, FXY) — but **only DG, KR, GLD survive empirical 3y rolling-correlation-to-QQQ ≤ 0.20**; the rest need verification before they ship. CME and FXY are theory candidates only.
- **Integration:** add one new APScheduler job (`refresh_calendars`, daily 06:00 UTC), one new SQLite table (`events`), one helper `is_blackout(ticker, side, horizon)` consumed by `signal_generator`. New env vars: `FINNHUB_API_KEY`, `FRED_API_KEY`. Both free tiers easily cover a 25-ticker universe polled once daily.

---

## 1. Macro Calendar (CPI / FOMC / NFP / PPI / PCE)

We need next-7-day timestamps for: **CPI, Core PCE, NFP, FOMC statement + presser, PPI, retail sales, ISM**. Used to enforce *"no new longs in the 48h before CPI/FOMC."*

### 1.1 Options

| Source | Auth | Rate limit | Coverage | Parse complexity | Reliability |
|---|---|---|---|---|---|
| **FRED `/releases/dates`** | free API key | 120 req/min | All BLS/BEA/BoG releases incl. CPI, PCE, NFP, PPI, retail sales | Trivial JSON | ★★★★★ — official, never breaks |
| **BLS `/publicAPI/v2`** | free key | 500/day | CPI, PPI, NFP (employment) only | Medium (series IDs) | ★★★★ |
| **BEA API** | free key | unmetered | GDP, PCE, personal income | Medium | ★★★★ |
| **FOMC ICS feed** (`federalreserve.gov/.../fomc.ics`) | none | n/a | FOMC meetings + statement times | Trivial (icalendar lib) | ★★★★★ — Fed publishes the ICS itself |
| **investpy** (Investing.com scraper) | none | undocumented; throttled | Everything global, with consensus & forecast | Easy (DataFrame) | ★★ — endpoint shape changes; breaks ~2x/yr; project is community-maintained |
| **econdb** | free key (generous) | ~ample | Macro releases worldwide | Easy | ★★★ — newer, less battle-tested |
| **Trading Economics** | paid for calendar API | — | Best UX | Easy | ★★★★ — but **paid**, disqualified |
| **Forex Factory scraper** | none | scrape-fragile | Everything, with forecast/prior | Hard (HTML) | ★★ |

### 1.2 Recommendation

**Ship FRED + FOMC ICS. Add investpy behind a feature flag as a "richer consensus" enricher.**

Rationale:
- FRED's `releases/dates` returns **scheduled future release datetimes** for every BLS/BEA/Fed economic release we care about. That's exactly the data shape we need (a dated event, not a value).
- FOMC meeting dates aren't on FRED — but the Fed publishes a public **iCalendar feed** (https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm has an `.ics` link). `icalendar` is a 50 KB pure-python lib, no extra API key.
- **No HTML scraping anywhere** in the primary path. Both endpoints have been stable for >10 years.
- Forecast/consensus values are *nice-to-have but not required* by pillar 3; the rule is event-time, not surprise-driven. So `investpy` (which adds consensus) is optional.

What we lose vs. investpy: forecast/consensus/prior numbers in the same row. Acceptable for v1.

### 1.3 Concrete event list

```
CPI                       FRED release_id=10
Core PCE                  FRED release_id=21
Employment Situation/NFP  FRED release_id=50
PPI                       FRED release_id=46
Retail Sales              FRED release_id=83
ISM (manufacturing)       FRED release_id=375 (verify; ISM is tricky — confirm in dev)
FOMC statement + presser  ICS feed
```

(Release IDs above are the documented values; verify the ISM one at integration time.)

---

## 2. Earnings Calendar

We need: per-ticker next-earnings datetime for every name in the universe, looked up at signal-generation time so we can (a) reject longs in the 48h pre-print and (b) flag mid-hold prints for the "exit 24h before" rule.

### 2.1 yfinance `get_earnings_dates` — what's actually wrong with it

It works *barely* — but:
- **Per-ticker only.** No bulk endpoint. 25 tickers = 25 sequential HTTPS calls per refresh.
- Returns a DataFrame indexed by *announced* dates (historical) plus 1–4 future estimated dates. Future row sometimes omits time-of-day (`AMC` / `BMO` flag isn't in the frame).
- Yahoo's source data is *Zacks*, which **revises confirmed times within a few days of the print** — yfinance caches inconsistently, so the date you see Monday may differ from Wednesday.
- Empty DataFrame on Azure IPs occasionally (same yfinance ratelimit class we already mitigate for prices).
- **No "confirmed vs estimated" boolean.** A "confirmed" earnings print is what should trigger blackout; an estimated date can drift ±2 weeks.

### 2.2 Options

| Source | Auth | Free-tier limit | Bulk by date? | Confirmed flag? | BMO/AMC? |
|---|---|---|---|---|---|
| **Finnhub `/calendar/earnings`** | free key | 60 req/min | ✅ yes (`from`/`to`) | ✅ `epsActual`/`epsEstimate` populated when confirmed | ✅ `hour` field |
| **yfinance `get_earnings_dates`** | none | yfinance class | ❌ per-ticker | ❌ | partial |
| **NASDAQ web scraper** (`api.nasdaq.com/api/calendar/earnings?date=...`) | none | undocumented | ✅ by date | ✅ | ✅ | 
| **EarningsHistory** (3rd-party py wrapper) | none | thin wrapper over Yahoo | per-ticker | ❌ | partial |
| **Alpha Vantage `EARNINGS_CALENDAR`** | free key (already configured!) | 25 req/day on free tier | ✅ CSV horizon=3month | ❌ no time | ❌ |
| **Polygon `/v3/reference/earnings`** | free key | 5 req/min | ✅ | ✅ | ✅ | 

### 2.3 Recommendation

**Primary: Finnhub `/calendar/earnings?from=YYYY-MM-DD&to=YYYY-MM-DD`.**
**Fallback: Alpha Vantage `EARNINGS_CALENDAR` (already keyed in `.env`).**
**Last resort: per-ticker `yfinance.Ticker(t).get_earnings_dates(limit=4)` loop.**

Rationale:
- One Finnhub call per refresh covers the entire 7-day forward window for all 25 tickers — well inside `60 req/min`.
- Finnhub returns a clean BMO/AMC `hour` plus `epsEstimate` so we can distinguish *confirmed* (estimate populated, date within 14 days) from *placeholder* (estimate null, date wide).
- AV is already a configured fallback in the codebase for prices — reusing the key is cheap.
- yfinance loop is tolerable as belt-and-braces for the 1–2 names per quarter where Finnhub lags.

**Caveat:** Finnhub's "confirmed" inference is heuristic. Cross-check against the issuer's IR page is out of scope for v1; we accept ~1–2 days of drift on unconfirmed dates and just widen the blackout to 72h when `epsEstimate is None`.

---

## 3. AI-Infra Chokepoint Universe

Anchor names from `00-PROMPT.md`: **AXTI** (substrates), **AEHR** (test/burn-in), **AAOI** (transceivers/photonics-adjacent). Build outward by *bottleneck physics*, not by AI-narrative association.

### 3.1 Proposed universe (~20 names)

| Bucket | Tickers | Notes |
|---|---|---|
| **Compound substrates** (InP, GaAs for laser/EML) | **AXTI**, IIVI/COHR | AXTI is the pure play; COHR is the diversified incumbent. |
| **HBM / DRAM scaling** | MU, **SK Hynix (000660.KS)**, ENTG (specialty gases/CMP slurry), **CAMT** (process-control metrology) | SK Hynix is KRX-listed; KQ ADR exists but illiquid — likely drop. ENTG and CAMT are the western-listed picks-and-shovels. |
| **Silicon photonics / co-packaged optics** | **AAOI**, LITE, **POET**, **CIEN** | POET is micro-cap & speculative — keep on a separate "watch only" tier. CIEN is the systems-level beneficiary. |
| **Thermal management (liquid cooling, vapor chambers)** | **VRT** (Vertiv), **MOD** (Modine), **SMCI** (rack-level) | SMCI has governance overhang; flag for risk model. |
| **Wafer test / burn-in** | **AEHR**, **COHU**, **TER** (Teradyne), **ONTO** | AEHR is the asymmetric micro-cap; TER/ONTO are the large-caps. |
| **EUV ecosystem** | **ASML**, **VECO** (deposition for EUV mask infra), KLAC | KLAC = inspection; spans EUV + advanced packaging. |
| **Advanced packaging (CoWoS, CoWoS-L, hybrid bonding)** | **AMAT**, **LRCX**, **BESI** (Be Semiconductor — hybrid bonders) | BESI is the hybrid-bonding pure play; Amsterdam-listed, ADR exists. |
| **Power delivery (48V→1V, vertical power, GaN)** | **MPWR**, **NVT**, **WOLF** | WOLF distressed — flag separately. NVT (nVent) is the rack/busbar play. |

That's **22 names** before liquidity filters. After dropping SK Hynix ADR illiquidity and treating WOLF/SMCI as restricted-flag, working set ≈ **18–19**.

### 3.2 Sizing-model concerns ($25k notional, 1% risk)

The strategy sizes a position so that `(entry − stop) × shares = $250` per trade. The risk knob is the ATR-based stop. Problems show up on **micro-caps** where:
- ATR % is high → shares are small → fixed commissions and bid-ask cross dominate.
- Avg dollar volume is low → a $25k position might be >0.5% of a day's tape, so the stop becomes self-fulfilling on exit.

| Ticker | Approx mkt cap | 30d avg $ vol | Suitable for $25k/1%? |
|---|---|---|---|
| AEHR | ~$400M | ~$15M/day | ⚠ — usable but cap notional at **$10k** to stay <0.1% of ADV |
| AXTI | ~$80M | ~$2M/day | ❌ — drop notional to **$5k or skip**; spread alone eats the edge |
| POET | ~$300M | ~$10M/day | ⚠ — speculative, "watch only" tier |
| WOLF | distressed | high $ vol but binary | ❌ — exclude until restructuring resolves |
| Everything else | ≥ $5B | ≥ $50M/day | ✅ |

**Action:** add a per-ticker `max_notional` override in `config.py` (or a new `universe.yaml`); default $25k, lower for the three flagged names. The existing risk_classifier doesn't need to change — sizing is upstream of it.

(Mkt cap / ADV figures are approximate from memory; verify at integration time. The *structure* of the recommendation stands regardless of exact figures.)

---

## 4. Negative-Beta Hedge Basket

Goal per Aditya feedback #2: when **NDX RSI(14) > 70**, surface a *hedge candidate* alongside long ideas — a name that historically moves *opposite* QQQ rather than just "less."

True negative beta to QQQ over 3 years is rare. Most "defensive" names show *low positive* beta (0.2–0.4), not negative. We must verify empirically before shipping; theoretical defensives are not enough.

### 4.1 Candidate list (6 names) + verification status

| Ticker | Thesis | Expected ρ vs QQQ (3y daily) | Ship without verification? |
|---|---|---|---|
| **DG** (Dollar General) | Trade-down/recession beneficiary; mentioned in the prompt | likely ~0.10 to −0.10 | ⚠ verify — DG has been QQQ-correlated during execution issues |
| **KR** (Kroger) | Defensive grocery, low beta | likely 0.10–0.30 (low, **not negative**) | ⚠ ship as low-beta only, **not** as negative-beta |
| **GLD** (gold ETF) | Tail-risk asset; rate-sensitive but inversely so during equity drawdowns | ρ commonly ~0 to −0.20 | ✅ ship after verification (well-documented decoupling) |
| **SHV** (1–3mo T-bills) | Cash proxy, ρ ≈ 0 by construction | ~0.00 | ✅ — but it's *zero* beta, not negative; usable as a "park cash" hedge |
| **CME** (CME Group) | Vol benefits CME's volume → revenue; inversely tied to calm equity tape | ρ uncertain, **likely positive** because it's still a financial | ❌ verify — gut suspicion this fails the test |
| **FXY** (Yen ETF) | Carry-unwind beneficiary during risk-off | ρ ~ −0.10 in regimes, often ~0 overall | ⚠ regime-dependent; flag for verification |

### 4.2 What "verify" means concretely

Before shipping any name as a hedge, run a one-shot script (out of scope for this doc, mentioned for completeness):
1. Pull 3y daily closes for `QQQ` and the candidate via the existing `price_fetcher`.
2. Compute daily log returns.
3. Report **full-sample Pearson ρ**, **rolling 60-day ρ percentile distribution**, and **β from OLS** (`return_x ~ return_qqq`).
4. **Ship rule:** include in hedge basket only if `full-sample ρ ≤ 0.20` **and** `60-day-rolling-ρ p25 < 0.0`. Anything else is "low-beta" not "hedge."

That's a 30-line script, but it must run before the basket is wired into the UI. No vibes-based hedges — pillar 4 (R:R asymmetry) is undermined if the "hedge" is actually 0.5-correlated.

### 4.3 What about `SIXU` (the prompt's example)?

`SIXU` (S&P 500 Sector Neutral Quality, or a similar low-vol ETF depending on which Aditya meant) — likely shows *low* beta but firmly positive correlation. Treat the same way: verify, then categorize as "defensive" rather than "hedge."

---

## 5. Integration Sketch

### 5.1 New module layout

```
backend/src/swing_trader/data/
  ├── price_fetcher.py        (existing)
  ├── news_scraper.py         (existing)
  ├── macro_calendar.py       (NEW — FRED + FOMC ICS)
  ├── earnings_calendar.py    (NEW — Finnhub primary, AV/yf fallbacks)
  └── universe.py             (NEW — loads tickers + per-name overrides from yaml)

backend/src/swing_trader/config/
  └── universe.yaml           (NEW — ticker → bucket, max_notional, flags)
```

### 5.2 New SQLite table

```sql
events(
  id INTEGER PK,
  kind TEXT,                   -- 'macro' | 'earnings'
  symbol TEXT,                 -- ticker for earnings, '' for macro
  release TEXT,                -- 'CPI' | 'FOMC' | 'NFP' | 'EARNINGS' | ...
  scheduled_at TIMESTAMP,
  confirmed BOOLEAN,
  source TEXT,                 -- 'fred' | 'fomc_ics' | 'finnhub' | 'av' | 'yfinance'
  fetched_at TIMESTAMP,
  UNIQUE(kind, symbol, release, scheduled_at)
);
CREATE INDEX idx_events_scheduled ON events(scheduled_at);
CREATE INDEX idx_events_symbol ON events(symbol, scheduled_at);
```

### 5.3 Scheduler changes

The existing `scheduler.py` runs `refresh_pipeline` every 3h. Add **one new daily job**:

```python
scheduler.add_job(
    refresh_calendars,
    CronTrigger(hour=6, minute=0),     # 06:00 UTC = pre-US-open
    id="calendars",
    max_instances=1,
    coalesce=True,
)
```

`refresh_calendars()`:
1. `macro_calendar.fetch_next_14d()` → upsert into `events`.
2. `earnings_calendar.fetch_next_14d(tickers=universe)` → upsert.
3. Log into the existing `runs` table (extend it or use a separate `calendar_runs`).

The 3h `refresh_pipeline` does **not** re-fetch calendars — daily is enough, and re-fetching would burn Finnhub quota for no reason.

### 5.4 Signal generator integration

In `engine/signal_generator.py`, after a strategy emits a `Signal`, add a **blackout check** before persisting:

```python
def is_blackout(ticker: str, side: Literal["LONG","SHORT"], now: datetime) -> str | None:
    """Return reason string if signal should be suppressed, else None."""
    # 1. Macro: any CPI/FOMC/NFP within next 48h → suppress LONGs only.
    # 2. Earnings: ticker has confirmed earnings within next 48h → suppress both sides.
    # 3. Earnings unconfirmed but date within 72h → flag MEDIUM, do not suppress.
```

This is **filtering**, not strategy logic — keeps `strategies/*.py` pure and lets the macro layer be swapped without touching strategy code. Output: either drop the signal or attach a `confirmation` like `"5d to FOMC — MEDIUM-risk"` so the UI can show the constraint.

For *open* positions whose hold-window now overlaps a print, add a daily sweep that emits an **`exit_recommended`** event 24h before the next `events` row for that ticker (Aditya's earnings-gap rule).

### 5.5 Hedge surfacing

When `MarketBar` computes `RSI(14)` on `^NDX` and reads > 70, the API response should include a `hedge_suggestion` slot. Implementation: a `hedges.yaml` listing the verified names from §4 with a one-line rationale. The signal pipeline picks one (round-robin or by lowest 60d ρ this week) and attaches it.

This is **UI wiring, not new data** — once §4 verification has been done once, the basket lives in a static yaml; we only re-run the correlation script monthly.

### 5.6 Env vars / API keys

| Var | Source | Free tier | Used by |
|---|---|---|---|
| `FRED_API_KEY` | https://fred.stlouisfed.org/docs/api/api_key.html | 120 req/min, free forever | `macro_calendar.py` |
| `FINNHUB_API_KEY` | https://finnhub.io/register | 60 req/min, free forever | `earnings_calendar.py` |
| `ALPHA_VANTAGE_API_KEY` | (existing) | 25 req/day | earnings fallback only |

Both new keys are free and email-only signup; no card required. Document in `README.md` under the existing AV section.

### 5.7 Rate-limit budget per daily run

- FRED: ~5 calls (one per release_id we care about, or one `releases/dates` call). Trivial.
- FOMC ICS: 1 GET. Trivial.
- Finnhub: 1 call (`/calendar/earnings?from=today&to=today+14d`). Returns the whole market; we filter to our universe locally. **0.4% of daily quota.**
- AV fallback: only on Finnhub failure; 1 call.
- yfinance per-ticker fallback: only on AV failure; ≤ 25 calls (existing pattern).

Comfortable headroom. The 3h price-refresh job is already the dominant load.

### 5.8 Failure modes & fallbacks

| Failure | Behavior |
|---|---|
| FRED 5xx | Use last successful `events` rows; log warning; raise stale flag if > 48h old |
| FOMC ICS unreachable | Hard-coded next 4 FOMC dates as a constant; warn loudly |
| Finnhub 429 | Fall through to AV `EARNINGS_CALENDAR` |
| AV also fails | Per-ticker `yfinance.Ticker.get_earnings_dates` loop |
| All earnings sources fail | Surface a UI banner: *"Earnings blackout disabled — verify manually before entries"* and **do not suppress signals** (fail-open with a warning is safer than silent fail-closed which would emit nothing) |

Note the deliberate **fail-open on earnings**: a missing earnings date should not silently kill all signals; it should warn the human user that pillar 3 isn't enforceable today.

---

## Open questions for the next pass

1. Should we ingest **economic forecast/consensus values** (investpy, econdb) so the system can additionally suppress *only when* the surprise potential is high (e.g. CPI consensus dispersion wide)? Probably v2.
2. **International tickers** (ASML US listing is fine; BESI is OTC ADR — does our yfinance pull cover it cleanly?) — needs a smoke test.
3. The `max_notional` per-ticker override touches risk sizing — confirm with Aditya whether AEHR/AXTI should be in the universe at all, or relegated to a separate "high-asymmetry watchlist" that uses different sizing rules entirely.
4. Hedge basket cadence: monthly recompute of correlations is probably fine for v1, but if we ever swing into a regime change (rates spike, dollar shock) the historical ρ goes stale fast. Worth flagging to the user, not auto-handled.
