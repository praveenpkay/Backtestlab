"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Backtest" },
  { href: "/scenarios", label: "Scenarios" },
  { href: "/daily-log", label: "Daily Log" },
  { href: "/signal-history", label: "Signal History" },
];

export default function NavBar() {
  const pathname = usePathname();

  return (
    <header className="border-b border-black/10 dark:border-white/10">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-lg font-semibold text-[color:var(--tile-ink)]">Backtest Lab</span>
          <span className="rounded bg-black/5 px-1.5 py-0.5 text-[11px] font-medium text-[#52514e] dark:bg-white/10 dark:text-[#c3c2b7]">
            MVP
          </span>
        </div>
        <nav className="flex items-center gap-4 text-sm">
          {LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={
                pathname === link.href
                  ? "font-medium text-[color:var(--tile-ink)]"
                  : "text-[#898781] hover:text-[color:var(--tile-ink)]"
              }
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
