#!/usr/bin/env python
"""
Master Test Runner
Runs all test suites and generates comprehensive report
"""

import sys
import unittest
from pathlib import Path

# Add tests directory to path
sys.path.insert(0, str(Path(__file__).parent))

from test_pool_registry import TestPoolRegistryIntegrator, TestPoolRegistryPathfinding
from test_opportunity_detector import TestOpportunityDetector, TestOpportunityScoring
from test_tvl_fetchers import TestTVLFetchers, TestTVLOrchestrator
from test_core_modules import (
    TestArbRequestEncoder,
    TestMEVRelay,
    TestMerkleRewardDistributor,
    TestMLAnalyticsEngine,
    TestDexProtocolPrecheck
)


def run_all_tests():
    """Run all test suites"""
    
    print("=" * 80)
    print("  QUANT ARBITRAGE SYSTEM - COMPREHENSIVE TEST SUITE")
    print("  Validating all modules against README specifications")
    print("=" * 80)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        # Pool Registry
        TestPoolRegistryIntegrator,
        TestPoolRegistryPathfinding,
        # Opportunity Detection
        TestOpportunityDetector,
        TestOpportunityScoring,
        # TVL Fetchers
        TestTVLFetchers,
        TestTVLOrchestrator,
        # Core Modules
        TestArbRequestEncoder,
        TestMEVRelay,
        TestMerkleRewardDistributor,
        TestMLAnalyticsEngine,
        TestDexProtocolPrecheck
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Display comprehensive summary
    print("\n" + "=" * 80)
    print("  COMPREHENSIVE TEST SUMMARY")
    print("=" * 80)
    print()
    
    print(f"📊 Test Statistics:")
    print(f"   Total Tests Run: {result.testsRun}")
    print(f"   ✅ Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   ❌ Failures: {len(result.failures)}")
    print(f"   🔥 Errors: {len(result.errors)}")
    print()
    
    # Module breakdown
    print(f"📦 Module Coverage:")
    print(f"   ✓ Pool Registry & Pathfinding")
    print(f"   ✓ Opportunity Detection & ML Scoring")
    print(f"   ✓ TVL Fetchers (Balancer, Curve, Uniswap V3)")
    print(f"   ✓ TVL Orchestrator (Parallel Fetching)")
    print(f"   ✓ Arbitrage Request Encoder")
    print(f"   ✓ MEV Relay Integration")
    print(f"   ✓ Merkle Reward Distribution")
    print(f"   ✓ ML Analytics Engine")
    print(f"   ✓ DEX Protocol Precheck")
    print()
    
    # Success/failure status
    if result.wasSuccessful():
        print("🎉 " + "=" * 76)
        print("   ALL TESTS PASSED!")
        print("   System implementation matches README specifications")
        print("=" * 80)
        return 0
    else:
        print("⚠️  " + "=" * 76)
        print("   SOME TESTS FAILED")
        print("   Review failures above for details")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
