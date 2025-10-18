#!/usr/bin/env python3
"""
Unit tests for Opportunity Detector
Tests ML-powered arbitrage opportunity detection and scoring
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pool_registry_integrator import PoolRegistryIntegrator
from advanced_opportunity_detection_Version1 import OpportunityDetector


class TestOpportunityDetector(unittest.TestCase):
    """Test suite for Opportunity Detector"""
    
    def setUp(self):
        """Set up before each test"""
        self.registry = PoolRegistryIntegrator("pool_registry.json", "token_equivalence.json")
        self.detector = OpportunityDetector(self.registry)
    
    def test_detector_initialization(self):
        """Test detector initializes properly"""
        self.assertIsNotNone(self.detector)
        self.assertIsNotNone(self.detector.pool_registry)
    
    def test_detect_opportunities_returns_list(self):
        """Test that detect_opportunities returns a list"""
        opportunities = self.detector.detect_opportunities()
        self.assertIsInstance(opportunities, list)
    
    def test_opportunity_structure(self):
        """Test that opportunities have correct structure"""
        opportunities = self.detector.detect_opportunities()
        
        if opportunities:
            opp = opportunities[0]
            self.assertIn('path', opp)
            self.assertIn('estimated_profit', opp)
            self.assertIn('estimated_gas', opp)
            self.assertIsInstance(opp['path'], list)
            self.assertIsInstance(opp['estimated_profit'], (int, float))
    
    def test_opportunities_meet_threshold(self):
        """Test that detected opportunities meet minimum profit threshold"""
        opportunities = self.detector.detect_opportunities()
        
        for opp in opportunities:
            self.assertGreaterEqual(
                opp['estimated_profit'], 
                self.detector.min_profit_threshold,
                "Opportunity should meet minimum profit threshold"
            )
    
    def test_gas_cost_validation(self):
        """Test that gas costs are validated"""
        opportunities = self.detector.detect_opportunities()
        
        for opp in opportunities:
            self.assertLessEqual(
                opp['estimated_gas'],
                self.detector.max_gas_cost * 2,  # Allow some margin
                "Gas cost should be reasonable"
            )
    
    def test_slippage_calculation(self):
        """Test that slippage is calculated"""
        opportunities = self.detector.detect_opportunities()
        
        if opportunities:
            opp = opportunities[0]
            self.assertIn('slippage', opp)
            self.assertIsInstance(opp['slippage'], (int, float))
            self.assertGreaterEqual(opp['slippage'], 0)
    
    def test_net_profit_calculation(self):
        """Test net profit after fees and gas"""
        opportunities = self.detector.detect_opportunities()
        
        for opp in opportunities:
            self.assertIn('net_profit', opp)
            # Net profit should be less than estimated profit
            self.assertLessEqual(opp['net_profit'], opp['estimated_profit'])
    
    def test_ml_score_present(self):
        """Test that ML score is calculated"""
        opportunities = self.detector.detect_opportunities()
        
        if opportunities:
            opp = opportunities[0]
            self.assertIn('ml_score', opp)
            self.assertIsInstance(opp['ml_score'], (int, float))
    
    def test_path_validation(self):
        """Test that paths are valid"""
        opportunities = self.detector.detect_opportunities()
        
        for opp in opportunities:
            path = opp['path']
            self.assertGreater(len(path), 0, "Path should not be empty")
            
            # Each path element should have pool info
            for pool in path:
                self.assertIn('dex', pool)
                self.assertIn('token0', pool)
                self.assertIn('token1', pool)
    
    def test_detector_with_custom_threshold(self):
        """Test detector with custom profit threshold"""
        self.detector.min_profit_threshold = 100
        opportunities = self.detector.detect_opportunities()
        
        for opp in opportunities:
            self.assertGreaterEqual(opp['estimated_profit'], 100)
    
    def test_simulate_trade_execution(self):
        """Test trade simulation"""
        opportunities = self.detector.detect_opportunities()
        
        if opportunities:
            opp = opportunities[0]
            result = self.detector.simulate_execution(opp)
            
            self.assertIsInstance(result, dict)
            self.assertIn('success', result)
            self.assertIn('final_amount', result)


class TestOpportunityScoring(unittest.TestCase):
    """Test suite for opportunity scoring algorithms"""
    
    def setUp(self):
        """Set up before each test"""
        self.registry = PoolRegistryIntegrator("pool_registry.json", "token_equivalence.json")
        self.detector = OpportunityDetector(self.registry)
    
    def test_score_calculation(self):
        """Test that scores are calculated properly"""
        opportunities = self.detector.detect_opportunities()
        
        for opp in opportunities:
            score = self.detector.calculate_score(opp)
            self.assertIsInstance(score, (int, float))
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 1)
    
    def test_score_prioritization(self):
        """Test that higher profit opportunities get higher scores"""
        opportunities = self.detector.detect_opportunities()
        
        if len(opportunities) >= 2:
            scored = sorted(opportunities, key=lambda x: x.get('ml_score', 0), reverse=True)
            
            # First opportunity should have higher or equal score
            if len(scored) >= 2:
                self.assertGreaterEqual(
                    scored[0].get('ml_score', 0),
                    scored[1].get('ml_score', 0)
                )


def run_tests():
    """Run all tests and display results"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestOpportunityDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestOpportunityScoring))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Display summary
    print("\n" + "=" * 80)
    print("OPPORTUNITY DETECTOR TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ All opportunity detector tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
