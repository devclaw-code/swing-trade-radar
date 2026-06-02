import type { RegimeContext } from "@/lib/api";

function tone(regime: RegimeContext): "favorable" | "cautious" | "unfavorable" {
  const trend = regime.spy_above_200sma && regime.qqq_above_200sma;
  if (trend && regime.vix < 18 && regime.vix_term_structure !== "backwardation") return "favorable";
  if (!trend || regime.vix > 25 || regime.vix_term_structure === "backwardation") return "unfavorable";
  return "cautious";
}

const toneStyles: Record<ReturnType<typeof tone>, string> = {
  favorable: "border-emerald-500/50 bg-emerald-950",
  cautious: "border-amber-500/50 bg-amber-950",
  unfavorable: "border-rose-500/50 bg-rose-950",
};

const toneLabel: Record<ReturnType<typeof tone>, string> = {
  favorable: "Favorable",
  cautious: "Cautious",
  unfavorable: "Unfavorable",
};

const toneBadge: Record<ReturnType<typeof tone>, string> = {
  favorable: "bg-emerald-500 text-emerald-950 border-emerald-400",
  cautious: "bg-amber-500 text-amber-950 border-amber-400",
  unfavorable: "bg-rose-600 text-white border-rose-500",
};

const toneAccent: Record<ReturnType<typeof tone>, string> = {
  favorable: "text-emerald-300",
  cautious: "text-amber-300",
  unfavorable: "text-rose-300",
};

function CheckRow({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <span
        className={`inline-flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-bold ${
          ok ? "bg-emerald-500 text-white" : "bg-rose-500 text-white"
        }`}
        aria-hidden
      >
        {ok ? "✓" : "✕"}
      </span>
      <span className="text-slate-100">{label}</span>
    </div>
  );
}

export function RegimeCard({ regime, asOf }: { regime: RegimeContext; asOf?: string }) {
  const t = tone(regime);
  return (
    <section
      aria-label="Market regime"
      className={`rounded-xl border-2 p-3 shadow-lg sm:p-5 ${toneStyles[t]}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className={`text-[10px] font-semibold uppercase tracking-wider ${toneAccent[t]}`}>
            Market regime
          </div>
          <h2 className="mt-1 text-xl font-bold text-slate-50">
            {regime.regime_verdict.charAt(0).toUpperCase() + regime.regime_verdict.slice(1)}
          </h2>
          {asOf && <div className="mt-0.5 text-xs text-slate-400">As of {asOf}</div>}
        </div>
        <span
          className={`rounded-md border px-2.5 py-1 text-xs font-bold uppercase tracking-wide ${toneBadge[t]}`}
        >
          {toneLabel[t]}
        </span>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-x-6 gap-y-2 sm:grid-cols-4">
        <CheckRow label="SPY > 200-SMA" ok={regime.spy_above_200sma} />
        <CheckRow label="QQQ > 200-SMA" ok={regime.qqq_above_200sma} />
        <div className="text-sm">
          <span className="text-slate-400">VIX </span>
          <span className="font-mono font-semibold text-slate-50">{regime.vix.toFixed(1)}</span>
        </div>
        <div className="text-sm">
          <span className="text-slate-400">Term </span>
          <span className="font-mono font-semibold capitalize text-slate-50">
            {regime.vix_term_structure}
          </span>
        </div>
      </div>
    </section>
  );
}
