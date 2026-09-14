"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, fetchBacktest, type BacktestResponse } from "@/lib/api";
import StatTiles from "@/components/StatTiles";
import EquityCurveChart from "@/components/EquityCurveChart";
import DrawdownChart from "@/components/DrawdownChart";
import MonthlyGrid from "@/components/MonthlyGrid";
import TradeLogTable from "@/components/TradeLogTable";
import ExitRuleControls, { type ExitRuleState } from "@/components/ExitRuleControls";
import ExitReasonBreakdown from "@/components/ExitReasonBreakdown";

const WEIGHT_LABEL: Record<number, { label: string; tone: string }> = {
  1: { label: "TQQQ (bullish)", tone: "bg-[#2a78d6]/10 text-[#184f95] dark:text-[#86b6ef]" },
  0: { label: "Cash (neutral)", tone: "bg-black/5 text-[#52514e] dark:bg-white/10 dark:text-[#c3c2b7]" },
  [-1]: { label: "SQQQ (bearish)", tone: "bg-[#e34948]/10 text-[#d03b3b]" },
};

const DEFAULT_EXIT_RULES: ExitRuleState = {
  enableStopLoss: true,
  stopLossPct: 0.12,
  enableFastTrendBreak: true,
  fastMaPeriod: 20,
  enableMeanReversionExit: true,
  extensionPct: 0.2,
};

export default function BacktestPage() {
  const [data, setData] = useState<BacktestResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [initialCapital, setInitialCapital] = useState(10000);
  const [exitRules, setExitRules] = useState<ExitRuleState>(DEFAULT_EXIT_RULES);

  const load = useCallback(async (refresh: boolean) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchBacktest({
        initialCapital,
        refresh,
        enableStopLoss: exitRules.enableStopLoss,
        stopLossPct: exitRules.stopLossPct,
        enableFastTrendBreak: exitRules.enableFastTrendBreak,
        fastMaPeriod: exitRules.fastMaPeriod,
        enableMeanReversionExit: exitRules.enableMeanReversionExit,
        extensionPct: exitRules.extensionPct,
      });
      setData(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unexpected error fetching backtest results.");
    } finally {
      setLoading(false);
    }
  }, [initialCapital, exitRules]);

  useEffect(() => {
    // Initial data fetch on mount; load() intentionally sets loading/error/data state.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load(false);
    // Only re-run on mount -- load() picks up the latest state via the ref below,
    // but we don't want to auto-refetch on every keystroke, only on explicit clicks.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const lastRow = data?.equity_curve[data.equity_curve.length - 1];
  const currentWeight = lastRow ? WEIGHT_LABEL[lastRow.target_weight] : undefined;

  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-[color:var(--tile-ink)]">
            Track A backtest — real TQQQ / SQQQ prices, 2010-onward
          </h1>
          <p className="mt-1 text-sm text-[#898781]">
            Entry (Job 1): {data ? `${data.config.ma_fast}d` : "50d"} &amp;{" "}
            {data ? `${data.config.ma_slow}d` : "250d"} moving averages on {data?.config.index_ticker ?? "^NDX"}.
            Above both → TQQQ. Below both → SQQQ. Otherwise → cash. Exit (Job 3): whichever of the
            rules below fires first.
          </p>
          {data && (
            <p className="mt-1 text-xs text-[#898781]">
              Data source: {data.config.data_source}
              {data.config.signal_ticker_used !== data.config.index_ticker && (
                <>
                  {" "}
                  — signal computed on {data.config.signal_ticker_used} (proxy for {data.config.index_ticker}
                  , unavailable from this data source)
                </>
              )}
            </p>
          )}
        </div>
        {currentWeight && (
          <div className={`rounded-lg px-3 py-2 text-sm font-medium ${currentWeight.tone}`}>
            Latest signal ({lastRow!.date}): {currentWeight.label}
          </div>
        )}
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
          onClick={() => load(false)}
          disabled={loading}
          className="rounded bg-[#2a78d6] px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {loading ? "Running…" : "Run backtest"}
        </button>
        <button
          onClick={() => load(true)}
          disabled={loading}
          className="rounded border border-black/15 px-3 py-1.5 text-sm font-medium text-[color:var(--tile-ink)] disabled:opacity-50 dark:border-white/15"
        >
          Refresh price data
        </button>
        {data && (
          <span className="text-xs text-[#898781]">
            {data.summary.start_date} → {data.summary.end_date}
          </span>
        )}
      </div>

      <div className="mb-6">
        <ExitRuleControls state={exitRules} onChange={setExitRules} />
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-[#d03b3b]/30 bg-[#d03b3b]/5 px-4 py-3 text-sm text-[#d03b3b]">
          <p className="font-medium">Couldn&apos;t load backtest data.</p>
          <p className="mt-1">{error}</p>
          <p className="mt-1 text-[#898781]">
            This usually means the backend can&apos;t reach Yahoo Finance and has no cached data yet — run
            the backend somewhere with normal internet access at least once.
          </p>
        </div>
      )}

      {loading && !data && (
        <div className="rounded-lg border border-black/10 bg-white px-4 py-8 text-center text-sm text-[#898781] dark:border-white/10 dark:bg-[#1a1a19]">
          Loading backtest…
        </div>
      )}

      {data && (
        <div className="flex flex-col gap-6">
          <StatTiles summary={data.summary} />
          <EquityCurveChart rows={data.equity_curve} />
          <DrawdownChart rows={data.drawdown} />
          <ExitReasonBreakdown breakdown={data.summary.exit_reason_breakdown} />
          <MonthlyGrid rows={data.monthly_returns} />
          <TradeLogTable trades={data.trade_log} />
        </div>
      )}
    </main>
  );
}
