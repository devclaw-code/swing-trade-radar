import { AutoRefreshBadge } from "@/components/AutoRefreshBadge";
import { Dashboard } from "@/components/Dashboard";
import {
  getLastUpdated,
  getRegime,
  getVerdicts,
  type LastUpdated,
  type RegimeResponse,
  type VerdictsResponse,
} from "@/lib/api";

export default async function Home() {
  let verdicts: VerdictsResponse = { count: 0, as_of: "", verdicts: [] };
  let regime: RegimeResponse | null = null;
  let updated: LastUpdated | null = null;
  let error: string | null = null;

  try {
    const [v, r, u] = await Promise.all([getVerdicts(), getRegime(), getLastUpdated()]);
    verdicts = v;
    regime = r;
    updated = u;
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }

  return (
    <>
      <header className="border-b border-white/10 px-6 py-5">
        <div className="mx-auto flex max-w-7xl flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Today&apos;s Verdicts</h1>
            <p className="text-sm text-white/50">
              Per-ticker swing-trade research for the NDX-100 mega-caps · {verdicts.as_of || "—"}
            </p>
          </div>
          <AutoRefreshBadge initial={updated} />
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-6 py-6">
        {error && (
          <div className="mb-4 rounded-lg border border-rose-500/40 bg-rose-500/10 p-3 text-sm text-rose-200">
            Backend unreachable: <span className="font-mono">{error}</span> — showing mock data if
            available, or set <code>NEXT_PUBLIC_USE_MOCKS=1</code>.
          </div>
        )}
        {regime && (
          <Dashboard
            initialVerdicts={verdicts}
            initialRegime={regime}
            initialUpdated={updated}
          />
        )}
      </section>
    </>
  );
}
