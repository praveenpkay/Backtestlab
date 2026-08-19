# Backtest Lab

A personal tool to backtest a trend-following long/short strategy on TQQQ/SQQQ
(3x leveraged NASDAQ-100 ETFs), signaled off the underlying `^NDX` index. See
the original build spec for the full context and rationale.

**MVP scope (this build):** Track A only — a real, honest backtest on actual
TQQQ/SQQQ/^NDX daily prices from 2010 onward, using a single Job 1 rule (price
above/below the 50-day and 250-day moving averages). No synthetic leverage
simulation, no Track B pre-2010 stress test, no daily live-signal tracking yet
— those come after the backtest itself is trusted. The "exit" for this MVP
*is* the entry rule flipping (price crosses back below the MAs); a smarter
Job 3 exit can be layered on top of `backend/app/signals.py` later.

## Architecture

- **`backend/`** — Python FastAPI service. Pulls daily prices via yfinance,
  computes the signal, runs the backtest, and serves the results as JSON.
- **`frontend/`** — Next.js app. Fetches `/api/backtest` and renders the
  equity curve, drawdown chart, monthly return grid, summary stats, and trade
  log.

## Important: this needs real internet access to Yahoo Finance

The backend fetches price data from Yahoo Finance via `yfinance`. If you're
running this in a network-restricted environment (like a CI sandbox), the
`/api/backtest` endpoint will return a `503` with a clear error message
instead of crashing. Run the backend on your own machine (or anywhere with
normal internet access) at least once to populate `backend/data_cache/` —
after that, cached data is reused for up to `CACHE_TTL_HOURS` (see
`backend/app/config.py`) even if Yahoo is briefly unreachable.

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

- **Signal (Job 1):** on `^NDX`, price above both the 50d and 250d moving
  average → target TQQQ; below both → target SQQQ; otherwise → cash. The
  signal on day *T*'s close sets the position held from *T* to *T+1* (no
  lookahead — see `backend/app/backtest.py`).
- **Trade log:** one row per completed (or currently open) position — symbol,
  start/end date, duration, buy/sell price, share size, profit, profit %,
  win/loss, long/short.
- **Equity curve:** strategy equity vs. QQQ buy-and-hold, both starting from
  the same capital.
- **Drawdown:** the underwater plot — % below the running peak, at every
  point in time.
- **Monthly returns grid:** year × month compounded returns, plus a yearly
  total column.
- **Summary stats:** CAGR, total return, win rate, profit/loss ratio, max
  drawdown and its duration.

## Not built yet (by design, per current priorities)

- Daily persisted signal log / "how am I doing today" dashboard tab
  (`Daily Log` in the nav is a placeholder).
- Job 2 (position sizing) and Job 3 (a smarter exit than "the trend flipped").
- Track B (pre-2010 `^NDX` signal-only stress test).
- Paper trading / Alpaca integration.
