import type { DailyLogRow } from "@/lib/api";

const SYMBOL_STYLE: Record<string, { label: string; tone: string }> = {
  TQQQ: { label: "TQQQ (bullish)", tone: "bg-[#2a78d6]/10 text-[#184f95] dark:text-[#86b6ef]" },
  CASH: { label: "Cash (neutral)", tone: "bg-black/5 text-[#52514e] dark:bg-white/10 dark:text-[#c3c2b7]" },
  SQQQ: { label: "SQQQ (bearish)", tone: "bg-[#e34948]/10 text-[#d03b3b]" },
};

export default function DailySignalCard({ row }: { row: DailyLogRow | null }) {
  if (!row) {
    return (
      <div className="rounded-lg border border-black/10 bg-white p-6 text-center text-sm text-[#898781] dark:border-white/10 dark:bg-[#1a1a19]">
        No signal logged yet. Click &quot;Log today&apos;s signal&quot; to record the first entry.
      </div>
    );
  }

  const style = SYMBOL_STYLE[row.symbol] ?? SYMBOL_STYLE.CASH;

  return (
    <div className="rounded-lg border border-black/10 bg-white p-6 dark:border-white/10 dark:bg-[#1a1a19]">
      <div className="text-xs font-medium uppercase tracking-wide text-[#898781]">
        Latest logged signal — {row.date}
      </div>
      <div className={`mt-2 inline-block rounded-lg px-3 py-1.5 text-lg font-semibold ${style.tone}`}>
        {style.label}
      </div>
      <dl className="mt-4 grid grid-cols-3 gap-4 text-sm">
        <div>
          <dt className="text-[#898781]">^NDX close</dt>
          <dd className="tabular-nums text-[color:var(--tile-ink)]">{row.ndx_close.toFixed(2)}</dd>
        </div>
        <div>
          <dt className="text-[#898781]">50d MA</dt>
          <dd className="tabular-nums text-[color:var(--tile-ink)]">
            {row.ma_fast == null ? "—" : row.ma_fast.toFixed(2)}
          </dd>
        </div>
        <div>
          <dt className="text-[#898781]">250d MA</dt>
          <dd className="tabular-nums text-[color:var(--tile-ink)]">
            {row.ma_slow == null ? "—" : row.ma_slow.toFixed(2)}
          </dd>
        </div>
      </dl>
      {row.rationale && (
        <p className="mt-4 border-t border-black/5 pt-3 text-sm text-[color:var(--tile-ink)] dark:border-white/5">
          <span className="font-medium">Why: </span>
          {row.rationale}
        </p>
      )}
      {row.next_exit_trigger && (
        <p className="mt-2 text-sm text-[#898781]">
          <span className="font-medium text-[color:var(--tile-ink)]">Next exit trigger: </span>
          {row.next_exit_trigger}
        </p>
      )}
    </div>
  );
}
