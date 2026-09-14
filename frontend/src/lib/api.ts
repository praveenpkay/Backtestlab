export interface TradeLogRow {
  symbol: string;
  start_date: string;
  end_date: string;
  duration_days: number;
  buy_price: number;
  sell_price: number;
  share_size: number;
  profit: number;
  profit_pct: number;
  is_profitable: boolean;
  is_short: boolean;
  is_open: boolean;
  exit_reason: string | null;
}

export interface EquityCurveRow {
  date: string;
  strategy_equity: number;
  benchmark_equity: number;
  target_weight: number;
}

export interface DrawdownRow {
  date: string;
  drawdown_pct: number;
}

export interface MonthlyReturnRow {
  year: number;
  month: number;
  return_pct: number;
}

export interface SummaryStats {
  start_date: string;
  end_date: string;
  initial_capital: number;
  final_equity: number;
  cagr_pct: number;
  total_return_pct: number;
  num_trades: number;
  win_rate_pct: number;
  profit_loss_ratio: number | null;
  max_drawdown_pct: number;
  max_drawdown_days: number;
  exit_reason_breakdown: Record<string, number>;
}

export interface ExitRulesConfig {
  enable_stop_loss: boolean;
  stop_loss_pct: number;
  enable_fast_trend_break: boolean;
  fast_ma_period: number;
  enable_mean_reversion_exit: boolean;
  extension_pct: number;
}

export interface BacktestConfig {
  index_ticker: string;
  signal_ticker_used: string;
  data_source: string;
  long_ticker: string;
  short_ticker: string;
  benchmark_ticker: string;
  ma_fast: number;
  ma_slow: number;
  track_a_start: string;
  exit_rules: ExitRulesConfig;
}

export interface BacktestResponse {
  trade_log: TradeLogRow[];
  equity_curve: EquityCurveRow[];
  drawdown: DrawdownRow[];
  monthly_returns: MonthlyReturnRow[];
  summary: SummaryStats;
  config: BacktestConfig;
}

export interface DailyLogRow {
  date: string;
  ndx_close: number;
  ma_fast: number | null;
  ma_slow: number | null;
  target_weight: number;
  symbol: string;
  signal_ticker: string | null;
  rationale: string | null;
  next_exit_trigger: string | null;
}

export interface SignalHistoryRow {
  date: string;
  close: number;
  ma_fast: number | null;
  ma_slow: number | null;
  target_weight: number;
}

export interface RegimeStreak {
  count: number;
  longest_days: number;
}

export interface RegimeStats {
  pct_days_long: number;
  pct_days_short: number;
  pct_days_cash: number;
  num_regime_changes: number;
  long_streaks: RegimeStreak;
  short_streaks: RegimeStreak;
  cash_streaks: RegimeStreak;
}

export interface SignalHistoryResponse {
  signal_only: true;
  disclaimer: string;
  ticker_used: string;
  start_date: string | null;
  end_date: string | null;
  series: SignalHistoryRow[];
  regime_stats: RegimeStats;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {}

export interface FetchBacktestOpts {
  initialCapital?: number;
  refresh?: boolean;
  enableStopLoss?: boolean;
  stopLossPct?: number;
  enableFastTrendBreak?: boolean;
  fastMaPeriod?: number;
  enableMeanReversionExit?: boolean;
  extensionPct?: number;
}

export async function fetchBacktest(opts: FetchBacktestOpts = {}): Promise<BacktestResponse> {
  const params = new URLSearchParams();
  if (opts.initialCapital) params.set("initial_capital", String(opts.initialCapital));
  if (opts.refresh) params.set("refresh", "true");
  if (opts.enableStopLoss !== undefined) params.set("enable_stop_loss", String(opts.enableStopLoss));
  if (opts.stopLossPct !== undefined) params.set("stop_loss_pct", String(opts.stopLossPct));
  if (opts.enableFastTrendBreak !== undefined)
    params.set("enable_fast_trend_break", String(opts.enableFastTrendBreak));
  if (opts.fastMaPeriod !== undefined) params.set("fast_ma_period", String(opts.fastMaPeriod));
  if (opts.enableMeanReversionExit !== undefined)
    params.set("enable_mean_reversion_exit", String(opts.enableMeanReversionExit));
  if (opts.extensionPct !== undefined) params.set("extension_pct", String(opts.extensionPct));

  const res = await fetch(`${API_BASE}/api/backtest?${params.toString()}`, {
    cache: "no-store",
  });

  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // ignore parse errors, fall back to the generic message
    }
    throw new ApiError(detail);
  }

  return res.json();
}

export async function fetchDailyLog(limit?: number): Promise<{ rows: DailyLogRow[] }> {
  const params = new URLSearchParams();
  if (limit) params.set("limit", String(limit));

  const res = await fetch(`${API_BASE}/api/daily-log?${params.toString()}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new ApiError(`Request failed with status ${res.status}`);
  }
  return res.json();
}

export async function refreshDailyLog(): Promise<DailyLogRow> {
  const res = await fetch(`${API_BASE}/api/daily-log/refresh`, {
    method: "POST",
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // ignore parse errors, fall back to the generic message
    }
    throw new ApiError(detail);
  }
  return res.json();
}

export async function fetchSignalHistory(refresh?: boolean): Promise<SignalHistoryResponse> {
  const params = new URLSearchParams();
  if (refresh) params.set("refresh", "true");

  const res = await fetch(`${API_BASE}/api/signal-history?${params.toString()}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // ignore parse errors, fall back to the generic message
    }
    throw new ApiError(detail);
  }
  return res.json();
}
