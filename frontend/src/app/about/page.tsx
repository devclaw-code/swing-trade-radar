import Link from "next/link";

export const metadata = {
  title: "About / Methodology",
  description:
    "How Swing Trade Radar produces its verdicts. Educational only — not financial advice.",
};

const REPO = "https://github.com/";

const STRATEGIES = [
  {
    id: "S1",
    name: "Trend (50/200 SMA + regime)",
    philosophy:
      "The boring one that works. Long-only trend following, regime-gated by SPY > 200-SMA.",
  },
  {
    id: "S2",
    name: "Clenow Time-Series Momentum",
    philosophy:
      "Rank the universe by 90d slope/vol; ride the top decile until it falls out. Survives most skeptic tests.",
  },
  {
    id: "S3",
    name: "Connors RSI(2) Mean Reversion",
    philosophy:
      "Bounce-buy oversold names inside an established uptrend. Dead in chop, alive when properly regime-filtered.",
  },
  {
    id: "S4",
    name: "Minervini VCP",
    philosophy:
      "Volatility contraction → breakout on volume. Heuristic-detected; surfaced as a score, not a hard fire.",
  },
  {
    id: "S5",
    name: "PEAD (Post-Earnings Drift)",
    philosophy:
      "Earnings winners drift up for 2-4 weeks. Documented since 1989 and still alive in mega-cap tech.",
  },
];

const RISK_WARNINGS = [
  "All edges decay. RSI(2)-style mean reversion is materially weaker post-2015 — backtest aggressively before trusting any number on this site.",
  "NDX-100 is a tech-heavy basket; mega-cap concentration means single-name event risk is real. Always size by ATR, not by gut.",
  "Backtests assume frictionless fills and zero slippage. Real-world fills, especially on gap-ups and breakouts, will degrade results.",
  "No strategy here uses news-event filtering beyond earnings dates. A regulatory or geopolitical shock will not be in the model.",
  "This site does not track your portfolio, your risk budget, or your tax situation. Position sizes are hints based on a generic 1% rule.",
];

export default function AboutPage() {
  return (
    <>
      <header className="border-b border-slate-700/60 bg-slate-900 px-6 py-5">
        <div className="mx-auto max-w-3xl">
          <h1 className="text-2xl font-bold tracking-tight text-slate-50">About / Methodology</h1>
          <p className="text-sm text-slate-400">
            What this is, what it isn&apos;t, and how to read the verdicts.
          </p>
        </div>
      </header>

      <section className="mx-auto max-w-3xl space-y-8 px-6 py-8">
        <div className="rounded-xl border border-amber-500/50 bg-amber-950 p-4 text-sm text-amber-100">
          <strong className="text-amber-50">This is a research desk, not a broker.</strong> Swing
          Trade Radar produces daily algorithmic verdicts on a fixed list of NDX-100 mega-caps. It
          does not place trades, it does not know your account, and it is{" "}
          <strong className="text-amber-50">not financial advice</strong>. Educational use only —
          paper-trade and verify everything yourself.
        </div>

        <div>
          <h2 className="mb-2 text-lg font-bold text-slate-50">How a verdict is built</h2>
          <ol className="list-decimal space-y-2 pl-5 text-sm leading-relaxed text-slate-200">
            <li>
              Daily OHLCV is fetched (yfinance primary, Alpha Vantage fallback) and cached in
              SQLite.
            </li>
            <li>
              Five rule-based strategies are evaluated independently on every ticker. Each returns a
              fire/no-fire bit, a score, and an evidence list.
            </li>
            <li>
              A regime filter (SPY/QQQ vs 200-SMA, VIX level + term structure) gates everything. In
              an unfavorable regime, all long fires get downgraded.
            </li>
            <li>
              Event risk filters (earnings within 7 days, VIX &gt; 25) further downgrade verdicts.
            </li>
            <li>
              The synthesizer combines outputs into <code>BUY</code>, <code>WATCH</code>,{" "}
              <code>AVOID</code>, or <code>NO_SETUP</code> — with an explicit conviction score,
              stop, target, R:R, and a historical base rate computed from 10 years of cached bars.
            </li>
            <li>
              Counter-arguments are pulled from a curated{" "}
              <code className="font-mono">risk_notes.yaml</code> keyed by setup-type and ticker, so
              every claim is auditable against the source research.
            </li>
          </ol>
        </div>

        <div>
          <h2 className="mb-2 text-lg font-bold text-slate-50">The five strategies</h2>
          <ul className="space-y-3">
            {STRATEGIES.map((s) => (
              <li
                key={s.id}
                className="rounded-md border border-slate-700/60 bg-slate-900 px-4 py-3 transition hover:border-slate-600"
              >
                <div className="text-sm font-semibold text-slate-50">
                  <span className="font-mono text-slate-500">{s.id}</span> · {s.name}
                </div>
                <div className="mt-0.5 text-sm text-slate-300">{s.philosophy}</div>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-sm text-slate-400">
            See{" "}
            <Link href="/strategies" className="text-sky-400 hover:text-sky-300 hover:underline">
              Strategies
            </Link>{" "}
            for current backtest stats (Sharpe, deflated Sharpe, win rate, max DD).
          </p>
        </div>

        <div>
          <h2 className="mb-2 text-lg font-bold text-slate-50">Risk warnings</h2>
          <ul className="list-disc space-y-2 pl-5 text-sm text-slate-200">
            {RISK_WARNINGS.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </div>

        <div>
          <h2 className="mb-2 text-lg font-bold text-slate-50">Source research</h2>
          <p className="text-sm text-slate-300">
            Every doc-ref attached to a verdict points back into the underlying research. Start at{" "}
            <a
              href={`${REPO}blob/main/research/00-INDEX.md`}
              target="_blank"
              rel="noreferrer"
              className="font-mono text-sky-400 hover:text-sky-300 hover:underline"
            >
              research/00-INDEX.md
            </a>
            .
          </p>
        </div>

        <div className="rounded-xl border border-slate-700/60 bg-slate-900 p-4 text-xs text-slate-400">
          <strong className="text-slate-200">Disclaimer.</strong> Swing Trade Radar is provided{" "}
          <em>as-is</em> for educational and research purposes only. Nothing here is investment,
          legal, or tax advice. Past performance does not guarantee future results. Trading
          securities involves risk of loss, including total loss of principal. You are solely
          responsible for any decisions you make based on the output of this system.
        </div>
      </section>
    </>
  );
}
