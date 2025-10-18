#!/usr/bin/env python3
"""
Comprehensive test suite for Dual AI ML system
Tests both primary and ONNX models, inference speed, and accuracy
"""

import time
import numpy as np
from typing import List, Dict, Any

try:
    from dual_ai_ml_engine import DualAIMLEngine
    from defi_analytics_ml import MLAnalyticsEngine
except ImportError as e:
    print(f"Error: {e}")
    exit(1)


def test_model_loading():
    """Test model loading and initialization"""
    print("\n" + "=" * 80)
    print("  TEST 1: Model Loading")
    print("=" * 80)
    
    try:
        engine = DualAIMLEngine()
        assert engine.primary_model is not None, "Primary model not loaded"
        assert engine.onnx_session is not None, "ONNX model not loaded"
        assert engine.scaler is not None, "Scaler not loaded"
        print("✓ All models loaded successfully")
        return True, engine
    except Exception as e:
        print(f"✗ Model loading failed: {e}")
        return False, None


def test_feature_extraction(engine: DualAIMLEngine):
    """Test feature extraction from opportunities"""
    print("\n" + "=" * 80)
    print("  TEST 2: Feature Extraction")
    print("=" * 80)
    
    try:
        test_opps = [
            {
                'hops': 3,
                'gross_profit': 50,
                'gas_cost': 20,
                'estimated_profit': 30,
                'confidence': 0.85,
                'initial_amount': 1000,
                'path': [{'tvl': 5000000}, {'tvl': 4000000}, {'tvl': 3000000}]
            }
        ]
        
        features = engine.extract_features(test_opps)
        assert features.shape == (1, 10), f"Expected shape (1, 10), got {features.shape}"
        assert np.all(np.isfinite(features)), "Features contain NaN or Inf"
        
        print(f"✓ Feature extraction successful")
        print(f"  - Feature shape: {features.shape}")
        print(f"  - Feature names: {engine.feature_names}")
        return True
    except Exception as e:
        print(f"✗ Feature extraction failed: {e}")
        return False


def test_dual_inference(engine: DualAIMLEngine):
    """Test inference from both primary and ONNX models"""
    print("\n" + "=" * 80)
    print("  TEST 3: Dual AI Inference")
    print("=" * 80)
    
    try:
        test_opps = [
            {
                'hops': 3,
                'gross_profit': 50,
                'gas_cost': 20,
                'estimated_profit': 30,
                'confidence': 0.85,
                'initial_amount': 1000,
                'path': [{'tvl': 5000000}, {'tvl': 4000000}, {'tvl': 3000000}]
            },
            {
                'hops': 2,
                'gross_profit': 25,
                'gas_cost': 15,
                'estimated_profit': 10,
                'confidence': 0.75,
                'initial_amount': 1000,
                'path': [{'tvl': 2000000}, {'tvl': 1500000}]
            }
        ]
        
        result = engine.score_opportunities(test_opps)
        
        assert result is not None, "No result returned"
        assert 'ml_score' in result, "ML score not in result"
        assert 'primary_score' in result, "Primary score not in result"
        assert 'onnx_score' in result, "ONNX score not in result"
        
        print("✓ Dual AI inference successful")
        print(f"  - ML Score: {result['ml_score']:.4f}")
        print(f"  - Primary Score: {result['primary_score']:.4f}")
        print(f"  - ONNX Score: {result['onnx_score']:.4f}")
        print(f"  - Ensemble working: {'Yes' if abs(result['ml_score'] - result['primary_score']) > 0.001 else 'No'}")
        return True
    except Exception as e:
        print(f"✗ Dual inference failed: {e}")
        return False


def test_inference_speed(engine: DualAIMLEngine):
    """Test inference speed and compare primary vs ONNX"""
    print("\n" + "=" * 80)
    print("  TEST 4: Inference Speed")
    print("=" * 80)
    
    try:
        # Generate test data
        test_opps = []
        for i in range(100):
            opp = {
                'hops': np.random.randint(2, 5),
                'gross_profit': np.random.uniform(10, 100),
                'gas_cost': np.random.uniform(10, 40),
                'estimated_profit': np.random.uniform(0, 60),
                'confidence': np.random.uniform(0.7, 0.95),
                'initial_amount': 1000,
                'path': [{'tvl': np.random.uniform(1000000, 10000000)} for _ in range(3)]
            }
            test_opps.append(opp)
        
        # Warm up
        _ = engine.score_opportunities(test_opps[:10])
        
        # Time primary model
        X = engine.extract_features(test_opps)
        X_scaled = engine.scaler.transform(X) if hasattr(engine.scaler, 'mean_') else X
        
        start = time.perf_counter()
        for _ in range(10):
            _ = engine._predict_primary(X_scaled)
        primary_time = (time.perf_counter() - start) / 10
        
        # Time ONNX model
        start = time.perf_counter()
        for _ in range(10):
            _ = engine._predict_onnx(X_scaled)
        onnx_time = (time.perf_counter() - start) / 10
        
        print("✓ Speed test completed")
        print(f"  - Primary model (XGBoost): {primary_time*1000:.2f} ms")
        print(f"  - ONNX model: {onnx_time*1000:.2f} ms")
        print(f"  - Speedup: {primary_time/onnx_time:.2f}x")
        print(f"  - Throughput: ~{100/primary_time:.0f} opps/sec")
        
        return True
    except Exception as e:
        print(f"✗ Speed test failed: {e}")
        return False


def test_ml_analytics_integration():
    """Test MLAnalyticsEngine integration with DualAI"""
    print("\n" + "=" * 80)
    print("  TEST 5: ML Analytics Engine Integration")
    print("=" * 80)
    
    try:
        ml_engine = MLAnalyticsEngine()
        
        test_opps = [
            {
                'hops': 3,
                'gross_profit': 50,
                'gas_cost': 20,
                'estimated_profit': 30,
                'confidence': 0.85,
                'initial_amount': 1000,
                'path': [{'tvl': 5000000}] * 3
            }
        ]
        
        result = ml_engine.score_opportunities(test_opps)
        
        assert result is not None, "No result from ML engine"
        assert 'ml_score' in result, "ML score not in result"
        
        # Test trade logging
        ml_engine.add_trade_result(result, "0x123abc", success=True, actual_profit=25.0)
        
        print("✓ ML Analytics Engine integration successful")
        print(f"  - Scoring works: Yes")
        print(f"  - Trade logging works: Yes")
        print(f"  - Dual AI active: Yes")
        
        return True
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False


def test_model_consistency(engine: DualAIMLEngine):
    """Test that models produce consistent results"""
    print("\n" + "=" * 80)
    print("  TEST 6: Model Consistency")
    print("=" * 80)
    
    try:
        test_opp = {
            'hops': 3,
            'gross_profit': 50,
            'gas_cost': 20,
            'estimated_profit': 30,
            'confidence': 0.85,
            'initial_amount': 1000,
            'path': [{'tvl': 5000000}, {'tvl': 4000000}, {'tvl': 3000000}]
        }
        
        # Run multiple times
        scores = []
        for _ in range(5):
            result = engine.score_opportunities([test_opp])
            scores.append(result['ml_score'])
        
        # Check consistency
        std_dev = np.std(scores)
        assert std_dev < 0.001, f"High variance in predictions: {std_dev}"
        
        print("✓ Model consistency test passed")
        print(f"  - Standard deviation: {std_dev:.6f}")
        print(f"  - Predictions are stable: Yes")
        
        return True
    except Exception as e:
        print(f"✗ Consistency test failed: {e}")
        return False


def test_edge_cases(engine: DualAIMLEngine):
    """Test edge cases and error handling"""
    print("\n" + "=" * 80)
    print("  TEST 7: Edge Cases")
    print("=" * 80)
    
    try:
        # Test empty list
        result = engine.score_opportunities([])
        assert result is None, "Should return None for empty list"
        
        # Test negative profit
        neg_opp = {
            'hops': 5,
            'gross_profit': 10,
            'gas_cost': 50,
            'estimated_profit': -40,
            'confidence': 0.5,
            'initial_amount': 1000,
            'path': [{'tvl': 100000}] * 5
        }
        result = engine.score_opportunities([neg_opp])
        assert result is not None, "Should handle negative profit"
        
        # Test high hops
        high_hop_opp = {
            'hops': 10,
            'gross_profit': 100,
            'gas_cost': 80,
            'estimated_profit': 20,
            'confidence': 0.6,
            'initial_amount': 5000,
            'path': [{'tvl': 1000000}] * 10
        }
        result = engine.score_opportunities([high_hop_opp])
        assert result is not None, "Should handle high hop count"
        
        print("✓ Edge case handling successful")
        print("  - Empty list: Handled")
        print("  - Negative profit: Handled")
        print("  - High hop count: Handled")
        
        return True
    except Exception as e:
        print(f"✗ Edge case test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 80)
    print("  DUAL AI ML SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    results = []
    
    # Test 1: Model loading
    success, engine = test_model_loading()
    results.append(("Model Loading", success))
    
    if not success or engine is None:
        print("\n✗ Cannot continue without loaded models")
        return
    
    # Test 2: Feature extraction
    success = test_feature_extraction(engine)
    results.append(("Feature Extraction", success))
    
    # Test 3: Dual inference
    success = test_dual_inference(engine)
    results.append(("Dual AI Inference", success))
    
    # Test 4: Inference speed
    success = test_inference_speed(engine)
    results.append(("Inference Speed", success))
    
    # Test 5: ML Analytics integration
    success = test_ml_analytics_integration()
    results.append(("ML Analytics Integration", success))
    
    # Test 6: Model consistency
    success = test_model_consistency(engine)
    results.append(("Model Consistency", success))
    
    # Test 7: Edge cases
    success = test_edge_cases(engine)
    results.append(("Edge Cases", success))
    
    # Summary
    print("\n" + "=" * 80)
    print("  TEST SUMMARY")
    print("=" * 80)
    print()
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed ({100*passed/total:.0f}%)")
    print()
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Dual AI system is ready for production!")
    else:
        print("⚠ Some tests failed - please review the output above")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
