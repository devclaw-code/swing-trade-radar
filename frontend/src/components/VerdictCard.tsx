"use client";

import Link from "next/link";
import type { EvidenceItem, RiskTier, Verdict, VerdictKind } from "@/lib/api";
import { Sparkline } from "./Sparkline";

const verdictBadge: Record<VerdictKind, string> = {
  BUY: "bg-emerald-500/20 text-emerald-200 border-emerald-500/40",
  WATCH: "bg-amber-500/20 text-amber-200 border-amber-500/40",
  AVOID: "bg-rose-500/20 text-rose-200 border-rose-500/40",
  NO_SETUP: "bg-white/10 text-white/60 border-white/15",
};

const riskBadge: Record<RiskTier, string> = {
  LOW: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
  MEDIUM: "bg-amber-500/15 text-amber-300 border-amber-500/40",
  HIGH: "bg-rose-500/15 text-rose-300 border-rose-500/40",
};

function fmt(n: number, d = 2) {
  return n.toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
}
function pct(n: number, d = 2) {
  return `${n >= 0 ? "+" : ""}${(n * 100).toFixed(d)}%`;
}

function ConvictionBar({ value }: { value: number }) {
  const v = Math.max(0, Math.min(1, value));
  const tone =
    v >= 0.6 ? "bg-emerald-400" : v >= 0.35 ? "bg-amber-400" : "bg-white/30";
  const pctVal = Math.round(v * 100);
  return (
    <div className="flex items-center gap-2" title={`Conviction ${pctVal}%`}>
      <div
        className="h-1.5 w-24 overflow-hidden rounded-full bg-white/10"
      >
        <div className={`h-full ${tone}`} style={{ width: `${v * 100}%` }} />
      </div>
      <span className="font-mono text-xs text-white/70">{pctVal}%</span>
    </div>
  );
}

function EvidenceRow({ e }: { e: EvidenceItem }) {
  const widthPct = Math.round(Math.min(1, Math.max(0, e.weight)) * 100);
  return (
    <li className="grid grid-cols-[minmax(0,1fr)_80px_minmax(0,1fr)] items-center gap-3 py-1.5">
      <div className="flex items-center gap-2 text-sm">
        <span
          className={`inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
            e.passed ? "bg-emerald-500/30 text-emerald-100" : "bg-rose-500/30 text-rose-100"
          }`}
          aria-hidden
        >
          {e.passed ? "✓" : "✕"}
        </span>
        <span className="text-white/85">{e.factor}</span>
        {e.value && <span className="font-mono text-xs text-white/50">{e.value}</span>}
      </div>
      <div
        className="h-1.5 overflow-hidden rounded-full bg-white/5"
        title={`weight ${widthPct}%`}
      >
        <div
          className={`h-full ${e.passed ? "bg-sky-400/70" : "bg-white/20"}`}
          style={{ width: `${widthPct}%` }}
        />
      </div>
      <div className="text-xs text-white/60">{e.note}</div>
    </li>
  );
}

function Section({
  title,
  count,
  children,
  defaultOpen = false,
  tone = "default",
}: {
  title: string;
  count?: number;
  children: React.ReactNode;
  defaultOpen?: boolean;
  tone?: "default" | "warn";
}) {
  return (
    <details
      className="group rounded-md border border-white/10 bg-white/[0.02] open:bg-white/[0.04]"
      open={defaultOpen}
    >
      <summary
        className={`flex cursor-pointer list-none items-center justify-between gap-2 px-3 py-2 text-xs font-semibold uppercase tracking-wide ${
          tone === "warn" ? "text-amber-200/90" : "text-white/70"
        } hover:text-white`}
      >
        <span className="flex items-center gap-2">
          <span
            className="inline-block h-3 w-3 transition-transform group-open:rotate-90"
            aria-hidden
          >
            ▶
          </span>
          {title}
          {typeof count === "number" && (
            <span className="rounded bg-white/10 px-1.5 py-0.5 font-mono text-[10px]">{count}</span>
          )}
        </span>
      </summary>
      <div className="border-t border-white/5 px-3 py-3">{children}</div>
    </details>
  );
}

export function VerdictCard({ v, defaultExpanded = false }: { v: Verdict; defaultExpanded?: boolean }) {
  const muted = v.verdict === "AVOID" || v.verdict === "NO_SETUP";
  const dayChange = v.day_change_pct ?? 0;
  const expanded = defaultExpanded;

  return (
    <article
      className={`flex flex-col rounded-xl border bg-white/[0.04] shadow-lg backdrop-blur transition ${
        muted ? "border-white/10 opacity-80 hover:opacity-100" : "border-white/10 hover:border-white/20"
      }`}
    >
      {/* Header */}
      <header className="flex flex-wrap items-start justify-between gap-3 border-b border-white/5 px-5 py-4">
        <div className="flex items-baseline gap-3">
          <Link
            href={`/ticker/${v.ticker}`}
            className="text-xl font-bold tracking-tight text-white hover:text-sky-300"
          >
            {v.ticker}
          </Link>
          {typeof v.price === "number" && (
            <span className="font-mono text-base text-white/85">${fmt(v.price)}</span>
          )}
          {typeof v.day_change_pct === "number" && (
            <span
              className={`font-mono text-xs ${
                dayChange >= 0 ? "text-emerald-300" : "text-rose-300"
              }`}
            >
              {pct(dayChange)}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`rounded-md border px-2 py-0.5 text-[11px] font-semibold uppercase ${riskBadge[v.risk_tier]}`}
          >
            {v.risk_tier}
          </span>
          <span
            className={`rounded-md border px-2.5 py-1 text-xs font-bold uppercase ${verdictBadge[v.verdict]}`}
          >
            {v.verdict.replace("_", " ")}
          </span>
        </div>
      </header>

      {/* Body */}
      <div className="flex-1 space-y-3 px-5 py-4">
        <div className="flex items-center justify-between gap-3">
          <div className="text-xs text-white/55">
            {v.primary_setup ? (
              <span>
                Setup:{" "}
                <span className="font-medium text-white/85">{v.primary_setup}</span>
              </span>
            ) : (
              <span className="text-white/40">No active setup</span>
            )}
          </div>
          <ConvictionBar value={v.conviction} />
        </div>

        <p className="text-sm leading-snug text-white/80">{v.why.headline}</p>

        {v.sparkline && v.sparkline.length > 1 && (
          <div className="rounded-md bg-white/[0.02] px-1 py-1">
            <Sparkline values={v.sparkline} positive={dayChange >= 0} />
          </div>
        )}

        {/* Trade params */}
        {(v.entry_zone || v.stop_loss || v.target) && (
          <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 rounded-md bg-white/[0.02] px-3 py-2 text-xs sm:grid-cols-5">
            <div>
              <div className="text-[10px] uppercase text-white/40">Entry</div>
              <div className="font-mono text-white/90">
                {v.entry_zone ? `$${fmt(v.entry_zone.price)}` : "—"}
              </div>
            </div>
            <div>
              <div className="text-[10px] uppercase text-rose-300/70">Stop</div>
              <div className="font-mono text-rose-300">
                {v.stop_loss ? `$${fmt(v.stop_loss.price)}` : "—"}
              </div>
              {v.stop_loss && (
                <div className="text-[10px] text-rose-300/70">-{v.stop_loss.risk_pct.toFixed(1)}%</div>
              )}
            </div>
            <div>
              <div className="text-[10px] uppercase text-emerald-300/70">Target</div>
              <div className="font-mono text-emerald-300">
                {v.target ? `$${fmt(v.target.price)}` : "—"}
              </div>
            </div>
            <div>
              <div className="text-[10px] uppercase text-white/40">R:R</div>
              <div className="font-mono text-white/85">{v.target ? v.target.rr.toFixed(2) : "—"}</div>
            </div>
            <div className="col-span-2 sm:col-span-1">
              <div className="text-[10px] uppercase text-white/40">Hold</div>
              <div className="text-white/80">{v.max_hold ?? "—"}</div>
            </div>
          </div>
        )}

        {/* Collapsible sections */}
        <div className="space-y-2 pt-1">
          <Section title="Why this trade" count={v.why.evidence.length} defaultOpen={expanded || (!muted && v.verdict === "BUY")}>
            <ul className="space-y-1">
              {v.why.evidence.map((e) => (
                <EvidenceRow key={e.factor} e={e} />
              ))}
            </ul>
            {v.supporting_setups.length > 0 && (
              <div className="mt-3 text-xs text-white/55">
                <span className="uppercase tracking-wide text-white/40">Supporting: </span>
                {v.supporting_setups.join(" · ")}
              </div>
            )}
          </Section>

          {v.why.what_could_invalidate.length > 0 && (
            <Section title="What could invalidate" count={v.why.what_could_invalidate.length} defaultOpen={expanded}>
              <ul className="space-y-1 text-sm text-white/80">
                {v.why.what_could_invalidate.map((x) => (
                  <li key={x} className="flex gap-2">
                    <span className="text-white/30">·</span>
                    <span>{x}</span>
                  </li>
                ))}
              </ul>
            </Section>
          )}

          {v.why.counter_arguments.length > 0 && (
            <Section
              title="Counter-arguments"
              count={v.why.counter_arguments.length}
              defaultOpen={expanded}
              tone="warn"
            >
              <ul className="space-y-1 text-sm text-amber-100/80">
                {v.why.counter_arguments.map((x) => (
                  <li key={x} className="flex gap-2">
                    <span className="text-amber-300/50">⚠</span>
                    <span>{x}</span>
                  </li>
                ))}
              </ul>
            </Section>
          )}

          {v.why.historical_base_rate && (
            <Section title="Historical base rate" defaultOpen={expanded}>
              <p className="text-sm text-white/80">
                On <span className="font-mono text-white">{v.ticker}</span>, this setup occurred{" "}
                <span className="font-semibold text-white">
                  {v.why.historical_base_rate.occurrences}
                </span>{" "}
                times. Win rate{" "}
                <span className="font-semibold text-emerald-300">
                  {(v.why.historical_base_rate.win_rate * 100).toFixed(0)}%
                </span>
                . Avg R ={" "}
                <span
                  className={`font-mono font-semibold ${
                    v.why.historical_base_rate.avg_r >= 0 ? "text-emerald-300" : "text-rose-300"
                  }`}
                >
                  {v.why.historical_base_rate.avg_r >= 0 ? "+" : ""}
                  {v.why.historical_base_rate.avg_r.toFixed(2)}
                </span>
                . Median hold {v.why.historical_base_rate.median_hold} days.
              </p>
            </Section>
          )}
        </div>
      </div>

      {/* Footer doc refs */}
      {v.why.doc_refs.length > 0 && (
        <footer className="border-t border-white/5 px-5 py-2 text-[11px] text-white/40">
          <span className="uppercase tracking-wide">Refs: </span>
          {v.why.doc_refs.map((d, i) => (
            <span key={d}>
              {i > 0 && <span className="mx-1 text-white/20">·</span>}
              <a
                href={`https://github.com/`}
                target="_blank"
                rel="noreferrer"
                className="font-mono text-white/55 hover:text-sky-300"
                title={d}
              >
                {d}
              </a>
            </span>
          ))}
        </footer>
      )}
    </article>
  );
}
