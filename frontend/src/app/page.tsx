import { AutoRefreshBadge } from "@/components/AutoRefreshBadge";
import { Dashboard } from "@/components/Dashboard";
import {
  type BacktestAllResponse,
  type BacktestResult,
  fetchJson,
  type LastUpdated,
  type NewsItem,
  type NewsResponse,
  type Signal,
  type SignalsResponse,
} from "@/lib/api";

export default async function Home() {
  let signals: Signal[] = [];
  let news: NewsItem[] = [];
  let backtest: Record<string, BacktestResult[]> = {};
  let updated: LastUpdated | null = null;
  let error: string | null = null;

  try {
    const [sigs, newsRes, bt, upd] = await Promise.all([
      fetchJson<SignalsResponse>("/api/strategies"),
      fetchJson<NewsResponse>("/api/news"),
      fetchJson<BacktestAllResponse>("/api/backtest"),
      fetchJson<LastUpdated>("/api/last-updated"),
    ]);
    signals = sigs.signals;
    news = newsRes.news;
    backtest = bt.strategies;
    updated = upd;
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }

  return (
    <main className="min-h-dvh bg-zinc-950 text-zinc-100">
      <header className="border-b border-white/10 px-6 py-4">
        <div className="mx-auto flex max-w-7xl flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">📡 NASDAQ-100 Swing Trade Radar</h1>
            <p className="text-sm text-white/50">
              Educational signals — not financial advice. Paper-trade only.
            </p>
          </div>
          <AutoRefreshBadge initial={updated} />
        </div>
      </header>

      <div className="border-b border-amber-500/30 bg-amber-500/10 px-6 py-2 text-center text-xs text-amber-200">
        ⚠️ <strong>Educational demo only.</strong> Not financial advice. Signals are
        algorithmic outputs on historical data — do not trade real money based on this. Paper-trade,
        backtest, and verify everything yourself.
      </div>

      <section className="mx-auto max-w-7xl px-6 py-6">
        {error && (
          <div className="mb-4 rounded-lg border border-rose-500/40 bg-rose-500/10 p-3 text-sm text-rose-200">
            Backend unreachable: <span className="font-mono">{error}</span> — is FastAPI running on{" "}
            <code>:8000</code>?
          </div>
        )}
        <Dashboard signals={signals} news={news} backtest={backtest} />
      </section>

      <footer className="mt-6 border-t border-white/10 px-6 py-4 text-center text-xs text-white/40">
        Swing Trade Radar v0.2 · Next.js + FastAPI
      </footer>
    </main>
  );
}
