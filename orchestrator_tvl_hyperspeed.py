#!/usr/bin/env python3
"""
Parallel TVL Fetching & Real-Time Analytics Orchestrator
Event-driven, multi-threaded Python orchestrator fetching TVL and pool analytics
for thousands of pools across Balancer, Curve, Uniswap V3, etc.
"""

import asyncio
import concurrent.futures
from typing import List, Dict, Any
import time


class TVLOrchestrator:
    """Event-driven TVL orchestrator with parallel fetching capabilities"""
    
    def __init__(self, chains: List[str] = None):
        self.chains = chains or ["ethereum", "polygon", "bsc", "arbitrum"]
        self.pools_data = {}
        self.last_update = {}
        
    async def fetch_balancer_tvl(self, chain: str) -> Dict[str, Any]:
        """Fetch TVL from Balancer pools"""
        try:
            from balancer_tvl_fetcher import BalancerTVLFetcher
            fetcher = BalancerTVLFetcher(chain)
            return await fetcher.fetch_all_pools()
        except ImportError:
            print(f"[TVL] ⚠ Balancer TVL fetcher not available for {chain}")
            return {"chain": chain, "protocol": "balancer", "tvl": 0, "pools": []}
    
    async def fetch_curve_tvl(self, chain: str) -> Dict[str, Any]:
        """Fetch TVL from Curve pools"""
        try:
            from curve_tvl_fetcher import CurveTVLFetcher
            fetcher = CurveTVLFetcher(chain)
            return await fetcher.fetch_all_pools()
        except ImportError:
            print(f"[TVL] ⚠ Curve TVL fetcher not available for {chain}")
            return {"chain": chain, "protocol": "curve", "tvl": 0, "pools": []}
    
    async def fetch_uniswapv3_tvl(self, chain: str) -> Dict[str, Any]:
        """Fetch TVL from Uniswap V3 pools"""
        try:
            from uniswapv3_tvl_fetcher import UniswapV3TVLFetcher
            fetcher = UniswapV3TVLFetcher(chain)
            return await fetcher.fetch_all_pools()
        except ImportError:
            print(f"[TVL] ⚠ Uniswap V3 TVL fetcher not available for {chain}")
            return {"chain": chain, "protocol": "uniswapv3", "tvl": 0, "pools": []}
    
    async def fetch_chain_tvl(self, chain: str) -> Dict[str, Any]:
        """Fetch TVL for all protocols on a given chain"""
        print(f"[TVL] Fetching TVL for {chain}...")
        start_time = time.time()
        
        # Fetch all protocols in parallel
        results = await asyncio.gather(
            self.fetch_balancer_tvl(chain),
            self.fetch_curve_tvl(chain),
            self.fetch_uniswapv3_tvl(chain),
            return_exceptions=True
        )
        
        # Aggregate results
        total_tvl = 0
        all_pools = []
        protocols = {}
        
        for result in results:
            if isinstance(result, Exception):
                print(f"[TVL] ⚠ Error fetching {chain}: {result}")
                continue
            
            if isinstance(result, dict):
                protocol = result.get("protocol", "unknown")
                tvl = result.get("tvl", 0)
                pools = result.get("pools", [])
                
                total_tvl += tvl
                all_pools.extend(pools)
                protocols[protocol] = {"tvl": tvl, "pool_count": len(pools)}
        
        elapsed = time.time() - start_time
        
        chain_data = {
            "chain": chain,
            "total_tvl": total_tvl,
            "protocols": protocols,
            "pool_count": len(all_pools),
            "pools": all_pools,
            "fetch_time_ms": int(elapsed * 1000),
            "timestamp": time.time()
        }
        
        self.pools_data[chain] = chain_data
        self.last_update[chain] = time.time()
        
        print(f"[TVL] ✓ {chain}: ${total_tvl:,.2f} across {len(all_pools)} pools ({elapsed*1000:.0f}ms)")
        
        return chain_data
    
    async def fetch_all_chains(self) -> Dict[str, Any]:
        """Fetch TVL for all configured chains in parallel"""
        print(f"\n[TVL] Starting parallel TVL fetch for {len(self.chains)} chains...")
        start_time = time.time()
        
        # Fetch all chains in parallel
        results = await asyncio.gather(
            *[self.fetch_chain_tvl(chain) for chain in self.chains],
            return_exceptions=True
        )
        
        # Aggregate global stats
        total_tvl = 0
        total_pools = 0
        
        for result in results:
            if isinstance(result, Exception):
                print(f"[TVL] ⚠ Chain fetch error: {result}")
                continue
            
            if isinstance(result, dict):
                total_tvl += result.get("total_tvl", 0)
                total_pools += result.get("pool_count", 0)
        
        elapsed = time.time() - start_time
        
        summary = {
            "global_tvl": total_tvl,
            "total_pools": total_pools,
            "chains": len(self.chains),
            "fetch_time_ms": int(elapsed * 1000),
            "timestamp": time.time(),
            "chain_data": self.pools_data
        }
        
        print(f"\n[TVL] ✓ Global: ${total_tvl:,.2f} across {total_pools} pools")
        print(f"[TVL] ✓ Total fetch time: {elapsed*1000:.0f}ms")
        
        return summary
    
    async def continuous_update_loop(self, interval_seconds: int = 60):
        """Continuously update TVL data at specified interval"""
        print(f"[TVL] Starting continuous update loop (interval: {interval_seconds}s)")
        
        iteration = 0
        while True:
            iteration += 1
            print(f"\n[TVL] === Update Iteration {iteration} ===")
            
            try:
                await self.fetch_all_chains()
            except Exception as e:
                print(f"[TVL] ✗ Update error: {e}")
            
            await asyncio.sleep(interval_seconds)


async def main():
    """Main entry point for TVL orchestrator"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TVL Hyperspeed Orchestrator')
    parser.add_argument('--chains', nargs='+', 
                       default=["ethereum", "polygon", "bsc"],
                       help='Chains to monitor')
    parser.add_argument('--interval', type=int, default=60,
                       help='Update interval in seconds')
    parser.add_argument('--once', action='store_true',
                       help='Run once and exit')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("  TVL HYPERSPEED ORCHESTRATOR")
    print("  Multi-threaded, Event-driven TVL Fetching")
    print("=" * 80)
    
    orchestrator = TVLOrchestrator(chains=args.chains)
    
    if args.once:
        print("\n[TVL] Single-run mode")
        result = await orchestrator.fetch_all_chains()
        print(f"\n[TVL] ✓ Fetch complete. Monitored {result['total_pools']} pools")
    else:
        print("\n[TVL] Continuous mode")
        await orchestrator.continuous_update_loop(interval_seconds=args.interval)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[TVL] Shutting down gracefully...")
