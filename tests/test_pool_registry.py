#!/usr/bin/env python3
"""
Unit tests for Pool Registry Integrator
Tests dynamic cross-chain pool discovery and registry management
"""

import unittest
import sys
import os
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pool_registry_integrator import PoolRegistryIntegrator


class TestPoolRegistryIntegrator(unittest.TestCase):
    """Test suite for Pool Registry Integrator"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.registry_path = "pool_registry.json"
        cls.token_equiv_path = "token_equivalence.json"
    
    def setUp(self):
        """Set up before each test"""
        self.registry = PoolRegistryIntegrator(
            self.registry_path,
            self.token_equiv_path
        )
    
    def test_registry_loads_successfully(self):
        """Test that registry loads from JSON file"""
        self.assertIsNotNone(self.registry)
        self.assertIsInstance(self.registry.pools, list)
    
    def test_registry_has_pools(self):
        """Test that registry contains pool data"""
        self.assertGreater(len(self.registry.pools), 0, 
                          "Registry should contain at least one pool")
    
    def test_active_chains_detected(self):
        """Test that active chains are properly detected"""
        self.assertGreater(len(self.registry.active_chains), 0,
                          "At least one chain should be active")
        self.assertIn("polygon", self.registry.active_chains)
    
    def test_graph_structure_built(self):
        """Test that arbitrage graph is properly constructed"""
        self.assertIsNotNone(self.registry.graph)
        self.assertGreater(len(self.registry.graph), 0,
                          "Graph should contain token connections")
    
    def test_get_statistics(self):
        """Test statistics retrieval"""
        stats = self.registry.get_statistics()
        
        self.assertIn('total_pools', stats)
        self.assertIn('active_chains', stats)
        self.assertIn('tokens', stats)
        
        self.assertGreater(stats['total_pools'], 0)
        self.assertIsInstance(stats['active_chains'], int)
        self.assertGreater(stats['tokens'], 0)
    
    def test_find_pools_by_token_pair(self):
        """Test finding pools by token pair"""
        # Use tokens from test data
        token0 = "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"  # WMATIC
        token1 = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"  # USDC
        
        pools = self.registry.find_pools_by_pair(token0, token1)
        self.assertIsInstance(pools, list)
    
    def test_find_arbitrage_paths(self):
        """Test arbitrage path finding"""
        # Use token from test data
        start_token = "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"  # WMATIC
        
        paths = self.registry.find_arbitrage_paths(start_token, max_hops=3)
        self.assertIsInstance(paths, list)
    
    def test_add_pool_dynamically(self):
        """Test dynamic pool addition"""
        initial_count = len(self.registry.pools)
        
        new_pool = {
            "id": "0x999",
            "dex": "test-dex",
            "chain": "polygon",
            "token0": "0xTEST1",
            "token0_symbol": "TEST1",
            "token1": "0xTEST2",
            "token1_symbol": "TEST2",
            "tvl": 100000,
            "fee": 0.003
        }
        
        self.registry.add_pool(new_pool)
        self.assertEqual(len(self.registry.pools), initial_count + 1)
    
    def test_filter_pools_by_chain(self):
        """Test filtering pools by chain"""
        polygon_pools = self.registry.filter_pools(chain="polygon")
        self.assertIsInstance(polygon_pools, list)
        
        for pool in polygon_pools:
            self.assertEqual(pool.get('chain'), 'polygon')
    
    def test_filter_pools_by_dex(self):
        """Test filtering pools by DEX"""
        uniswap_pools = self.registry.filter_pools(dex="uniswap-v3")
        self.assertIsInstance(uniswap_pools, list)
    
    def test_filter_pools_by_min_tvl(self):
        """Test filtering pools by minimum TVL"""
        min_tvl = 1000000
        filtered_pools = self.registry.filter_pools(min_tvl=min_tvl)
        
        for pool in filtered_pools:
            self.assertGreaterEqual(pool.get('tvl', 0), min_tvl)
    
    def test_activate_deactivate_chain(self):
        """Test chain activation/deactivation"""
        # Deactivate a chain
        self.registry.deactivate_chain("ethereum")
        self.assertNotIn("ethereum", self.registry.active_chains)
        
        # Reactivate the chain
        self.registry.activate_chain("ethereum")
        self.assertIn("ethereum", self.registry.active_chains)
    
    def test_registry_update_timestamp(self):
        """Test that last update timestamp is tracked"""
        self.assertIsNotNone(self.registry.last_update)
        self.assertIsInstance(self.registry.last_update, (int, float))


class TestPoolRegistryPathfinding(unittest.TestCase):
    """Test suite for pathfinding algorithms"""
    
    def setUp(self):
        """Set up before each test"""
        self.registry = PoolRegistryIntegrator(
            "pool_registry.json",
            "token_equivalence.json"
        )
    
    def test_pathfinding_exists(self):
        """Test that pathfinding methods exist"""
        self.assertTrue(hasattr(self.registry, 'find_arbitrage_paths'))
    
    def test_triangular_arbitrage_detection(self):
        """Test detection of triangular arbitrage opportunities"""
        # WMATIC -> USDC -> WETH -> WMATIC should form a triangle
        token = "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"  # WMATIC
        
        paths = self.registry.find_arbitrage_paths(token, max_hops=3)
        self.assertIsInstance(paths, list)
    
    def test_path_hop_limit(self):
        """Test that path hop limit is respected"""
        token = "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"
        
        paths_2hop = self.registry.find_arbitrage_paths(token, max_hops=2)
        paths_3hop = self.registry.find_arbitrage_paths(token, max_hops=3)
        
        # Verify all paths respect hop limit
        for path in paths_2hop:
            self.assertLessEqual(len(path), 2)
        
        for path in paths_3hop:
            self.assertLessEqual(len(path), 3)


def run_tests():
    """Run all tests and display results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPoolRegistryIntegrator))
    suite.addTests(loader.loadTestsFromTestCase(TestPoolRegistryPathfinding))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Display summary
    print("\n" + "=" * 80)
    print("POOL REGISTRY TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ All pool registry tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
