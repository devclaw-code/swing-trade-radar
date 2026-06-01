import Link from "next/link";
import { notFound } from "next/navigation";
import { RegimeCard } from "@/components/RegimeCard";
import { VerdictCard } from "@/components/VerdictCard";
import { getStrategies, getVerdict, type Verdict } from "@/lib/api";

function fmt(n: number, d = 2) {
  return n.toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
}

export default async function TickerPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol } = await params;
  const sym = symbol.toUpperCase();

  let verdict: Verdict;
  try {
    verdict = await getVerdict(sym);
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    if (msg.startsWith("404")) notFound();
    return (
      <section className="mx-auto max-w-3xl px-6 py-10">
        <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 p-4 text-sm text-rose-200">
          Failed to load ticker {sym}: <span className="font-mono">{msg}</span>
        </div>
      </section>
    );
  }

  const strategies = await getStrategies().catch(() => null);

  return (
    <>
      <header className="border-b border-white/10 px-6 py-5">
        <div className="mx-auto flex max-w-6xl flex-wrap items-end justify-between gap-3">
          <div className="flex items-end gap-4">
            <Link
              href="/"
              className="rounded-md border border-white/15 bg-white/5 px-2 py-1 text-xs text-white/70 hover:bg-white/10"
            >
              ← Back
            </Link>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">{verdict.ticker}</h1>
              <p className="text-xs text-white/50">As of {verdict.as_of}</p>
            </div>
            {typeof verdict.price === "number" && (
              <div className="ml-4 flex items-baseline gap-2">
                <span className="font-mono text-2xl font-semibold">${fmt(verdict.price)}</span>
                {typeof verdict.day_change_pct === "number" && (
                  <span
                    className={`font-mono text-sm ${
                      verdict.day_change_pct >= 0 ? "text-emerald-300" : "text-rose-300"
                    }`}
                  >
                    {verdict.day_change_pct >= 0 ? "▲ +" : "▼ "}
                    {(verdict.day_change_pct * 100).toFixed(2)}%
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-6xl space-y-6 px-6 py-6">
        <RegimeCard regime={verdict.regime_context} asOf={verdict.as_of} />

        <VerdictCard v={verdict} defaultExpanded />

        {/* Strategy evaluation table */}
        {strategies && (
          <div>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-white/60">
              Strategy evaluation for {verdict.ticker}
            </h2>
            <div className="overflow-x-auto rounded-xl border border-white/10 bg-white/5">
              <table className="w-full text-sm">
                <thead className="bg-white/5 text-left text-[10px] uppercase tracking-wide text-white/50">
                  <tr>
                    <th className="px-4 py-2">Strategy</th>
                    <th className="px-4 py-2">Status</th>
                    <th className="px-4 py-2">Reason</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {strategies.strategies.map((s) => {
                    const fired =
                      verdict.primary_setup === s.name ||
                      verdict.supporting_setups.some((x) => x.toLowerCase().includes(s.name.toLowerCase().split(" ")[0]));
                    return (
                      <tr key={s.id}>
                        <td className="px-4 py-2 font-mono text-white/85">
                          {s.id} · {s.name}
                        </td>
                        <td className="px-4 py-2">
                          {fired ? (
                            <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-xs font-semibold text-emerald-200">
                              Fired
                            </span>
                          ) : (
                            <span className="rounded bg-white/10 px-2 py-0.5 text-xs text-white/55">
                              No fire
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-2 text-xs text-white/65">
                          {fired
                            ? "Conditions met — see Why panel above."
                            : verdict.verdict === "NO_SETUP" || verdict.verdict === "AVOID"
                              ? "One or more entry conditions failed."
                              : "Did not fire on this bar (other strategy is primary)."}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Past 30-day verdict history (placeholder) */}
        <div>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-white/60">
            Past 30 days
          </h2>
          <div className="rounded-lg border border-dashed border-white/10 bg-white/[0.02] p-6 text-center text-sm text-white/45">
            Verdict history endpoint not wired yet. Will render a 30-day timeline of BUY/WATCH/AVOID
            calls with realized R per closed trade once the backend exposes{" "}
            <code className="font-mono text-white/60">/api/verdicts/{`{ticker}`}/history</code>.
          </div>
        </div>
      </section>
    </>
  );
}
