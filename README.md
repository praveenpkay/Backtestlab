# Backtest Lab

A personal tool to backtest a trend-following long/short strategy on TQQQ/SQQQ
(3x leveraged NASDAQ-100 ETFs), signaled off the underlying `^NDX` index. See
the original build spec for the full context and rationale.

**MVP scope (this build):** Track A only — a real, honest backtest on actual
TQQQ/SQQQ/^NDX daily prices from 2010 onward. Job 1 (entry/direction: 50-day
and 250-day moving averages on `^NDX`) plus Job 3 (exit/square-off: three
basic, toggleable rules — see below), a persisted daily signal log so you can
track what the live signal says day over day, and a deploy path so you can
get a real hosted link. No synthetic leverage simulation, no Track B pre-2010
stress test, no Job 2 (position sizing — still always 100% in or out) yet.

## Architecture

- **`backend/`** — Python FastAPI service. Pulls daily prices from a
  pluggable data source, computes the signal, runs the backtest, and serves
  the results as JSON.
- **`frontend/`** — Next.js app. Fetches `/api/backtest` and renders the
  equity curve, drawdown chart, monthly return grid, summary stats, and trade
  log.

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
accordingly (both on the backtest page and in `/api/backtest`'s
`config.signal_ticker_used` field) so you always know which one was actually
used.

If you're running this in a network-restricted environment (like a CI
sandbox), `/api/backtest` returns a `503` with a clear error message instead
of crashing. Run the backend somewhere with normal internet access at least
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

Run the test suite (uses a deterministic synthetic price fixture, no network
required):

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

## What the backtest computes

- **Entry signal (Job 1):** on `^NDX`, price above both the 50d and 250d
  moving average → target TQQQ; below both → target SQQQ; otherwise → cash.
  The signal on day *T*'s close sets the position held from *T* to *T+1* (no
  lookahead — see `backend/app/signals.py`).
- **Exit rules (Job 3):** layered on top of Job 1 in `backend/app/exits.py`,
  each independently toggleable via `/api/backtest` query params (all on by
  default) and the frontend's "Job 3 — exit rules" panel:
  - **Stop-loss** — exit if the held ETF is down more than `stop_loss_pct`
    (default 12%) from entry.
  - **Fast trend-break** — exit if `^NDX` closes back across a faster moving
    average (default 20d) than the slow 250d one Job 1 waits for.
  - **Mean-reversion extension** — exit if `^NDX` has stretched more than
    `extension_pct` (default 20%) above/below its 50d MA.

  Whichever rule (including Job 1's own signal flip) fires first on a given
  day closes the trade; every trade is tagged with `exit_reason` so you can
  see which rule is actually doing the work, rolled up into a per-backtest
  breakdown in the summary. Disabling all three reproduces plain Job
  1-only behavior exactly (see `test_all_rules_disabled_reproduces_job1_signal_exactly`
  in `backend/tests/test_exits.py`).
- **Trade log:** one row per completed (or currently open) position — symbol,
  start/end date, duration, buy/sell price, share size, profit, profit %,
  win/loss, long/short, and which rule closed it.
- **Equity curve:** strategy equity vs. QQQ buy-and-hold, both starting from
  the same capital.
- **Drawdown:** the underwater plot — % below the running peak, at every
  point in time.
- **Monthly returns grid:** year × month compounded returns, plus a yearly
  total column.
- **Summary stats:** CAGR, total return, win rate, profit/loss ratio, max
  drawdown and its duration.

## Daily signal log

The `Daily Log` tab (`frontend/src/app/daily-log`) shows the current dial
(TQQQ / cash / SQQQ) and a history table + chart. Clicking "Log today's
signal" calls `POST /api/daily-log/refresh`, which recomputes the Job 1
signal off the latest `^NDX` data and upserts a row into a local SQLite file
(`backend/backtestlab.db`, keyed by trading date — safe to click more than
once on the same day). This is deliberately separate from the backtest: it
accumulates real history over time regardless of how backtest parameters get
tuned later, and is the actual "am I doing well" record. There's no
scheduler yet — you (or a cron job you set up) need to trigger the refresh
near each day's close.

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
  redeploy. The backtest itself is unaffected (it re-fetches from Yahoo
  Finance each time), but the daily signal log won't persist across
  redeploys until it's backed by a real disk or a hosted database — a
  reasonable next step once you're using it daily.

## Not built yet (by design, per current priorities)

- Job 2 (position sizing — always 100% in or out for now).
- Track B (pre-2010 `^NDX` signal-only stress test).
- Paper trading / Alpaca integration.
- Automatic daily scheduling of the signal-log refresh (currently manual/on-demand).
- Persistent storage for the daily log on the free-tier deploy path above.
