#!/usr/bin/env python
"""Balancer TVL Fetcher - Real Data Implementation"""

import requests
import time
from typing import Dict, List, Optional
from web3 import Web3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BalancerTVLFetcher:
    """Fetch TVL data from Balancer pools using The Graph subgraph and Balancer API"""
    
    # The Graph subgraph endpoints (public, no auth required)
    SUBGRAPH_URLS = {
        "ethereum": "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-v2",
        "polygon": "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-polygon-v2",
        "arbitrum": "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-arbitrum-v2",
        "optimism": "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-optimism-v2"
    }
    
    # Balancer API endpoints (aggregates data from multiple sources)
    BALANCER_API_URLS = {
        "ethereum": "https://api.balancer.fi/pools/1",
        "polygon": "https://api.balancer.fi/pools/137",
        "arbitrum": "https://api.balancer.fi/pools/42161",
        "optimism": "https://api.balancer.fi/pools/10"
    }
    
    def __init__(self, chain="ethereum", min_tvl_usd=50000, rpc_url=None):
        """
        Initialize Balancer TVL Fetcher
        
        Args:
            chain: Blockchain network (ethereum, polygon, arbitrum, optimism)
            min_tvl_usd: Minimum TVL in USD to filter pools
            rpc_url: Optional Web3 RPC URL for direct contract calls
        """
        self.chain = chain.lower()
        self.protocol = "balancer"
        self.min_tvl_usd = min_tvl_usd
        self.rpc_url = rpc_url
        self.w3 = Web3(Web3.HTTPProvider(rpc_url)) if rpc_url else None
        
        # Get the appropriate URLs
        self.subgraph_url = self.SUBGRAPH_URLS.get(self.chain, self.SUBGRAPH_URLS["ethereum"])
        self.api_url = self.BALANCER_API_URLS.get(self.chain, self.BALANCER_API_URLS["ethereum"])
        
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
    
    def _fetch_from_api(self, retries: int = 3) -> Optional[List[Dict]]:
        """
        Fetch pools from Balancer API (preferred method - more reliable)
        
        Args:
            retries: Number of retry attempts
            
        Returns:
            List of pool data or None on failure
        """
        self._rate_limit()
        
        for attempt in range(retries):
            try:
                response = requests.get(
                    self.api_url,
                    timeout=30,
                    headers={"Accept": "application/json"}
                )
                response.raise_for_status()
                data = response.json()
                
                pools = []
                for pool in data:
                    try:
                        tvl = float(pool.get("totalLiquidity", 0))
                        
                        # Filter by minimum TVL
                        if tvl < self.min_tvl_usd:
                            continue
                        
                        # Parse token data
                        tokens = []
                        weights = []
                        for token in pool.get("tokens", []):
                            tokens.append({
                                "address": token.get("address"),
                                "symbol": token.get("symbol"),
                                "name": token.get("name", ""),
                                "decimals": int(token.get("decimals", 18)),
                                "balance": float(token.get("balance", 0)),
                                "weight": float(token.get("weight", 0))
                            })
                            weights.append(float(token.get("weight", 0)))
                        
                        pools.append({
                            "id": pool.get("id"),
                            "address": pool.get("address"),
                            "protocol": self.protocol,
                            "chain": self.chain,
                            "name": pool.get("name", ""),
                            "pool_type": pool.get("poolType", ""),
                            "tokens": tokens,
                            "weights": weights,
                            "tvl": tvl,
                            "volume_24h": float(pool.get("totalSwapVolume", 0)),
                            "fees_24h": float(pool.get("totalSwapFee", 0)),
                            "swap_count": int(pool.get("swapsCount", 0)),
                            "swap_fee": float(pool.get("swapFee", 0))
                        })
                    except (KeyError, ValueError, TypeError) as e:
                        logger.warning(f"Error parsing pool data: {e}")
                        continue
                
                logger.info(f"Fetched {len(pools)} Balancer pools from API")
                return pools
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"API request attempt {attempt + 1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All retry attempts failed for API request")
                    return None
        
        return None
    
    def _fetch_from_subgraph(self, limit: int = 100, retries: int = 3) -> Optional[List[Dict]]:
        """
        Fetch pools from The Graph subgraph (fallback method)
        
        Args:
            limit: Maximum number of pools to fetch
            retries: Number of retry attempts
            
        Returns:
            List of pool data or None on failure
        """
        self._rate_limit()
        
        query = """
        query TopPools($first: Int!, $minLiquidity: String!) {
          pools(
            first: $first
            orderBy: totalLiquidity
            orderDirection: desc
            where: { totalLiquidity_gte: $minLiquidity }
          ) {
            id
            address
            poolType
            name
            swapFee
            totalLiquidity
            totalSwapVolume
            totalSwapFee
            swapsCount
            tokens {
              address
              symbol
              name
              decimals
              balance
              weight
            }
          }
        }
        """
        
        variables = {
            "first": limit,
            "minLiquidity": str(self.min_tvl_usd)
        }
        
        for attempt in range(retries):
            try:
                response = requests.post(
                    self.subgraph_url,
                    json={"query": query, "variables": variables},
                    timeout=30,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                data = response.json()
                
                if "errors" in data:
                    logger.error(f"GraphQL errors: {data['errors']}")
                    return None
                
                pools_data = data.get("data", {}).get("pools", [])
                
                pools = []
                for pool in pools_data:
                    try:
                        tokens = []
                        weights = []
                        for token in pool.get("tokens", []):
                            tokens.append({
                                "address": token.get("address"),
                                "symbol": token.get("symbol"),
                                "name": token.get("name", ""),
                                "decimals": int(token.get("decimals", 18)),
                                "balance": float(token.get("balance", 0)),
                                "weight": float(token.get("weight") or 0)
                            })
                            weights.append(float(token.get("weight") or 0))
                        
                        pools.append({
                            "id": pool["id"],
                            "address": pool.get("address"),
                            "protocol": self.protocol,
                            "chain": self.chain,
                            "name": pool.get("name", ""),
                            "pool_type": pool.get("poolType", ""),
                            "tokens": tokens,
                            "weights": weights,
                            "tvl": float(pool.get("totalLiquidity", 0)),
                            "volume_24h": float(pool.get("totalSwapVolume", 0)),
                            "fees_24h": float(pool.get("totalSwapFee", 0)),
                            "swap_count": int(pool.get("swapsCount", 0)),
                            "swap_fee": float(pool.get("swapFee", 0))
                        })
                    except (KeyError, ValueError, TypeError) as e:
                        logger.warning(f"Error parsing pool data: {e}")
                        continue
                
                logger.info(f"Fetched {len(pools)} Balancer pools from subgraph")
                return pools
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Subgraph request attempt {attempt + 1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All retry attempts failed for subgraph request")
                    return None
        
        return None
    
    def fetch_tvl(self) -> dict:
        """
        Fetch TVL data from Balancer pools
        
        Returns:
            Dictionary with protocol, chain, total TVL, pools list, and timestamp
        """
        # Check cache
        current_time = time.time()
        if self.cache and (current_time - self.cache_timestamp) < self.cache_ttl:
            logger.info("Returning cached data")
            return self.cache
        
        # Try API first, then fall back to subgraph
        pools = self._fetch_from_api()
        if not pools:
            logger.info("API fetch failed, trying subgraph fallback")
            pools = self._fetch_from_subgraph()
        
        if not pools:
            logger.warning("No pools fetched from any source, returning empty result")
            return {
                "protocol": self.protocol,
                "chain": self.chain,
                "total_tvl": 0,
                "pools": [],
                "timestamp": int(current_time),
                "error": "Failed to fetch pools from all sources"
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
    
    def get_pool_by_id(self, pool_id: str) -> Optional[Dict]:
        """
        Find a specific pool by ID
        
        Args:
            pool_id: Pool ID or address
            
        Returns:
            Pool data or None if not found
        """
        data = self.fetch_tvl()
        pools = data.get("pools", [])
        
        for pool in pools:
            if pool["id"] == pool_id or pool.get("address") == pool_id:
                return pool
        
        return None
