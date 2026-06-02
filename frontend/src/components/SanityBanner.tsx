import type { SanityFlag, SanitySeverity } from "@/lib/api";

const palette: Record<SanitySeverity, { container: string; badge: string; label: string }> = {
  info: {
    container: "border-sky-700/60 bg-sky-950/60 text-sky-100",
    badge: "border-sky-500 bg-sky-700 text-sky-50",
    label: "Info",
  },
  warning: {
    container: "border-amber-600/70 bg-amber-950/60 text-amber-100",
    badge: "border-amber-500 bg-amber-600 text-amber-50",
    label: "Warning",
  },
  high: {
    container: "border-rose-600/70 bg-rose-950/60 text-rose-100",
    badge: "border-rose-500 bg-rose-700 text-rose-50",
    label: "Critical",
  },
};

const severityRank: Record<SanitySeverity, number> = { info: 0, warning: 1, high: 2 };

export function highestSeverity(flags: SanityFlag[] | undefined | null): SanitySeverity | null {
  if (!flags || flags.length === 0) return null;
  return flags.reduce<SanitySeverity>((acc, f) => {
    return severityRank[f.severity] > severityRank[acc] ? f.severity : acc;
  }, "info");
}

export function SanityBanner({ flags }: { flags?: SanityFlag[] | null }) {
  if (!flags || flags.length === 0) return null;

  // Group by severity, rendered worst-first.
  const sorted = [...flags].sort((a, b) => severityRank[b.severity] - severityRank[a.severity]);
  const top = sorted[0].severity;
  const tone = palette[top];

  return (
    <div
      className={`rounded-lg border px-4 py-3 text-sm shadow-sm ${tone.container}`}
      role="alert"
      data-testid="sanity-banner"
    >
      <div className="mb-2 flex items-center gap-2">
        <span
          className={`rounded border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${tone.badge}`}
        >
          ⚠ Data sanity · {tone.label}
        </span>
        <span className="text-xs opacity-80">
          {sorted.length} {sorted.length === 1 ? "flag" : "flags"} on this bar
        </span>
      </div>
      <ul className="space-y-1.5">
        {sorted.map((f) => {
          const sub = palette[f.severity];
          return (
            <li
              key={`${f.code}-${f.severity}-${f.value ?? ""}-${f.threshold ?? ""}`}
              className="flex items-start gap-2"
            >
              <span
                className={`mt-0.5 rounded border px-1.5 py-0.5 font-mono text-[10px] uppercase ${sub.badge}`}
              >
                {f.severity}
              </span>
              <div className="min-w-0">
                <div className="font-mono text-xs opacity-70">{f.code}</div>
                <div className="text-sm leading-snug">{f.message}</div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export function SanityDot({ flags }: { flags?: SanityFlag[] | null }) {
  const sev = highestSeverity(flags);
  if (!sev || sev === "info") return null;
  const cls =
    sev === "high"
      ? "bg-rose-500 ring-rose-300/40"
      : "bg-amber-400 ring-amber-200/40";
  return (
    <span
      title={`Data sanity: ${sev}`}
      className={`inline-block h-2 w-2 rounded-full ring-2 ${cls}`}
      data-testid="sanity-dot"
    />
  );
}
