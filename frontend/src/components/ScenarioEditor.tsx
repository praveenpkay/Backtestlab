"use client";

import type { ScenarioDefinition } from "@/lib/api";

export interface EditableScenario {
  id: string;
  name: string;
  maFast: number;
  maSlow: number;
  exitPreset: "none" | "default";
  enableSizing: boolean;
  feeBps: number;
}

export function toScenarioDefinition(row: EditableScenario): ScenarioDefinition {
  const exitsOn = row.exitPreset === "default";
  return {
    name: row.name,
    ma_fast: row.maFast,
    ma_slow: row.maSlow,
    enable_stop_loss: exitsOn,
    enable_fast_trend_break: exitsOn,
    enable_mean_reversion_exit: exitsOn,
    enable_sizing: row.enableSizing,
    fee_bps: row.feeBps,
  };
}

let nextId = 1;
export function blankScenario(): EditableScenario {
  return {
    id: `scenario-${nextId++}`,
    name: "New scenario",
    maFast: 50,
    maSlow: 250,
    exitPreset: "default",
    enableSizing: false,
    feeBps: 5,
  };
}

export default function ScenarioEditor({
  rows,
  onChange,
}: {
  rows: EditableScenario[];
  onChange: (rows: EditableScenario[]) => void;
}) {
  const update = (id: string, patch: Partial<EditableScenario>) => {
    onChange(rows.map((r) => (r.id === id ? { ...r, ...patch } : r)));
  };
  const remove = (id: string) => onChange(rows.filter((r) => r.id !== id));
  const add = () => onChange([...rows, blankScenario()]);

  return (
    <div className="rounded-lg border border-black/10 bg-white p-4 dark:border-white/10 dark:bg-[#1a1a19]">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[color:var(--tile-ink)]">Scenarios to compare</h3>
        <button
          onClick={add}
          className="rounded border border-black/15 px-2 py-1 text-xs font-medium text-[color:var(--tile-ink)] dark:border-white/15"
        >
          + Add scenario
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] border-collapse text-xs">
          <thead>
            <tr className="text-left text-[#898781]">
              <th className="py-1.5 pr-3 font-medium">Name</th>
              <th className="py-1.5 pr-3 font-medium">MA fast</th>
              <th className="py-1.5 pr-3 font-medium">MA slow</th>
              <th className="py-1.5 pr-3 font-medium">Job 3 exits</th>
              <th className="py-1.5 pr-3 font-medium">Job 2 sizing</th>
              <th className="py-1.5 pr-3 font-medium">Fees (bps)</th>
              <th className="py-1.5 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-t border-black/5 dark:border-white/5">
                <td className="py-1.5 pr-3">
                  <input
                    value={row.name}
                    onChange={(e) => update(row.id, { name: e.target.value })}
                    className="w-40 rounded border border-black/15 bg-transparent px-2 py-1 text-[color:var(--tile-ink)] dark:border-white/15"
                  />
                </td>
                <td className="py-1.5 pr-3">
                  <input
                    type="number"
                    min={2}
                    value={row.maFast}
                    onChange={(e) => update(row.id, { maFast: Number(e.target.value) })}
                    className="w-16 rounded border border-black/15 bg-transparent px-2 py-1 tabular-nums text-[color:var(--tile-ink)] dark:border-white/15"
                  />
                </td>
                <td className="py-1.5 pr-3">
                  <input
                    type="number"
                    min={2}
                    value={row.maSlow}
                    onChange={(e) => update(row.id, { maSlow: Number(e.target.value) })}
                    className="w-16 rounded border border-black/15 bg-transparent px-2 py-1 tabular-nums text-[color:var(--tile-ink)] dark:border-white/15"
                  />
                </td>
                <td className="py-1.5 pr-3">
                  <select
                    value={row.exitPreset}
                    onChange={(e) => update(row.id, { exitPreset: e.target.value as "none" | "default" })}
                    className="rounded border border-black/15 bg-transparent px-2 py-1 text-[color:var(--tile-ink)] dark:border-white/15"
                  >
                    <option value="none">Off (signal-flip only)</option>
                    <option value="default">On (default thresholds)</option>
                  </select>
                </td>
                <td className="py-1.5 pr-3">
                  <input
                    type="checkbox"
                    checked={row.enableSizing}
                    onChange={(e) => update(row.id, { enableSizing: e.target.checked })}
                    className="h-4 w-4"
                  />
                </td>
                <td className="py-1.5 pr-3">
                  <input
                    type="number"
                    min={0}
                    value={row.feeBps}
                    onChange={(e) => update(row.id, { feeBps: Number(e.target.value) })}
                    className="w-16 rounded border border-black/15 bg-transparent px-2 py-1 tabular-nums text-[color:var(--tile-ink)] dark:border-white/15"
                  />
                </td>
                <td className="py-1.5">
                  <button
                    onClick={() => remove(row.id)}
                    disabled={rows.length <= 1}
                    className="text-[#d03b3b] disabled:opacity-30"
                  >
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
