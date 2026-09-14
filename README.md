# Backtest Lab

A personal tool to backtest a trend-following long/short strategy on TQQQ/SQQQ
(3x leveraged NASDAQ-100 ETFs), signaled off the underlying `^NDX` index. See
the original build spec for the full context and rationale.

**What's built:** a real, honest backtest on actual TQQQ/SQQQ/^NDX daily
prices from 2010 onward (Track A), plus a signal-only stress test on real
index history back to 1985 (Track B, never turned into fake dollar returns).
Job 1 (entry/direction), Job 2 (position sizing), and Job 3 (exit/square-off)
are all implemented, tunable, and layered on top of each other. A scenario
engine runs several parameter combinations against the same history at once
with buy-and-hold benchmarks, extra risk KPIs, a plain-English readout, and
walk-forward validation. Fees/slippage are modeled and on by default. A daily
signal log persists what the live signal says day over day, with a plain-
English explanation of today's call and what would flip it. No synthetic
leveraged-return simulation anywhere in the app.

## Architecture

- **`backend/`** — Python FastAPI service. Pulls daily prices from a
  pluggable data source, runs the signal/sizing/exit/fee pipeline, and
  serves backtests, scenario comparisons, walk-forward results, the daily
  signal log, and the Track B signal history as JSON.
- **`frontend/`** — Next.js app with four pages: **Backtest** (single-run
  detail), **Scenarios** (compare several runs + walk-forward), **Daily
  Log** (today's signal + history), **Signal History** (Track B).

## Data sources

Real data only, from each fund's real inception (TQQQ/SQQQ from 2010) — this
app never fabricates or simulates pre-inception leveraged-ETF prices.

- **Stooq (default, no setup)** — `backend/app/datasources/stooq.py`. Free,
  documented, no API key. This is what the app uses out of the box
  (`DATA_SOURCE=stooq`).
- **Polygon.io (optional)** — free key, ~2 minutes to get:
  1. Sign up at https://polygon.io/dashboard/signup and copy your API key.
  2. `cp backend/.env.example backend/.env`, paste it into `POLYGON_API_KEY=`.
  3. Set `DATA_SOURCE=polygon` in that same `.env` file.
- **Alpaca (optional)** — free key pair, ~2 minutes to get:
  1. Sign up at https://app.alpaca.markets/signup (the free paper-trading
     account includes market data).
  2. Copy the key ID and secret into `backend/.env`
     (`ALPACA_API_KEY_ID=`, `ALPACA_SECRET_KEY=`).
  3. Set `DATA_SOURCE=alpaca`.

Neither key is required — the app works fully with zero setup on Stooq. If
`^NDX` isn't available from whatever source is configured, the app falls
back to `QQQ` as the signal proxy automatically, and labels results
accordingly (both in the UI and in `config.signal_ticker_used` in API
responses) so you always know which one was actually used.

If you're running this in a network-restricted environment (like a CI
sandbox), the API returns a `503` with a clear error message instead of
crashing. Run the backend somewhere with normal internet access at least
once to populate `backend/data_cache/` — after that, cached data is reused
for up to `CACHE_TTL_HOURS` (see `backend/app/config.py`) even if the data
source is briefly unreachable.

## Running it locally

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt   # includes pytest + httpx for tests
uvicorn app.main:app --reload --port 8000
```

Run the test suite (100+ tests, all against a deterministic synthetic price
fixture or mocked HTTP responses — no network required):

```bash
pytest
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # points at http://localhost:8000 by default
npm run dev
```

Open http://localhost:3000.

If you run the backend on a non-default host/port, set
`NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local` and `CORS_ORIGINS` (comma
separated) when starting the backend, e.g.:

```bash
CORS_ORIGINS="http://localhost:3000" uvicorn app.main:app --reload
```

## The strategy pipeline

Each job is its own module, composed in `backend/app/backtest.py`:

1. **Entry signal (Job 1, `signals.py`):** on `^NDX`, price above both the
   50d and 250d moving average → target TQQQ; below both → target SQQQ;
   otherwise → cash. The signal on day *T*'s close sets the position held
   from *T* to *T+1* (no lookahead). MA lengths are overridable per scenario.
2. **Exit rules (Job 3, `exits.py`):** a pluggable registry (`EXIT_RULES`) of
   independently-toggleable rules evaluated in order, each just a function +
   a config flag/threshold — adding a fourth rule needs no changes to the
   overlay loop itself:
   - **Stop-loss** — exit if the held ETF is down more than `stop_loss_pct`
     (default 12%) from entry.
   - **Fast trend-break** — exit if `^NDX` closes back across a faster
     moving average (default 20d) than the slow 250d one Job 1 waits for.
   - **Mean-reversion extension** — exit if `^NDX` has stretched more than
     `extension_pct` (default 20%) above/below its 50d MA.

   Whichever rule (including Job 1's own signal flip) fires first closes
   the position. Disabling all three reproduces plain Job-1-only behavior
   byte-for-byte (regression-tested).
3. **Position sizing (Job 2, `sizing.py`):** off by default (always 100% in
   or out). When enabled, scales exposure by `^NDX` rate-of-change —
   accelerating trend → bigger size, decelerating → trimmed to a partial or
   minimum weight. Sign always matches Job 1+3's direction; sizing only
   scales magnitude. A pure resize (same direction, different size) shows up
   in the trade log tagged `exit_reason: "resize"`, distinct from a real exit.
4. **Fees/slippage (`fee_bps` in `run_backtest`):** a flat cost in basis
   points of notional, charged on every rebalance proportional to how much
   the target weight actually changed. On by default (5 bps) at the API
   level — the spec's own "show results with it on" — off by default at the
   raw function level. Reported as `summary.total_fees_paid`.

Every trade is tagged with `exit_reason` (`signal_flip`, `stop_loss`,
`fast_trend_break`, `mean_reversion_extension`, or `resize`) and rolled up
into a per-backtest breakdown, so you can see which rule is actually doing
the work rather than guessing.

**Outputs, per run:** trade log (symbol, dates, duration, buy/sell price,
share size, size %, profit, profit %, win/loss, long/short, exit reason —
downloadable as CSV), equity curve vs. QQQ buy-and-hold, drawdown ("underwater")
series, monthly/yearly return grid, and summary stats (CAGR, total return,
win rate, profit/loss ratio, max drawdown + duration, total fees paid).

## Scenario comparison + walk-forward validation

The **Scenarios** page (`/scenarios`, `backend/app/scenarios.py`) runs
several named parameter combinations — different MA lengths, exit rules
on/off, sizing on/off, fees — against the same real history in one pass,
alongside buy-and-hold TQQQ and QQQ benchmark rows. Beyond the per-run
summary stats, each scenario also gets (`backend/app/kpis.py`):

- The full list of **drawdown episodes** (peak/trough/recovery dates, depth,
  length), not just the single worst one, including ongoing (unrecovered)
  episodes.
- Count of **drawdowns worse than 20%**.
- **Worst single day** and **worst month**.
- **Longest losing-trade streak**, with its compounded (not summed) cost.
- **Calmar ratio** (CAGR per unit of max drawdown) for risk-adjusted
  comparison against the benchmarks.
- A deterministic **plain-English readout** (`backend/app/readout.py`)
  answering: does this beat buy-and-hold, risk-adjusted? How deep/long are
  the worst drawdowns? How bad have losing streaks been? Is this a fragile,
  small-sample result?

Optionally set a **walk-forward split date**: each scenario is then scored
separately on the in-sample period before that date and the out-of-sample
period after it (each rebased to start fresh at the split, so one period's
drawdowns don't contaminate the other's). The panel flags loudly — with a
specific reason — when out-of-sample has no trades, when in-sample looked
strong but out-of-sample went negative, or when out-of-sample's drawdown is
notably worse, so an in-sample-only result doesn't quietly pass as proven.

## Track B: long-history signal stress test

The **Signal History** page (`/signal-history`, `backend/app/trackb.py`)
runs the Job 1 signal on real index history back to 1985 — covering the 2000
dot-com and 2008 crashes the 2010+ TQQQ/SQQQ data doesn't contain. It is
**always** signal-only: regime percentages (time spent long/short/cash),
number of regime changes, longest streaks — never simulated dollar returns,
per the original spec's warning about naive `×3` leveraged-return simulation.

## Daily signal log

The **Daily Log** page (`/daily-log`) shows the current dial (TQQQ / cash /
SQQQ), a plain-English explanation of *why* (`backend/app/rationale.py`) and
what would flip it next (Job 1's own flip level, plus the Job 3 rules that
don't need a live entry price — stop-loss is called out as needing your own
actual entry, which this snapshot doesn't track), and a history table +
chart. Clicking "Log today's signal" calls `POST /api/daily-log/refresh`,
which upserts a row into a local SQLite file (`backend/backtestlab.db`,
keyed by trading date — safe to click more than once on the same day). This
is deliberately separate from the backtest: it accumulates real history over
time regardless of how backtest parameters get tuned later, and is the
actual "am I doing well" record. There's no scheduler yet — you (or a cron
job you set up) need to trigger the refresh near each day's close.

## Deploy your own copy (get a real link)

This session has no hosting credentials of its own, so there's no link I can
generate for you directly — but the repo is set up so you can get one
yourself in about 5 minutes, on free tiers, with no credit card:

1. **Backend → [Render](https://render.com):** click
   **[Deploy to Render](https://render.com/deploy?repo=https://github.com/praveenpkay/Backtestlab)**.
   Render reads `render.yaml` at the repo root and provisions the FastAPI
   service automatically. Once it's live, copy its URL (e.g.
   `https://backtestlab-api.onrender.com`).
2. **Frontend → [Vercel](https://vercel.com):** click
   **[Deploy to Vercel](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fpraveenpkay%2FBacktestlab&root-directory=frontend&env=NEXT_PUBLIC_API_BASE_URL&envDescription=URL%20of%20the%20backend%20you%20deployed%20on%20Render%20in%20step%201)**.
   When prompted for `NEXT_PUBLIC_API_BASE_URL`, paste the Render URL from
   step 1. This gives you your real, shareable link.
3. **Connect them:** back in the Render dashboard, set the backend's
   `CORS_ORIGINS` env var to your new Vercel URL and redeploy, so the
   frontend is allowed to call it.

**Known limitations of the free tiers** (fine for trying it out, worth
knowing about):
- Render's free plan spins the backend down after 15 minutes idle — the
  first request after a while can take 30–60s to wake it up.
- Render's free plan has an ephemeral filesystem, so `backend/data_cache/`
  and the daily-log SQLite file (`backend/backtestlab.db`) reset on every
  redeploy. The backtest itself is unaffected (it re-fetches on demand), but
  the daily signal log won't persist across redeploys until it's backed by a
  real disk or a hosted database — a reasonable next step once you're using
  it daily.

## Not built yet (by design, per current priorities)

- Paper trading / live order placement (this is backtest + daily signal
  logging only, as the spec's hard constraints require).
- Automatic daily scheduling of the signal-log refresh (currently manual/
  on-demand).
- Persistent storage for the daily log on the free-tier deploy path above.
- A UI for defining fully custom Job 3/Job 2 thresholds per scenario (the
  Scenarios page uses simplified on/off presets per row; the main Backtest
  page has the full threshold controls for a single run).
