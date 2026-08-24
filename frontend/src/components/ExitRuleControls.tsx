export interface ExitRuleState {
  enableStopLoss: boolean;
  stopLossPct: number;
  enableFastTrendBreak: boolean;
  fastMaPeriod: number;
  enableMeanReversionExit: boolean;
  extensionPct: number;
}

function Rule({
  checked,
  onCheckedChange,
  label,
  description,
  value,
  onValueChange,
  unit,
  step,
  min,
}: {
  checked: boolean;
  onCheckedChange: (v: boolean) => void;
  label: string;
  description: string;
  value: number;
  onValueChange: (v: number) => void;
  unit: string;
  step: number;
  min: number;
}) {
  return (
    <div className="flex flex-wrap items-center gap-3 py-2">
      <label className="flex items-center gap-2 text-sm text-[color:var(--tile-ink)]">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onCheckedChange(e.target.checked)}
          className="h-4 w-4"
        />
        <span className="font-medium">{label}</span>
      </label>
      <span className="text-xs text-[#898781]">{description}</span>
      <span className="ml-auto flex items-center gap-1 text-sm">
        <input
          type="number"
          min={min}
          step={step}
          value={value}
          disabled={!checked}
          onChange={(e) => onValueChange(Number(e.target.value))}
          className="w-20 rounded border border-black/15 bg-transparent px-2 py-1 text-sm tabular-nums disabled:opacity-40 dark:border-white/15"
        />
        <span className="text-[#898781]">{unit}</span>
      </span>
    </div>
  );
}

export default function ExitRuleControls({
  state,
  onChange,
}: {
  state: ExitRuleState;
  onChange: (state: ExitRuleState) => void;
}) {
  return (
    <div className="rounded-lg border border-black/10 bg-white px-4 py-2 dark:border-white/10 dark:bg-[#1a1a19]">
      <h3 className="pt-2 text-sm font-semibold text-[color:var(--tile-ink)]">
        Job 3 — exit rules
      </h3>
      <p className="pb-1 text-xs text-[#898781]">
        Layered on top of the Job 1 entry rule. Without these, you only exit when the entry rule
        itself flips.
      </p>
      <div className="divide-y divide-black/5 dark:divide-white/5">
        <Rule
          checked={state.enableStopLoss}
          onCheckedChange={(v) => onChange({ ...state, enableStopLoss: v })}
          label="Stop-loss"
          description="Exit if the held ETF is down this much from entry"
          value={Math.round(state.stopLossPct * 100)}
          onValueChange={(v) => onChange({ ...state, stopLossPct: v / 100 })}
          unit="%"
          step={1}
          min={1}
        />
        <Rule
          checked={state.enableFastTrendBreak}
          onCheckedChange={(v) => onChange({ ...state, enableFastTrendBreak: v })}
          label="Fast trend-break"
          description="Exit if ^NDX closes back across this faster MA"
          value={state.fastMaPeriod}
          onValueChange={(v) => onChange({ ...state, fastMaPeriod: v })}
          unit="days"
          step={1}
          min={2}
        />
        <Rule
          checked={state.enableMeanReversionExit}
          onCheckedChange={(v) => onChange({ ...state, enableMeanReversionExit: v })}
          label="Mean-reversion extension"
          description="Exit if ^NDX stretches this far above/below its 50d MA"
          value={Math.round(state.extensionPct * 100)}
          onValueChange={(v) => onChange({ ...state, extensionPct: v / 100 })}
          unit="%"
          step={1}
          min={1}
        />
      </div>
    </div>
  );
}
