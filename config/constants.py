"""
Central constants for Neural Options Oracle++
Import from here instead of scattering literals throughout the codebase.
"""

# ---------------------------------------------------------------------------
# OpenAI model names
# ---------------------------------------------------------------------------
MODEL_LARGE = "gpt-4o"
MODEL_SMALL = "gpt-4o-mini"

# ---------------------------------------------------------------------------
# Completion defaults
# ---------------------------------------------------------------------------
DEFAULT_MAX_TOKENS = 4000
DEFAULT_TEMPERATURE = 0.7

# ---------------------------------------------------------------------------
# Agent base weights (must sum to 1.0)
# ---------------------------------------------------------------------------
BASE_WEIGHTS = {
    "technical": 0.60,
    "sentiment": 0.10,
    "flow": 0.10,
    "history": 0.20,
}

# ---------------------------------------------------------------------------
# Trading signal thresholds (decision score -> direction)
# ---------------------------------------------------------------------------
SIGNAL_STRONG_BUY = 0.6
SIGNAL_BUY = 0.3
SIGNAL_SELL = -0.3
SIGNAL_STRONG_SELL = -0.6

# ---------------------------------------------------------------------------
# Signal strength thresholds (|decision score| -> label)
# ---------------------------------------------------------------------------
STRENGTH_STRONG = 0.7
STRENGTH_MODERATE = 0.4

# ---------------------------------------------------------------------------
# Market data caching
# ---------------------------------------------------------------------------
CACHE_TTL_SECONDS = 300          # 5 minutes
TICKER_CACHE_TTL_SECONDS = 300   # yfinance Ticker cache

# ---------------------------------------------------------------------------
# Default trading / risk parameters
# ---------------------------------------------------------------------------
DEFAULT_ACCOUNT_BALANCE = 100_000    # paper trading starting balance ($)
DEFAULT_MAX_POSITION_SIZE = 0.05     # 5% of account per position
OPTION_CONTRACT_MULTIPLIER = 100     # standard options lot size
DEFAULT_STOP_LOSS_RATIO = 0.5        # 50% of premium
DEFAULT_PROFIT_TARGET_RATIO = 2.0    # 2× premium (100% gain)
