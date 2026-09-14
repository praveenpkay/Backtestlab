"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, fetchSignalHistory, type SignalHistoryResponse } from "@/lib/api";
import SignalOnlyBanner from "@/components/SignalOnlyBanner";
import RegimeStatTiles from "@/components/RegimeStatTiles";
import SignalPriceChart from "@/components/SignalPriceChart";
import SignalRegimeChart from "@/components/SignalRegimeChart";

export default function SignalHistoryPage() {
  const [data, setData] = useState<SignalHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (refresh: boolean) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchSignalHistory(refresh);
      setData(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unexpected error fetching signal history.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-[color:var(--tile-ink)]">
            Track B — long-history signal stress test
          </h1>
          <p className="mt-1 text-sm text-[#898781]">
            Runs the same Job 1 entry rule on real index history back to {data?.start_date ?? "1985"},
            covering crash regimes (2000 dot-com, 2008) the 2010+ TQQQ/SQQQ backtest never sees.
          </p>
        </div>
        <button
          onClick={() => load(true)}
          disabled={loading}
          className="rounded border border-black/15 px-3 py-1.5 text-sm font-medium text-[color:var(--tile-ink)] disabled:opacity-50 dark:border-white/15"
        >
          {loading ? "Loading…" : "Refresh data"}
        </button>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-[#d03b3b]/30 bg-[#d03b3b]/5 px-4 py-3 text-sm text-[#d03b3b]">
          <p className="font-medium">Couldn&apos;t load signal history.</p>
          <p className="mt-1">{error}</p>
        </div>
      )}

      {loading && !data && (
        <div className="rounded-lg border border-black/10 bg-white px-4 py-8 text-center text-sm text-[#898781] dark:border-white/10 dark:bg-[#1a1a19]">
          Loading…
        </div>
      )}

      {data && (
        <div className="flex flex-col gap-6">
          <SignalOnlyBanner disclaimer={data.disclaimer} tickerUsed={data.ticker_used} />
          <RegimeStatTiles stats={data.regime_stats} />
          <SignalPriceChart rows={data.series} tickerUsed={data.ticker_used} />
          <SignalRegimeChart rows={data.series} />
        </div>
      )}
    </main>
  );
}
