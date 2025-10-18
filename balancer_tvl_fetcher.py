#!/usr/bin/env python3
"""Balancer TVL Fetcher"""

class BalancerTVLFetcher:
    def __init__(self, chain):
        self.chain = chain
    
    async def fetch_all_pools(self):
        return {"chain": self.chain, "protocol": "balancer", "tvl": 0, "pools": []}
