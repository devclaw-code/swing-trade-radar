import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { SiteFooter, SiteNav } from "@/components/SiteChrome";
import { USE_MOCKS } from "@/lib/api";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#020617",
};

export const metadata: Metadata = {
  title: {
    default: "Swing Trade Radar",
    template: "%s · Swing Trade Radar",
  },
  description:
    "Daily research desk: per-ticker swing-trade verdicts on the NASDAQ-100 with full evidence, base rates, and counter-arguments. Educational only — not financial advice.",
  openGraph: {
    title: "Swing Trade Radar",
    description:
      "Per-ticker swing-trade verdicts with evidence, base rates, and counter-arguments.",
    type: "website",
  },
  icons: {
    icon: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ctext y='26' font-size='28'%3E%F0%9F%93%A1%3C/text%3E%3C/svg%3E",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      data-theme="dark"
    >
      <body className="flex min-h-full flex-col bg-slate-950 text-slate-100">
        <SiteNav />
        {USE_MOCKS && (
          <div className="border-b-2 border-rose-500 bg-rose-700 px-6 py-2 text-center text-xs font-bold uppercase tracking-wider text-white">
            ⚠ MOCK DATA — Backend not connected. Prices, verdicts, and base rates are placeholder
            values, NOT real market data.
          </div>
        )}
        <div className="border-b border-amber-500/40 bg-amber-900/40 px-3 py-1.5 text-center text-[11px] font-medium text-amber-200 sm:px-6">
          Educational research desk — not financial advice. No trades are executed by this system.
        </div>
        <main className="flex-1">{children}</main>
        <SiteFooter />
      </body>
    </html>
  );
}
