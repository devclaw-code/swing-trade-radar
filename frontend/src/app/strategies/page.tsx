import { getStrategies } from "@/lib/api";

export const metadata = {
  title: "Strategies",
  description: "The five strategies powering Swing Trade Radar verdicts, with backtest stats.",
};

function fmtPct(n: number, d = 1) {
  return `${(n * 100).toFixed(d)}%`;
}
function fmtSigned(n: number, d = 2) {
  return `${n >= 0 ? "+" : ""}${n.toFixed(d)}`;
}

function StatBox({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: string;
  tone?: "default" | "good" | "bad";
}) {
  const cls =
    tone === "good"
      ? "text-emerald-300"
      : tone === "bad"
        ? "text-rose-300"
        : "text-slate-50";
  return (
    <div className="rounded-md border border-slate-700/60 bg-slate-950 px-3 py-2">
      <div className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-0.5 font-mono text-sm font-semibold ${cls}`}>{value}</div>
    </div>
  );
}

export default async function StrategiesPage() {
  let payload: Awaited<ReturnType<typeof getStrategies>> = { count: 0, strategies: [] };
  let error: string | null = null;
  try {
    payload = await getStrategies();
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }

  return (
    <>
      <header className="border-b border-slate-700/60 bg-slate-900 px-6 py-5">
        <div className="mx-auto max-w-5xl">
          <h1 className="text-2xl font-bold tracking-tight text-slate-50">Strategies</h1>
          <p className="text-sm text-slate-400">
            Each verdict is the synthesis of these five rule-based strategies. Each must pass a
            walk-forward backtest with deflated Sharpe ≥ 1.0 before going live.
          </p>
        </div>
      </header>

      <section className="mx-auto max-w-5xl space-y-5 px-6 py-6">
        {error && (
          <div className="rounded-lg border border-rose-500/60 bg-rose-950 p-3 text-sm text-rose-200">
            {error}
          </div>
        )}

        {payload.strategies.map((s) => (
          <article
            key={s.id}
            className="rounded-xl border border-slate-700/60 bg-slate-900 p-5 shadow-lg transition hover:border-slate-600"
          >
            <header className="flex flex-wrap items-baseline justify-between gap-3">
              <h2 className="text-lg font-bold text-slate-50">
                <span className="font-mono text-slate-500">{s.id}</span> · {s.name}
              </h2>
              <div className="text-[11px] text-slate-500">
                {s.doc_refs.map((d, i) => (
                  <span key={d}>
                    {i > 0 && <span className="mx-1 text-slate-700">·</span>}
                    <span className="font-mono">{d}</span>
                  </span>
                ))}
              </div>
            </header>

            <p className="mt-2 text-sm leading-relaxed text-slate-200">{s.description}</p>

            {s.backtest ? (
              <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-7">
                <StatBox label="Sharpe" value={s.backtest.sharpe.toFixed(2)} />
                <StatBox
                  label="Deflated Sharpe"
                  value={s.backtest.deflated_sharpe.toFixed(2)}
                  tone={s.backtest.deflated_sharpe >= 1 ? "good" : "bad"}
                />
                <StatBox label="Win rate" value={fmtPct(s.backtest.win_rate, 0)} />
                <StatBox
                  label="Avg R"
                  value={fmtSigned(s.backtest.avg_r)}
                  tone={s.backtest.avg_r >= 0 ? "good" : "bad"}
                />
                <StatBox label="Profit factor" value={s.backtest.profit_factor.toFixed(2)} />
                <StatBox label="Max DD (R)" value={s.backtest.max_dd_r.toFixed(2)} tone="bad" />
                <StatBox label="Trades" value={String(s.backtest.n_trades)} />
              </div>
            ) : (
              <div className="mt-3 text-xs text-slate-500">No backtest results yet.</div>
            )}
          </article>
        ))}
      </section>
    </>
  );
}
