"use client";

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { SignalHistoryRow } from "@/lib/api";

const LINE_COLOR = "#2a78d6";
const WEIGHT_LABEL: Record<number, string> = { 1: "TQQQ", 0: "Cash", [-1]: "SQQQ" };

function downsample<T>(rows: T[], maxPoints = 3000): T[] {
  if (rows.length <= maxPoints) return rows;
  const step = Math.ceil(rows.length / maxPoints);
  const out = rows.filter((_, i) => i % step === 0);
  const last = rows[rows.length - 1];
  if (out[out.length - 1] !== last) out.push(last);
  return out;
}

export default function SignalRegimeChart({ rows }: { rows: SignalHistoryRow[] }) {
  const data = downsample(rows);

  return (
    <div className="rounded-lg border border-black/10 bg-white p-4 dark:border-white/10 dark:bg-[#1a1a19]">
      <h3 className="mb-3 text-sm font-semibold text-[color:var(--tile-ink)]">Regime over time</h3>
      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={data} margin={{ top: 4, right: 12, left: 4, bottom: 4 }}>
          <CartesianGrid stroke="#e1e0d9" strokeDasharray="0" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: "#898781" }}
            tickFormatter={(d: string) => d.slice(0, 4)}
            axisLine={{ stroke: "#c3c2b7" }}
            tickLine={false}
            minTickGap={50}
          />
          <YAxis
            domain={[-1, 1]}
            ticks={[-1, 0, 1]}
            tickFormatter={(v: number) => WEIGHT_LABEL[v] ?? ""}
            tick={{ fontSize: 11, fill: "#898781" }}
            axisLine={false}
            tickLine={false}
            width={48}
          />
          <Tooltip
            formatter={(value) => [WEIGHT_LABEL[Number(value)] ?? String(value), "Regime"]}
            contentStyle={{ fontSize: 12, borderRadius: 8, borderColor: "#e1e0d9" }}
          />
          <Line
            type="stepAfter"
            dataKey="target_weight"
            stroke={LINE_COLOR}
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
