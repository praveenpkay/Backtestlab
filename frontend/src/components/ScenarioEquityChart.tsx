"use client";

import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ScenarioRow } from "@/lib/api";

// Fixed categorical order (dataviz palette) -- never cycled per-series.
const SERIES_COLORS = [
  "#2a78d6", // blue
  "#eb6834", // orange
  "#1baf7a", // aqua
  "#eda100", // yellow
  "#e87ba4", // magenta
  "#008300", // green
  "#4a3aa7", // violet
  "#e34948", // red
];

function downsample<T>(rows: T[], maxPoints = 1500): T[] {
  if (rows.length <= maxPoints) return rows;
  const step = Math.ceil(rows.length / maxPoints);
  const out = rows.filter((_, i) => i % step === 0);
  const last = rows[rows.length - 1];
  if (out[out.length - 1] !== last) out.push(last);
  return out;
}

function formatUsd(v: number) {
  return `$${v.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

export default function ScenarioEquityChart({ rows }: { rows: ScenarioRow[] }) {
  if (rows.length === 0) return null;

  const dates = rows[0].equity_curve.map((r) => r.date);
  const merged = dates.map((date, i) => {
    const point: Record<string, string | number> = { date };
    for (const row of rows) {
      point[row.name] = row.equity_curve[i]?.strategy_equity ?? row.equity_curve[i]?.benchmark_equity ?? null;
    }
    return point;
  });
  const data = downsample(merged);

  return (
    <div className="rounded-lg border border-black/10 bg-white p-4 dark:border-white/10 dark:bg-[#1a1a19]">
      <h3 className="mb-3 text-sm font-semibold text-[color:var(--tile-ink)]">Equity curves, overlaid</h3>
      <ResponsiveContainer width="100%" height={360}>
        <LineChart data={data} margin={{ top: 4, right: 12, left: 4, bottom: 4 }}>
          <CartesianGrid stroke="#e1e0d9" strokeDasharray="0" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: "#898781" }}
            tickFormatter={(d: string) => d.slice(0, 4)}
            axisLine={{ stroke: "#c3c2b7" }}
            tickLine={false}
            minTickGap={40}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#898781" }}
            tickFormatter={formatUsd}
            axisLine={false}
            tickLine={false}
            width={70}
          />
          <Tooltip
            formatter={(value, name) => [formatUsd(Number(value)), String(name)]}
            contentStyle={{ fontSize: 12, borderRadius: 8, borderColor: "#e1e0d9" }}
          />
          <Legend wrapperStyle={{ fontSize: 11 }} formatter={(value) => <span style={{ color: "#52514e" }}>{value}</span>} />
          {rows.map((row, i) => (
            <Line
              key={row.name}
              type="monotone"
              dataKey={row.name}
              name={row.name}
              stroke={SERIES_COLORS[i % SERIES_COLORS.length]}
              strokeWidth={row.kind === "benchmark" ? 1.5 : 2}
              strokeDasharray={row.kind === "benchmark" ? "4 3" : undefined}
              dot={false}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
