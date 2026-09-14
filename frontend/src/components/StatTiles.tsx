import type { SummaryStats } from "@/lib/api";

function Tile({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: string;
  tone?: "neutral" | "good" | "bad";
}) {
  const toneClass =
    tone === "good"
      ? "text-[#006300] dark:text-[#0ca30c]"
      : tone === "bad"
      ? "text-[#d03b3b]"
      : "text-[color:var(--tile-ink)]";

  return (
    <div className="rounded-lg border border-black/10 bg-white px-4 py-3 dark:border-white/10 dark:bg-[#1a1a19]">
      <div className="text-xs font-medium uppercase tracking-wide text-[#898781]">{label}</div>
      <div className={`mt-1 text-2xl font-semibold tabular-nums ${toneClass}`}>{value}</div>
    </div>
  );
}

export default function StatTiles({ summary }: { summary: SummaryStats }) {
  const plRatio = summary.profit_loss_ratio;
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      <Tile
        label="CAGR"
        value={`${summary.cagr_pct.toFixed(1)}%`}
        tone={summary.cagr_pct >= 0 ? "good" : "bad"}
      />
      <Tile
        label="Total return"
        value={`${summary.total_return_pct.toFixed(1)}%`}
        tone={summary.total_return_pct >= 0 ? "good" : "bad"}
      />
      <Tile label="Win rate" value={`${summary.win_rate_pct.toFixed(1)}%`} />
      <Tile label="Profit / loss ratio" value={plRatio == null ? "—" : plRatio.toFixed(2)} />
      <Tile
        label="Max drawdown"
        value={`${summary.max_drawdown_pct.toFixed(1)}%`}
        tone="bad"
      />
      <Tile label="Max DD duration" value={`${summary.max_drawdown_days}d`} />
      <Tile
        label="Fees/slippage paid"
        value={summary.total_fees_paid > 0 ? `$${summary.total_fees_paid.toLocaleString(undefined, { maximumFractionDigits: 0 })}` : "$0"}
      />
    </div>
  );
}
