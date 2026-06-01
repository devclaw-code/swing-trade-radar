"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import type { LastUpdated } from "@/lib/api";
import { fetchJson } from "@/lib/api";

export function AutoRefreshBadge({ initial }: { initial: LastUpdated | null }) {
  const router = useRouter();
  const [updated, setUpdated] = useState<LastUpdated | null>(initial);
  const [lastVersion, setLastVersion] = useState<number>(initial?.version ?? 0);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const tick = async () => {
      try {
        const next = await fetchJson<LastUpdated>("/api/last-updated");
        if (cancelled) return;
        setUpdated(next);
        if (next.version > lastVersion) {
          setLastVersion(next.version);
          setRefreshing(true);
          // Trigger Next.js server-component re-fetch; cards update in place.
          router.refresh();
          setTimeout(() => !cancelled && setRefreshing(false), 1500);
        }
      } catch {
        // ignore polling errors
      }
    };
    const id = setInterval(tick, 30_000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [lastVersion, router]);

  return (
    <div className="text-right text-xs text-slate-400">
      <div>
        Last update: <span className="font-mono text-slate-200">{updated?.ts ?? "—"}</span>
        {refreshing && (
          <span className="ml-2 inline-flex items-center gap-1 rounded-md border border-emerald-500/50 bg-emerald-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase text-emerald-300">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
            Updating
          </span>
        )}
      </div>
      <div>
        v<span className="font-mono text-slate-300">{updated?.version ?? 0}</span> · errors{" "}
        <span className="font-mono text-slate-300">{updated?.errors ?? 0}</span>
      </div>
    </div>
  );
}
