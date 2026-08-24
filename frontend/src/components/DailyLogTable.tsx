import type { DailyLogRow } from "@/lib/api";

const SYMBOL_TONE: Record<string, string> = {
  TQQQ: "bg-[#2a78d6]/10 text-[#184f95] dark:text-[#86b6ef]",
  CASH: "bg-black/5 text-[#52514e] dark:bg-white/10 dark:text-[#c3c2b7]",
  SQQQ: "bg-[#e34948]/10 text-[#d03b3b]",
};

export default function DailyLogTable({ rows }: { rows: DailyLogRow[] }) {
  const ordered = [...rows].reverse();

  return (
    <div className="rounded-lg border border-black/10 bg-white p-4 dark:border-white/10 dark:bg-[#1a1a19]">
      <h3 className="mb-3 text-sm font-semibold text-[color:var(--tile-ink)]">
        Signal history ({rows.length})
      </h3>
      {rows.length === 0 ? (
        <p className="py-6 text-center text-sm text-[#898781]">
          Nothing logged yet — this fills in one row per day as you log the signal.
        </p>
      ) : (
        <div className="max-h-[420px] overflow-auto">
          <table className="w-full min-w-[520px] border-collapse text-xs">
            <thead className="sticky top-0 bg-white dark:bg-[#1a1a19]">
              <tr className="text-left text-[#898781]">
                <th className="py-1.5 pr-3 font-medium">Date</th>
                <th className="py-1.5 pr-3 text-right font-medium">^NDX close</th>
                <th className="py-1.5 pr-3 text-right font-medium">50d MA</th>
                <th className="py-1.5 pr-3 text-right font-medium">250d MA</th>
                <th className="py-1.5 font-medium">Signal</th>
              </tr>
            </thead>
            <tbody>
              {ordered.map((row) => (
                <tr key={row.date} className="border-t border-black/5 dark:border-white/5">
                  <td className="py-1.5 pr-3 tabular-nums text-[color:var(--tile-ink)]">{row.date}</td>
                  <td className="py-1.5 pr-3 text-right tabular-nums text-[color:var(--tile-ink)]">
                    {row.ndx_close.toFixed(2)}
                  </td>
                  <td className="py-1.5 pr-3 text-right tabular-nums text-[color:var(--tile-ink)]">
                    {row.ma_fast == null ? "—" : row.ma_fast.toFixed(2)}
                  </td>
                  <td className="py-1.5 pr-3 text-right tabular-nums text-[color:var(--tile-ink)]">
                    {row.ma_slow == null ? "—" : row.ma_slow.toFixed(2)}
                  </td>
                  <td className="py-1.5">
                    <span className={`rounded px-1.5 py-0.5 text-[11px] font-medium ${SYMBOL_TONE[row.symbol] ?? ""}`}>
                      {row.symbol}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
