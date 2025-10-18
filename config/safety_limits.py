#!/usr/bin/env python3
"""
Safety Limits and Circuit Breaker Configuration
Defines hard limits for profit, loss, slippage, and other safety parameters
"""

# Circuit Breaker Thresholds
MAX_LOSS_PER_TRADE_USD = 500  # Maximum loss allowed per trade in USD
MAX_LOSS_PER_HOUR_USD = 2000  # Maximum cumulative loss per hour
MAX_LOSS_PER_DAY_USD = 10000  # Maximum cumulative loss per day

# Profit Thresholds
MIN_PROFIT_USD = 10  # Minimum profit to execute trade
MAX_POSITION_SIZE_USD = 100000  # Maximum position size per trade

# Slippage Limits
MAX_SLIPPAGE_PERCENT = 3.0  # Maximum acceptable slippage (3%)
MAX_MARKET_IMPACT_PERCENT = 5.0  # Maximum market impact allowed (5%)

# Gas Limits
MAX_GAS_PRICE_GWEI = 150  # Maximum gas price to execute trade
MAX_GAS_COST_USD = 100  # Maximum gas cost per trade

# Pool Depth Limits (as percentage of pool reserves)
MAX_TRADE_SIZE_PERCENT_OF_POOL = 30.0  # Max 30% of pool reserves
SAFE_TRADE_SIZE_PERCENT_OF_POOL = 10.0  # Safe default for production

# Time-based Circuit Breakers
MAX_FAILED_TRADES_PER_HOUR = 10  # Pause if too many failures
CIRCUIT_BREAKER_COOLDOWN_SECONDS = 300  # 5 minutes cooldown after trigger

# Emergency Controls
EMERGENCY_SHUTDOWN = False  # Global emergency shutdown flag
TRADING_PAUSED = False  # Trading pause flag

# Rate Limiting
MAX_TRADES_PER_MINUTE = 10
MAX_TRADES_PER_HOUR = 300

# Flashloan-Specific Safety
FLASHLOAN_FEE_BUFFER = 1.1  # Add 10% buffer to flashloan fees for safety
MIN_PROFIT_MARGIN_PERCENT = 0.5  # Minimum profit margin (0.5%)
GAS_PRICE_SPIKE_THRESHOLD = 2.0  # Alert if gas > 2x average

# Liquidity Provider Failover
ENABLE_FAILOVER = True
PRIMARY_LIQUIDITY_PROVIDERS = ["aave", "dydx", "compound"]
FALLBACK_LIQUIDITY_PROVIDERS = ["uniswap_v3", "balancer"]

# Monitoring and Alerting
ALERT_ON_HIGH_SLIPPAGE = True
ALERT_ON_GAS_SPIKE = True
ALERT_ON_UNUSUAL_PROFIT = True
ALERT_ON_LIQUIDITY_DROP = True

def get_safety_limits():
    """Return all safety limits as a dictionary"""
    return {
        "max_loss_per_trade_usd": MAX_LOSS_PER_TRADE_USD,
        "max_loss_per_hour_usd": MAX_LOSS_PER_HOUR_USD,
        "max_loss_per_day_usd": MAX_LOSS_PER_DAY_USD,
        "min_profit_usd": MIN_PROFIT_USD,
        "max_position_size_usd": MAX_POSITION_SIZE_USD,
        "max_slippage_percent": MAX_SLIPPAGE_PERCENT,
        "max_market_impact_percent": MAX_MARKET_IMPACT_PERCENT,
        "max_gas_price_gwei": MAX_GAS_PRICE_GWEI,
        "max_gas_cost_usd": MAX_GAS_COST_USD,
        "max_trade_size_percent_of_pool": MAX_TRADE_SIZE_PERCENT_OF_POOL,
        "safe_trade_size_percent_of_pool": SAFE_TRADE_SIZE_PERCENT_OF_POOL,
        "emergency_shutdown": EMERGENCY_SHUTDOWN,
        "trading_paused": TRADING_PAUSED
    }

def is_trading_allowed():
    """Check if trading is currently allowed"""
    return not EMERGENCY_SHUTDOWN and not TRADING_PAUSED

if __name__ == "__main__":
    import json
    print("Safety Limits Configuration:")
    print(json.dumps(get_safety_limits(), indent=2))
