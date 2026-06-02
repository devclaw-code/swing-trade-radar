"use client";

import { useEffect, useState } from "react";

const REFRESH_HOUR_ET = 16; // 4 PM
const REFRESH_MIN_ET = 5;

// Returns the wall-clock parts of `date` in America/New_York.
function partsInET(date: Date) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    weekday: "short",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).formatToParts(date);
  const get = (t: string) => parts.find((p) => p.type === t)?.value ?? "";
  // weekday: Sun..Sat -> 0..6
  const dows: Record<string, number> = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 };
  let h = parseInt(get("hour"), 10);
  if (h === 24) h = 0; // some locales return 24 for midnight
  return {
    y: parseInt(get("year"), 10),
    mo: parseInt(get("month"), 10),
    d: parseInt(get("day"), 10),
    h,
    mi: parseInt(get("minute"), 10),
    dow: dows[get("weekday")] ?? 0,
  };
}

// Compute the next 16:05 ET on Mon–Fri after `now`.
function nextRefreshAt(now: Date): Date {
  const et = partsInET(now);
  // Days to add until we land on a weekday whose 16:05 ET is still in the future.
  for (let i = 0; i < 8; i++) {
    const candidateDow = (et.dow + i) % 7;
    const isWeekday = candidateDow >= 1 && candidateDow <= 5;
    if (!isWeekday) continue;
    if (i === 0) {
      // Today — only valid if 16:05 ET hasn't passed yet.
      if (et.h < REFRESH_HOUR_ET || (et.h === REFRESH_HOUR_ET && et.mi < REFRESH_MIN_ET)) {
        return resolveET(et.y, et.mo, et.d, REFRESH_HOUR_ET, REFRESH_MIN_ET);
      }
      continue;
    }
    // Add `i` days to base date in ET.
    const base = new Date(Date.UTC(et.y, et.mo - 1, et.d) + i * 86400_000);
    return resolveET(
      base.getUTCFullYear(),
      base.getUTCMonth() + 1,
      base.getUTCDate(),
      REFRESH_HOUR_ET,
      REFRESH_MIN_ET,
    );
  }
  return now; // unreachable
}

// Given ET wall-clock y/m/d/h/mi, return the actual UTC Date.
// Uses Intl to discover the UTC↔ET offset at the candidate instant, then corrects.
function resolveET(y: number, mo: number, d: number, h: number, mi: number): Date {
  const targetUtcMs = Date.UTC(y, mo - 1, d, h, mi);
  // Two passes are enough: first finds the offset, second refines if we crossed a DST boundary.
  let guess = new Date(targetUtcMs);
  for (let i = 0; i < 2; i++) {
    const got = partsInET(guess);
    const gotAsUtcMs = Date.UTC(got.y, got.mo - 1, got.d, got.h, got.mi);
    const offsetMs = gotAsUtcMs - guess.getTime(); // ET wall-clock minus actual UTC instant = -tz_offset
    const corrected = new Date(targetUtcMs - offsetMs);
    if (corrected.getTime() === guess.getTime()) break;
    guess = corrected;
  }
  return guess;
}

function formatCountdown(ms: number): string {
  if (ms <= 0) return "now";
  const totalMin = Math.floor(ms / 60_000);
  const days = Math.floor(totalMin / 1440);
  const hours = Math.floor((totalMin % 1440) / 60);
  const mins = totalMin % 60;
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${mins}m`;
  return `${mins}m`;
}

export function NextRefreshBadge() {
  const [now, setNow] = useState<Date | null>(null);

  useEffect(() => {
    setNow(new Date());
    const id = setInterval(() => setNow(new Date()), 30_000);
    return () => clearInterval(id);
  }, []);

  if (!now) {
    // Render a static placeholder during SSR/hydration to avoid mismatch.
    return (
      <span
        className="inline-flex items-center gap-1.5 rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-[10px] font-medium text-slate-400"
        title="Daily refresh: 16:05 America/New_York, Mon–Fri"
      >
        <span aria-hidden>⏱</span>
        Next refresh 16:05 ET
      </span>
    );
  }

  const next = nextRefreshAt(now);
  const localStr = next.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    weekday: "short",
  });
  const countdown = formatCountdown(next.getTime() - now.getTime());

  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-[10px] font-medium text-slate-300"
      title={`Daily refresh runs at 16:05 America/New_York, Mon–Fri.\nNext: ${next.toString()}`}
    >
      <span aria-hidden>⏱</span>
      <span className="text-slate-500">Next refresh</span>
      <span className="font-mono text-slate-200">{localStr}</span>
      <span className="text-slate-500">·</span>
      <span className="font-mono text-slate-200">in {countdown}</span>
    </span>
  );
}
