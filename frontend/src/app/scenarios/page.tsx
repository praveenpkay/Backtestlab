"use client";

import { useState } from "react";
import { ApiError, compareScenarios, type CompareResponse } from "@/lib/api";
import ScenarioEditor, { toScenarioDefinition, type EditableScenario } from "@/components/ScenarioEditor";
import ScenarioComparisonTable from "@/components/ScenarioComparisonTable";
import ScenarioEquityChart from "@/components/ScenarioEquityChart";
import ScenarioDetailCard from "@/components/ScenarioDetailCard";

function defaultRows(): EditableScenario[] {
  return [
    { id: "s1", name: "Job 1 only (50/250)", maFast: 50, maSlow: 250, exitPreset: "none", enableSizing: false },
    { id: "s2", name: "Job 1 + Job 3 (50/250)", maFast: 50, maSlow: 250, exitPreset: "default", enableSizing: false },
    {
      id: "s3",
      name: "Job 1 + Job 3 + Job 2 (50/250)",
      maFast: 50,
      maSlow: 250,
      exitPreset: "default",
      enableSizing: true,
    },
    { id: "s4", name: "Faster entry (20/100)", maFast: 20, maSlow: 100, exitPreset: "default", enableSizing: false },
  ];
}

export default function ScenariosPage() {
  const [rows, setRows] = useState<EditableScenario[]>(defaultRows());
  const [initialCapital, setInitialCapital] = useState(10000);
  const [result, setResult] = useState<CompareResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async (refresh: boolean) => {
    setLoading(true);
    setError(null);
    try {
      const response = await compareScenarios({
        initialCapital,
        refresh,
        scenarios: rows.map(toScenarioDefinition),
      });
      setResult(response);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unexpected error running the comparison.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-[color:var(--tile-ink)]">Scenario comparison</h1>
        <p className="mt-1 text-sm text-[#898781]">
          Run several rule combinations against the same real price history at once, side by side with
          buy-and-hold TQQQ and QQQ, instead of tweaking the main backtest page one run at a time.
        </p>
      </div>

      <div className="mb-6 flex flex-wrap items-center gap-3 rounded-lg border border-black/10 bg-white px-4 py-3 dark:border-white/10 dark:bg-[#1a1a19]">
        <label className="flex items-center gap-2 text-sm text-[color:var(--tile-ink)]">
          Starting capital
          <input
            type="number"
            min={100}
            step={100}
            value={initialCapital}
            onChange={(e) => setInitialCapital(Number(e.target.value))}
            className="w-28 rounded border border-black/15 bg-transparent px-2 py-1 text-sm tabular-nums dark:border-white/15"
          />
        </label>
        <button
          onClick={() => run(false)}
          disabled={loading}
          className="rounded bg-[#2a78d6] px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {loading ? "Running…" : "Run comparison"}
        </button>
        <button
          onClick={() => run(true)}
          disabled={loading}
          className="rounded border border-black/15 px-3 py-1.5 text-sm font-medium text-[color:var(--tile-ink)] disabled:opacity-50 dark:border-white/15"
        >
          Refresh price data
        </button>
      </div>

      <div className="mb-6">
        <ScenarioEditor rows={rows} onChange={setRows} />
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-[#d03b3b]/30 bg-[#d03b3b]/5 px-4 py-3 text-sm text-[#d03b3b]">
          <p className="font-medium">Couldn&apos;t run the comparison.</p>
          <p className="mt-1">{error}</p>
        </div>
      )}

      {result && (
        <div className="flex flex-col gap-6">
          <ScenarioComparisonTable rows={result.scenarios} />
          <ScenarioEquityChart rows={result.scenarios} />
          {result.scenarios.map((row) => (
            <ScenarioDetailCard key={row.name} row={row} />
          ))}
        </div>
      )}

      {!result && !loading && (
        <div className="rounded-lg border border-black/10 bg-white px-4 py-8 text-center text-sm text-[#898781] dark:border-white/10 dark:bg-[#1a1a19]">
          Set up your scenarios above, then click &quot;Run comparison.&quot;
        </div>
      )}
    </main>
  );
}
