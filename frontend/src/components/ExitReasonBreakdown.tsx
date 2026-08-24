const REASON_META: Record<string, { label: string; color: string }> = {
  signal_flip: { label: "Signal flip (Job 1)", color: "#898781" },
  stop_loss: { label: "Stop-loss", color: "#e34948" },
  fast_trend_break: { label: "Fast trend-break", color: "#eb6834" },
  mean_reversion_extension: { label: "Mean-reversion extension", color: "#2a78d6" },
};

export default function ExitReasonBreakdown({ breakdown }: { breakdown: Record<string, number> }) {
  const entries = Object.entries(breakdown);
  const total = entries.reduce((sum, [, n]) => sum + n, 0);

  if (total === 0) {
    return null;
  }

  return (
    <div className="rounded-lg border border-black/10 bg-white p-4 dark:border-white/10 dark:bg-[#1a1a19]">
      <h3 className="mb-3 text-sm font-semibold text-[color:var(--tile-ink)]">
        Why trades closed ({total})
      </h3>
      <div className="flex flex-wrap gap-2">
        {entries.map(([reason, count]) => {
          const meta = REASON_META[reason] ?? { label: reason, color: "#898781" };
          const pct = total ? (count / total) * 100 : 0;
          return (
            <div
              key={reason}
              className="flex items-center gap-2 rounded-lg border border-black/10 px-3 py-1.5 text-sm dark:border-white/10"
            >
              <span
                className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
                style={{ backgroundColor: meta.color }}
              />
              <span className="text-[color:var(--tile-ink)]">{meta.label}</span>
              <span className="tabular-nums text-[#898781]">
                {count} ({pct.toFixed(0)}%)
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
