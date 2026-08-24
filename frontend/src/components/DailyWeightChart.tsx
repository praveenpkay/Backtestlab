"use client";

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DailyLogRow } from "@/lib/api";

const LINE_COLOR = "#2a78d6";

const WEIGHT_LABEL: Record<number, string> = { 1: "TQQQ", 0: "Cash", [-1]: "SQQQ" };

export default function DailyWeightChart({ rows }: { rows: DailyLogRow[] }) {
  if (rows.length < 2) {
    return (
      <div className="rounded-lg border border-black/10 bg-white p-4 dark:border-white/10 dark:bg-[#1a1a19]">
        <h3 className="mb-1 text-sm font-semibold text-[color:var(--tile-ink)]">Dial over time</h3>
        <p className="py-6 text-center text-sm text-[#898781]">
          Log the signal on at least two days to see the dial move over time.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-black/10 bg-white p-4 dark:border-white/10 dark:bg-[#1a1a19]">
      <h3 className="mb-3 text-sm font-semibold text-[color:var(--tile-ink)]">Dial over time</h3>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={rows} margin={{ top: 4, right: 12, left: 4, bottom: 4 }}>
          <CartesianGrid stroke="#e1e0d9" strokeDasharray="0" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: "#898781" }}
            axisLine={{ stroke: "#c3c2b7" }}
            tickLine={false}
            minTickGap={40}
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
            formatter={(value) => [WEIGHT_LABEL[Number(value)] ?? String(value), "Signal"]}
            contentStyle={{ fontSize: 12, borderRadius: 8, borderColor: "#e1e0d9" }}
          />
          <Line
            type="stepAfter"
            dataKey="target_weight"
            stroke={LINE_COLOR}
            strokeWidth={2}
            dot={{ r: 3 }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
