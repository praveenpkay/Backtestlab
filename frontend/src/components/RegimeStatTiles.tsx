import type { RegimeStats } from "@/lib/api";

function Tile({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-lg border border-black/10 bg-white px-4 py-3 dark:border-white/10 dark:bg-[#1a1a19]">
      <div className="text-xs font-medium uppercase tracking-wide text-[#898781]">{label}</div>
      <div className="mt-1 text-2xl font-semibold tabular-nums text-[color:var(--tile-ink)]">{value}</div>
      {sub && <div className="mt-0.5 text-xs text-[#898781]">{sub}</div>}
    </div>
  );
}

export default function RegimeStatTiles({ stats }: { stats: RegimeStats }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      <Tile label="Time in TQQQ regime" value={`${stats.pct_days_long.toFixed(1)}%`} />
      <Tile label="Time in SQQQ regime" value={`${stats.pct_days_short.toFixed(1)}%`} />
      <Tile label="Time in cash regime" value={`${stats.pct_days_cash.toFixed(1)}%`} />
      <Tile label="Regime changes" value={String(stats.num_regime_changes)} />
      <Tile
        label="Longest TQQQ streak"
        value={`${stats.long_streaks.longest_days}d`}
        sub={`${stats.long_streaks.count} streaks total`}
      />
      <Tile
        label="Longest SQQQ streak"
        value={`${stats.short_streaks.longest_days}d`}
        sub={`${stats.short_streaks.count} streaks total`}
      />
      <Tile
        label="Longest cash streak"
        value={`${stats.cash_streaks.longest_days}d`}
        sub={`${stats.cash_streaks.count} streaks total`}
      />
    </div>
  );
}
