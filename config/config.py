"""General configuration"""

# RPC Endpoints
RPC_ENDPOINTS = {
    "ethereum": "https://eth.llamarpc.com",
    "polygon": "https://polygon-rpc.com",
    "bsc": "https://bsc-dataseed.binance.org",
    "arbitrum": "https://arb1.arbitrum.io/rpc",
}

# Trading Parameters
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
