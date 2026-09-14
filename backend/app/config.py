import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parent.parent
DATA_CACHE_DIR = BACKEND_ROOT / "data_cache"
DB_PATH = BACKEND_ROOT / "backtestlab.db"

load_dotenv(BACKEND_ROOT / ".env")  # optional; POLYGON_API_KEY / ALPACA_* / DATA_SOURCE

DATA_CACHE_DIR.mkdir(exist_ok=True)

# Which price data source to use: "stooq" (default, no key), "polygon", or
# "alpaca" (both need a free API key -- see backend/.env.example).
DATA_SOURCE = os.environ.get("DATA_SOURCE", "stooq")

# Track A start date: TQQQ/SQQQ actually began trading Feb 2010; we pull from
# 2010-01-01 and let the data naturally start wherever each symbol's history begins.
TRACK_A_START = "2010-01-01"

# Track B (signal-only stress test): real ^NDX history goes back further than
# TQQQ/SQQQ existed. Never used to simulate leveraged dollar returns -- see
# signals-only logic in data.py -- only to check whether the entry signal
# would have gone risk-on/off at the right times in crashes the 2010+ data
# doesn't contain (2000 dot-com, 2008).
TRACK_B_START = "1985-01-01"

INDEX_TICKER = "^NDX"
LONG_TICKER = "TQQQ"
SHORT_TICKER = "SQQQ"
BENCHMARK_TICKER = "QQQ"  # also used as the signal proxy if INDEX_TICKER is unavailable

MA_FAST = 50
MA_SLOW = 250

# How long a cached data file is trusted before we try to refresh it.
CACHE_TTL_HOURS = 20

# Job 3 exit-rule defaults. Each rule is independently toggleable; these are
# the starting thresholds -- deliberately simple, round numbers rather than
# fitted to the data (fitting exit thresholds to 2010-2026 history is exactly
# the kind of overfitting the honesty-first approach is meant to avoid).
EXIT_FAST_MA_PERIOD = 20  # "faster signal to bail before the slow 250-day average catches up"
EXIT_STOP_LOSS_PCT = 0.12  # exit if the held ETF is down >12% from entry
EXIT_EXTENSION_PCT = 0.20  # exit if ^NDX is >20% above/below its 50-day MA ("stretched too far too fast")

# Job 2 position sizing (rate-of-change based). Off by default -- Job 1 + Job 3
# alone are always 100% in or out; enabling this scales that down when the
# trend is decelerating.
SIZING_ROC_PERIOD = 20
SIZING_ROC_FULL_THRESHOLD = 0.10  # |ROC| at or above this -> 100% sized
SIZING_ROC_PARTIAL_THRESHOLD = 0.03  # |ROC| at or above this (below full) -> partial size
SIZING_PARTIAL_WEIGHT = 0.65
SIZING_MIN_WEIGHT = 0.30

# Fees / slippage (Job "realism"): a flat round-trip-style cost applied at
# every rebalance, in basis points of the traded notional.
DEFAULT_FEE_BPS = 5.0
