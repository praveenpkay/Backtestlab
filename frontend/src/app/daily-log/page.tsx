"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, fetchDailyLog, refreshDailyLog, type DailyLogRow } from "@/lib/api";
import DailySignalCard from "@/components/DailySignalCard";
import DailyWeightChart from "@/components/DailyWeightChart";
import DailyLogTable from "@/components/DailyLogTable";

export default function DailyLogPage() {
  const [rows, setRows] = useState<DailyLogRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchDailyLog();
      setRows(result.rows);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unexpected error fetching the daily log.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    setError(null);
    try {
      await refreshDailyLog();
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unexpected error logging today's signal.");
    } finally {
      setRefreshing(false);
    }
  };

  const latest = rows.length ? rows[rows.length - 1] : null;

  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-[color:var(--tile-ink)]">Daily signal log</h1>
          <p className="mt-1 text-sm text-[#898781]">
            A persisted, day-by-day record of what the Job 1 signal said — independent of any single
            backtest run. Log it once near the close on a day you want tracked.
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="rounded bg-[#2a78d6] px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {refreshing ? "Logging…" : "Log today's signal"}
        </button>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-[#d03b3b]/30 bg-[#d03b3b]/5 px-4 py-3 text-sm text-[#d03b3b]">
          <p className="font-medium">Something went wrong.</p>
          <p className="mt-1">{error}</p>
        </div>
      )}

      {loading ? (
        <div className="rounded-lg border border-black/10 bg-white px-4 py-8 text-center text-sm text-[#898781] dark:border-white/10 dark:bg-[#1a1a19]">
          Loading…
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          <DailySignalCard row={latest} />
          <DailyWeightChart rows={rows} />
          <DailyLogTable rows={rows} />
        </div>
      )}
    </main>
  );
}
