"use client";

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { SignalHistoryRow } from "@/lib/api";

const PRICE_COLOR = "#2a78d6";

function downsample<T>(rows: T[], maxPoints = 2000): T[] {
  if (rows.length <= maxPoints) return rows;
  const step = Math.ceil(rows.length / maxPoints);
  const out = rows.filter((_, i) => i % step === 0);
  const last = rows[rows.length - 1];
  if (out[out.length - 1] !== last) out.push(last);
  return out;
}

export default function SignalPriceChart({ rows, tickerUsed }: { rows: SignalHistoryRow[]; tickerUsed: string }) {
  const data = downsample(rows);

  return (
    <div className="rounded-lg border border-black/10 bg-white p-4 dark:border-white/10 dark:bg-[#1a1a19]">
      <h3 className="mb-3 text-sm font-semibold text-[color:var(--tile-ink)]">
        {tickerUsed} price, long history (log scale)
      </h3>
      <ResponsiveContainer width="100%" height={260}>
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
            scale="log"
            domain={["auto", "auto"]}
            tick={{ fontSize: 11, fill: "#898781" }}
            axisLine={false}
            tickLine={false}
            width={56}
          />
          <Tooltip
            formatter={(value) => [Number(value).toFixed(2), tickerUsed]}
            contentStyle={{ fontSize: 12, borderRadius: 8, borderColor: "#e1e0d9" }}
          />
          <Line
            type="monotone"
            dataKey="close"
            stroke={PRICE_COLOR}
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
