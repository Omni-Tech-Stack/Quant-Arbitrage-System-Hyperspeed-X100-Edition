#!/usr/bin/env python
"""
Pool Registry Integrator
High-performance, in-memory graph for sub-millisecond pathfinding
Runtime updates, chain activation/deactivation, and custom pool filters
"""

import json
import time
from typing import Dict, List, Any, Optional
from collections import defaultdict
import heapq


class PoolRegistryIntegrator:
    """High-performance pool registry with graph-based pathfinding"""
    
    def __init__(self, registry_path: str, token_equivalence_path: Optional[str] = None):
        self.registry_path = registry_path
        self.token_equivalence_path = token_equivalence_path
        self.pools = []
        self.graph = defaultdict(list)  # token -> [(neighbor_token, pool)]
        self.active_chains = set()
        self.pool_filters = []
        self.last_update = 0
        
        # Load data
        self._load_registry()
        if token_equivalence_path:
            self._load_token_equivalence()
        
        # Build graph
        self._build_graph()
    
    def _load_registry(self):
        """Load pool registry from JSON file"""
        try:
            with open(self.registry_path, 'r') as f:
                data = json.load(f)
            
            # Handle different registry formats
            if isinstance(data, dict):
                # Extract pools from chain-organized structure
                for chain, chain_data in data.items():
                    if isinstance(chain_data, dict) and 'pools' in chain_data:
                        self.pools.extend(chain_data['pools'])
                        self.active_chains.add(chain)
                    elif isinstance(chain_data, list):
                        self.pools.extend(chain_data)
                        self.active_chains.add(chain)
            elif isinstance(data, list):
                self.pools = data
            
            self.last_update = time.time()
            print(f"[Registry] ✓ Loaded {len(self.pools)} pools from {len(self.active_chains)} chains")
            
        except FileNotFoundError:
            print(f"[Registry] ⚠ Registry file not found: {self.registry_path}")
            print("[Registry] Creating empty registry")
            self.pools = []
        except json.JSONDecodeError as e:
            print(f"[Registry] ✗ Error parsing registry: {e}")
            self.pools = []
    
    def _load_token_equivalence(self):
        """Load token equivalence mappings"""
        try:
            with open(self.token_equivalence_path, 'r') as f:
                self.token_equivalence = json.load(f)
            print(f"[Registry] ✓ Loaded token equivalence map")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[Registry] ⚠ Token equivalence not loaded: {e}")
            self.token_equivalence = {}
    
    def _build_graph(self):
        """Build arbitrage graph from pools"""
        print(f"[Registry] Building arbitrage graph...")
        start_time = time.time()
        
        edge_count = 0
        for pool in self.pools:
            token0 = pool.get('token0')
            token1 = pool.get('token1')
            
            if not token0 or not token1:
                continue
            
            # Add bidirectional edges
            self.graph[token0].append((token1, pool))
            self.graph[token1].append((token0, pool))
            edge_count += 2
        
        elapsed = (time.time() - start_time) * 1000
        print(f"[Registry] ✓ Built graph: {len(self.graph)} tokens, {edge_count} edges ({elapsed:.1f}ms)")
    
    def find_arbitrage_paths(self, start_token: str, max_hops: int = 3, 
                            min_pools_per_hop: int = 1) -> List[List[Dict[str, Any]]]:
        """
        Find potential arbitrage paths using BFS
        Returns list of paths, where each path is a list of pools
        """
        paths = []
        queue = [(start_token, [start_token], [])]  # (current_token, token_path, pool_path)
        visited = set()
        
        while queue:
            current, token_path, pool_path = queue.pop(0)
            
            # Check if we've completed a cycle back to start
            if len(token_path) > 1 and current == start_token and len(pool_path) <= max_hops:
                paths.append(pool_path)
                continue
            
            # Don't go deeper than max_hops
            if len(pool_path) >= max_hops:
                continue
            
            # Explore neighbors
            for neighbor, pool in self.graph.get(current, []):
                # Skip if we've been to this token (except for closing the loop)
                if neighbor in token_path[1:] and neighbor != start_token:
                    continue
                
                # Apply pool filters
                if not self._passes_filters(pool):
                    continue
                
                new_token_path = token_path + [neighbor]
                new_pool_path = pool_path + [pool]
                state = (tuple(new_token_path), tuple(id(p) for p in new_pool_path))
                
                if state not in visited:
                    visited.add(state)
                    queue.append((neighbor, new_token_path, new_pool_path))
        
        return paths
    
    def find_shortest_path(self, token_a: str, token_b: str, max_hops: int = 3) -> Optional[List[Dict[str, Any]]]:
        """
        Find shortest path between two tokens using Dijkstra's algorithm
        Returns list of pools forming the path
        """
        # Priority queue: (distance, current_token, path)
        pq = [(0, token_a, [])]
        visited = {token_a: 0}
        
        while pq:
            dist, current, path = heapq.heappop(pq)
            
            if current == token_b:
                return path
            
            if len(path) >= max_hops:
                continue
            
            for neighbor, pool in self.graph.get(current, []):
                if not self._passes_filters(pool):
                    continue
                
                # Use negative log of (1 - fee) as edge weight for optimal path
                fee = pool.get('fee', 0.003)
                edge_weight = -1.0 * (1.0 - fee)
                new_dist = dist + edge_weight
                
                if neighbor not in visited or new_dist < visited[neighbor]:
                    visited[neighbor] = new_dist
                    heapq.heappush(pq, (new_dist, neighbor, path + [pool]))
        
        return None
    
    def add_pool_filter(self, filter_func):
        """Add a custom pool filter function"""
        self.pool_filters.append(filter_func)
    
    def _passes_filters(self, pool: Dict[str, Any]) -> bool:
        """Check if pool passes all filters"""
        for filter_func in self.pool_filters:
            if not filter_func(pool):
                return False
        return True
    
    def activate_chain(self, chain: str):
        """Activate a blockchain for routing"""
        self.active_chains.add(chain)
        print(f"[Registry] ✓ Activated chain: {chain}")
    
    def deactivate_chain(self, chain: str):
        """Deactivate a blockchain from routing"""
        self.active_chains.discard(chain)
        print(f"[Registry] ✓ Deactivated chain: {chain}")
    
    def get_pools_for_token(self, token: str) -> List[Dict[str, Any]]:
        """Get all pools containing a specific token"""
        return [pool for _, pool in self.graph.get(token, [])]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics"""
        return {
            "total_pools": len(self.pools),
            "active_chains": len(self.active_chains),
            "chains": list(self.active_chains),
            "tokens": len(self.graph),
            "edges": sum(len(neighbors) for neighbors in self.graph.values()),
            "last_update": self.last_update
        }
    
    def refresh(self):
        """Reload registry and rebuild graph"""
        print("[Registry] Refreshing data...")
        self._load_registry()
        self.graph.clear()
        self._build_graph()
    
    def add_pool(self, pool: Dict[str, Any]):
        """Dynamically add a new pool to the registry"""
        self.pools.append(pool)
        
        # Update graph
        token0 = pool.get('token0')
        token1 = pool.get('token1')
        
        if token0 and token1:
            self.graph[token0].append((token1, pool))
            self.graph[token1].append((token0, pool))
        
        # Update chain if needed
        chain = pool.get('chain')
        if chain:
            self.active_chains.add(chain)
        
        self.last_update = time.time()
    
    def find_pools_by_pair(self, token0: str, token1: str) -> List[Dict[str, Any]]:
        """Find all pools for a specific token pair"""
        matching_pools = []
        
        for pool in self.pools:
            pool_token0 = pool.get('token0')
            pool_token1 = pool.get('token1')
            
            # Check both directions
            if (pool_token0 == token0 and pool_token1 == token1) or \
               (pool_token0 == token1 and pool_token1 == token0):
                matching_pools.append(pool)
        
        return matching_pools
    
    def filter_pools(self, chain: Optional[str] = None, 
                    dex: Optional[str] = None,
                    min_tvl: Optional[float] = None,
                    min_liquidity: Optional[float] = None) -> List[Dict[str, Any]]:
        """Filter pools by various criteria"""
        filtered = self.pools
        
        if chain:
            filtered = [p for p in filtered if p.get('chain') == chain]
        
        if dex:
            filtered = [p for p in filtered if p.get('dex') == dex]
        
        if min_tvl is not None:
            filtered = [p for p in filtered if p.get('tvl', 0) >= min_tvl]
        
        if min_liquidity is not None:
            filtered = [p for p in filtered if p.get('liquidity', 0) >= min_liquidity]
        
        return filtered


def main():
    """Example usage"""
    import sys
    
    registry_path = sys.argv[1] if len(sys.argv) > 1 else "pool_registry.json"
    token_eq_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    print("=" * 80)
    print("  POOL REGISTRY INTEGRATOR")
    print("=" * 80)
    
    integrator = PoolRegistryIntegrator(registry_path, token_eq_path)
    
    # Display statistics
    stats = integrator.get_statistics()
    print("\n📊 Registry Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Example: Find arbitrage paths
    if integrator.graph:
        sample_token = list(integrator.graph.keys())[0]
        print(f"\n🔍 Finding arbitrage paths starting from {sample_token}...")
        paths = integrator.find_arbitrage_paths(sample_token, max_hops=3)
        print(f"  Found {len(paths)} potential arbitrage paths")


if __name__ == "__main__":
    main()
