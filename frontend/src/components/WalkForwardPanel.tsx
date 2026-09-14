import type { WalkForwardPeriodKpis, WalkForwardResult } from "@/lib/api";

function Column({ label, kpis }: { label: string; kpis: WalkForwardPeriodKpis }) {
  return (
    <div className="flex-1 rounded border border-black/10 p-3 dark:border-white/10">
      <div className="text-xs font-semibold uppercase tracking-wide text-[#898781]">{label}</div>
      <div className="mt-1 text-xs text-[#898781]">
        {kpis.start_date} → {kpis.end_date}
      </div>
      <dl className="mt-2 grid grid-cols-2 gap-1 text-xs">
        <dt className="text-[#898781]">CAGR</dt>
        <dd className="text-right tabular-nums text-[color:var(--tile-ink)]">{kpis.cagr_pct.toFixed(1)}%</dd>
        <dt className="text-[#898781]">Total return</dt>
        <dd className="text-right tabular-nums text-[color:var(--tile-ink)]">{kpis.total_return_pct.toFixed(1)}%</dd>
        <dt className="text-[#898781]">Max drawdown</dt>
        <dd className="text-right tabular-nums text-[#d03b3b]">{kpis.max_drawdown_pct.toFixed(1)}%</dd>
        <dt className="text-[#898781]">Trades</dt>
        <dd className="text-right tabular-nums text-[color:var(--tile-ink)]">{kpis.num_trades}</dd>
        <dt className="text-[#898781]">Win rate</dt>
        <dd className="text-right tabular-nums text-[color:var(--tile-ink)]">{kpis.win_rate_pct.toFixed(1)}%</dd>
        <dt className="text-[#898781]">Calmar</dt>
        <dd className="text-right tabular-nums text-[color:var(--tile-ink)]">
          {kpis.calmar_ratio == null ? "—" : kpis.calmar_ratio.toFixed(2)}
        </dd>
      </dl>
    </div>
  );
}

export default function WalkForwardPanel({ result }: { result: WalkForwardResult }) {
  if (result.error) {
    return (
      <div className="rounded border border-[#d03b3b]/30 bg-[#d03b3b]/5 p-3 text-xs text-[#d03b3b]">
        Walk-forward split failed: {result.error}
      </div>
    );
  }

  return (
    <div>
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[#898781]">
        Walk-forward: split at {result.split_date}
      </h4>
      <div className="flex flex-col gap-2 sm:flex-row">
        <Column label="In-sample" kpis={result.in_sample} />
        <Column label="Out-of-sample" kpis={result.out_of_sample} />
      </div>
      {result.flag && result.flag_reason && (
        <p className="mt-2 rounded border border-[#eda100]/40 bg-[#eda100]/10 p-2 text-xs text-[color:var(--tile-ink)]">
          ⚠ {result.flag_reason}
        </p>
      )}
    </div>
  );
}
