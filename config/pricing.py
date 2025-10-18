"""Pricing configuration"""

# Price Feed Sources
PRICE_FEEDS = {
    "chainlink": "https://api.chainlink.com",
    "coingecko": "https://api.coingecko.com/api/v3",
}

# Fee Structures
DEX_FEES = {
    "uniswap-v2": 0.003,
    "uniswap-v3": 0.0005,  # varies by pool
    "sushiswap": 0.003,
    "curve": 0.0004,
}
