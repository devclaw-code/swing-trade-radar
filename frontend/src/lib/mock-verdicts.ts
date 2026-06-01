import type { RegimeContext, StrategySummary, Verdict } from "./api";

export const mockAsOf = "2026-05-30";

export const mockRegime: RegimeContext = {
  spy_above_200sma: true,
  qqq_above_200sma: true,
  vix: 14.8,
  vix_term_structure: "contango",
  regime_verdict: "favorable for long swings",
};

// Generate a plausible 60-bar sparkline around a base price.
function spark(base: number, drift: number, vol: number, seed: number): number[] {
  let s = seed;
  const rng = () => {
    s = (s * 1664525 + 1013904223) % 4294967296;
    return s / 4294967296;
  };
  const out: number[] = [];
  let p = base * 0.92;
  for (let i = 0; i < 60; i++) {
    p = p * (1 + drift / 60 + (rng() - 0.5) * vol);
    out.push(Number(p.toFixed(2)));
  }
  return out;
}

export const mockVerdicts: Verdict[] = [
  {
    ticker: "NVDA",
    as_of: mockAsOf,
    verdict: "BUY",
    conviction: 0.72,
    primary_setup: "Connors RSI(2) Mean Reversion",
    supporting_setups: ["50/200 trend up", "Golden cross intact"],
    entry_zone: { price: 138.2, method: "next-day open" },
    stop_loss: { price: 132.4, method: "2x ATR(14) below entry", risk_pct: 4.2 },
    target: { price: 148.5, method: "previous swing high", rr: 1.78 },
    max_hold: "10 trading days (RSI(2) reverts or stop)",
    position_size_hint: "≤ 1% account risk; ~145 shares for $25k account",
    regime_context: mockRegime,
    risk_tier: "MEDIUM",
    price: 140.5,
    day_change_pct: 0.012,
    sparkline: spark(140, 0.08, 0.018, 7),
    why: {
      headline:
        "RSI(2) hit 6.4 (extreme oversold) inside an established uptrend. Mean reversion edge is strongest in this setup.",
      evidence: [
        {
          factor: "RSI(2) = 6.4",
          value: "6.4",
          weight: 0.35,
          passed: true,
          note: "<10 threshold; Connors documented edge",
        },
        {
          factor: "Above 200-SMA",
          value: "yes",
          weight: 0.25,
          passed: true,
          note: "regime filter passed",
        },
        {
          factor: "ADX(14) trending mildly",
          value: "22",
          weight: 0.15,
          passed: true,
          note: "trend strong enough not to be choppy",
        },
        {
          factor: "Volume on red candle 1.2x avg",
          value: "1.2×",
          weight: 0.1,
          passed: true,
          note: "no panic dump signature",
        },
        {
          factor: "No earnings within 7 days",
          value: "12d away",
          weight: 0.15,
          passed: true,
          note: "event risk clear",
        },
      ],
      historical_base_rate: {
        occurrences: 87,
        win_rate: 0.68,
        avg_r: 0.83,
        median_hold: 4,
      },
      what_could_invalidate: [
        "Close below $132.40 (the ATR stop)",
        "Gap down >3% on no news (regime shift signal)",
        "VIX spikes above 25 (regime kill)",
      ],
      counter_arguments: [
        "RSI(2) edge has decayed since 2015 — see research/07 §2",
        "Mag7 concentration risk: NVDA already ~8% of QQQ",
      ],
      doc_refs: ["research/01 §8", "research/02 §3", "research/05 cheat-sheet:NVDA"],
    },
  },
  {
    ticker: "AAPL",
    as_of: mockAsOf,
    verdict: "WATCH",
    conviction: 0.41,
    primary_setup: "Minervini VCP (forming)",
    supporting_setups: ["Above 200-SMA", "RS rank 78"],
    entry_zone: { price: 232.5, method: "breakout above pivot $232.50 on volume ≥1.5×" },
    stop_loss: { price: 224.8, method: "low of last contraction", risk_pct: 3.3 },
    target: { price: 248.0, method: "prior high + measured move", rr: 2.0 },
    max_hold: "4-6 weeks",
    position_size_hint: "Wait for confirmed breakout before sizing",
    regime_context: mockRegime,
    risk_tier: "MEDIUM",
    price: 229.4,
    day_change_pct: 0.004,
    sparkline: spark(229, 0.04, 0.012, 13),
    why: {
      headline:
        "VCP-likely pattern: 3 lower-volatility pullbacks detected, each <60% of prior. Awaiting breakout confirmation.",
      evidence: [
        {
          factor: "Contractions detected",
          value: "3",
          weight: 0.3,
          passed: true,
          note: "12% → 7% → 4% range compression",
        },
        {
          factor: "RS rank (IBD-style)",
          value: "78",
          weight: 0.2,
          passed: true,
          note: "top quartile vs NDX",
        },
        {
          factor: "Volume on breakout candle",
          value: "0.9×",
          weight: 0.25,
          passed: false,
          note: "not yet ≥1.5× avg — not confirmed",
        },
        {
          factor: "Above 200-SMA",
          value: "yes",
          weight: 0.15,
          passed: true,
          note: "regime filter passed",
        },
        {
          factor: "No earnings within 7 days",
          value: "21d away",
          weight: 0.1,
          passed: true,
          note: "clear",
        },
      ],
      historical_base_rate: {
        occurrences: 41,
        win_rate: 0.54,
        avg_r: 0.62,
        median_hold: 18,
      },
      what_could_invalidate: [
        "Close below $224.80 (contraction low)",
        "Failed breakout that closes back inside the base",
        "Sector rotation out of mega-cap tech",
      ],
      counter_arguments: [
        "VCP auto-detection is heuristic — manual chart review recommended",
        "Mega-cap VCPs have lower follow-through than mid-caps historically",
      ],
      doc_refs: ["research/01 §11", "research/05 cheat-sheet:AAPL"],
    },
  },
  {
    ticker: "MSFT",
    as_of: mockAsOf,
    verdict: "BUY",
    conviction: 0.61,
    primary_setup: "Clenow Time-Series Momentum",
    supporting_setups: ["50/200 trend up"],
    entry_zone: { price: 442.1, method: "weekly rebalance — top decile" },
    stop_loss: { price: 419.0, method: "2x ATR(14) below entry", risk_pct: 5.2 },
    target: { price: 478.0, method: "trailing chandelier 3× ATR", rr: 1.55 },
    max_hold: "Until exits top quintile or breaks 100-SMA",
    position_size_hint: "Equal-weight slice of momentum sleeve",
    regime_context: mockRegime,
    risk_tier: "LOW",
    price: 440.8,
    day_change_pct: 0.007,
    sparkline: spark(440, 0.12, 0.01, 21),
    why: {
      headline:
        "Ranks in top decile of NDX-100 by 90-day risk-adjusted return. Slope/vol = 0.21 — strongest of mega-caps.",
      evidence: [
        {
          factor: "90d slope/vol rank",
          value: "#3 of 100",
          weight: 0.5,
          passed: true,
          note: "top decile threshold cleared",
        },
        {
          factor: "Above 100-SMA (exit filter)",
          value: "yes",
          weight: 0.2,
          passed: true,
          note: "no exit trigger",
        },
        {
          factor: "Above 200-SMA",
          value: "yes",
          weight: 0.2,
          passed: true,
          note: "regime filter passed",
        },
        {
          factor: "Drawdown from 52w high",
          value: "-3%",
          weight: 0.1,
          passed: true,
          note: "shallow — momentum intact",
        },
      ],
      historical_base_rate: {
        occurrences: 124,
        win_rate: 0.59,
        avg_r: 0.71,
        median_hold: 34,
      },
      what_could_invalidate: [
        "Drops out of top quintile at next weekly rebalance",
        "Closes below 100-SMA",
        "VIX > 25 — momentum regime kill",
      ],
      counter_arguments: [
        "Clenow momentum is crowded post-2020; alpha decay possible",
        "Long holds expose to single-name event risk in mega-caps",
      ],
      doc_refs: ["research/01 §6", "research/04 §2"],
    },
  },
  {
    ticker: "TSLA",
    as_of: mockAsOf,
    verdict: "AVOID",
    conviction: 0.18,
    primary_setup: null,
    supporting_setups: [],
    entry_zone: null,
    stop_loss: null,
    target: null,
    max_hold: null,
    position_size_hint: null,
    regime_context: mockRegime,
    risk_tier: "HIGH",
    price: 198.2,
    day_change_pct: -0.024,
    sparkline: spark(210, -0.18, 0.03, 47),
    why: {
      headline:
        "Below 200-SMA, ADX falling, earnings in 4 days. No active strategy fires; multiple regime filters fail.",
      evidence: [
        {
          factor: "Above 200-SMA",
          value: "no (-6%)",
          weight: 0.35,
          passed: false,
          note: "regime filter failed — blocks trend + RSI(2) setups",
        },
        {
          factor: "Earnings within 7 days",
          value: "4d",
          weight: 0.25,
          passed: false,
          note: "event risk too close",
        },
        {
          factor: "ADX(14) declining",
          value: "16↓",
          weight: 0.2,
          passed: false,
          note: "no trend to ride",
        },
        {
          factor: "Realized vol vs basket",
          value: "2.1×",
          weight: 0.2,
          passed: false,
          note: "elevated — sizing penalty",
        },
      ],
      historical_base_rate: null,
      what_could_invalidate: [
        "Reclaim 200-SMA on volume",
        "Post-earnings gap up >5% with continuation",
      ],
      counter_arguments: [
        "TSLA has historically had violent reversals — wait for confirmation, don't catch the knife",
      ],
      doc_refs: ["research/05 cheat-sheet:TSLA", "research/07 §4"],
    },
  },
  {
    ticker: "GOOGL",
    as_of: mockAsOf,
    verdict: "NO_SETUP",
    conviction: 0.0,
    primary_setup: null,
    supporting_setups: [],
    entry_zone: null,
    stop_loss: null,
    target: null,
    max_hold: null,
    position_size_hint: null,
    regime_context: mockRegime,
    risk_tier: "LOW",
    price: 375.4,
    day_change_pct: 0.002,
    sparkline: spark(375, 0.02, 0.008, 53),
    why: {
      headline: "No strategy fires today. Trend is mildly up but no momentum/mean-rev/VCP/PEAD trigger.",
      evidence: [
        { factor: "S1 Trend", value: "neutral", weight: 0.2, passed: false, note: "above SMAs but no fresh entry" },
        { factor: "S2 Clenow", value: "rank 38", weight: 0.2, passed: false, note: "outside top decile" },
        { factor: "S3 RSI(2)", value: "47", weight: 0.2, passed: false, note: "not oversold" },
        { factor: "S4 VCP", value: "—", weight: 0.2, passed: false, note: "no contraction sequence" },
        { factor: "S5 PEAD", value: "—", weight: 0.2, passed: false, note: "no recent earnings beat" },
      ],
      historical_base_rate: null,
      what_could_invalidate: [],
      counter_arguments: [],
      doc_refs: ["research/01"],
    },
  },
];

export const mockStrategies: StrategySummary[] = [
  {
    id: "S1",
    name: "Trend (50/200 SMA + regime)",
    description:
      "Long-bias trend following. Fires when price > 50-SMA > 200-SMA and SPY > 200-SMA. Stops at 2× ATR(14); trails with 3× ATR chandelier exit. Hold 2-6 weeks typical.",
    doc_refs: ["research/01 §3", "research/04 §1"],
    backtest: {
      sharpe: 0.94,
      deflated_sharpe: 1.12,
      win_rate: 0.51,
      avg_r: 0.66,
      max_dd_r: -4.2,
      n_trades: 312,
      profit_factor: 1.62,
    },
  },
  {
    id: "S2",
    name: "Clenow Time-Series Momentum",
    description:
      "Rank NDX-100 by 90-day risk-adjusted return (slope/vol). Long top decile, weekly rebalance. Exit when ticker drops out of top quintile or breaks 100-SMA.",
    doc_refs: ["research/01 §6", "research/04 §2"],
    backtest: {
      sharpe: 1.08,
      deflated_sharpe: 1.21,
      win_rate: 0.58,
      avg_r: 0.74,
      max_dd_r: -3.6,
      n_trades: 198,
      profit_factor: 1.81,
    },
  },
  {
    id: "S3",
    name: "Connors RSI(2) Mean Reversion",
    description:
      "Regime-gated mean reversion. Fires when RSI(2) < 10 AND above 200-SMA AND no earnings within 7 days AND VIX < 25. Exit on RSI(2) > 70, 5 days, or stop.",
    doc_refs: ["research/01 §8", "research/02 §3", "research/07 §2"],
    backtest: {
      sharpe: 1.32,
      deflated_sharpe: 1.05,
      win_rate: 0.68,
      avg_r: 0.83,
      max_dd_r: -2.8,
      n_trades: 412,
      profit_factor: 2.04,
    },
  },
  {
    id: "S4",
    name: "Minervini VCP",
    description:
      "Volatility contraction pattern: ≥3 lower-volatility pullbacks, each <60% of prior. Fires on breakout above pivot with volume ≥1.5× avg AND IBD-style RS top quartile. Auto-detection is heuristic — surfaced as a score, not a hard fire.",
    doc_refs: ["research/01 §11"],
    backtest: {
      sharpe: 0.78,
      deflated_sharpe: 0.62,
      win_rate: 0.46,
      avg_r: 0.51,
      max_dd_r: -5.1,
      n_trades: 88,
      profit_factor: 1.34,
    },
  },
  {
    id: "S5",
    name: "PEAD (Post-Earnings Drift)",
    description:
      "Long the earnings winner. Fires on EPS beat > 5% AND positive surprise AND gap-up open in top 1/3 of 20-day range. Hold 10-20 days; stop at gap-fill (pre-earnings close).",
    doc_refs: ["research/01 §13"],
    backtest: {
      sharpe: 1.17,
      deflated_sharpe: 1.31,
      win_rate: 0.62,
      avg_r: 0.79,
      max_dd_r: -3.1,
      n_trades: 156,
      profit_factor: 1.92,
    },
  },
];
