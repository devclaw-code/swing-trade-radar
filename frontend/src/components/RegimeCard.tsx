import type { RegimeContext } from "@/lib/api";

function tone(regime: RegimeContext): "favorable" | "cautious" | "unfavorable" {
  const trend = regime.spy_above_200sma && regime.qqq_above_200sma;
  if (trend && regime.vix < 18 && regime.vix_term_structure !== "backwardation") return "favorable";
  if (!trend || regime.vix > 25 || regime.vix_term_structure === "backwardation") return "unfavorable";
  return "cautious";
}

const toneStyles: Record<ReturnType<typeof tone>, string> = {
  favorable: "border-emerald-500/40 bg-emerald-500/10",
  cautious: "border-amber-500/40 bg-amber-500/10",
  unfavorable: "border-rose-500/40 bg-rose-500/10",
};

const toneLabel: Record<ReturnType<typeof tone>, string> = {
  favorable: "Favorable",
  cautious: "Cautious",
  unfavorable: "Unfavorable",
};

const toneBadge: Record<ReturnType<typeof tone>, string> = {
  favorable: "bg-emerald-500/20 text-emerald-200",
  cautious: "bg-amber-500/20 text-amber-200",
  unfavorable: "bg-rose-500/20 text-rose-200",
};

function CheckRow({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <span
        className={`inline-flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-bold ${
          ok ? "bg-emerald-500/30 text-emerald-100" : "bg-rose-500/30 text-rose-100"
        }`}
        aria-hidden
      >
        {ok ? "✓" : "✕"}
      </span>
      <span className="text-white/80">{label}</span>
    </div>
  );
}

export function RegimeCard({ regime, asOf }: { regime: RegimeContext; asOf?: string }) {
  const t = tone(regime);
  return (
    <section
      aria-label="Market regime"
      className={`rounded-xl border p-5 backdrop-blur ${toneStyles[t]}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-white/50">Market regime</div>
          <h2 className="mt-1 text-xl font-semibold text-white">
            {regime.regime_verdict.charAt(0).toUpperCase() + regime.regime_verdict.slice(1)}
          </h2>
          {asOf && <div className="mt-0.5 text-xs text-white/50">As of {asOf}</div>}
        </div>
        <span
          className={`rounded-md px-2.5 py-1 text-xs font-semibold uppercase ${toneBadge[t]}`}
        >
          {toneLabel[t]}
        </span>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-x-6 gap-y-2 sm:grid-cols-4">
        <CheckRow label="SPY > 200-SMA" ok={regime.spy_above_200sma} />
        <CheckRow label="QQQ > 200-SMA" ok={regime.qqq_above_200sma} />
        <div className="text-sm">
          <span className="text-white/60">VIX </span>
          <span className="font-mono font-semibold text-white">{regime.vix.toFixed(1)}</span>
        </div>
        <div className="text-sm">
          <span className="text-white/60">Term </span>
          <span className="font-mono font-semibold text-white capitalize">
            {regime.vix_term_structure}
          </span>
        </div>
      </div>
    </section>
  );
}
