"use client";

import Link from "next/link";
import type { TacticalCard as TacticalCardType } from "@/lib/api";

const riskBadge: Record<string, string> = {
  LOW: "bg-emerald-500/15 text-emerald-300 border-emerald-500/50",
  MEDIUM: "bg-amber-500/15 text-amber-300 border-amber-500/50",
  HIGH: "bg-rose-500/15 text-rose-300 border-rose-500/50",
};

function fmt(n: number | null | undefined, d = 2) {
  if (typeof n !== "number") return "—";
  return n.toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
}

// Price with `$` prefix only when numeric; bare em-dash otherwise.
function price(n: number | null | undefined) {
  return typeof n === "number" ? `$${fmt(n)}` : "—";
}

export function TacticalCard({ c }: { c: TacticalCardType }) {
  const entry = c.entry_zone?.price;
  const stop = c.stop_loss?.price;
  const target = c.target?.price;
  const rr = c.target?.rr;
  return (
    <div className="flex flex-col gap-3 rounded-xl border border-slate-700/60 bg-slate-900 p-4 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Link
          href={`/ticker/${c.ticker}`}
          className="font-mono text-lg font-bold text-slate-100 hover:text-sky-300"
        >
          {c.ticker}
        </Link>
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="rounded-md border border-sky-500/50 bg-sky-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-sky-300">
            Tactical
          </span>
          {typeof c.volatility_atr === "number" && (
            <span
              className="rounded-md border border-slate-600/60 bg-slate-800/60 px-2 py-0.5 font-mono text-[10px] text-slate-300"
              title="Daily ATR(14)"
            >
              ATR {fmt(c.volatility_atr)}
            </span>
          )}
          <span
            className={`rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase ${
              riskBadge[c.risk_tier] ?? riskBadge.MEDIUM
            }`}
          >
            {c.risk_tier}
          </span>
        </div>
      </div>

      <div>
        <div className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
          {c.setup_name}
        </div>
        <p className="mt-0.5 text-sm text-slate-300">{c.headline}</p>
      </div>

      <div className="grid grid-cols-3 gap-2 rounded-lg border border-slate-800 bg-slate-950/60 p-2 font-mono text-xs">
        <div>
          <div className="text-[9px] uppercase text-slate-500">
            Entry{c.entry_zone?.type === "stop" ? " (stop)" : ""}
          </div>
          <div className="text-slate-100">{price(entry)}</div>
        </div>
        <div>
          <div className="text-[9px] uppercase text-slate-500">Stop</div>
          <div className="text-rose-300">{price(stop)}</div>
        </div>
        <div>
          <div className="text-[9px] uppercase text-slate-500">
            Target{typeof rr === "number" ? ` · ${rr.toFixed(1)}R` : ""}
          </div>
          <div className="text-emerald-300">{price(target)}</div>
        </div>
      </div>

      <div className="flex items-center justify-between text-[11px] text-slate-500">
        <span>{c.max_hold}</span>
        <span className="font-mono">score {(c.score * 100).toFixed(0)}</span>
      </div>
    </div>
  );
}
