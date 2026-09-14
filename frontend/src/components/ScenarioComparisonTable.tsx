import type { ScenarioRow } from "@/lib/api";

function fmtPct(v: number | null | undefined, digits = 1) {
  return v == null ? "—" : `${v.toFixed(digits)}%`;
}

export default function ScenarioComparisonTable({ rows }: { rows: ScenarioRow[] }) {
  return (
    <div className="rounded-lg border border-black/10 bg-white p-4 dark:border-white/10 dark:bg-[#1a1a19]">
      <h3 className="mb-3 text-sm font-semibold text-[color:var(--tile-ink)]">Comparison</h3>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1100px] border-collapse text-xs">
          <thead>
            <tr className="text-left text-[#898781]">
              <th className="py-1.5 pr-3 font-medium">Scenario</th>
              <th className="py-1.5 pr-3 text-right font-medium">CAGR</th>
              <th className="py-1.5 pr-3 text-right font-medium">Total return</th>
              <th className="py-1.5 pr-3 text-right font-medium">Win rate</th>
              <th className="py-1.5 pr-3 text-right font-medium">P/L ratio</th>
              <th className="py-1.5 pr-3 text-right font-medium">Calmar</th>
              <th className="py-1.5 pr-3 text-right font-medium">Max DD</th>
              <th className="py-1.5 pr-3 text-right font-medium">Max DD days</th>
              <th className="py-1.5 pr-3 text-right font-medium">DDs &gt;20%</th>
              <th className="py-1.5 pr-3 text-right font-medium">Worst day</th>
              <th className="py-1.5 pr-3 text-right font-medium">Worst month</th>
              <th className="py-1.5 pr-3 text-right font-medium">Losing streak</th>
              <th className="py-1.5 text-right font-medium">Trades</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.name}
                className={`border-t border-black/5 dark:border-white/5 ${
                  row.kind === "benchmark" ? "bg-black/[0.02] dark:bg-white/[0.03]" : ""
                }`}
              >
                <td className="py-1.5 pr-3 font-medium text-[color:var(--tile-ink)]">
                  {row.name}
                  {row.kind === "benchmark" && (
                    <span className="ml-1.5 rounded bg-black/5 px-1 py-0.5 text-[10px] font-normal text-[#898781] dark:bg-white/10">
                      benchmark
                    </span>
                  )}
                </td>
                <td
                  className={`py-1.5 pr-3 text-right tabular-nums ${
                    row.kpis.cagr_pct >= 0 ? "text-[#006300] dark:text-[#0ca30c]" : "text-[#d03b3b]"
                  }`}
                >
                  {fmtPct(row.kpis.cagr_pct)}
                </td>
                <td className="py-1.5 pr-3 text-right tabular-nums text-[color:var(--tile-ink)]">
                  {fmtPct(row.kpis.total_return_pct)}
                </td>
                <td className="py-1.5 pr-3 text-right tabular-nums text-[color:var(--tile-ink)]">
                  {fmtPct(row.kpis.win_rate_pct)}
                </td>
                <td className="py-1.5 pr-3 text-right tabular-nums text-[color:var(--tile-ink)]">
                  {row.kpis.profit_loss_ratio == null ? "—" : row.kpis.profit_loss_ratio.toFixed(2)}
                </td>
                <td className="py-1.5 pr-3 text-right tabular-nums text-[color:var(--tile-ink)]">
                  {row.kpis.calmar_ratio == null ? "—" : row.kpis.calmar_ratio.toFixed(2)}
                </td>
                <td className="py-1.5 pr-3 text-right tabular-nums text-[#d03b3b]">
                  {fmtPct(row.kpis.max_drawdown_pct)}
                </td>
                <td className="py-1.5 pr-3 text-right tabular-nums text-[color:var(--tile-ink)]">
                  {row.kpis.max_drawdown_days}d
                </td>
                <td className="py-1.5 pr-3 text-right tabular-nums text-[color:var(--tile-ink)]">
                  {row.kpis.num_drawdowns_over_20pct}
                </td>
                <td className="py-1.5 pr-3 text-right tabular-nums text-[#d03b3b]">
                  {row.kpis.worst_day ? fmtPct(row.kpis.worst_day.return_pct) : "—"}
                </td>
                <td className="py-1.5 pr-3 text-right tabular-nums text-[#d03b3b]">
                  {row.kpis.worst_month ? fmtPct(row.kpis.worst_month.return_pct) : "—"}
                </td>
                <td className="py-1.5 pr-3 text-right tabular-nums text-[color:var(--tile-ink)]">
                  {row.kpis.max_consecutive_losses > 0
                    ? `${row.kpis.max_consecutive_losses} (${fmtPct(row.kpis.worst_losing_streak_pct)})`
                    : "—"}
                </td>
                <td className="py-1.5 text-right tabular-nums text-[color:var(--tile-ink)]">
                  {row.kpis.num_trades}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
