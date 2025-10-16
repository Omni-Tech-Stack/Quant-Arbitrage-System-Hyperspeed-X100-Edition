/**
 * SYMEN-MAX System Integration Test Suite
 * Validates all components work together correctly
 */

const {
  computeSlippage,
  computeUniswapV3Slippage,
  computeCurveSlippage,
  computeBalancerSlippage,
  computeAggregatorSlippage,
  getOptimalTradeSize
} = require('./dist/index.js');

// Test results tracking
let testsPassed = 0;
let testsFailed = 0;
const tests = [];

function test(name, fn) {
  tests.push({ name, fn });
}

function runTests() {
  console.log('\n=== SYSTEM INTEGRATION TEST ===\n');
  
  tests.forEach(({ name, fn }) => {
    try {
      fn();
      console.log(`✓ ${name}`);
      testsPassed++;
    } catch (error) {
      console.log(`✗ ${name}`);
      console.log(`  Error: ${error.message}`);
      testsFailed++;
    }
  });
  
  console.log('\n=== TEST SUMMARY ===');
  console.log(`Tests passed: ${testsPassed}`);
  console.log(`Tests failed: ${testsFailed}`);
  console.log(`Total tests: ${testsPassed + testsFailed}`);
  
  if (testsFailed === 0) {
    console.log('\n✓ ALL TESTS PASSED - System integration verified!\n');
    process.exit(0);
  } else {
    console.log('\n✗ SOME TESTS FAILED\n');
    process.exit(1);
  }
}

// Helper function for assertions
function assert(condition, message) {
  if (!condition) {
    throw new Error(message || 'Assertion failed');
  }
}

function assertGreaterThan(actual, expected, message) {
  if (actual <= expected) {
    throw new Error(message || `Expected ${actual} to be greater than ${expected}`);
  }
}

function assertLessThan(actual, expected, message) {
  if (actual >= expected) {
    throw new Error(message || `Expected ${actual} to be less than ${expected}`);
  }
}

function assertApproximately(actual, expected, tolerance, message) {
  const diff = Math.abs(actual - expected);
  if (diff > tolerance) {
    throw new Error(message || `Expected ${actual} to be approximately ${expected} (tolerance: ${tolerance}), but difference was ${diff}`);
  }
}

// Test 1: Uniswap V2 Slippage Calculation
test('Uniswap V2 slippage calculation', () => {
  const reserveIn = 1000000;
  const reserveOut = 2000000;
  const amountIn = 10000;
  
  const slippage = computeSlippage(reserveIn, reserveOut, amountIn);
  
  assert(slippage > 0, 'Slippage should be positive');
  assert(slippage < 100, 'Slippage should be less than 100%');
  assertLessThan(slippage, 2, 'Slippage should be reasonable for this trade size');
});

// Test 2: Uniswap V3 Slippage Calculation
test('Uniswap V3 slippage calculation', () => {
  const liquidity = 5000000;
  const sqrtPrice = 1.5;
  const amountIn = 10000;
  
  const slippage = computeUniswapV3Slippage(liquidity, sqrtPrice, amountIn);
  
  assert(slippage >= 0, 'Slippage should be non-negative');
  assert(slippage < 100, 'Slippage should be less than 100%');
});

// Test 3: Curve Slippage Calculation
test('Curve slippage calculation', () => {
  const balanceIn = 1000000;
  const balanceOut = 1000000;
  const amountIn = 10000;
  const amplification = 100;
  
  const slippage = computeCurveSlippage(balanceIn, balanceOut, amountIn, amplification);
  
  assert(slippage >= 0, 'Slippage should be non-negative');
  assert(slippage < 100, 'Slippage should be less than 100%');
  // Curve should have lower slippage than Uniswap for stablecoins
  assertLessThan(slippage, 1, 'Curve slippage should be low for balanced pools');
});

// Test 4: Balancer Slippage Calculation
test('Balancer slippage calculation', () => {
  const balanceIn = 1000000;
  const balanceOut = 2000000;
  const weightIn = 0.5;
  const weightOut = 0.5;
  const amountIn = 10000;
  
  const slippage = computeBalancerSlippage(balanceIn, balanceOut, weightIn, weightOut, amountIn);
  
  assert(slippage >= 0, 'Slippage should be non-negative');
  assert(slippage < 100, 'Slippage should be less than 100%');
});

// Test 5: Aggregator Route Optimization
test('Aggregator returns minimum slippage', () => {
  const uniswapSlippage = computeSlippage(1000000, 2000000, 10000);
  const curveSlippage = computeCurveSlippage(1000000, 1000000, 10000, 100);
  const balancerSlippage = computeBalancerSlippage(1000000, 2000000, 0.5, 0.5, 10000);
  
  const slippages = [uniswapSlippage, curveSlippage, balancerSlippage];
  const bestSlippage = computeAggregatorSlippage(slippages);
  
  const minSlippage = Math.min(...slippages);
  assertApproximately(bestSlippage, minSlippage, 0.0001, 'Aggregator should return minimum slippage');
});

// Test 6: Optimal Trade Size (Profitable)
test('Optimal trade size for profitable scenario', () => {
  const reserveIn = 1000000;
  const reserveOut = 2000000;
  const gasCost = 100;
  const minProfit = 50;
  
  const optimalSize = getOptimalTradeSize(reserveIn, reserveOut, gasCost, minProfit);
  
  assert(optimalSize > 0, 'Optimal trade size should be positive for profitable scenario');
  assertLessThan(optimalSize, reserveIn * 0.1, 'Optimal trade size should be reasonable');
});

// Test 7: Optimal Trade Size (Unprofitable)
test('Optimal trade size for unprofitable scenario', () => {
  const reserveIn = 1000000;
  const reserveOut = 1000000;
  const gasCost = 10000; // Very high gas cost
  const minProfit = 5000; // High minimum profit
  
  const optimalSize = getOptimalTradeSize(reserveIn, reserveOut, gasCost, minProfit);
  
  assert(optimalSize === 0, 'Optimal trade size should be 0 for unprofitable scenario');
});

// Test 8: Trade Size Impact
test('Large trade shows higher slippage than small trade', () => {
  const reserveIn = 1000000;
  const reserveOut = 2000000;
  const smallAmount = 1000;
  const largeAmount = 50000;
  
  const smallSlippage = computeSlippage(reserveIn, reserveOut, smallAmount);
  const largeSlippage = computeSlippage(reserveIn, reserveOut, largeAmount);
  
  assertGreaterThan(largeSlippage, smallSlippage, 'Larger trades should have higher slippage');
});

// Test 9: Edge Case Handling
test('Functions handle zero trade size', () => {
  const slippage = computeSlippage(1000000, 2000000, 0);
  assert(slippage === 0, 'Zero trade size should result in zero slippage');
  
  const optimalSize = getOptimalTradeSize(1000000, 2000000, 100, 50);
  assert(typeof optimalSize === 'number', 'Should return a number');
});

// Test 10: Full Arbitrage Workflow
test('Full arbitrage workflow integration', () => {
  // Step 1: Calculate slippage on multiple DEXs
  const uniV2Slippage = computeSlippage(1000000, 2000000, 10000);
  const uniV3Slippage = computeUniswapV3Slippage(5000000, 1.5, 10000);
  const curveSlippage = computeCurveSlippage(1000000, 1000000, 10000, 100);
  
  // Step 2: Find best route
  const bestRoute = computeAggregatorSlippage([uniV2Slippage, uniV3Slippage, curveSlippage]);
  
  // Step 3: Calculate optimal trade size
  const optimalSize = getOptimalTradeSize(1000000, 2000000, 100, 50);
  
  // Verify all components work
  assert(typeof uniV2Slippage === 'number', 'Uniswap V2 calculation failed');
  assert(typeof uniV3Slippage === 'number', 'Uniswap V3 calculation failed');
  assert(typeof curveSlippage === 'number', 'Curve calculation failed');
  assert(typeof bestRoute === 'number', 'Aggregator calculation failed');
  assert(typeof optimalSize === 'number', 'Optimal size calculation failed');
  
  // Verify workflow makes sense
  assert(bestRoute <= Math.min(uniV2Slippage, uniV3Slippage, curveSlippage), 
    'Best route should have minimum slippage');
});

// Run all tests
runTests();
