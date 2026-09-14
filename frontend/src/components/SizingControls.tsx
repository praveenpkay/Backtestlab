export interface SizingState {
  enabled: boolean;
  rocPeriod: number;
  fullThreshold: number;
  partialThreshold: number;
  partialWeight: number;
  minWeight: number;
}

function NumberField({
  label,
  value,
  onChange,
  unit,
  step,
  min,
  disabled,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  unit: string;
  step: number;
  min: number;
  disabled: boolean;
}) {
  return (
    <label className="flex items-center gap-2 text-sm text-[color:var(--tile-ink)]">
      {label}
      <input
        type="number"
        min={min}
        step={step}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-20 rounded border border-black/15 bg-transparent px-2 py-1 text-sm tabular-nums disabled:opacity-40 dark:border-white/15"
      />
      <span className="text-[#898781]">{unit}</span>
    </label>
  );
}

export default function SizingControls({
  state,
  onChange,
}: {
  state: SizingState;
  onChange: (state: SizingState) => void;
}) {
  return (
    <div className="rounded-lg border border-black/10 bg-white px-4 py-2 dark:border-white/10 dark:bg-[#1a1a19]">
      <label className="flex items-center gap-2 pt-2 text-sm">
        <input
          type="checkbox"
          checked={state.enabled}
          onChange={(e) => onChange({ ...state, enabled: e.target.checked })}
          className="h-4 w-4"
        />
        <span className="font-semibold text-[color:var(--tile-ink)]">Job 2 — position sizing</span>
      </label>
      <p className="pb-1 text-xs text-[#898781]">
        Off: always 100% in or out. On: scales the position by {"^NDX"}&apos;s rate-of-change —
        stronger momentum → bigger size, weaker → trimmed.
      </p>
      <div className="flex flex-wrap gap-4 py-2">
        <NumberField
          label="ROC lookback"
          value={state.rocPeriod}
          onChange={(v) => onChange({ ...state, rocPeriod: v })}
          unit="days"
          step={1}
          min={2}
          disabled={!state.enabled}
        />
        <NumberField
          label="Full size at ≥"
          value={Math.round(state.fullThreshold * 100)}
          onChange={(v) => onChange({ ...state, fullThreshold: v / 100 })}
          unit="% ROC"
          step={1}
          min={1}
          disabled={!state.enabled}
        />
        <NumberField
          label="Partial size at ≥"
          value={Math.round(state.partialThreshold * 100)}
          onChange={(v) => onChange({ ...state, partialThreshold: v / 100 })}
          unit="% ROC"
          step={1}
          min={0}
          disabled={!state.enabled}
        />
        <NumberField
          label="Partial weight"
          value={Math.round(state.partialWeight * 100)}
          onChange={(v) => onChange({ ...state, partialWeight: v / 100 })}
          unit="%"
          step={5}
          min={1}
          disabled={!state.enabled}
        />
        <NumberField
          label="Min weight"
          value={Math.round(state.minWeight * 100)}
          onChange={(v) => onChange({ ...state, minWeight: v / 100 })}
          unit="%"
          step={5}
          min={1}
          disabled={!state.enabled}
        />
      </div>
    </div>
  );
}
