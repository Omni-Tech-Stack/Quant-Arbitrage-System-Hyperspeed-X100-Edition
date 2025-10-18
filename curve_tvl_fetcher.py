#!/usr/bin/env python3
"""Curve TVL Fetcher"""

import random


class CurveTVLFetcher:
    """Fetch TVL data from Curve pools"""
    
    def __init__(self, chain="ethereum"):
        self.chain = chain
        self.protocol = "curve"
    
    def fetch_tvl(self) -> dict:
        """Fetch TVL data (simulated for testing)"""
        # Simulate fetching data
        mock_pools = [
            {
                "id": f"curve-pool-{i}",
                "tvl": random.randint(500000, 10000000),
                "amplification": 100,
                "tokens": ["USDC", "DAI", "USDT"]
            }
            for i in range(3)
        ]
        
        total_tvl = sum(p['tvl'] for p in mock_pools)
        
        return {
            "protocol": self.protocol,
            "chain": self.chain,
            "total_tvl": total_tvl,
            "pools": mock_pools,
            "timestamp": None
        }
    
    async def fetch_all_pools(self):
        """Async fetch method for compatibility"""
        return self.fetch_tvl()
