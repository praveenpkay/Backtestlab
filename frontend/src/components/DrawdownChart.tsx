"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { DrawdownRow } from "@/lib/api";

const DRAWDOWN_COLOR = "#e34948";

function downsample<T>(rows: T[], maxPoints = 1500): T[] {
  if (rows.length <= maxPoints) return rows;
  const step = Math.ceil(rows.length / maxPoints);
  const out = rows.filter((_, i) => i % step === 0);
  const last = rows[rows.length - 1];
  if (out[out.length - 1] !== last) out.push(last);
  return out;
}

export default function DrawdownChart({ rows }: { rows: DrawdownRow[] }) {
  const data = downsample(rows);

  return (
    <div className="rounded-lg border border-black/10 bg-white p-4 dark:border-white/10 dark:bg-[#1a1a19]">
      <h3 className="mb-1 text-sm font-semibold text-[color:var(--tile-ink)]">Drawdown</h3>
      <p className="mb-3 text-xs text-[#898781]">
        How far below the running peak the strategy&apos;s equity has fallen — the &quot;underwater&quot; plot.
      </p>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data} margin={{ top: 4, right: 12, left: 4, bottom: 4 }}>
          <defs>
            <linearGradient id="ddFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={DRAWDOWN_COLOR} stopOpacity={0.35} />
              <stop offset="100%" stopColor={DRAWDOWN_COLOR} stopOpacity={0.05} />
            </linearGradient>
          </defs>
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
            tickFormatter={(v: number) => `${v}%`}
            axisLine={false}
            tickLine={false}
            width={48}
          />
          <Tooltip
            formatter={(value) => [`${Number(value).toFixed(1)}%`, "Drawdown"]}
            contentStyle={{ fontSize: 12, borderRadius: 8, borderColor: "#e1e0d9" }}
          />
          <Area
            type="monotone"
            dataKey="drawdown_pct"
            stroke={DRAWDOWN_COLOR}
            strokeWidth={2}
            fill="url(#ddFill)"
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
