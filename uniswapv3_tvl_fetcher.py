#!/usr/bin/env python3
"""Uniswap V3 TVL Fetcher"""

class UniswapV3TVLFetcher:
    def __init__(self, chain):
        self.chain = chain
    
    async def fetch_all_pools(self):
        return {"chain": self.chain, "protocol": "uniswapv3", "tvl": 0, "pools": []}
