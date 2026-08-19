import type { MonthlyReturnRow } from "@/lib/api";

const MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const POSITIVE_HEX = "42, 120, 214"; // blue, rgb triplet for alpha blending
const NEGATIVE_HEX = "227, 73, 72"; // red

function cellStyle(value: number | undefined, scaleMax: number) {
  if (value === undefined) return {};
  const magnitude = Math.min(Math.abs(value) / scaleMax, 1);
  const alpha = value === 0 ? 0 : 0.12 + magnitude * 0.68;
  const rgb = value >= 0 ? POSITIVE_HEX : NEGATIVE_HEX;
  return { backgroundColor: `rgba(${rgb}, ${alpha.toFixed(3)})` };
}

export default function MonthlyGrid({ rows }: { rows: MonthlyReturnRow[] }) {
  const byYear = new Map<number, Map<number, number>>();
  let scaleMax = 1;
  for (const r of rows) {
    if (!byYear.has(r.year)) byYear.set(r.year, new Map());
    byYear.get(r.year)!.set(r.month, r.return_pct);
    scaleMax = Math.max(scaleMax, Math.abs(r.return_pct));
  }
  const years = [...byYear.keys()].sort((a, b) => b - a);

  return (
    <div className="rounded-lg border border-black/10 bg-white p-4 dark:border-white/10 dark:bg-[#1a1a19]">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[color:var(--tile-ink)]">Monthly returns</h3>
        <div className="flex items-center gap-3 text-xs text-[#898781]">
          <span className="flex items-center gap-1">
            <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: "rgba(227,73,72,0.55)" }} />
            loss
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: "rgba(42,120,214,0.55)" }} />
            gain
          </span>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] border-collapse text-xs">
          <thead>
            <tr>
              <th className="w-14 py-1 pr-2 text-left font-medium text-[#898781]">Year</th>
              {MONTH_LABELS.map((m) => (
                <th key={m} className="px-1 py-1 text-center font-medium text-[#898781]">
                  {m}
                </th>
              ))}
              <th className="px-1 py-1 text-center font-medium text-[#898781]">Year</th>
            </tr>
          </thead>
          <tbody>
            {years.map((year) => {
              const months = byYear.get(year)!;
              const values = [...months.values()];
              const compounded = (values.reduce((acc, v) => acc * (1 + v / 100), 1) - 1) * 100;
              return (
                <tr key={year}>
                  <td className="py-1 pr-2 font-medium tabular-nums text-[color:var(--tile-ink)]">{year}</td>
                  {MONTH_LABELS.map((_, i) => {
                    const month = i + 1;
                    const value = months.get(month);
                    return (
                      <td
                        key={month}
                        className="px-1 py-1 text-center tabular-nums text-[color:var(--tile-ink)]"
                        style={cellStyle(value, scaleMax)}
                      >
                        {value === undefined ? "" : value.toFixed(1)}
                      </td>
                    );
                  })}
                  <td className="px-1 py-1 text-center font-semibold tabular-nums text-[color:var(--tile-ink)]">
                    {compounded.toFixed(1)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
