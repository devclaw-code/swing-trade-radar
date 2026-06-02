"use client";

import { useEffect, useMemo, useState } from "react";
import useSWR from "swr";
import {
  type FilterMode,
  type FilteredVerdict,
  type LastUpdated,
  type MarginalVerdict,
  type RegimeResponse,
  type Verdict,
  type VerdictKind,
  type VerdictsResponse,
  swrFetcher,
} from "@/lib/api";
import { RegimeCard } from "./RegimeCard";
import { VerdictCard } from "./VerdictCard";

type VerdictFilter = "all" | "BUY" | "WATCH" | "AVOID_NO_SETUP";
type RiskFilter = "all" | "LOW" | "MEDIUM" | "HIGH";

const VERDICT_ORDER: Record<VerdictKind, number> = {
  BUY: 0,
  WATCH: 1,
  AVOID: 2,
  NO_SETUP: 3,
};

const MODE_STORAGE_KEY = "str.mode";

interface Props {
  initialVerdicts: VerdictsResponse;
  initialRegime: RegimeResponse;
  initialUpdated: LastUpdated | null;
}

function pillClass(active: boolean) {
  return `rounded-full border px-3 py-1 text-xs font-semibold transition ${
    active
      ? "border-sky-500 bg-sky-500/20 text-sky-200"
      : "border-slate-700 bg-slate-900 text-slate-400 hover:border-slate-600 hover:bg-slate-800 hover:text-slate-100"
  }`;
}

function matchesVerdictFilter(v: Verdict, f: VerdictFilter): boolean {
  if (f === "all") return true;
  if (f === "AVOID_NO_SETUP") return v.verdict === "AVOID" || v.verdict === "NO_SETUP";
  return v.verdict === f;
}

function MarginalBadge() {
  return (
    <span className="absolute right-2 top-2 z-10 rounded-md border border-amber-500/60 bg-amber-500/20 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-amber-200">
      Marginal
    </span>
  );
}

export function Dashboard({ initialVerdicts, initialRegime, initialUpdated }: Props) {
  // Mode is read from localStorage on mount; default to "all" on the server.
  const [mode, setMode] = useState<FilterMode>("all");
  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(MODE_STORAGE_KEY);
      if (stored === "conservative" || stored === "all") setMode(stored);
    } catch {
      /* ignore */
    }
  }, []);

  const setModePersisted = (m: FilterMode) => {
    setMode(m);
    try {
      window.localStorage.setItem(MODE_STORAGE_KEY, m);
    } catch {
      /* ignore */
    }
  };

  const verdictsUrl =
    mode === "conservative" ? "/api/verdicts?mode=conservative" : "/api/verdicts";

  const { data: verdictsData } = useSWR<VerdictsResponse>(verdictsUrl, swrFetcher, {
    fallbackData: mode === "all" ? initialVerdicts : undefined,
    refreshInterval: 60_000,
    revalidateOnFocus: false,
  });
  const { data: regimeData } = useSWR<RegimeResponse>("/api/regime", swrFetcher, {
    fallbackData: initialRegime,
    refreshInterval: 60_000,
    revalidateOnFocus: false,
  });

  const [verdictFilter, setVerdictFilter] = useState<VerdictFilter>("all");
  const [riskFilter, setRiskFilter] = useState<RiskFilter>("all");
  const [search, setSearch] = useState("");
  const [showFilteredOut, setShowFilteredOut] = useState(false);

  const verdicts = verdictsData?.verdicts ?? [];
  const regime = regimeData ?? initialRegime;
  const asOf = verdictsData?.as_of ?? initialVerdicts.as_of;

  // In conservative mode, the visible grid is passed + marginal.
  // In all mode, it's the full verdicts list.
  const conservative = mode === "conservative" && verdictsData?.mode === "conservative";
  const passed = verdictsData?.passed ?? [];
  const marginal: MarginalVerdict[] = verdictsData?.marginal ?? [];
  const filteredOut: FilteredVerdict[] = verdictsData?.filtered_out ?? [];

  const marginalTickers = useMemo(
    () => new Set(marginal.map((m) => m.verdict.ticker)),
    [marginal],
  );

  const baseList: Verdict[] = useMemo(() => {
    if (conservative) {
      return [...passed, ...marginal.map((m) => m.verdict)];
    }
    return verdicts;
  }, [conservative, passed, marginal, verdicts]);

  const filtered = useMemo(() => {
    const q = search.trim().toUpperCase();
    return baseList
      .filter((v) => matchesVerdictFilter(v, verdictFilter))
      .filter((v) => (riskFilter === "all" ? true : v.risk_tier === riskFilter))
      .filter((v) => (q ? v.ticker.includes(q) : true));
  }, [baseList, verdictFilter, riskFilter, search]);

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      const o = VERDICT_ORDER[a.verdict] - VERDICT_ORDER[b.verdict];
      if (o !== 0) return o;
      if (a.conviction !== b.conviction) return b.conviction - a.conviction;
      return a.ticker.localeCompare(b.ticker);
    });
  }, [filtered]);

  const counts = useMemo(() => {
    const c: Record<VerdictKind, number> = { BUY: 0, WATCH: 0, AVOID: 0, NO_SETUP: 0 };
    for (const v of baseList) c[v.verdict]++;
    return c;
  }, [baseList]);

  return (
    <div className="space-y-6">
      <RegimeCard regime={regime} asOf={asOf} />

      {/* Mode toggle */}
      <div className="flex flex-col gap-2 rounded-lg border border-slate-700/60 bg-slate-900 p-2 sm:flex-row sm:items-center sm:gap-3 sm:p-3">
        <span className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">Mode</span>
        <div className="flex gap-1.5 sm:gap-2">
          <button
            type="button"
            onClick={() => setModePersisted("all")}
            className={pillClass(mode === "all")}
          >
            All trades
          </button>
          <button
            type="button"
            onClick={() => setModePersisted("conservative")}
            className={pillClass(mode === "conservative")}
            title="Stops <8%, R:R ≥2.0, not extended, no near-term earnings, n≥20, avg_R>0"
          >
            Conservative
          </button>
        </div>
        {conservative && (
          <span className="text-[11px] text-slate-400 sm:ml-2">
            <span className="font-mono text-emerald-300">{passed.length}</span> passed ·{" "}
            <span className="font-mono text-amber-300">{marginal.length}</span> marginal ·{" "}
            <span className="font-mono text-slate-500">{filteredOut.length}</span> filtered out
          </span>
        )}
      </div>

      {/* Filter bar */}
      <div className="flex flex-col gap-2 rounded-lg border border-slate-700/60 bg-slate-900 p-2 sm:flex-row sm:flex-wrap sm:items-center sm:gap-3 sm:p-3">
        <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
          <span className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">Verdict</span>
          {(
            [
              ["all", `All (${baseList.length})`],
              ["BUY", `Buy (${counts.BUY})`],
              ["WATCH", `Watch (${counts.WATCH})`],
              ["AVOID_NO_SETUP", `Avoid/None (${counts.AVOID + counts.NO_SETUP})`],
            ] as const
          ).map(([k, label]) => (
            <button
              key={k}
              type="button"
              onClick={() => setVerdictFilter(k)}
              className={pillClass(verdictFilter === k)}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
          <span className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">Risk</span>
          {(["all", "LOW", "MEDIUM", "HIGH"] as const).map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => setRiskFilter(r)}
              className={pillClass(riskFilter === r)}
            >
              {r === "all" ? "All" : r}
            </button>
          ))}
        </div>

        <div className="flex w-full items-center gap-2 sm:ml-auto sm:w-auto">
          <label htmlFor="ticker-search" className="shrink-0 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
            Ticker
          </label>
          <input
            id="ticker-search"
            type="search"
            placeholder="NVDA…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 rounded-md border border-slate-700 bg-slate-950 px-2 py-1 font-mono text-xs uppercase text-slate-100 placeholder:text-slate-600 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500 sm:w-32 sm:flex-none"
          />
        </div>
      </div>

      {/* Grid */}
      {sorted.length === 0 ? (
        <div className="rounded-lg border border-slate-700/60 bg-slate-900 p-10 text-center text-slate-400">
          No verdicts match the current filters.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:gap-5 lg:grid-cols-2 xl:grid-cols-3">
          {sorted.map((v) => (
            <div key={v.ticker} className="relative">
              {conservative && marginalTickers.has(v.ticker) && <MarginalBadge />}
              <VerdictCard v={v} />
            </div>
          ))}
        </div>
      )}

      {/* Filtered-out collapsible (conservative only) */}
      {conservative && filteredOut.length > 0 && (
        <div className="rounded-lg border border-slate-700/60 bg-slate-900">
          <button
            type="button"
            onClick={() => setShowFilteredOut((s) => !s)}
            className="flex w-full items-center justify-between px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-800"
          >
            <span>
              <span className="font-semibold">{filteredOut.length}</span> trades filtered out
            </span>
            <span className="text-slate-500">{showFilteredOut ? "▾ hide" : "▸ show"}</span>
          </button>
          {showFilteredOut && (
            <ul className="divide-y divide-slate-800 border-t border-slate-800">
              {filteredOut.map((f) => (
                <li
                  key={f.verdict.ticker}
                  className="flex flex-col gap-1 px-3 py-2 sm:flex-row sm:items-start sm:gap-4"
                >
                  <span className="font-mono text-sm font-bold text-slate-200 sm:w-20">
                    {f.verdict.ticker}
                  </span>
                  <ul className="flex flex-wrap gap-1.5">
                    {f.reasons.map((r) => (
                      <li
                        key={r.code}
                        className="rounded border border-rose-500/40 bg-rose-950/40 px-1.5 py-0.5 font-mono text-[11px] text-rose-200"
                      >
                        {r.message}
                      </li>
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      <div className="text-right text-[11px] text-slate-500">
        Auto-refresh every 60s · Last server version{" "}
        <span className="font-mono text-slate-400">{initialUpdated?.version ?? 0}</span>
      </div>
    </div>
  );
}
