"use client";

import { useState } from "react";
import type { ScenarioRow } from "@/lib/api";

export default function ScenarioDetailCard({ row }: { row: ScenarioRow }) {
  const [open, setOpen] = useState(false);
  const episodes = [...row.kpis.drawdown_episodes].sort((a, b) => a.depth_pct - b.depth_pct);

  return (
    <div className="rounded-lg border border-black/10 bg-white p-4 dark:border-white/10 dark:bg-[#1a1a19]">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between text-left"
      >
        <span className="text-sm font-semibold text-[color:var(--tile-ink)]">{row.name}</span>
        <span className="text-xs text-[#898781]">{open ? "Hide details ▲" : "Show details ▼"}</span>
      </button>
      <p className="mt-2 text-sm text-[color:var(--tile-ink)]">{row.readout}</p>
      {open && (
        <div className="mt-3 max-h-[280px] overflow-auto border-t border-black/5 pt-3 dark:border-white/5">
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[#898781]">
            Drawdown episodes ({episodes.length})
          </h4>
          {episodes.length === 0 ? (
            <p className="text-xs text-[#898781]">No drawdowns in this window.</p>
          ) : (
            <table className="w-full min-w-[500px] border-collapse text-xs">
              <thead>
                <tr className="text-left text-[#898781]">
                  <th className="py-1 pr-3 font-medium">Peak</th>
                  <th className="py-1 pr-3 font-medium">Trough</th>
                  <th className="py-1 pr-3 font-medium">Recovered</th>
                  <th className="py-1 pr-3 text-right font-medium">Depth</th>
                  <th className="py-1 text-right font-medium">Length</th>
                </tr>
              </thead>
              <tbody>
                {episodes.map((ep) => (
                  <tr key={ep.peak_date} className="border-t border-black/5 dark:border-white/5">
                    <td className="py-1 pr-3 tabular-nums text-[color:var(--tile-ink)]">{ep.peak_date}</td>
                    <td className="py-1 pr-3 tabular-nums text-[color:var(--tile-ink)]">{ep.trough_date}</td>
                    <td className="py-1 pr-3 tabular-nums text-[color:var(--tile-ink)]">
                      {ep.recovery_date ?? (
                        <span className="rounded bg-[#eda100]/10 px-1 py-0.5 text-[10px] font-medium text-[#eda100]">
                          ongoing
                        </span>
                      )}
                    </td>
                    <td className="py-1 pr-3 text-right tabular-nums text-[#d03b3b]">
                      {ep.depth_pct.toFixed(1)}%
                    </td>
                    <td className="py-1 text-right tabular-nums text-[color:var(--tile-ink)]">
                      {ep.length_days}d
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
