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
