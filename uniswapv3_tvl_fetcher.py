#!/usr/bin/env python
"""Uniswap V3 TVL Fetcher - Real Data Implementation"""

import requests
import time
from typing import Dict, List, Optional
from web3 import Web3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UniswapV3TVLFetcher:
    """Fetch TVL data from Uniswap V3 pools using The Graph subgraph"""
    
    # The Graph subgraph endpoints (public, no auth required)
    SUBGRAPH_URLS = {
        "ethereum": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
        "polygon": "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-polygon",
        "arbitrum": "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-arbitrum-one",
        "optimism": "https://api.thegraph.com/subgraphs/name/ianlapham/optimism-post-regenesis"
    }
    
    def __init__(self, chain="ethereum", min_tvl_usd=50000, rpc_url=None):
        """
        Initialize Uniswap V3 TVL Fetcher
        
        Args:
            chain: Blockchain network (ethereum, polygon, arbitrum, optimism)
            min_tvl_usd: Minimum TVL in USD to filter pools
            rpc_url: Optional Web3 RPC URL for direct contract calls
        """
        self.chain = chain.lower()
        self.protocol = "uniswap-v3"
        self.min_tvl_usd = min_tvl_usd
        self.rpc_url = rpc_url
        self.w3 = Web3(Web3.HTTPProvider(rpc_url)) if rpc_url else None
        
        # Get the appropriate subgraph URL
        self.subgraph_url = self.SUBGRAPH_URLS.get(self.chain)
        if not self.subgraph_url:
            logger.warning(f"No subgraph URL for chain {self.chain}, using ethereum")
            self.subgraph_url = self.SUBGRAPH_URLS["ethereum"]
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests
        
        # Cache
        self.cache = None
        self.cache_timestamp = 0
        self.cache_ttl = 300  # 5 minutes cache TTL
    
    def _rate_limit(self):
        """Implement rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _make_subgraph_request(self, query: str, variables: dict = None, retries: int = 3) -> Optional[dict]:
        """
        Make a request to The Graph subgraph with retry logic
        
        Args:
            query: GraphQL query string
            variables: Optional query variables
            retries: Number of retry attempts
            
        Returns:
            Response data or None on failure
        """
        self._rate_limit()
        
        for attempt in range(retries):
            try:
                response = requests.post(
                    self.subgraph_url,
                    json={"query": query, "variables": variables or {}},
                    timeout=30,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                data = response.json()
                
                if "errors" in data:
                    logger.error(f"GraphQL errors: {data['errors']}")
                    return None
                
                return data.get("data")
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request attempt {attempt + 1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All retry attempts failed for subgraph request")
                    return None
        
        return None
    
    def fetch_top_pools(self, limit: int = 100) -> List[Dict]:
        """
        Fetch top Uniswap V3 pools by TVL
        
        Args:
            limit: Maximum number of pools to fetch
            
        Returns:
            List of pool data dictionaries
        """
        query = """
        query TopPools($first: Int!, $minLiquidity: String!) {
          pools(
            first: $first
            orderBy: totalValueLockedUSD
            orderDirection: desc
            where: { totalValueLockedUSD_gte: $minLiquidity }
          ) {
            id
            token0 {
              id
              symbol
              name
              decimals
            }
            token1 {
              id
              symbol
              name
              decimals
            }
            feeTier
            liquidity
            sqrtPrice
            tick
            token0Price
            token1Price
            volumeUSD
            txCount
            totalValueLockedToken0
            totalValueLockedToken1
            totalValueLockedUSD
            feesUSD
          }
        }
        """
        
        variables = {
            "first": limit,
            "minLiquidity": str(self.min_tvl_usd)
        }
        
        data = self._make_subgraph_request(query, variables)
        
        if not data or "pools" not in data:
            logger.error("Failed to fetch pools from subgraph")
            return []
        
        pools = []
        for pool in data["pools"]:
            try:
                pools.append({
                    "id": pool["id"],
                    "address": pool["id"],
                    "protocol": self.protocol,
                    "chain": self.chain,
                    "token0": {
                        "address": pool["token0"]["id"],
                        "symbol": pool["token0"]["symbol"],
                        "name": pool["token0"].get("name", ""),
                        "decimals": int(pool["token0"]["decimals"])
                    },
                    "token1": {
                        "address": pool["token1"]["id"],
                        "symbol": pool["token1"]["symbol"],
                        "name": pool["token1"].get("name", ""),
                        "decimals": int(pool["token1"]["decimals"])
                    },
                    "fee_tier": int(pool["feeTier"]) / 1000000,  # Convert to decimal (e.g., 3000 -> 0.003)
                    "liquidity": pool["liquidity"],
                    "tvl": float(pool["totalValueLockedUSD"]),
                    "tvl_token0": float(pool["totalValueLockedToken0"]),
                    "tvl_token1": float(pool["totalValueLockedToken1"]),
                    "volume_usd": float(pool.get("volumeUSD", 0)),
                    "fees_usd": float(pool.get("feesUSD", 0)),
                    "tx_count": int(pool.get("txCount", 0)),
                    "sqrt_price": pool.get("sqrtPrice"),
                    "tick": pool.get("tick"),
                    "token0_price": float(pool.get("token0Price", 0)),
                    "token1_price": float(pool.get("token1Price", 0))
                })
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Error parsing pool data: {e}")
                continue
        
        logger.info(f"Fetched {len(pools)} Uniswap V3 pools from {self.chain}")
        return pools
    
    def fetch_tvl(self) -> dict:
        """
        Fetch TVL data from Uniswap V3 pools
        
        Returns:
            Dictionary with protocol, chain, total TVL, pools list, and timestamp
        """
        # Check cache
        current_time = time.time()
        if self.cache and (current_time - self.cache_timestamp) < self.cache_ttl:
            logger.info("Returning cached data")
            return self.cache
        
        # Fetch fresh data
        pools = self.fetch_top_pools(limit=100)
        
        if not pools:
            logger.warning("No pools fetched, returning empty result")
            return {
                "protocol": self.protocol,
                "chain": self.chain,
                "total_tvl": 0,
                "pools": [],
                "timestamp": int(current_time),
                "error": "Failed to fetch pools"
            }
        
        total_tvl = sum(p['tvl'] for p in pools)
        
        result = {
            "protocol": self.protocol,
            "chain": self.chain,
            "total_tvl": total_tvl,
            "pool_count": len(pools),
            "pools": pools,
            "timestamp": int(current_time)
        }
        
        # Update cache
        self.cache = result
        self.cache_timestamp = current_time
        
        logger.info(f"Total TVL for {self.protocol} on {self.chain}: ${total_tvl:,.2f}")
        return result
    
    async def fetch_all_pools(self):
        """Async fetch method for compatibility"""
        return self.fetch_tvl()
    
    def get_pool_by_tokens(self, token0_symbol: str, token1_symbol: str, fee_tier: Optional[float] = None) -> Optional[Dict]:
        """
        Find a specific pool by token pair and optional fee tier
        
        Args:
            token0_symbol: First token symbol
            token1_symbol: Second token symbol
            fee_tier: Optional fee tier (e.g., 0.003 for 0.3%)
            
        Returns:
            Pool data or None if not found
        """
        data = self.fetch_tvl()
        pools = data.get("pools", [])
        
        for pool in pools:
            t0 = pool["token0"]["symbol"]
            t1 = pool["token1"]["symbol"]
            
            # Check both orderings
            match = (t0 == token0_symbol and t1 == token1_symbol) or \
                   (t0 == token1_symbol and t1 == token0_symbol)
            
            if match:
                if fee_tier is None or abs(pool["fee_tier"] - fee_tier) < 0.0001:
                    return pool
        
        return None
