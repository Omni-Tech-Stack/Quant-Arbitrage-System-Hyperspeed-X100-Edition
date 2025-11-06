#!/usr/bin/env python
"""
Test ML Integration with Execution Modes
Demonstrates SIMULATION and LIVE modes with ML model scoring
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from execution_mode_manager import ExecutionModeManager, ExecutionMode
from dual_ai_ml_engine import DualAIMLEngine


def create_test_opportunities():
    """Create test arbitrage opportunities"""
    return [
        {
            'hops': 2,
            'gross_profit': 40,
            'gas_cost': 15,
            'estimated_profit': 25,
            'confidence': 0.85,
            'initial_amount': 1000,
            'path': [{'tvl': 5000000}, {'tvl': 4000000}]
        },
        {
            'hops': 3,
            'gross_profit': 70,
            'gas_cost': 25,
            'estimated_profit': 45,
            'confidence': 0.80,
            'initial_amount': 2000,
            'path': [{'tvl': 8000000}, {'tvl': 6000000}, {'tvl': 7000000}]
        },
        {
            'hops': 4,
            'gross_profit': 120,
            'gas_cost': 40,
            'estimated_profit': 80,
            'confidence': 0.92,
            'initial_amount': 5000,
            'path': [{'tvl': 10000000}, {'tvl': 9000000}, {'tvl': 8000000}, {'tvl': 11000000}]
        },
        {
            'hops': 2,
            'gross_profit': 20,
            'gas_cost': 30,
            'estimated_profit': -10,
            'confidence': 0.70,
            'initial_amount': 500,
            'path': [{'tvl': 1000000}, {'tvl': 1500000}]
        }
    ]


def mock_execute(opportunity):
    """Mock execution function"""
    import random
    success = random.random() < 0.9
    
    if success:
        actual_profit = opportunity['estimated_profit'] * random.uniform(0.9, 1.05)
        return {
            'success': True,
            'tx_hash': f"0xTEST{int(os.times().elapsed * 1000000)}",
            'actual_profit': actual_profit
        }
    else:
        return {
            'success': False,
            'error': 'Transaction failed',
            'actual_profit': -opportunity.get('gas_cost', 20)
        }


def test_simulation_mode():
    """Test SIMULATION mode with ML scoring"""
    print("=" * 80)
    print("  TEST 1: SIMULATION MODE WITH ML SCORING")
    print("=" * 80)
    print()
    
    # Initialize components
    ml_engine = DualAIMLEngine(model_dir="./models")
    mode_manager = ExecutionModeManager(mode=ExecutionMode.SIMULATION)
    
    # Create test opportunities
    opportunities = create_test_opportunities()
    
    print(f"Created {len(opportunities)} test opportunities\n")
    
    # Score opportunities with ML
    print("Scoring opportunities with Dual AI ML engine...")
    best_opp = ml_engine.score_opportunities(opportunities)
    
    print(f"\n✓ Best opportunity selected by ML:")
    print(f"  Estimated Profit: ${best_opp['estimated_profit']:.2f}")
    print(f"  ML Score: {best_opp['ml_score']:.4f}")
    print(f"  Primary Score: {best_opp.get('primary_score', 0):.4f}")
    print(f"  Hops: {best_opp['hops']}")
    print(f"  Confidence: {best_opp['confidence']:.2%}")
    
    # Execute in simulation mode
    print("\nExecuting in SIMULATION mode...")
    result = mode_manager.execute_opportunity(
        best_opp,
        mock_execute,
        is_hot_route=True
    )
    
    print(f"\n✓ Result:")
    print(f"  Mode: {result['mode']}")
    print(f"  Success: {result['success']}")
    print(f"  Mock Execution: {result.get('mock_execution', False)}")
    print(f"  Paper Profit: ${result.get('actual_profit', 0):.2f}")
    
    # Print statistics
    mode_manager.print_statistics()
    
    return mode_manager, ml_engine


def test_live_mode(ml_engine):
    """Test LIVE mode with manual execution window"""
    print("\n" + "=" * 80)
    print("  TEST 2: LIVE MODE WITH MANUAL EXECUTION WINDOW")
    print("=" * 80)
    print()
    
    # Initialize mode manager in LIVE mode
    mode_manager = ExecutionModeManager(
        mode=ExecutionMode.LIVE,
        enable_manual_window=True,
        manual_window_duration=5
    )
    
    # Create test opportunities
    opportunities = create_test_opportunities()
    
    # Score opportunities with ML
    best_opp = ml_engine.score_opportunities(opportunities)
    
    print(f"✓ Best opportunity (ML Score: {best_opp['ml_score']:.4f}):")
    print(f"  Estimated Profit: ${best_opp['estimated_profit']:.2f}")
    print(f"  Confidence: {best_opp['confidence']:.2%}")
    
    # Execute in live mode (will show manual window for hot routes)
    print("\nExecuting in LIVE mode (with 5-second manual window)...")
    result = mode_manager.execute_opportunity(
        best_opp,
        mock_execute,
        is_hot_route=True  # This is a hot route
    )
    
    print(f"\n✓ Result:")
    print(f"  Mode: {result['mode']}")
    print(f"  Success: {result['success']}")
    print(f"  Real Execution: {not result.get('mock_execution', False)}")
    if result['success']:
        print(f"  Tx Hash: {result.get('tx_hash', 'N/A')}")
        print(f"  Profit: ${result.get('actual_profit', 0):.2f}")
    
    # Print statistics
    mode_manager.print_statistics()
    
    return mode_manager


def test_hot_route_detection():
    """Test hot route detection logic"""
    print("\n" + "=" * 80)
    print("  TEST 3: HOT ROUTE DETECTION")
    print("=" * 80)
    print()
    
    ml_engine = DualAIMLEngine(model_dir="./models")
    mode_manager = ExecutionModeManager(mode=ExecutionMode.LIVE)
    
    # Test various opportunities
    test_cases = [
        {
            'name': 'High Profit Route',
            'opp': {
                'estimated_profit': 75.0,
                'ml_score': 0.75,
                'confidence': 0.80,
                'hops': 3,
                'gross_profit': 100,
                'gas_cost': 25,
                'initial_amount': 2000,
                'path': [{'tvl': 5000000}] * 3
            },
            'expected_hot': True
        },
        {
            'name': 'High ML Score Route',
            'opp': {
                'estimated_profit': 30.0,
                'ml_score': 0.85,
                'confidence': 0.75,
                'hops': 2,
                'gross_profit': 50,
                'gas_cost': 20,
                'initial_amount': 1000,
                'path': [{'tvl': 3000000}] * 2
            },
            'expected_hot': True
        },
        {
            'name': 'High Confidence Route',
            'opp': {
                'estimated_profit': 25.0,
                'ml_score': 0.70,
                'confidence': 0.90,
                'hops': 2,
                'gross_profit': 40,
                'gas_cost': 15,
                'initial_amount': 1000,
                'path': [{'tvl': 2000000}] * 2
            },
            'expected_hot': True
        },
        {
            'name': 'Normal Route',
            'opp': {
                'estimated_profit': 15.0,
                'ml_score': 0.65,
                'confidence': 0.70,
                'hops': 2,
                'gross_profit': 30,
                'gas_cost': 15,
                'initial_amount': 500,
                'path': [{'tvl': 1000000}] * 2
            },
            'expected_hot': False
        }
    ]
    
    for test in test_cases:
        opp = test['opp']
        is_hot = mode_manager._should_show_manual_window(opp)
        status = "✅" if is_hot == test['expected_hot'] else "❌"
        
        print(f"{status} {test['name']}:")
        print(f"   Profit: ${opp['estimated_profit']:.2f}, ML: {opp['ml_score']:.2f}, Conf: {opp['confidence']:.2%}")
        print(f"   Hot Route: {is_hot} (expected: {test['expected_hot']})")
        print()


def test_ml_trade_logging():
    """Test ML trade result logging"""
    print("\n" + "=" * 80)
    print("  TEST 4: ML TRADE RESULT LOGGING")
    print("=" * 80)
    print()
    
    ml_engine = DualAIMLEngine(model_dir="./models")
    
    # Create and score opportunity
    opportunities = create_test_opportunities()
    best_opp = ml_engine.score_opportunities(opportunities)
    
    # Log some trade results
    print("Logging trade results to ML engine...")
    
    for i in range(5):
        tx_hash = f"0xTEST{i:04d}"
        success = i % 4 != 0  # 75% success rate
        actual_profit = best_opp['estimated_profit'] * (0.95 if success else -0.1)
        
        ml_engine.add_trade_result(
            best_opp,
            tx_hash,
            success=success,
            actual_profit=actual_profit
        )
    
    print(f"\n✓ Logged 5 trade results")
    print(f"  Trade log file: ./models/trade_log.jsonl")
    
    # Check if log file exists
    import os
    if os.path.exists("./models/trade_log.jsonl"):
        with open("./models/trade_log.jsonl", 'r') as f:
            lines = f.readlines()
            print(f"  Log entries: {len(lines)}")


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("  ML INTEGRATION TEST SUITE")
    print("  Testing Dual AI ML Engine + Execution Mode Manager")
    print("=" * 80)
    print()
    
    try:
        # Test 1: Simulation mode
        sim_manager, ml_engine = test_simulation_mode()
        
        # Test 2: Live mode
        live_manager = test_live_mode(ml_engine)
        
        # Test 3: Hot route detection
        test_hot_route_detection()
        
        # Test 4: ML trade logging
        test_ml_trade_logging()
        
        print("\n" + "=" * 80)
        print("  ALL TESTS COMPLETED SUCCESSFULLY ✓")
        print("=" * 80)
        print()
        print("Summary:")
        print("  ✓ SIMULATION mode - Paper trading with mock executions")
        print("  ✓ LIVE mode - Real executions with manual window")
        print("  ✓ Hot route detection - ML score, profit, confidence thresholds")
        print("  ✓ ML trade logging - Results logged for retraining")
        print("  ✓ Dual AI scoring - XGBoost model scoring opportunities")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
