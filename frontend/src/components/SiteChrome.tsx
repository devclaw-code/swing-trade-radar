import Link from "next/link";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/strategies", label: "Strategies" },
  { href: "/about", label: "About" },
];

export function SiteNav() {
  return (
    <nav aria-label="Primary" className="border-b border-slate-700 bg-slate-900">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-2 px-3 py-3 sm:px-6">
        <Link
          href="/"
          className="flex items-center gap-2 text-sm font-bold tracking-tight text-slate-50"
        >
          <span aria-hidden className="text-base">
            📡
          </span>
          <span className="hidden xs:inline">Swing Trade Radar</span>
          <span className="inline xs:hidden">STR</span>
          <span className="ml-1 hidden rounded border border-slate-700 bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] text-slate-300 sm:inline">
            v0.2
          </span>
        </Link>
        <ul className="flex items-center gap-0.5 text-xs sm:gap-1 sm:text-sm">
          {links.map((l) => (
            <li key={l.href}>
              <Link
                href={l.href}
                className="rounded-md px-2 py-1.5 font-medium text-slate-300 transition hover:bg-slate-800 hover:text-slate-50 sm:px-3"
              >
                {l.label}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}

export function SiteFooter() {
  return (
    <footer className="mt-10 border-t border-slate-800 bg-slate-950 px-4 py-6 text-xs text-slate-500 sm:px-6">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3">
        <div>
          Swing Trade Radar v0.2 · Next.js + FastAPI · Educational research desk —{" "}
          <strong className="text-slate-300">not financial advice</strong>.
        </div>
        <div className="flex items-center gap-4">
          <Link href="/about" className="hover:text-slate-100">
            Methodology
          </Link>
          <a
            href="https://github.com/devclaw-code/swing-trade-radar"
            target="_blank"
            rel="noreferrer"
            className="hover:text-slate-100"
          >
            GitHub
          </a>
        </div>
      </div>
    </footer>
  );
}
