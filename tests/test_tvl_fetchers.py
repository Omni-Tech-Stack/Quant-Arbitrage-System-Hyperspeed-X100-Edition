#!/usr/bin/env python3
"""
Unit tests for TVL Fetchers
Tests parallel TVL fetching and real-time analytics
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from balancer_tvl_fetcher import BalancerTVLFetcher
from curve_tvl_fetcher import CurveTVLFetcher
from uniswapv3_tvl_fetcher import UniswapV3TVLFetcher
from orchestrator_tvl_hyperspeed import TVLOrchestrator


class TestTVLFetchers(unittest.TestCase):
    """Test suite for individual TVL fetchers"""
    
    def test_balancer_fetcher_initialization(self):
        """Test Balancer TVL fetcher initializes"""
        fetcher = BalancerTVLFetcher()
        self.assertIsNotNone(fetcher)
        self.assertEqual(fetcher.protocol, "balancer")
    
    def test_curve_fetcher_initialization(self):
        """Test Curve TVL fetcher initializes"""
        fetcher = CurveTVLFetcher()
        self.assertIsNotNone(fetcher)
        self.assertEqual(fetcher.protocol, "curve")
    
    def test_uniswap_v3_fetcher_initialization(self):
        """Test Uniswap V3 TVL fetcher initializes"""
        fetcher = UniswapV3TVLFetcher()
        self.assertIsNotNone(fetcher)
        self.assertEqual(fetcher.protocol, "uniswap-v3")
    
    def test_balancer_fetch_tvl(self):
        """Test Balancer TVL fetching"""
        fetcher = BalancerTVLFetcher()
        result = fetcher.fetch_tvl()
        
        self.assertIsInstance(result, dict)
        self.assertIn('total_tvl', result)
        self.assertIn('pools', result)
        self.assertGreaterEqual(result['total_tvl'], 0)
    
    def test_curve_fetch_tvl(self):
        """Test Curve TVL fetching"""
        fetcher = CurveTVLFetcher()
        result = fetcher.fetch_tvl()
        
        self.assertIsInstance(result, dict)
        self.assertIn('total_tvl', result)
        self.assertIn('pools', result)
        self.assertGreaterEqual(result['total_tvl'], 0)
    
    def test_uniswap_v3_fetch_tvl(self):
        """Test Uniswap V3 TVL fetching"""
        fetcher = UniswapV3TVLFetcher()
        result = fetcher.fetch_tvl()
        
        self.assertIsInstance(result, dict)
        self.assertIn('total_tvl', result)
        self.assertIn('pools', result)
        self.assertGreaterEqual(result['total_tvl'], 0)
    
    def test_fetcher_handles_errors(self):
        """Test that fetchers handle errors gracefully"""
        fetcher = BalancerTVLFetcher()
        # Should not raise exception even with bad data
        try:
            result = fetcher.fetch_tvl()
            self.assertIsInstance(result, dict)
        except Exception:
            self.fail("Fetcher should handle errors gracefully")


class TestTVLOrchestrator(unittest.TestCase):
    """Test suite for TVL Orchestrator"""
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initializes properly"""
        orchestrator = TVLOrchestrator()
        self.assertIsNotNone(orchestrator)
        self.assertIsInstance(orchestrator.fetchers, dict)
    
    def test_orchestrator_has_fetchers(self):
        """Test that orchestrator has registered fetchers"""
        orchestrator = TVLOrchestrator()
        
        self.assertGreater(len(orchestrator.fetchers), 0,
                          "Orchestrator should have registered fetchers")
        
        # Check for key protocols
        protocols = orchestrator.get_supported_protocols()
        self.assertIn('balancer', protocols)
        self.assertIn('curve', protocols)
        self.assertIn('uniswap-v3', protocols)
    
    def test_fetch_all_tvl(self):
        """Test fetching TVL from all protocols"""
        orchestrator = TVLOrchestrator()
        results = orchestrator.fetch_all_tvl()
        
        self.assertIsInstance(results, dict)
        self.assertGreater(len(results), 0)
        
        # Each result should have protocol data
        for protocol, data in results.items():
            self.assertIsInstance(data, dict)
            self.assertIn('total_tvl', data)
    
    def test_parallel_fetching(self):
        """Test that parallel fetching works"""
        orchestrator = TVLOrchestrator()
        
        # Fetch in parallel mode
        results = orchestrator.fetch_all_tvl(parallel=True)
        self.assertIsInstance(results, dict)
        self.assertGreater(len(results), 0)
    
    def test_aggregate_tvl(self):
        """Test TVL aggregation across protocols"""
        orchestrator = TVLOrchestrator()
        results = orchestrator.fetch_all_tvl()
        
        total = orchestrator.aggregate_tvl(results)
        self.assertIsInstance(total, (int, float))
        self.assertGreaterEqual(total, 0)
    
    def test_get_statistics(self):
        """Test statistics retrieval"""
        orchestrator = TVLOrchestrator()
        results = orchestrator.fetch_all_tvl()
        
        stats = orchestrator.get_statistics(results)
        self.assertIsInstance(stats, dict)
        self.assertIn('total_tvl', stats)
        self.assertIn('protocols', stats)
        self.assertIn('pools', stats)
    
    def test_filter_by_min_tvl(self):
        """Test filtering pools by minimum TVL"""
        orchestrator = TVLOrchestrator()
        results = orchestrator.fetch_all_tvl()
        
        min_tvl = 1000000
        filtered = orchestrator.filter_pools(results, min_tvl=min_tvl)
        
        # All filtered pools should have TVL >= min_tvl
        for protocol, data in filtered.items():
            for pool in data.get('pools', []):
                self.assertGreaterEqual(pool.get('tvl', 0), min_tvl)
    
    def test_performance_metrics(self):
        """Test that performance metrics are tracked"""
        orchestrator = TVLOrchestrator()
        results = orchestrator.fetch_all_tvl()
        
        metrics = orchestrator.get_performance_metrics()
        self.assertIsInstance(metrics, dict)
        self.assertIn('fetch_time', metrics)
        self.assertIn('protocols_fetched', metrics)


def run_tests():
    """Run all tests and display results"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestTVLFetchers))
    suite.addTests(loader.loadTestsFromTestCase(TestTVLOrchestrator))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Display summary
    print("\n" + "=" * 80)
    print("TVL FETCHER TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ All TVL fetcher tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
