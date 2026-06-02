import type { ScoreBreakdown, ScoreComponent } from "@/lib/api";

interface Props {
  breakdown: ScoreBreakdown;
  correlationPenalty?: number;
}

const COMPONENT_ORDER: { key: keyof ScoreBreakdown; label: string }[] = [
  { key: "trend_quality", label: "Trend quality" },
  { key: "momentum", label: "Momentum" },
  { key: "mean_reversion", label: "Mean reversion" },
  { key: "risk_reward", label: "Risk / reward" },
  { key: "volatility", label: "Volatility" },
  { key: "earnings_risk", label: "Earnings risk" },
  { key: "historical_reliability", label: "Historical reliability" },
  { key: "extension_risk", label: "Extension risk" },
];

function barColor(v: number): string {
  if (v >= 75) return "bg-emerald-500";
  if (v >= 55) return "bg-lime-500";
  if (v >= 40) return "bg-amber-500";
  if (v >= 25) return "bg-orange-500";
  return "bg-rose-500";
}

function ComponentBar({ label, comp }: { label: string; comp: ScoreComponent }) {
  const pct = Math.max(0, Math.min(100, comp.value));
  return (
    <div className="space-y-1">
      <div className="flex items-baseline justify-between gap-3 text-xs">
        <span className="font-medium text-slate-200">{label}</span>
        <span className="font-mono text-slate-400">
          {comp.value.toFixed(0)}{" "}
          <span className="text-slate-500">· w={(comp.weight * 100).toFixed(0)}%</span>
        </span>
      </div>
      <div className="relative h-2 w-full overflow-hidden rounded-full bg-slate-800">
        <div
          className={`absolute left-0 top-0 h-full rounded-full ${barColor(comp.value)}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {comp.note && <p className="text-[11px] leading-snug text-slate-500">{comp.note}</p>}
    </div>
  );
}

export function ScoreBreakdownCard({ breakdown, correlationPenalty = 0 }: Props) {
  const total = Math.round(breakdown.total);
  const totalColor =
    total >= 70 ? "text-emerald-400" : total >= 50 ? "text-amber-400" : "text-rose-400";

  return (
    <section className="rounded-xl border border-slate-700/60 bg-slate-900 p-4 sm:p-5">
      <header className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-sm font-bold uppercase tracking-wide text-slate-300">
          Score breakdown
        </h2>
        <div className="flex items-baseline gap-2">
          <span className={`font-mono text-3xl font-bold ${totalColor}`}>{total}</span>
          <span className="text-xs text-slate-500">/ 100</span>
          {correlationPenalty > 0 && (
            <span
              className="ml-2 rounded border border-amber-700/60 bg-amber-950/60 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-amber-300"
              title="Points subtracted because this trade correlates highly with a higher-scoring pick in the same run."
            >
              −{correlationPenalty.toFixed(0)} corr
            </span>
          )}
        </div>
      </header>

      <div className="grid gap-3 sm:grid-cols-2">
        {COMPONENT_ORDER.map(({ key, label }) => (
          <ComponentBar key={key} label={label} comp={breakdown[key] as ScoreComponent} />
        ))}
      </div>

      <footer className="mt-4 border-t border-slate-800 pt-3 text-[11px] text-slate-500">
        <span className="font-semibold text-slate-400">Weights:</span>{" "}
        {COMPONENT_ORDER.map(({ key, label }, i) => {
          const w = breakdown.weights[key as string] ?? (breakdown[key] as ScoreComponent).weight;
          return (
            <span key={key as string}>
              {i > 0 && " · "}
              <span className="text-slate-400">{label}</span>{" "}
              <span className="font-mono text-slate-500">{(w * 100).toFixed(0)}%</span>
            </span>
          );
        })}
      </footer>
    </section>
  );
}

/**
 * Compact mini-bars for use inside dashboard rows / hover popovers.
 * Renders just the top 3 contributors and bottom 2 detractors.
 */
export function ScoreBreakdownMini({ breakdown }: { breakdown: ScoreBreakdown }) {
  const items = COMPONENT_ORDER.map(({ key, label }) => ({
    label,
    value: (breakdown[key] as ScoreComponent).value,
  }));
  const sorted = [...items].sort((a, b) => b.value - a.value);
  const top = sorted.slice(0, 3);
  const bottom = sorted.slice(-2).reverse();

  return (
    <div className="space-y-1.5 text-[11px]">
      <div>
        <span className="font-semibold text-emerald-400">Top:</span>{" "}
        {top.map((t, i) => (
          <span key={t.label} className="text-slate-300">
            {i > 0 && ", "}
            {t.label} <span className="font-mono text-slate-400">{t.value.toFixed(0)}</span>
          </span>
        ))}
      </div>
      <div>
        <span className="font-semibold text-rose-400">Drag:</span>{" "}
        {bottom.map((t, i) => (
          <span key={t.label} className="text-slate-300">
            {i > 0 && ", "}
            {t.label} <span className="font-mono text-slate-400">{t.value.toFixed(0)}</span>
          </span>
        ))}
      </div>
    </div>
  );
}
