"""
General System Configuration
- RPC Endpoints categorized by use case
- API keys for various services
- Trading parameters
"""

# ==================================================================
# ===================== RPC ENDPOINT CONFIGURATION =================
# ==================================================================

# Using specific endpoints for different tasks improves performance and security.
# - data_fetching: General purpose, high-rate-limit RPCs for reading chain state.
# - tx_broadcasting: Specialized, secure RPCs for submitting transactions.
# - websockets: For real-time data streams like mempool monitoring.

RPC_CONFIG = {
    "data_fetching": {
        "ethereum": "https://mainnet.infura.io/v3/ed05b301f1a949f59bfbc1c128910937",
        "polygon": "https://polygon-mainnet.g.alchemy.com/v2/YXw_o8m9DTfqafsqX3ebqH5QP1kClfZG",
        "arbitrum": "https://orbital-special-moon.arbitrum-mainnet.quiknode.pro/6858e3e0efef9ed7238363fbc4c2809b52a7a059",
        "optimism": "https://orbital-special-moon.optimism.quiknode.pro/6858e3e0efef9ed7238363fbc4c2809b52a7a059",
        "bsc": "https://orbital-special-moon.bsc.quiknode.pro/6858e3e0efef9ed7238363fbc4c2809b52a7a059",
        "base": "https://orbital-special-moon.base-mainnet.quiknode.pro/6858e3e0efef9ed7238363fbc4c2809b52a7a059",
        "ankr_polygon": "https://rpc.ankr.com/polygon", # Fallback/general purpose
    },
    "tx_broadcasting": {
        # QuickNode is designated for transaction broadcasting ONLY for security.
        "polygon": "https://orbital-special-moon.matic.quiknode.pro/6858e3e0efef9ed7238363fbc4c2809b52a7a059",
        "ethereum": "https://mainnet.infura.io/v3/ed05b301f1a949f59bfbc1c128910937", # Replace with a dedicated TX endpoint if available
        "arbitrum": "https://orbital-special-moon.arbitrum-mainnet.quiknode.pro/6858e3e0efef9ed7238363fbc4c2809b52a7a059",
        "optimism": "https://orbital-special-moon.optimism.quiknode.pro/6858e3e0efef9ed7238363fbc4c2809b52a7a059",
    },
    "websockets": {
        "polygon": "wss://orbital-special-moon.matic.quiknode.pro/6858e3e0efef9ed7238363fbc4c2809b52a7a059",
        "ethereum": "wss://mainnet.infura.io/ws/v3/ed05b301f1a949f59bfbc1c128910937",
        "alchemy_polygon": "wss://polygon-mainnet.g.alchemy.com/v2/bbrqV8gVKk5IyIx5_jUlE",
    }
}

# Legacy RPC_ENDPOINTS for backward compatibility if needed, pointing to data_fetching endpoints.
RPC_ENDPOINTS = RPC_CONFIG["data_fetching"]


# ==================================================================
# ===================== API KEYS & ENDPOINTS =======================
# ==================================================================

API_KEYS = {
    "POLYGONSCAN": "7YGCQ5R2HYQWNM7Y21TA9D9DB62594RHQA",
    "COINGECKO": "CG-rAj2Cp3gkGpLfML135nSwpLE",
    "MORALIS": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImIxZjBmMGI5LWIwM2YtNDMzNC04ZTFiLTVmOGFlOThhMDIzYyIsIm9yZ0lkIjoiNDY3MTMxIiwidXNlcklkIjoiNDgwNTY4IiwidHlwZUlkIjoiNGNlMDVmODEtYTJlOC00ZjFlLTg0MjctYzhiMzJkMDMxM2JiIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NTYxMTMyNjMsImV4cCI6NDkxMTg3MzI2M30.FgI-dyMJzyF2d1LtGQ0Ubu4aDaNj1Zzp2JmSKo_dnS0",
    "ONEINCH": "d7U6jreN0czpr7CQJAvmcAFrGBDDsbjq"
}

API_ENDPOINTS = {
    "BINANCE": "https://api.binance.com/api/v3",
    "ONEINCH": "https://api.1inch.dev/swap/v5.2/137/quote",
    "ZER0X_POLYGON": "https://polygon.api.0x.org/swap/v1/price",
    "PARASWAP": "https://apiv5.paraswap.io/prices",
    "COINGECKO": "https://api.coingecko.com/api/v3",
    "PYTH": "https://xc-mainnet.pyth.network/api/latest_price_feeds"
}


# ==================================================================
# ===================== TRADING PARAMETERS =========================
# ==================================================================

MIN_PROFIT_USD = 10
MAX_GAS_PRICE_GWEI = 100
SLIPPAGE_TOLERANCE = 0.01  # 1%

# Execution Mode Configuration
# Options: "SIMULATION" or "LIVE"
EXECUTION_MODE = "SIMULATION"  # Start in safe mode by default

# Manual Execution Window (for LIVE mode only)
ENABLE_MANUAL_WINDOW = True  # Enable 5-second manual execution window for hot routes
MANUAL_WINDOW_DURATION = 5  # Seconds to wait for manual decision

# Hot Route Thresholds (triggers manual window in LIVE mode)
HOT_ROUTE_ML_SCORE_THRESHOLD = 0.8  # ML score threshold for hot routes
HOT_ROUTE_PROFIT_THRESHOLD = 50.0   # Minimum profit (USD) for hot routes
HOT_ROUTE_CONFIDENCE_THRESHOLD = 0.85  # Confidence threshold for hot routes

# ML Model Configuration
USE_DUAL_AI_ENGINE = True  # Use superior Dual AI (XGBoost + ONNX) instead of simple model
ML_MODEL_DIR = "./models"  # Directory for ML model files
RETRAIN_INTERVAL_HOURS = 24  # Hours between automatic model retraining
