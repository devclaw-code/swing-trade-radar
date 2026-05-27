"use client";

import { useEffect, useState } from "react";
import type { LastUpdated } from "@/lib/api";
import { fetchJson } from "@/lib/api";

export function AutoRefreshBadge({ initial }: { initial: LastUpdated | null }) {
  const [updated, setUpdated] = useState<LastUpdated | null>(initial);
  const [stale, setStale] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const tick = async () => {
      try {
        const next = await fetchJson<LastUpdated>("/api/last-updated");
        if (cancelled) return;
        if (initial && next.version > initial.version) setStale(true);
        setUpdated(next);
      } catch {
        // ignore polling errors
      }
    };
    const id = setInterval(tick, 30_000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [initial]);

  return (
    <div className="text-right text-xs text-white/50">
      <div>
        Last update: <span className="font-mono">{updated?.ts ?? "—"}</span>
      </div>
      <div>
        v<span className="font-mono">{updated?.version ?? 0}</span> · errors{" "}
        <span className="font-mono">{updated?.errors ?? 0}</span>
        {stale && (
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="ml-2 rounded-md border border-amber-500/40 bg-amber-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase text-amber-200 hover:bg-amber-500/25"
          >
            New data · refresh
          </button>
        )}
      </div>
    </div>
  );
}
