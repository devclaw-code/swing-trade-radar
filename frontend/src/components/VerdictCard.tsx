"use client";

import Link from "next/link";
import type {
  EvidenceItem,
  HistoricalStatsDisplay,
  Reliability,
  RiskTier,
  ScoreBreakdown,
  Verdict,
  VerdictKind,
} from "@/lib/api";
import { SanityDot } from "./SanityBanner";
import { Sparkline } from "./Sparkline";

const verdictBadge: Record<VerdictKind, string> = {
  BUY: "bg-emerald-600 text-white border-emerald-500 shadow-emerald-500/20 shadow-md",
  WATCH: "bg-amber-500 text-slate-950 border-amber-400 shadow-amber-500/20 shadow-md",
  AVOID: "bg-rose-600 text-white border-rose-500 shadow-rose-500/20 shadow-md",
  NO_SETUP: "bg-slate-700 text-slate-200 border-slate-600",
};

const riskBadge: Record<RiskTier, string> = {
  LOW: "bg-emerald-500/15 text-emerald-300 border-emerald-500/50",
  MEDIUM: "bg-amber-500/15 text-amber-300 border-amber-500/50",
  HIGH: "bg-rose-500/15 text-rose-300 border-rose-500/50",
};

const reliabilityBadge: Record<Reliability, string> = {
  high: "bg-emerald-500/15 text-emerald-300 border-emerald-500/50",
  medium: "bg-amber-500/15 text-amber-300 border-amber-500/50",
  low: "bg-orange-500/15 text-orange-300 border-orange-500/50",
  insufficient: "bg-slate-700/40 text-slate-400 border-slate-600/60",
};

const reliabilityLabel: Record<Reliability, string> = {
  high: "High reliability",
  medium: "Medium reliability",
  low: "Low reliability",
  insufficient: "Insufficient sample",
};

function ReliabilityBadge({
  display,
  prominent,
}: {
  display: HistoricalStatsDisplay;
  prominent: boolean;
}) {
  const tone = reliabilityBadge[display.tier];
  const label = reliabilityLabel[display.tier];
  const sizing = prominent
    ? "px-2.5 py-1 text-xs"
    : "px-2 py-0.5 text-[10px] sm:text-[11px]";
  const title =
    display.tier === "insufficient"
      ? `Only ${display.sample_size} historical occurrences — too few to draw conclusions`
      : `Based on ${display.sample_size} historical occurrences`;
  return (
    <span
      className={`rounded-md border font-semibold uppercase tracking-wide ${tone} ${sizing}`}
      title={title}
    >
      {label}
    </span>
  );
}

function fmt(n: number, d = 2) {
  return n.toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
}
function pct(n: number, d = 2) {
  return `${n >= 0 ? "+" : ""}${(n * 100).toFixed(d)}%`;
}

function ConvictionBar({ value }: { value: number }) {
  const v = Math.max(0, Math.min(1, value));
  // Gradient from emerald -> amber -> rose based on level
  const tone =
    v >= 0.6
      ? "bg-gradient-to-r from-emerald-500 to-emerald-400"
      : v >= 0.35
        ? "bg-gradient-to-r from-amber-500 to-amber-400"
        : "bg-gradient-to-r from-rose-600 to-rose-500";
  const pctVal = Math.round(v * 100);
  return (
    <div className="flex items-center gap-2" title={`Conviction ${pctVal}%`}>
      <div className="h-2 w-24 overflow-hidden rounded-full bg-slate-800 ring-1 ring-slate-700">
        <div className={`h-full ${tone}`} style={{ width: `${v * 100}%` }} />
      </div>
      <span className="font-mono text-xs font-semibold text-slate-300">{pctVal}%</span>
    </div>
  );
}

function ScoreBadge({
  score,
  breakdown,
  correlationPenalty,
}: {
  score: number;
  breakdown: ScoreBreakdown;
  correlationPenalty: number;
}) {
  const items: { label: string; value: number }[] = [
    { label: "Trend", value: breakdown.trend_quality.value },
    { label: "Momentum", value: breakdown.momentum.value },
    { label: "MeanRev", value: breakdown.mean_reversion.value },
    { label: "R/R", value: breakdown.risk_reward.value },
    { label: "Vol", value: breakdown.volatility.value },
    { label: "Earnings", value: breakdown.earnings_risk.value },
    { label: "History", value: breakdown.historical_reliability.value },
    { label: "Extension", value: breakdown.extension_risk.value },
  ];
  const sorted = [...items].sort((a, b) => b.value - a.value);
  const top = sorted.slice(0, 3);
  const bottom = sorted.slice(-2).reverse();
  const tip =
    `Score ${score.toFixed(0)}/100\n` +
    `Top:  ${top.map((t) => `${t.label} ${t.value.toFixed(0)}`).join(", ")}\n` +
    `Drag: ${bottom.map((t) => `${t.label} ${t.value.toFixed(0)}`).join(", ")}` +
    (correlationPenalty > 0 ? `\nCorrelation penalty: −1${correlationPenalty.toFixed(0)}` : "");

  const tone =
    score >= 70
      ? "border-emerald-500/60 bg-emerald-950/60 text-emerald-300"
      : score >= 50
        ? "border-amber-500/60 bg-amber-950/60 text-amber-300"
        : "border-rose-500/60 bg-rose-950/60 text-rose-300";

  return (
    <div
      className={`flex items-center gap-2 rounded-md border ${tone} px-2 py-1.5 text-xs`}
      title={tip}
    >
      <div className="flex items-baseline gap-1">
        <span className="text-[10px] uppercase tracking-wide opacity-70">Score</span>
        <span className="font-mono text-base font-bold">{Math.round(score)}</span>
        <span className="text-[10px] opacity-60">/100</span>
      </div>
      <div className="flex h-3 flex-1 items-center gap-px" aria-hidden>
        {items.map((it) => {
          const h = Math.max(2, Math.min(12, (it.value / 100) * 12));
          const c =
            it.value >= 70
              ? "bg-emerald-400"
              : it.value >= 50
                ? "bg-amber-400"
                : it.value >= 30
                  ? "bg-orange-400"
                  : "bg-rose-400";
          return (
            <span
              key={it.label}
              className={`block w-1.5 rounded-sm ${c}`}
              style={{ height: `${h}px` }}
            />
          );
        })}
      </div>
      {correlationPenalty > 0 && (
        <span className="font-mono text-[10px] text-amber-300" title="Correlation penalty">
          −{correlationPenalty.toFixed(0)}
        </span>
      )}
    </div>
  );
}

function EvidenceRow({ e }: { e: EvidenceItem }) {
  const widthPct = Math.round(Math.min(1, Math.max(0, e.weight)) * 100);
  return (
    <li className="grid grid-cols-1 gap-1 py-1.5 sm:grid-cols-[minmax(0,1fr)_80px_minmax(0,1fr)] sm:items-center sm:gap-3">
      <div className="flex items-center gap-2 text-sm">
        <span
          className={`inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
            e.passed ? "bg-emerald-500 text-white" : "bg-rose-500 text-white"
          }`}
          aria-hidden
        >
          {e.passed ? "✓" : "✕"}
        </span>
        <span className="text-slate-100">{e.factor}</span>
        {e.value && <span className="font-mono text-xs text-slate-400">{e.value}</span>}
      </div>
      <div
        className="hidden h-1.5 overflow-hidden rounded-full bg-slate-800 sm:block"
        title={`weight ${widthPct}%`}
      >
        <div
          className={`h-full ${e.passed ? "bg-sky-400" : "bg-slate-600"}`}
          style={{ width: `${widthPct}%` }}
        />
      </div>
      <div className="pl-6 text-xs text-slate-400 sm:pl-0">{e.note}</div>
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
      className="group rounded-md border border-slate-700/60 bg-slate-900/60 open:bg-slate-900 open:border-slate-600"
      open={defaultOpen}
    >
      <summary
        className={`flex cursor-pointer list-none items-center justify-between gap-2 px-3 py-2 text-xs font-semibold uppercase tracking-wide ${
          tone === "warn" ? "text-amber-300" : "text-slate-300"
        } hover:text-slate-50`}
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
            <span className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] text-slate-200">
              {count}
            </span>
          )}
        </span>
      </summary>
      <div className="border-t border-slate-700/60 px-3 py-3">{children}</div>
    </details>
  );
}

export function VerdictCard({ v, defaultExpanded = false }: { v: Verdict; defaultExpanded?: boolean }) {
  const muted = v.verdict === "AVOID" || v.verdict === "NO_SETUP";
  const isBuy = v.verdict === "BUY";
  const dayChange = v.day_change_pct ?? 0;
  const expanded = defaultExpanded;

  return (
    <article
      className={`flex flex-col rounded-xl border bg-slate-900 shadow-xl transition ${
        isBuy
          ? "border-emerald-500/60 ring-1 ring-emerald-500/30 hover:border-emerald-400"
          : muted
            ? "border-slate-800 opacity-85 hover:opacity-100 hover:border-slate-700"
            : "border-slate-700/60 hover:border-slate-600"
      }`}
    >
      {/* Header */}
      <header className="flex flex-wrap items-start justify-between gap-2 border-b border-slate-700/60 px-3 py-3 sm:gap-3 sm:px-5 sm:py-4">
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <Link
            href={`/ticker/${v.ticker}`}
            className="text-lg font-bold tracking-tight text-slate-50 hover:text-sky-300 sm:text-xl"
          >
            {v.ticker}
          </Link>
          <SanityDot flags={v.sanity_flags} />
          {typeof v.price === "number" && (
            <span className="font-mono text-sm text-slate-100 sm:text-base">${fmt(v.price)}</span>
          )}
          {typeof v.day_change_pct === "number" && (
            <span
              className={`font-mono text-xs font-semibold ${
                dayChange >= 0 ? "text-emerald-400" : "text-rose-400"
              }`}
            >
              {pct(dayChange)}
            </span>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
          {v.historical_stats_display && (
            <ReliabilityBadge display={v.historical_stats_display} prominent={expanded} />
          )}
          <span
            className={`rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase sm:text-[11px] ${riskBadge[v.risk_tier]}`}
          >
            {v.risk_tier}
          </span>
          <span
            className={`rounded-md border px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide sm:px-2.5 sm:py-1 sm:text-xs ${verdictBadge[v.verdict]}`}
          >
            {v.verdict.replace("_", " ")}
          </span>
        </div>
      </header>

      {/* Body */}
      <div className="flex-1 space-y-3 px-3 py-3 sm:px-5 sm:py-4">
        <div className="flex items-center justify-between gap-3">
          <div className="text-xs text-slate-400">
            {v.primary_setup ? (
              <span>
                Setup:{" "}
                <span className="font-medium text-slate-100">{v.primary_setup}</span>
              </span>
            ) : (
              <span className="text-slate-500">No active setup</span>
            )}
          </div>
          <ConvictionBar value={v.conviction} />
        </div>

        {typeof v.score === "number" && v.score_breakdown && (
          <ScoreBadge score={v.score} breakdown={v.score_breakdown} correlationPenalty={v.correlation_penalty ?? 0} />
        )}

        <p className="text-sm leading-snug text-slate-200">{v.why.headline}</p>

        {v.sparkline && v.sparkline.length > 1 && (
          <div className="rounded-md border border-slate-800 bg-slate-950 px-1 py-1">
            <Sparkline values={v.sparkline} positive={dayChange >= 0} />
          </div>
        )}

        {/* Trade params */}
        {(v.entry_zone || v.stop_loss || v.target) && (
          <div className="grid grid-cols-3 gap-x-3 gap-y-2 rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-xs sm:grid-cols-5 sm:gap-x-4">
            <div>
              <div className="text-[10px] uppercase text-slate-500">Entry</div>
              <div className="font-mono text-slate-100">
                {v.entry_zone ? `$${fmt(v.entry_zone.price)}` : "—"}
              </div>
            </div>
            <div>
              <div className="text-[10px] uppercase text-rose-400">Stop</div>
              <div className="font-mono text-rose-300">
                {v.stop_loss ? `$${fmt(v.stop_loss.price)}` : "—"}
              </div>
              {v.stop_loss && (
                <div className="text-[10px] text-rose-400/80">-{v.stop_loss.risk_pct.toFixed(1)}%</div>
              )}
            </div>
            <div>
              <div className="text-[10px] uppercase text-emerald-400">Target</div>
              <div className="font-mono text-emerald-300">
                {v.target ? `$${fmt(v.target.price)}` : "—"}
              </div>
              {v.target && v.entry_zone && v.entry_zone.price > 0 && (
                <div className="text-[10px] text-emerald-400/80">
                  +{(((v.target.price - v.entry_zone.price) / v.entry_zone.price) * 100).toFixed(1)}%
                </div>
              )}
            </div>
            <div>
              <div className="text-[10px] uppercase text-slate-500">R:R</div>
              <div className="font-mono text-slate-100">{v.target ? v.target.rr.toFixed(2) : "—"}</div>
            </div>
            <div className="col-span-2 sm:col-span-1">
              <div className="text-[10px] uppercase text-slate-500">Hold</div>
              <div className="text-slate-200">{v.max_hold ?? "—"}</div>
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
              <div className="mt-3 text-xs text-slate-400">
                <span className="uppercase tracking-wide text-slate-500">Supporting: </span>
                {v.supporting_setups.join(" · ")}
              </div>
            )}
          </Section>

          {v.why.what_could_invalidate.length > 0 && (
            <Section title="What could invalidate" count={v.why.what_could_invalidate.length} defaultOpen={expanded}>
              <ul className="space-y-1 text-sm text-slate-200">
                {v.why.what_could_invalidate.map((x) => (
                  <li key={x} className="flex gap-2">
                    <span className="text-slate-500">·</span>
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
              <ul className="space-y-1 text-sm text-amber-200">
                {v.why.counter_arguments.map((x) => (
                  <li key={x} className="flex gap-2">
                    <span className="text-amber-400">⚠</span>
                    <span>{x}</span>
                  </li>
                ))}
              </ul>
            </Section>
          )}

          {v.why.historical_base_rate && (
            <Section title="Historical base rate" defaultOpen={expanded}>
              {v.historical_stats_display?.tier === "insufficient" ? (
                <p className="text-sm">
                  <span className="inline-flex items-center gap-1 rounded-md border border-slate-600/60 bg-slate-700/40 px-2 py-0.5 text-xs text-slate-400">
                    {v.historical_stats_display.display_text}
                  </span>
                  <span className="ml-2 text-xs text-slate-500">
                    Win rate hidden — too few prior occurrences to be meaningful.
                  </span>
                </p>
              ) : v.historical_stats_display?.tier === "low" ? (
                <p className="text-xs leading-snug text-slate-400">
                  <span className="text-amber-400" title="Based on a small historical sample">⚠</span>{" "}
                  On <span className="font-mono text-slate-300">{v.ticker}</span>, this setup occurred{" "}
                  <span className="font-semibold text-slate-300">
                    {v.why.historical_base_rate.occurrences}
                  </span>{" "}
                  times. Win rate{" "}
                  <span
                    className="font-semibold text-slate-300"
                    title={`Based on only ${v.why.historical_base_rate.occurrences} historical occurrences`}
                  >
                    {(v.why.historical_base_rate.win_rate * 100).toFixed(0)}%
                  </span>
                  . Avg R ={" "}
                  <span className="font-mono font-semibold text-slate-300">
                    {v.why.historical_base_rate.avg_r >= 0 ? "+" : ""}
                    {v.why.historical_base_rate.avg_r.toFixed(2)}
                  </span>
                  . Median hold {v.why.historical_base_rate.median_hold} days.
                </p>
              ) : (
                <p className="text-sm text-slate-200">
                  On <span className="font-mono text-slate-50">{v.ticker}</span>, this setup occurred{" "}
                  <span className="font-semibold text-slate-50">
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
              )}
            </Section>
          )}
          {!v.why.historical_base_rate && v.historical_stats_display?.tier === "insufficient" && (
            <Section title="Historical base rate" defaultOpen={expanded}>
              <p className="text-sm">
                <span className="inline-flex items-center gap-1 rounded-md border border-slate-600/60 bg-slate-700/40 px-2 py-0.5 text-xs text-slate-400">
                  {v.historical_stats_display.display_text}
                </span>
              </p>
            </Section>
          )}
        </div>
      </div>

      {/* Footer doc refs */}
      {v.why.doc_refs.length > 0 && (
        <footer className="border-t border-slate-700/60 px-3 py-2 text-[11px] text-slate-500 sm:px-5">
          <span className="uppercase tracking-wide">Refs: </span>
          {v.why.doc_refs.map((d, i) => (
            <span key={d}>
              {i > 0 && <span className="mx-1 text-slate-700">·</span>}
              <a
                href={`https://github.com/`}
                target="_blank"
                rel="noreferrer"
                className="font-mono text-slate-400 hover:text-sky-300"
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
