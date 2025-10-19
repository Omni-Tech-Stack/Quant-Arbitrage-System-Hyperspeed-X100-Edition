#!/bin/bash
echo "================================================================================"
echo "  COMPREHENSIVE PYTHON MODULE TEST"
echo "================================================================================"
echo ""

success=0
failed=0

echo "Testing: main_quant_hybrid_orchestrator.py"
if python main_quant_hybrid_orchestrator.py --test > /dev/null 2>&1; then
    echo "✓ Main orchestrator: PASS"
    ((success++))
else
    echo "✗ Main orchestrator: FAIL"
    ((failed++))
fi

echo "Testing: orchestrator_tvl_hyperspeed.py"
if python orchestrator_tvl_hyperspeed.py --once --chains ethereum > /dev/null 2>&1; then
    echo "✓ TVL orchestrator: PASS"
    ((success++))
else
    echo "✗ TVL orchestrator: FAIL"
    ((failed++))
fi

echo "Testing: pool_registry_integrator.py"
if python pool_registry_integrator.py pool_registry.json > /dev/null 2>&1; then
    echo "✓ Pool registry integrator: PASS"
    ((success++))
else
    echo "✗ Pool registry integrator: FAIL"
    ((failed++))
fi

echo "Testing: scripts/test_simulation.py"
if python scripts/test_simulation.py > /dev/null 2>&1; then
    echo "✓ Test simulation: PASS"
    ((success++))
else
    echo "✗ Test simulation: FAIL"
    ((failed++))
fi

echo "Testing: scripts/backtesting.py"
if python scripts/backtesting.py > /dev/null 2>&1; then
    echo "✓ Backtesting: PASS"
    ((success++))
else
    echo "✗ Backtesting: FAIL"
    ((failed++))
fi

echo "Testing: scripts/monitoring.py"
if python scripts/monitoring.py > /dev/null 2>&1; then
    echo "✓ Monitoring: PASS"
    ((success++))
else
    echo "✗ Monitoring: FAIL"
    ((failed++))
fi

echo ""
echo "================================================================================"
echo "  TEST RESULTS"
echo "================================================================================"
echo "Passed: $success"
echo "Failed: $failed"
echo "Total:  $((success + failed))"
echo ""

if [ $failed -eq 0 ]; then
    echo "✅ All Python modules passed!"
    exit 0
else
    echo "⚠ Some tests failed"
    exit 1
fi
