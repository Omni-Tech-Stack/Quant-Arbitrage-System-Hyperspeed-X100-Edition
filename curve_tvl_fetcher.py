#!/usr/bin/env python3
"""Curve TVL Fetcher"""

class CurveTVLFetcher:
    def __init__(self, chain):
        self.chain = chain
    
    async def fetch_all_pools(self):
        return {"chain": self.chain, "protocol": "curve", "tvl": 0, "pools": []}
