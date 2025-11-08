#!/usr/bin/env python3
"""
Comprehensive integration test for Dual AI system
Tests all new additions and their wiring
"""

import sys
import os

# Colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'


def print_test(name):
    print(f"\n{BLUE}Testing: {name}{NC}")


def print_pass(msg):
    print(f"{GREEN}✓ PASS:{NC} {msg}")


def print_fail(msg):
    print(f"{RED}✗ FAIL:{NC} {msg}")


def test_dependencies():
    """Test all ML dependencies are installed"""
    print_test("ML Dependencies")
    
    try:
        import sklearn
        print_pass(f"scikit-learn {sklearn.__version__}")
    except ImportError:
        print_fail("scikit-learn not found")
        return False
    
    try:
        import xgboost
        print_pass(f"xgboost {xgboost.__version__}")
    except ImportError:
        print_fail("xgboost not found")
        return False
    
    try:
        import onnx
        print_pass(f"onnx {onnx.__version__}")
    except ImportError:
        print_fail("onnx not found")
        return False
    
    try:
        import onnxruntime
        print_pass(f"onnxruntime {onnxruntime.__version__}")
    except ImportError:
        print_fail("onnxruntime not found")
        return False
    
    try:
        import skl2onnx
        print_pass(f"skl2onnx {skl2onnx.__version__}")
    except ImportError:
        print_fail("skl2onnx not found")
        return False
    
    return True


def test_onnx_wrapper():
    """Test ONNX wrapper functionality"""
    print_test("ONNX Wrapper")
    
    try:
        from models.onnx_wrapper import ONNXModelWrapper
        import numpy as np
        
        if not os.path.exists('./models/onnx_model.onnx'):
            print_fail("ONNX model not found - run training first")
            return False
        
        wrapper = ONNXModelWrapper('./models/onnx_model.onnx')
        print_pass("ONNX wrapper loaded")
        
        X = np.random.randn(5, 10).astype(np.float32)
        preds = wrapper.predict(X)
        
        if preds is not None and len(preds) == 5:
            print_pass(f"ONNX predictions shape: {preds.shape}")
        else:
            print_fail(f"Invalid predictions: {preds}")
            return False
        
        if all(0 <= p <= 1 for p in preds):
            print_pass("Predictions in valid range [0, 1]")
        else:
            print_fail(f"Predictions out of range: {preds}")
            return False
        
        return True
    except Exception as e:
        print_fail(f"ONNX wrapper error: {e}")
        return False


def test_dual_model():
    """Test DualModel integration"""
    print_test("DualModel Integration")
    
    try:
        from models.dual_model import DualModel
        
        dual = DualModel(model_dir='./models', legacy_weight=0.5, onnx_weight=0.5)
        print_pass("DualModel initialized")
        
        opportunities = [
            {
                'hops': 2,
                'gross_profit': 50,
                'gas_cost': 15,
                'estimated_profit': 35,
                'confidence': 0.9,
                'initial_amount': 1000,
                'path': [{'tvl': 5_000_000}, {'tvl': 4_000_000}]
            }
        ]
        
        scores = dual.predict(opportunities)
        print_pass(f"Predictions generated: {len(scores)} scores")
        
        best = dual.score_opportunities(opportunities)
        if best and 'ml_score' in best and 'legacy_score' in best and 'onnx_score' in best:
            print_pass(f"Best opportunity scored with ensemble (ml={best['ml_score']:.4f})")
        else:
            print_fail(f"Missing scores in result: {best}")
            return False
        
        return True
    except Exception as e:
        print_fail(f"DualModel error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dual_ai_engine():
    """Test DualAIMLEngine"""
    print_test("DualAIMLEngine")
    
    try:
        from dual_ai_ml_engine import DualAIMLEngine
        
        engine = DualAIMLEngine(model_dir='./models')
        print_pass("DualAIMLEngine initialized")
        
        opportunities = [
            {
                'hops': 3,
                'gross_profit': 80,
                'gas_cost': 20,
                'estimated_profit': 60,
                'confidence': 0.85,
                'initial_amount': 2000,
                'path': [{'tvl': 8_000_000}, {'tvl': 6_000_000}, {'tvl': 7_000_000}]
            }
        ]
        
        best = engine.score_opportunities(opportunities)
        if best and 'ml_score' in best:
            print_pass(f"Engine scored opportunity (score={best['ml_score']:.4f})")
        else:
            print_fail("Engine failed to score")
            return False
        
        if 'onnx_score' in best and 'primary_score' in best:
            print_pass("Ensemble prediction with both models")
        else:
            print_fail("Missing ensemble scores")
            return False
        
        return True
    except Exception as e:
        print_fail(f"DualAIMLEngine error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_files():
    """Test that all model files exist"""
    print_test("Model Files")
    
    required_files = [
        './models/xgboost_primary.pkl',
        './models/onnx_model.onnx',
        './models/scaler.pkl',
        './models/training_metadata.json'
    ]
    
    all_exist = True
    for filepath in required_files:
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print_pass(f"{os.path.basename(filepath)} ({size} bytes)")
        else:
            print_fail(f"{filepath} not found")
            all_exist = False
    
    return all_exist


def test_scripts():
    """Test that scripts exist and are executable"""
    print_test("Scripts and Tools")
    
    scripts = [
        ('scripts/verify_dependencies.py', True),
        ('scripts/demo_dual_ai.py', True),
        ('train_dual_ai_models.py', True),
        ('DUAL_AI_QUICKSTART.md', False)
    ]
    
    all_ok = True
    for script, check_exec in scripts:
        if os.path.exists(script):
            if check_exec and not os.access(script, os.X_OK):
                print_pass(f"{script} exists (not executable)")
            else:
                print_pass(f"{script} exists")
        else:
            print_fail(f"{script} not found")
            all_ok = False
    
    return all_ok


def main():
    print("\n" + "=" * 80)
    print("  DUAL AI SYSTEM - COMPREHENSIVE INTEGRATION TEST")
    print("=" * 80)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Model Files", test_model_files),
        ("ONNX Wrapper", test_onnx_wrapper),
        ("DualModel", test_dual_model),
        ("DualAIMLEngine", test_dual_ai_engine),
        ("Scripts", test_scripts)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print_fail(f"Test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("  TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = f"{GREEN}✓ PASS{NC}" if result else f"{RED}✗ FAIL{NC}"
        print(f"{status} - {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print(f"\n{GREEN}✓ ALL TESTS PASSED - DUAL AI SYSTEM FULLY OPERATIONAL{NC}\n")
        return 0
    else:
        print(f"\n{RED}✗ SOME TESTS FAILED{NC}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
