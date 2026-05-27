import Link from "next/link";
import { notFound } from "next/navigation";
import { PriceChart } from "@/components/PriceChart";
import {
  type BacktestResult,
  fetchJson,
  type NewsItem,
  type Risk,
  type Signal,
  type TickerDetail,
} from "@/lib/api";

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
          <div className="text-sm font-bold uppercase text-white/70">
            {s.strategy.replace(/_/g, " ")}
          </div>
          <div className="text-xs text-white/40">{s.bar_date}</div>
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
      {s.confirmations.length > 0 && (
        <ul className="mt-3 space-y-1 text-xs text-white/70">
          {s.confirmations.map((c) => (
            <li key={c}>· {c}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function NewsRow({ n }: { n: NewsItem }) {
  return (
    <a
      href={n.url}
      target="_blank"
      rel="noreferrer"
      className="block rounded-lg border border-white/10 bg-white/5 p-3 hover:border-white/20 hover:bg-white/10"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 text-sm font-semibold text-white">{n.title}</div>
        <span
          className={`shrink-0 rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase ${sentStyles[n.sentiment]}`}
        >
          {n.sentiment}
        </span>
      </div>
      <div className="mt-1 flex flex-wrap items-center gap-2 text-[11px] text-white/40">
        <span className="font-mono">{n.source}</span>
        <span>·</span>
        <span>{n.published_at?.slice(0, 16).replace("T", " ") ?? "—"}</span>
      </div>
    </a>
  );
}

function BacktestMiniTable({ rows }: { rows: BacktestResult[] }) {
  if (rows.length === 0) {
    return <div className="text-sm text-white/50">No backtest results yet.</div>;
  }
  const sorted = [...rows].sort((a, b) => b.avg_r - a.avg_r);
  return (
    <div className="overflow-x-auto rounded-xl border border-white/10 bg-white/5">
      <table className="w-full text-sm">
        <thead className="bg-white/5 text-left text-[10px] uppercase tracking-wide text-white/50">
          <tr>
            <th className="px-3 py-2">Strategy</th>
            <th className="px-3 py-2 text-right">Trades</th>
            <th className="px-3 py-2 text-right">Win %</th>
            <th className="px-3 py-2 text-right">Avg R</th>
            <th className="px-3 py-2 text-right">PF</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {sorted.map((r) => (
            <tr key={r.strategy} className="hover:bg-white/5">
              <td className="px-3 py-2 font-mono text-white/90">{r.strategy}</td>
              <td className="px-3 py-2 text-right font-mono text-white/70">{r.n_trades}</td>
              <td className="px-3 py-2 text-right font-mono">
                {r.n_trades > 0 ? `${(r.win_rate * 100).toFixed(0)}%` : "—"}
              </td>
              <td
                className={`px-3 py-2 text-right font-mono ${
                  r.avg_r > 0 ? "text-emerald-300" : r.avg_r < 0 ? "text-rose-300" : "text-white/40"
                }`}
              >
                {r.n_trades > 0 ? `${r.avg_r >= 0 ? "+" : ""}${r.avg_r.toFixed(2)}` : "—"}
              </td>
              <td className="px-3 py-2 text-right font-mono text-white/70">
                {r.profit_factor >= 9999 ? "∞" : r.profit_factor.toFixed(2)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default async function TickerPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol } = await params;
  const sym = symbol.toUpperCase();

  let data: TickerDetail;
  try {
    data = await fetchJson<TickerDetail>(`/api/ticker/${sym}`);
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    if (msg.startsWith("404")) notFound();
    return (
      <main className="min-h-dvh bg-zinc-950 px-6 py-10 text-zinc-100">
        <div className="mx-auto max-w-3xl rounded-lg border border-rose-500/40 bg-rose-500/10 p-4 text-sm text-rose-200">
          Failed to load ticker {sym}: <span className="font-mono">{msg}</span>
        </div>
      </main>
    );
  }

  const bars = data.ohlcv;
  const last = bars.at(-1);
  const prev = bars.at(-2);
  const change = last && prev ? last.close - prev.close : 0;
  const changePct = last && prev ? (last.close - prev.close) / prev.close : 0;
  const up = change >= 0;

  return (
    <main className="min-h-dvh bg-zinc-950 text-zinc-100">
      <header className="border-b border-white/10 px-6 py-4">
        <div className="mx-auto flex max-w-7xl flex-wrap items-end justify-between gap-3">
          <div className="flex items-end gap-4">
            <Link
              href="/"
              className="rounded-md border border-white/15 bg-white/5 px-2 py-1 text-xs text-white/70 hover:bg-white/10"
            >
              ← Back
            </Link>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">{data.ticker}</h1>
              <p className="text-xs text-white/50">
                {bars.length} daily bars · {bars[0]?.date} → {last?.date}
              </p>
            </div>
            {last && (
              <div className="ml-4 flex items-baseline gap-2">
                <span className="font-mono text-2xl font-semibold">{fmt(last.close)}</span>
                <span className={`font-mono text-sm ${up ? "text-emerald-300" : "text-rose-300"}`}>
                  {up ? "▲" : "▼"} {change >= 0 ? "+" : ""}
                  {fmt(change)} ({changePct >= 0 ? "+" : ""}
                  {(changePct * 100).toFixed(2)}%)
                </span>
              </div>
            )}
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-7xl space-y-6 px-6 py-6">
        <div className="rounded-xl border border-white/10 bg-white/5 p-3">
          {bars.length > 0 ? (
            <PriceChart ohlcv={bars} signals={data.signals} />
          ) : (
            <div className="p-6 text-center text-white/60">No price data.</div>
          )}
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-white/60">
              📡 Active signals ({data.signals.length})
            </h2>
            {data.signals.length === 0 ? (
              <div className="rounded-lg border border-white/10 bg-white/5 p-6 text-center text-sm text-white/50">
                No open signals for {data.ticker}.
              </div>
            ) : (
              <div className="space-y-3">
                {data.signals.map((s) => (
                  <SignalCard key={s.id} s={s} />
                ))}
              </div>
            )}
          </div>

          <div className="space-y-6">
            <div>
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-white/60">
                📰 Recent news ({data.news.length})
              </h2>
              {data.news.length === 0 ? (
                <div className="rounded-lg border border-white/10 bg-white/5 p-6 text-center text-sm text-white/50">
                  No news mentions.
                </div>
              ) : (
                <div className="space-y-2">
                  {data.news.slice(0, 15).map((n) => (
                    <NewsRow key={n.id} n={n} />
                  ))}
                </div>
              )}
            </div>

            <div>
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-white/60">
                📊 Backtest by strategy
              </h2>
              <BacktestMiniTable rows={data.backtest} />
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
