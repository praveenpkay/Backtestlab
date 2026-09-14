export default function SignalOnlyBanner({ disclaimer, tickerUsed }: { disclaimer: string; tickerUsed: string }) {
  return (
    <div className="rounded-lg border border-[#eda100]/40 bg-[#eda100]/10 px-4 py-3 text-sm text-[color:var(--tile-ink)]">
      <p className="font-semibold">Track B — signal-only, illustration only</p>
      <p className="mt-1">{disclaimer}</p>
      <p className="mt-1 text-xs text-[#898781]">
        Series computed on {tickerUsed}. No dollar returns, no equity curve, no leverage simulated —
        just where the Job 1 signal would have pointed, day by day, back through crash regimes the
        2010+ TQQQ/SQQQ backtest doesn&apos;t contain.
      </p>
    </div>
  );
}
