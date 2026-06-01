import Link from "next/link";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/strategies", label: "Strategies" },
  { href: "/about", label: "About" },
];

export function SiteNav() {
  return (
    <nav
      aria-label="Primary"
      className="border-b border-white/10 bg-zinc-950/80 backdrop-blur"
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-3">
        <Link href="/" className="flex items-center gap-2 text-sm font-bold tracking-tight text-white">
          <span aria-hidden className="text-base">📡</span>
          <span>Swing Trade Radar</span>
          <span className="ml-1 hidden rounded bg-white/10 px-1.5 py-0.5 font-mono text-[10px] text-white/60 sm:inline">
            v0.2
          </span>
        </Link>
        <ul className="flex items-center gap-1 text-sm">
          {links.map((l) => (
            <li key={l.href}>
              <Link
                href={l.href}
                className="rounded-md px-3 py-1.5 text-white/70 transition hover:bg-white/10 hover:text-white"
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
    <footer className="mt-10 border-t border-white/10 px-6 py-6 text-xs text-white/45">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3">
        <div>
          Swing Trade Radar v0.2 · Next.js + FastAPI · Educational research desk —{" "}
          <strong className="text-white/60">not financial advice</strong>.
        </div>
        <div className="flex items-center gap-4">
          <Link href="/about" className="hover:text-white">
            Methodology
          </Link>
          <a
            href="https://github.com/"
            target="_blank"
            rel="noreferrer"
            className="hover:text-white"
          >
            GitHub
          </a>
        </div>
      </div>
    </footer>
  );
}
