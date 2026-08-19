export default function NavBar() {
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
          <span className="font-medium text-[color:var(--tile-ink)]">Backtest</span>
          <span
            className="cursor-not-allowed text-[#898781]"
            title="Daily signal log — coming next"
          >
            Daily Log (soon)
          </span>
        </nav>
      </div>
    </header>
  );
}
