import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { SiteFooter, SiteNav } from "@/components/SiteChrome";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

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
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`} data-theme="dark">
      <body className="flex min-h-full flex-col bg-slate-950 text-slate-100">
        <SiteNav />
        <div className="border-b border-amber-500/40 bg-amber-900/40 px-6 py-1.5 text-center text-[11px] font-medium text-amber-200">
          Educational research desk — not financial advice. Paper-trade only.
        </div>
        <main className="flex-1">{children}</main>
        <SiteFooter />
      </body>
    </html>
  );
}
