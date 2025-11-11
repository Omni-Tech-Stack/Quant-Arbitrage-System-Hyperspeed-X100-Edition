#!/usr/bin/env python
"""Curve TVL Fetcher - Real Data Implementation"""

import requests
import time
from typing import Dict, List, Optional
from web3 import Web3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CurveTVLFetcher:
    """Fetch TVL data from Curve pools using Curve API and The Graph"""
    
    # Curve API endpoints (official, public)
    CURVE_API_URLS = {
        "ethereum": "https://api.curve.fi/api/getPools/ethereum/main",
        "polygon": "https://api.curve.fi/api/getPools/polygon/main",
        "arbitrum": "https://api.curve.fi/api/getPools/arbitrum/main",
        "optimism": "https://api.curve.fi/api/getPools/optimism/main",
        "base": "https://api.curve.fi/api/getPools/base/main"
    }
    
    # Curve factory API endpoints
    CURVE_FACTORY_API_URLS = {
        "ethereum": "https://api.curve.fi/api/getPools/ethereum/factory",
        "polygon": "https://api.curve.fi/api/getPools/polygon/factory",
        "arbitrum": "https://api.curve.fi/api/getPools/arbitrum/factory",
        "optimism": "https://api.curve.fi/api/getPools/optimism/factory"
    }
    
    # The Graph subgraph endpoints (fallback)
    SUBGRAPH_URLS = {
        "ethereum": "https://api.thegraph.com/subgraphs/name/convex-community/curve-pools",
        "polygon": "https://api.thegraph.com/subgraphs/name/convex-community/curve-pools-polygon"
    }
    
    def __init__(self, chain="ethereum", min_tvl_usd=50000, rpc_url=None):
        """
        Initialize Curve TVL Fetcher
        
        Args:
            chain: Blockchain network (ethereum, polygon, arbitrum, optimism, base)
            min_tvl_usd: Minimum TVL in USD to filter pools
            rpc_url: Optional Web3 RPC URL for direct contract calls
        """
        self.chain = chain.lower()
        self.protocol = "curve"
        self.min_tvl_usd = min_tvl_usd
        self.rpc_url = rpc_url
        self.w3 = Web3(Web3.HTTPProvider(rpc_url)) if rpc_url else None
        
        # Get the appropriate URLs
        self.api_url = self.CURVE_API_URLS.get(self.chain, self.CURVE_API_URLS["ethereum"])
        self.factory_api_url = self.CURVE_FACTORY_API_URLS.get(self.chain)
        self.subgraph_url = self.SUBGRAPH_URLS.get(self.chain)
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.5  # 1.5 seconds between requests (more conservative for Curve)
        
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
    
    def _fetch_from_curve_api(self, url: str, retries: int = 3) -> Optional[Dict]:
        """
        Fetch pools from Curve API
        
        Args:
            url: API endpoint URL
            retries: Number of retry attempts
            
        Returns:
            API response data or None on failure
        """
        self._rate_limit()
        
        for attempt in range(retries):
            try:
                response = requests.get(
                    url,
                    timeout=30,
                    headers={"Accept": "application/json"}
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("success"):
                    return data.get("data", {})
                else:
                    logger.warning(f"API returned success=false: {data.get('message', 'Unknown error')}")
                    return None
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"API request attempt {attempt + 1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All retry attempts failed for API request to {url}")
                    return None
        
        return None
    
    def _parse_pool_data(self, pool_data: Dict, source: str = "api") -> Optional[Dict]:
        """
        Parse pool data from API response
        
        Args:
            pool_data: Raw pool data from API
            source: Data source identifier
            
        Returns:
            Parsed pool dictionary or None on error
        """
        try:
            # Extract TVL
            tvl = float(pool_data.get("usdTotal", 0) or pool_data.get("totalValueLockedUSD", 0))
            
            # Filter by minimum TVL
            if tvl < self.min_tvl_usd:
                return None
            
            # Parse coins/tokens
            coins = pool_data.get("coins", [])
            tokens = []
            for coin in coins:
                tokens.append({
                    "address": coin.get("address"),
                    "symbol": coin.get("symbol"),
                    "name": coin.get("name", ""),
                    "decimals": int(coin.get("decimals", 18)),
                    "balance": float(coin.get("poolBalance", 0))
                })
            
            # Get pool type and parameters
            pool_type = pool_data.get("assetType") or pool_data.get("poolType", "unknown")
            is_meta = pool_data.get("isMetaPool", False)
            
            return {
                "id": pool_data.get("id") or pool_data.get("address"),
                "address": pool_data.get("address"),
                "protocol": self.protocol,
                "chain": self.chain,
                "name": pool_data.get("name", ""),
                "pool_type": pool_type,
                "is_meta_pool": is_meta,
                "tokens": tokens,
                "tvl": tvl,
                "volume_24h": float(pool_data.get("volumeUSD", 0) or pool_data.get("volume24h", 0)),
                "fees_24h": float(pool_data.get("fees24h", 0)),
                "virtual_price": float(pool_data.get("virtualPrice", 0)),
                "amplification": int(pool_data.get("amplificationCoefficient", 0) or pool_data.get("A", 0)),
                "admin_fee": float(pool_data.get("adminFee", 0)),
                "source": source
            }
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Error parsing pool data: {e}")
            return None
    
    def fetch_main_pools(self) -> List[Dict]:
        """
        Fetch main Curve pools
        
        Returns:
            List of pool data dictionaries
        """
        data = self._fetch_from_curve_api(self.api_url)
        
        if not data:
            logger.warning("Failed to fetch main pools from Curve API")
            return []
        
        pools = []
        pool_data = data.get("poolData", [])
        
        for pool in pool_data:
            parsed = self._parse_pool_data(pool, source="main_api")
            if parsed:
                pools.append(parsed)
        
        logger.info(f"Fetched {len(pools)} main Curve pools")
        return pools
    
    def fetch_factory_pools(self) -> List[Dict]:
        """
        Fetch Curve factory pools
        
        Returns:
            List of pool data dictionaries
        """
        if not self.factory_api_url:
            logger.info(f"No factory API URL for chain {self.chain}")
            return []
        
        data = self._fetch_from_curve_api(self.factory_api_url)
        
        if not data:
            logger.warning("Failed to fetch factory pools from Curve API")
            return []
        
        pools = []
        pool_data = data.get("poolData", [])
        
        for pool in pool_data:
            parsed = self._parse_pool_data(pool, source="factory_api")
            if parsed:
                pools.append(parsed)
        
        logger.info(f"Fetched {len(pools)} factory Curve pools")
        return pools
    
    def fetch_tvl(self) -> dict:
        """
        Fetch TVL data from Curve pools
        
        Returns:
            Dictionary with protocol, chain, total TVL, pools list, and timestamp
        """
        # Check cache
        current_time = time.time()
        if self.cache and (current_time - self.cache_timestamp) < self.cache_ttl:
            logger.info("Returning cached data")
            return self.cache
        
        # Fetch main and factory pools
        main_pools = self.fetch_main_pools()
        factory_pools = self.fetch_factory_pools()
        
        all_pools = main_pools + factory_pools
        
        # Remove duplicates based on address
        seen_addresses = set()
        unique_pools = []
        for pool in all_pools:
            addr = pool.get("address")
            if addr and addr not in seen_addresses:
                seen_addresses.add(addr)
                unique_pools.append(pool)
        
        # Sort by TVL descending
        unique_pools.sort(key=lambda x: x.get("tvl", 0), reverse=True)
        
        if not unique_pools:
            logger.warning("No pools fetched, returning empty result")
            return {
                "protocol": self.protocol,
                "chain": self.chain,
                "total_tvl": 0,
                "pools": [],
                "timestamp": int(current_time),
                "error": "Failed to fetch pools"
            }
        
        total_tvl = sum(p['tvl'] for p in unique_pools)
        
        result = {
            "protocol": self.protocol,
            "chain": self.chain,
            "total_tvl": total_tvl,
            "pool_count": len(unique_pools),
            "main_pool_count": len(main_pools),
            "factory_pool_count": len(factory_pools),
            "pools": unique_pools,
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
    
    def get_pool_by_address(self, address: str) -> Optional[Dict]:
        """
        Find a specific pool by address
        
        Args:
            address: Pool address
            
        Returns:
            Pool data or None if not found
        """
        data = self.fetch_tvl()
        pools = data.get("pools", [])
        
        address_lower = address.lower()
        for pool in pools:
            if pool.get("address", "").lower() == address_lower:
                return pool
        
        return None
    
    def get_stablecoin_pools(self) -> List[Dict]:
        """
        Get all stablecoin pools (USD-pegged assets)
        
        Returns:
            List of stablecoin pool data
        """
        data = self.fetch_tvl()
        pools = data.get("pools", [])
        
        stablecoin_pools = []
        stablecoin_symbols = {"USDC", "USDT", "DAI", "FRAX", "TUSD", "BUSD", "UST", "USDD"}
        
        for pool in pools:
            tokens = pool.get("tokens", [])
            token_symbols = {t.get("symbol", "") for t in tokens}
            
            # Check if pool contains primarily stablecoins
            if token_symbols and token_symbols.issubset(stablecoin_symbols):
                stablecoin_pools.append(pool)
        
        return stablecoin_pools
