import Link from "next/link";
import { notFound } from "next/navigation";
import { RegimeCard } from "@/components/RegimeCard";
import { SanityBanner } from "@/components/SanityBanner";
import { ScoreBreakdownCard } from "@/components/ScoreBreakdownCard";
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
        <div className="rounded-lg border border-rose-500/60 bg-rose-950 p-4 text-sm text-rose-200">
          Failed to load ticker {sym}: <span className="font-mono text-rose-300">{msg}</span>
        </div>
      </section>
    );
  }

  const strategies = await getStrategies().catch(() => null);

  return (
    <>
      <header className="border-b border-slate-700/60 bg-slate-900 px-4 py-4 sm:px-6 sm:py-5">
        <div className="mx-auto flex max-w-6xl flex-wrap items-end justify-between gap-3">
          <div className="flex flex-wrap items-end gap-3 sm:gap-4">
            <Link
              href="/"
              className="rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-xs font-medium text-slate-200 transition hover:border-slate-600 hover:bg-slate-700 hover:text-slate-50"
            >
              ← Back
            </Link>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-50 sm:text-3xl">
                {verdict.ticker}
              </h1>
              <p className="text-xs text-slate-400">As of {verdict.as_of}</p>
            </div>
            {typeof verdict.price === "number" && (
              <div className="flex items-baseline gap-2 sm:ml-4">
                <span className="font-mono text-xl font-semibold text-slate-50 sm:text-2xl">
                  ${fmt(verdict.price)}
                </span>
                {typeof verdict.day_change_pct === "number" && (
                  <span
                    className={`font-mono text-sm font-semibold ${
                      verdict.day_change_pct >= 0 ? "text-emerald-400" : "text-rose-400"
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

      <section className="mx-auto max-w-6xl space-y-6 px-3 py-4 sm:px-6 sm:py-6">
        <SanityBanner flags={verdict.sanity_flags} />
        <RegimeCard regime={verdict.regime_context} asOf={verdict.as_of} />

        <VerdictCard v={verdict} defaultExpanded />

        {verdict.score_breakdown && (
          <ScoreBreakdownCard
            breakdown={verdict.score_breakdown}
            correlationPenalty={verdict.correlation_penalty ?? 0}
          />
        )}

        {/* Strategy evaluation table */}
        {strategies && (
          <div>
            <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-slate-300">
              Strategy evaluation for {verdict.ticker}
            </h2>
            <div className="overflow-x-auto rounded-xl border border-slate-700/60 bg-slate-900">
              <table className="w-full text-sm">
                <thead className="border-b border-slate-700/60 bg-slate-950 text-left text-[10px] font-semibold uppercase tracking-wide text-slate-400">
                  <tr>
                    <th className="px-4 py-2">Strategy</th>
                    <th className="px-4 py-2">Status</th>
                    <th className="px-4 py-2">Reason</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {strategies.strategies.map((s) => {
                    const fired =
                      verdict.primary_setup === s.name ||
                      verdict.supporting_setups.some((x) =>
                        x.toLowerCase().includes(s.name.toLowerCase().split(" ")[0]),
                      );
                    return (
                      <tr key={s.id} className="hover:bg-slate-800/50">
                        <td className="px-4 py-2 font-mono text-slate-100">
                          {s.id} · {s.name}
                        </td>
                        <td className="px-4 py-2">
                          {fired ? (
                            <span className="rounded border border-emerald-500 bg-emerald-600 px-2 py-0.5 text-xs font-bold uppercase text-white">
                              Fired
                            </span>
                          ) : (
                            <span className="rounded border border-slate-600 bg-slate-700 px-2 py-0.5 text-xs font-semibold uppercase text-slate-300">
                              No fire
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-2 text-xs text-slate-300">
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
          <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-slate-300">
            Past 30 days
          </h2>
          <div className="rounded-lg border border-dashed border-slate-700 bg-slate-900/50 p-6 text-center text-sm text-slate-500">
            Verdict history endpoint not wired yet. Will render a 30-day timeline of BUY/WATCH/AVOID
            calls with realized R per closed trade once the backend exposes{" "}
            <code className="font-mono text-slate-300">/api/verdicts/{`{ticker}`}/history</code>.
          </div>
        </div>
      </section>
    </>
  );
}
