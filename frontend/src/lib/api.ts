export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export type Risk = "LOW" | "MED" | "HIGH";
export type Direction = "LONG" | "SHORT";

export interface Signal {
  id: number;
  ticker: string;
  strategy: string;
  direction: Direction;
  entry: number;
  target: number;
  stop: number;
  stop_pct: number;
  rr_ratio: number;
  risk: Risk;
  confidence: number;
  confirmations: string[];
  bar_date: string | null;
  generated_at: string | null;
}

export interface SignalsResponse {
  count: number;
  signals: Signal[];
}

export interface LastUpdated {
  version: number;
  ts: string | null;
  errors: number;
}

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store", ...init });
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText} :: ${path}`);
  }
  return (await res.json()) as T;
}
