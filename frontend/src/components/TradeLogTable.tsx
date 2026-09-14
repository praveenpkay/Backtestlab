import type { TradeLogRow } from "@/lib/api";

const EXIT_REASON_LABEL: Record<string, string> = {
  signal_flip: "Signal flip",
  stop_loss: "Stop-loss",
  fast_trend_break: "Fast trend-break",
  mean_reversion_extension: "Mean-reversion",
  resize: "Resize (Job 2)",
};

function Badge({ children, tone }: { children: React.ReactNode; tone: "good" | "bad" | "neutral" }) {
  const cls =
    tone === "good"
      ? "bg-[#0ca30c]/10 text-[#006300] dark:text-[#0ca30c]"
      : tone === "bad"
      ? "bg-[#d03b3b]/10 text-[#d03b3b]"
      : "bg-black/5 text-[#52514e] dark:bg-white/10 dark:text-[#c3c2b7]";
  return <span className={`rounded px-1.5 py-0.5 text-[11px] font-medium ${cls}`}>{children}</span>;
}

export default function TradeLogTable({ trades }: { trades: TradeLogRow[] }) {
  const rows = [...trades].reverse();

  return (
    <div className="rounded-lg border border-black/10 bg-white p-4 dark:border-white/10 dark:bg-[#1a1a19]">
      <h3 className="mb-3 text-sm font-semibold text-[color:var(--tile-ink)]">
        Trade log ({trades.length})
      </h3>
      <div className="max-h-[420px] overflow-auto">
        <table className="w-full min-w-[1040px] border-collapse text-xs">
          <thead className="sticky top-0 bg-white dark:bg-[#1a1a19]">
            <tr className="text-left text-[#898781]">
              <th className="py-1.5 pr-3 font-medium">Symbol</th>
              <th className="py-1.5 pr-3 font-medium">Start</th>
              <th className="py-1.5 pr-3 font-medium">End</th>
              <th className="py-1.5 pr-3 font-medium">Duration</th>
              <th className="py-1.5 pr-3 text-right font-medium">Buy</th>
              <th className="py-1.5 pr-3 text-right font-medium">Sell</th>
              <th className="py-1.5 pr-3 text-right font-medium">Shares</th>
              <th className="py-1.5 pr-3 text-right font-medium">Size</th>
              <th className="py-1.5 pr-3 text-right font-medium">Profit</th>
              <th className="py-1.5 pr-3 text-right font-medium">Profit %</th>
              <th className="py-1.5 pr-3 font-medium">Result</th>
              <th className="py-1.5 pr-3 font-medium">Side</th>
              <th className="py-1.5 font-medium">Exit reason</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((t) => (
              <tr key={`${t.symbol}-${t.start_date}`} className="border-t border-black/5 dark:border-white/5">
                <td className="py-1.5 pr-3 font-medium tabular-nums text-[color:var(--tile-ink)]">{t.symbol}</td>
                <td className="py-1.5 pr-3 tabular-nums text-[color:var(--tile-ink)]">{t.start_date}</td>
                <td className="py-1.5 pr-3 tabular-nums text-[color:var(--tile-ink)]">{t.end_date}</td>
                <td className="py-1.5 pr-3 tabular-nums text-[color:var(--tile-ink)]">{t.duration_days}d</td>
                <td className="py-1.5 pr-3 text-right tabular-nums text-[color:var(--tile-ink)]">
                  ${t.buy_price.toFixed(2)}
                </td>
                <td className="py-1.5 pr-3 text-right tabular-nums text-[color:var(--tile-ink)]">
                  ${t.sell_price.toFixed(2)}
                </td>
                <td className="py-1.5 pr-3 text-right tabular-nums text-[color:var(--tile-ink)]">
                  {t.share_size.toFixed(2)}
                </td>
                <td className="py-1.5 pr-3 text-right tabular-nums text-[color:var(--tile-ink)]">
                  {t.size_pct.toFixed(0)}%
                </td>
                <td
                  className={`py-1.5 pr-3 text-right tabular-nums ${
                    t.profit >= 0 ? "text-[#006300] dark:text-[#0ca30c]" : "text-[#d03b3b]"
                  }`}
                >
                  ${t.profit.toFixed(2)}
                </td>
                <td
                  className={`py-1.5 pr-3 text-right tabular-nums ${
                    t.profit_pct >= 0 ? "text-[#006300] dark:text-[#0ca30c]" : "text-[#d03b3b]"
                  }`}
                >
                  {t.profit_pct.toFixed(2)}%
                </td>
                <td className="py-1.5 pr-3">
                  {t.is_open ? (
                    <Badge tone="neutral">Open</Badge>
                  ) : t.is_profitable ? (
                    <Badge tone="good">Win</Badge>
                  ) : (
                    <Badge tone="bad">Loss</Badge>
                  )}
                </td>
                <td className="py-1.5 pr-3">
                  <Badge tone="neutral">{t.is_short ? "Short" : "Long"}</Badge>
                </td>
                <td className="py-1.5 tabular-nums text-[color:var(--tile-ink)]">
                  {t.exit_reason ? EXIT_REASON_LABEL[t.exit_reason] ?? t.exit_reason : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
