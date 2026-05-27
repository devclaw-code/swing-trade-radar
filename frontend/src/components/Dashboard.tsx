"use client";

import { useMemo, useState } from "react";
import type { BacktestResult, NewsItem, Risk, Signal } from "@/lib/api";

type Tab = "signals" | "news" | "backtest";

const riskStyles: Record<Risk, string> = {
  LOW: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
  MED: "bg-amber-500/15 text-amber-300 border-amber-500/40",
  HIGH: "bg-rose-500/15 text-rose-300 border-rose-500/40",
};

const riskLabel: Record<Risk, string> = {
  LOW: "🟢 LOW",
  MED: "🟡 MEDIUM",
  HIGH: "🔴 HIGH",
};

const sentStyles: Record<NewsItem["sentiment"], string> = {
  pos: "bg-emerald-500/15 text-emerald-300",
  neu: "bg-white/10 text-white/60",
  neg: "bg-rose-500/15 text-rose-300",
};

function fmt(n: number, d = 2) {
  return n.toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
}
function pct(n: number, d = 2) {
  return `${(n * 100).toFixed(d)}%`;
}

function SignalCard({ s }: { s: Signal }) {
  const gainPct = (s.target - s.entry) / s.entry;
  const lossPct = (s.stop - s.entry) / s.entry;
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-5 shadow-lg backdrop-blur">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-xl font-bold tracking-tight">{s.ticker}</div>
          <div className="text-xs uppercase text-white/50">{s.strategy.replace(/_/g, " ")}</div>
        </div>
        <span className={`rounded-md border px-2 py-1 text-xs font-semibold ${riskStyles[s.risk]}`}>
          {riskLabel[s.risk]}
        </span>
      </div>
      <div className="mt-3 flex items-center gap-2">
        <span
          className={`rounded-md px-2 py-0.5 text-xs font-semibold ${
            s.direction === "LONG"
              ? "bg-emerald-500/20 text-emerald-300"
              : "bg-rose-500/20 text-rose-300"
          }`}
        >
          {s.direction === "LONG" ? "LONG 📈" : "SHORT 📉"}
        </span>
        <span className="text-xs text-white/40">{s.bar_date}</span>
      </div>
      <div className="mt-4 grid grid-cols-3 gap-2 text-sm">
        <div>
          <div className="text-[10px] uppercase text-white/40">Entry</div>
          <div className="font-mono">{fmt(s.entry)}</div>
        </div>
        <div>
          <div className="text-[10px] uppercase text-emerald-400/70">Target</div>
          <div className="font-mono text-emerald-300">{fmt(s.target)}</div>
          <div className="text-[10px] text-emerald-400/70">{pct(gainPct)}</div>
        </div>
        <div>
          <div className="text-[10px] uppercase text-rose-400/70">Stop</div>
          <div className="font-mono text-rose-300">{fmt(s.stop)}</div>
          <div className="text-[10px] text-rose-400/70">{pct(lossPct)}</div>
        </div>
      </div>
      <div className="mt-3 flex items-center gap-3 text-xs text-white/60">
        <span>
          R/R <span className="font-mono text-white/80">{fmt(s.rr_ratio, 2)}</span>
        </span>
        <span>
          Confidence{" "}
          <span className="font-mono text-white/80">{(s.confidence * 100).toFixed(0)}%</span>
        </span>
      </div>
      <ul className="mt-3 space-y-1 text-xs text-white/70">
        {s.confirmations.map((c) => (
          <li key={c}>· {c}</li>
        ))}
      </ul>
    </div>
  );
}

function NewsRow({ n }: { n: NewsItem }) {
  return (
    <a
      href={n.url}
      target="_blank"
      rel="noreferrer"
      className="block rounded-lg border border-white/10 bg-white/5 p-4 hover:border-white/20 hover:bg-white/10"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 text-sm font-semibold text-white">{n.title}</div>
        <span
          className={`shrink-0 rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase ${sentStyles[n.sentiment]}`}
        >
          {n.sentiment}
        </span>
      </div>
      {n.summary && <p className="mt-1 line-clamp-2 text-xs text-white/60">{n.summary}</p>}
      <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-white/40">
        <span className="font-mono">{n.source}</span>
        <span>·</span>
        <span>{n.published_at?.slice(0, 16).replace("T", " ") ?? "—"}</span>
        {n.tickers.length > 0 && (
          <>
            <span>·</span>
            {n.tickers.map((t) => (
              <span key={t} className="rounded bg-white/10 px-1.5 py-0.5 font-mono text-white/70">
                {t}
              </span>
            ))}
          </>
        )}
      </div>
    </a>
  );
}

function BacktestTable({ results }: { results: Record<string, BacktestResult[]> }) {
  const rows = useMemo(() => {
    return Object.entries(results)
      .map(([strategy, list]) => {
        const active = list.filter((r) => r.n_trades > 0);
        const totalTrades = active.reduce((a, r) => a + r.n_trades, 0);
        const wr =
          totalTrades > 0
            ? active.reduce((a, r) => a + r.win_rate * r.n_trades, 0) / totalTrades
            : 0;
        const avgR =
          totalTrades > 0 ? active.reduce((a, r) => a + r.avg_r * r.n_trades, 0) / totalTrades : 0;
        const pfs = active.map((r) => r.profit_factor).filter((p) => p < 9999);
        const pf = pfs.length ? pfs.reduce((a, b) => a + b, 0) / pfs.length : null;
        const dd = active.length ? Math.max(...active.map((r) => r.max_dd_r)) : 0;
        return { strategy, activeTickers: active.length, totalTrades, wr, avgR, pf, dd };
      })
      .sort((a, b) => b.avgR - a.avgR);
  }, [results]);

  return (
    <div className="overflow-x-auto rounded-xl border border-white/10 bg-white/5">
      <table className="w-full text-sm">
        <thead className="bg-white/5 text-left text-[10px] uppercase tracking-wide text-white/50">
          <tr>
            <th className="px-4 py-2">Strategy</th>
            <th className="px-4 py-2 text-right">Tickers</th>
            <th className="px-4 py-2 text-right">Trades</th>
            <th className="px-4 py-2 text-right">Win %</th>
            <th className="px-4 py-2 text-right">Avg R</th>
            <th className="px-4 py-2 text-right">Profit Factor</th>
            <th className="px-4 py-2 text-right">Max DD (R)</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {rows.map((r) => (
            <tr key={r.strategy} className="hover:bg-white/5">
              <td className="px-4 py-2 font-mono text-white/90">{r.strategy}</td>
              <td className="px-4 py-2 text-right font-mono text-white/70">{r.activeTickers}</td>
              <td className="px-4 py-2 text-right font-mono text-white/70">{r.totalTrades}</td>
              <td className="px-4 py-2 text-right font-mono">
                {r.totalTrades > 0 ? `${(r.wr * 100).toFixed(1)}%` : "—"}
              </td>
              <td
                className={`px-4 py-2 text-right font-mono ${
                  r.avgR > 0 ? "text-emerald-300" : r.avgR < 0 ? "text-rose-300" : "text-white/40"
                }`}
              >
                {r.totalTrades > 0 ? `${r.avgR >= 0 ? "+" : ""}${r.avgR.toFixed(2)}` : "—"}
              </td>
              <td className="px-4 py-2 text-right font-mono text-white/70">
                {r.pf !== null ? r.pf.toFixed(2) : "∞"}
              </td>
              <td className="px-4 py-2 text-right font-mono text-rose-300/80">
                {r.totalTrades > 0 ? r.dd.toFixed(2) : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Dashboard({
  signals,
  news,
  backtest,
}: {
  signals: Signal[];
  news: NewsItem[];
  backtest: Record<string, BacktestResult[]>;
}) {
  const [tab, setTab] = useState<Tab>("signals");
  const [running, setRunning] = useState(false);

  async function runBacktest() {
    setRunning(true);
    try {
      await fetch("/api/backtest/run", { method: "POST" });
      setTimeout(() => window.location.reload(), 60_000);
    } catch (e) {
      console.error(e);
      setRunning(false);
    }
  }

  return (
    <>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex gap-1 rounded-lg border border-white/10 bg-white/5 p-1">
          {(
            [
              ["signals", `📡 Signals (${signals.length})`],
              ["news", `📰 News (${news.length})`],
              ["backtest", `📊 Backtest`],
            ] as const
          ).map(([k, label]) => (
            <button
              key={k}
              type="button"
              onClick={() => setTab(k)}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${
                tab === k ? "bg-white/15 text-white" : "text-white/60 hover:text-white"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        {tab === "backtest" && (
          <button
            type="button"
            disabled={running}
            onClick={runBacktest}
            className="rounded-md border border-white/15 bg-white/10 px-3 py-1.5 text-sm font-medium text-white hover:bg-white/15 disabled:opacity-50"
          >
            {running ? "Running… (page will reload)" : "▶ Run backtest"}
          </button>
        )}
      </div>

      {tab === "signals" && (
        <>
          {signals.length === 0 ? (
            <div className="rounded-lg border border-white/10 bg-white/5 p-6 text-center text-white/60">
              No open signals. Scheduler runs every 3h.
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              {signals.map((s) => (
                <SignalCard key={s.id} s={s} />
              ))}
            </div>
          )}
        </>
      )}

      {tab === "news" && (
        <>
          {news.length === 0 ? (
            <div className="rounded-lg border border-white/10 bg-white/5 p-6 text-center text-white/60">
              No news yet.
            </div>
          ) : (
            <div className="space-y-3">
              {news.map((n) => (
                <NewsRow key={n.id} n={n} />
              ))}
            </div>
          )}
        </>
      )}

      {tab === "backtest" && (
        <>
          {Object.keys(backtest).length === 0 ? (
            <div className="rounded-lg border border-white/10 bg-white/5 p-6 text-center text-white/60">
              No backtest results yet. Click <strong>▶ Run backtest</strong> above (~60s).
            </div>
          ) : (
            <BacktestTable results={backtest} />
          )}
        </>
      )}
    </>
  );
}
