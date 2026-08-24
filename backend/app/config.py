from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
DATA_CACHE_DIR = BACKEND_ROOT / "data_cache"
DB_PATH = BACKEND_ROOT / "backtestlab.db"

DATA_CACHE_DIR.mkdir(exist_ok=True)

# Track A start date: TQQQ/SQQQ actually began trading Feb 2010; we pull from
# 2010-01-01 and let the data naturally start wherever each symbol's history begins.
TRACK_A_START = "2010-01-01"

INDEX_TICKER = "^NDX"
LONG_TICKER = "TQQQ"
SHORT_TICKER = "SQQQ"
BENCHMARK_TICKER = "QQQ"

MA_FAST = 50
MA_SLOW = 250

# How long a cached data file is trusted before we try to refresh it from yfinance.
CACHE_TTL_HOURS = 20

# Job 3 exit-rule defaults. Each rule is independently toggleable; these are
# the starting thresholds -- deliberately simple, round numbers rather than
# fitted to the data (fitting exit thresholds to 2010-2026 history is exactly
# the kind of overfitting the honesty-first approach is meant to avoid).
EXIT_FAST_MA_PERIOD = 20  # "faster signal to bail before the slow 250-day average catches up"
EXIT_STOP_LOSS_PCT = 0.12  # exit if the held ETF is down >12% from entry
EXIT_EXTENSION_PCT = 0.20  # exit if ^NDX is >20% above/below its 50-day MA ("stretched too far too fast")
