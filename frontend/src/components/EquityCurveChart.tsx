"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { EquityCurveRow } from "@/lib/api";

const STRATEGY_COLOR = "#2a78d6";
const BENCHMARK_COLOR = "#eb6834";

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

export default function EquityCurveChart({ rows }: { rows: EquityCurveRow[] }) {
  const data = downsample(rows);

  return (
    <div className="rounded-lg border border-black/10 bg-white p-4 dark:border-white/10 dark:bg-[#1a1a19]">
      <h3 className="mb-3 text-sm font-semibold text-[color:var(--tile-ink)]">
        Equity curve — Strategy vs. QQQ buy &amp; hold
      </h3>
      <ResponsiveContainer width="100%" height={340}>
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
            labelFormatter={(label) => label}
            contentStyle={{ fontSize: 12, borderRadius: 8, borderColor: "#e1e0d9" }}
          />
          <Legend
            wrapperStyle={{ fontSize: 12 }}
            formatter={(value) => <span style={{ color: "#52514e" }}>{value}</span>}
          />
          <Line
            type="monotone"
            dataKey="strategy_equity"
            name="Strategy"
            stroke={STRATEGY_COLOR}
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="benchmark_equity"
            name="QQQ buy & hold"
            stroke={BENCHMARK_COLOR}
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
