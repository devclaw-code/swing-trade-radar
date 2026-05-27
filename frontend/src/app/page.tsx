import type { Signal } from "@/lib/api";
import { fetchJson, type LastUpdated, type SignalsResponse } from "@/lib/api";

const riskStyles: Record<Signal["risk"], string> = {
  LOW: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
  MED: "bg-amber-500/15 text-amber-300 border-amber-500/40",
  HIGH: "bg-rose-500/15 text-rose-300 border-rose-500/40",
};

const riskLabel: Record<Signal["risk"], string> = {
  LOW: "🟢 LOW",
  MED: "🟡 MEDIUM",
  HIGH: "🔴 HIGH",
};

function fmt(n: number, d = 2): string {
  return n.toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
}

function pct(n: number, d = 2): string {
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

export default async function Home() {
  let signals: Signal[] = [];
  let updated: LastUpdated | null = null;
  let error: string | null = null;

  try {
    const [sigsRes, upd] = await Promise.all([
      fetchJson<SignalsResponse>("/api/strategies"),
      fetchJson<LastUpdated>("/api/last-updated"),
    ]);
    signals = sigsRes.signals;
    updated = upd;
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }

  return (
    <main className="min-h-dvh bg-zinc-950 text-zinc-100">
      <header className="border-b border-white/10 px-6 py-4">
        <div className="mx-auto flex max-w-7xl flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">📡 NASDAQ-100 Swing Trade Radar</h1>
            <p className="text-sm text-white/50">
              Educational signals — not financial advice. Paper-trade only.
            </p>
          </div>
          <div className="text-right text-xs text-white/50">
            <div>
              Last update: <span className="font-mono">{updated?.ts ?? "—"}</span>
            </div>
            <div>
              Version: <span className="font-mono">{updated?.version ?? 0}</span> · Errors:{" "}
              <span className="font-mono">{updated?.errors ?? 0}</span>
            </div>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-6 py-6">
        {error && (
          <div className="mb-4 rounded-lg border border-rose-500/40 bg-rose-500/10 p-3 text-sm text-rose-200">
            Backend unreachable: <span className="font-mono">{error}</span> — is the FastAPI server
            running on <code>:8000</code>?
          </div>
        )}

        {signals.length === 0 && !error && (
          <div className="rounded-lg border border-white/10 bg-white/5 p-6 text-center text-white/60">
            No open signals yet. Scheduler runs every 3h; the boot-refresh may still be fetching
            data.
          </div>
        )}

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {signals.map((s) => (
            <SignalCard key={s.id} s={s} />
          ))}
        </div>
      </section>

      <footer className="mt-6 border-t border-white/10 px-6 py-4 text-center text-xs text-white/40">
        Swing Trade Radar v0.1 · Built with Next.js + FastAPI
      </footer>
    </main>
  );
}
