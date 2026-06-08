// Default to relative URLs so both server-side (Next.js) and client-side
// (browser) requests go through the Next dev/prod server, which rewrites
// /api/* to the FastAPI backend (see next.config.ts).
// On the server, relative URLs need a base — we use localhost:8080 (this app).
export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ??
  (typeof window === "undefined" ? "http://localhost:8080" : "");

// Set NEXT_PUBLIC_USE_MOCKS=1 to bypass network and serve `mock-verdicts`.
// Also auto-falls back to mocks if a fetch errors (dev-only convenience).
export const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS === "1";

// ------------------------------------------------------------
// Phase-2 verdict types
// ------------------------------------------------------------

export type VerdictKind = "BUY" | "WATCH" | "AVOID" | "NO_SETUP";
export type TimeHorizon = "Core" | "Tactical";
export type RiskTier = "LOW" | "MEDIUM" | "HIGH";
export type VixTermStructure = "contango" | "backwardation" | "flat";

export interface PriceMethod {
  price: number;
  method: string;
}

export interface StopLoss extends PriceMethod {
  risk_pct: number;
}

export interface TargetSpec extends PriceMethod {
  rr: number;
}

export interface RegimeContext {
  spy_above_200sma: boolean;
  qqq_above_200sma: boolean;
  vix: number;
  vix_term_structure: VixTermStructure;
  regime_verdict: string;
}

export interface EvidenceItem {
  factor: string;
  value: string;
  weight: number;
  passed: boolean;
  note: string;
}

export interface BaseRate {
  occurrences: number;
  win_rate: number;
  avg_r: number;
  median_hold: number;
}

export interface WhyBlock {
  headline: string;
  evidence: EvidenceItem[];
  historical_base_rate: BaseRate | null;
  what_could_invalidate: string[];
  counter_arguments: string[];
  doc_refs: string[];
}

export type Reliability = "high" | "medium" | "low" | "insufficient";

export type SRLevelKind = "support" | "resistance";

// A ranked support/resistance zone near the current price.
// Produced by the backend `engine.sr_levels.compute_sr_levels`. Display-only:
// it does NOT feed the numeric conviction/score (strength weights are still
// being calibrated against the walk-forward harness).
export interface SRLevel extends PriceMethod {
  kind: SRLevelKind;
  /** Confluence score 0..1 (touches + method agreement + recency + round-number bonus). */
  strength: number;
  /** Signed % from current price (negative = below / support, positive = above / resistance). */
  distance_pct: number;
  /** Method tags that voted for this zone, e.g. ["swing_low", "classic_pivot_S1"]. */
  sources: string[];
  /** Number of historical swing touches in the zone. */
  touches: number;
}

export interface HistoricalStatsDisplay {
  tier: Reliability;
  sample_size: number;
  show_win_rate: boolean;
  display_text: string;
}

export interface Verdict {
  ticker: string;
  as_of: string;
  verdict: VerdictKind;
  conviction: number;
  primary_setup: string | null;
  supporting_setups: string[];
  time_horizon?: TimeHorizon;
  volatility_atr?: number | null;
  entry_zone: PriceMethod | null;
  stop_loss: StopLoss | null;
  target: TargetSpec | null;
  max_hold: string | null;
  position_size_hint: string | null;
  regime_context: RegimeContext;
  why: WhyBlock;
  risk_tier: RiskTier;
  // Optional fields the backend may include for richer rendering.
  price?: number;
  day_change_pct?: number;
  sparkline?: number[];
  sanity_flags?: SanityFlag[];
  score?: number | null;
  score_breakdown?: ScoreBreakdown | null;
  correlation_penalty?: number;
  reliability?: Reliability;
  confidence_adjusted_for_sample?: number | null;
  historical_stats_display?: HistoricalStatsDisplay | null;
  /** Ranked support/resistance zones near price (display-only). */
  levels?: SRLevel[];
}

export interface ScoreComponent {
  value: number;
  weight: number;
  note: string;
}

export interface ScoreBreakdown {
  trend_quality: ScoreComponent;
  momentum: ScoreComponent;
  mean_reversion: ScoreComponent;
  risk_reward: ScoreComponent;
  volatility: ScoreComponent;
  earnings_risk: ScoreComponent;
  historical_reliability: ScoreComponent;
  extension_risk: ScoreComponent;
  total: number;
  weights: Record<string, number>;
  correlation_penalty: number;
}

export type SanitySeverity = "info" | "warning" | "high";

export interface SanityFlag {
  code: string;
  severity: SanitySeverity;
  message: string;
  value?: number | null;
  threshold?: number | null;
}

export interface StrategySummary {
  id: string; // S1..S5
  name: string;
  description: string;
  doc_refs: string[];
  not_yet_active?: boolean;
  backtest: {
    sharpe: number;
    deflated_sharpe: number;
    win_rate: number;
    avg_r: number;
    max_dd_r: number;
    n_trades: number;
    profit_factor: number;
  } | null;
}

// ------------------------------------------------------------
// Legacy phase-1 types (kept for backwards compat; the ticker
// detail page still consumes some of them).
// ------------------------------------------------------------

export type Risk = "LOW" | "MED" | "HIGH";
export type Direction = "LONG" | "SHORT";
export type Sentiment = "pos" | "neu" | "neg";

export interface Signal {
  id: number;
  ticker: string;
  strategy: string;
  direction: Direction;
  entry: number;
  target: number;
  stop: number;
  stop_pct: number;
  rr_ratio: number;
  risk: Risk;
  confidence: number;
  confirmations: string[];
  bar_date: string | null;
  generated_at: string | null;
}

export interface SignalsResponse {
  count: number;
  signals: Signal[];
}

export interface LastUpdated {
  version: number;
  ts: string | null;
  errors: number;
}

export interface NewsItem {
  id: number;
  title: string;
  summary: string;
  source: string;
  url: string;
  published_at: string | null;
  tickers: string[];
  sentiment: Sentiment;
  sentiment_score: number;
}

export interface NewsResponse {
  count: number;
  news: NewsItem[];
}

export interface BacktestResult {
  strategy: string;
  ticker: string;
  period_start: string;
  period_end: string;
  n_trades: number;
  win_rate: number;
  avg_r: number;
  profit_factor: number;
  max_dd_r: number;
  sharpe: number;
  avg_hold_bars: number;
  ran_at: string | null;
}

export interface OhlcvBar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface TickerDetail {
  ticker: string;
  ohlcv: OhlcvBar[];
  signals: Signal[];
  news: NewsItem[];
  backtest: BacktestResult[];
  // Optional phase-2 enrichment:
  verdict?: Verdict;
  strategies_evaluated?: { id: string; name: string; fired: boolean; reason: string }[];
  past_verdicts?: { as_of: string; verdict: VerdictKind; conviction: number }[];
}

export interface BacktestAllResponse {
  count: number;
  strategies: Record<string, BacktestResult[]>;
}

// ------------------------------------------------------------
// Fetcher
// ------------------------------------------------------------

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store", ...init });
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText} :: ${path}`);
  }
  return (await res.json()) as T;
}

/** SWR-friendly fetcher: throws on non-2xx, returns parsed JSON. */
export const swrFetcher = async <T>(path: string): Promise<T> => fetchJson<T>(path);

// ------------------------------------------------------------
// Phase-2 endpoint helpers
// ------------------------------------------------------------

export interface VerdictsResponse {
  count: number;
  as_of: string;
  verdicts: Verdict[];
  // Present when the request was made with `?mode=conservative`.
  mode?: "all" | "conservative";
  passed?: Verdict[];
  marginal?: MarginalVerdict[];
  filtered_out?: FilteredVerdict[];
}

// --- Tactical Swings (1-5 day horizon) ------------------------------------
export interface TacticalEntryZone {
  price: number | null;
  type: string; // "market" | "stop"
}
export interface TacticalLevel {
  price: number | null;
  rr?: number | null;
}
export interface TacticalCard {
  ticker: string;
  as_of: string;
  time_horizon: "Tactical";
  setup_id: string;
  setup_name: string;
  score: number;
  headline: string;
  entry_zone: TacticalEntryZone;
  stop_loss: TacticalLevel;
  target: TacticalLevel;
  max_hold: string;
  max_hold_days: number;
  expected_hold_days: number | null;
  expected_hold: string | null;
  volatility_atr: number | null;
  risk_tier: RiskTier;
  regime_filter: string;
  evidence: EvidenceItem[];
  invalidation_conditions: string[];
}
export interface TacticalResponse {
  count: number;
  generated_at: string;
  regime_filter: string;
  n_scanned: number;
  errors: number;
  cards: TacticalCard[];
}

export type FilterMode = "all" | "conservative";

export interface FilterReason {
  code: string;
  message: string;
}

export interface FilteredVerdict {
  verdict: Verdict;
  reasons: FilterReason[];
}

export interface MarginalVerdict {
  verdict: Verdict;
  reasons: FilterReason[];
}

export interface RegimeResponse extends RegimeContext {
  as_of: string;
}

export interface StrategiesResponse {
  count: number;
  strategies: StrategySummary[];
}

async function withMockFallback<T>(path: string, mock: () => T): Promise<T> {
  if (USE_MOCKS) return mock();
  try {
    return await fetchJson<T>(path);
  } catch (e) {
    if (process.env.NODE_ENV !== "production") {
      // eslint-disable-next-line no-console
      console.warn(`[api] ${path} failed, falling back to mocks:`, e);
      return mock();
    }
    throw e;
  }
}

export async function getVerdicts(mode: FilterMode = "all"): Promise<VerdictsResponse> {
  const { mockVerdicts, mockAsOf } = await import("./mock-verdicts");
  const path = mode === "conservative" ? "/api/verdicts?mode=conservative" : "/api/verdicts";
  return withMockFallback(path, () => ({
    count: mockVerdicts.length,
    as_of: mockAsOf,
    verdicts: mockVerdicts,
  }));
}

export async function getVerdict(ticker: string): Promise<Verdict> {
  const { mockVerdicts } = await import("./mock-verdicts");
  return withMockFallback(`/api/verdicts/${ticker.toUpperCase()}`, () => {
    const v = mockVerdicts.find((m) => m.ticker === ticker.toUpperCase());
    if (!v) throw new Error(`404 mock not found :: ${ticker}`);
    return v;
  });
}

export async function getRegime(): Promise<RegimeResponse> {
  const { mockRegime, mockAsOf } = await import("./mock-verdicts");
  return withMockFallback("/api/regime", () => ({ ...mockRegime, as_of: mockAsOf }));
}

export async function getStrategies(): Promise<StrategiesResponse> {
  const { mockStrategies } = await import("./mock-verdicts");
  return withMockFallback("/api/strategies", () => ({
    count: mockStrategies.length,
    strategies: mockStrategies,
  }));
}

export async function getLastUpdated(): Promise<LastUpdated> {
  return withMockFallback("/api/last-updated", () => ({
    version: 1,
    ts: new Date().toISOString(),
    errors: 0,
  }));
}
