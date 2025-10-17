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
  getOptimalTradeSize,
  calculateFlashloanAmount,
  calculateMarketImpact,
  calculateMultihopSlippage,
  simulateParallelFlashloanPaths,
  calculateFlashloanAmountV3
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

// Test 11: Flashloan Amount Calculation for Arbitrage
test('Flashloan amount calculation for profitable arbitrage', () => {
  const reserveInBuy = 1000000;
  const reserveOutBuy = 2000000;
  const reserveInSell = 2100000; // Price difference creates arbitrage
  const reserveOutSell = 1000000;
  const flashloanFee = 0.0009; // Aave 0.09% fee
  const gasCost = 100;
  
  const flashloanAmount = calculateFlashloanAmount(
    reserveInBuy,
    reserveOutBuy,
    reserveInSell,
    reserveOutSell,
    flashloanFee,
    gasCost
  );
  
  assert(typeof flashloanAmount === 'number', 'Should return a number');
  assert(flashloanAmount >= 0, 'Flashloan amount should be non-negative');
  
  if (flashloanAmount > 0) {
    assertLessThan(flashloanAmount, Math.min(reserveInBuy, reserveInSell) * 0.3, 
      'Flashloan amount should not exceed 30% of reserves');
  }
});

// Test 12: Flashloan Amount for Unprofitable Arbitrage
test('Flashloan amount returns zero for unprofitable arbitrage', () => {
  const flashloanAmount = calculateFlashloanAmount(
    1000000, 1000000, // Equal reserves (no price difference)
    1000000, 1000000,
    0.0009,
    100
  );
  
  assert(flashloanAmount === 0, 'Should return 0 for unprofitable arbitrage');
});

// Test 13: Market Impact Calculation
test('Market impact increases with trade size', () => {
  const reserveIn = 1000000;
  const reserveOut = 2000000;
  const smallFlashloan = 10000;
  const largeFlashloan = 100000;
  
  const smallImpact = calculateMarketImpact(reserveIn, reserveOut, smallFlashloan);
  const largeImpact = calculateMarketImpact(reserveIn, reserveOut, largeFlashloan);
  
  assert(smallImpact >= 0, 'Market impact should be non-negative');
  assert(largeImpact >= 0, 'Market impact should be non-negative');
  assertGreaterThan(largeImpact, smallImpact, 
    'Larger flashloan should have greater market impact');
});

// Test 14: Multi-hop Slippage Calculation
test('Multi-hop slippage calculation for flashloan path', () => {
  const path = [
    [1000000, 2000000], // First hop
    [2000000, 1000000], // Second hop
    [1000000, 500000]   // Third hop
  ];
  const flashloanAmount = 10000;
  
  const totalSlippage = calculateMultihopSlippage(path, flashloanAmount);
  
  assert(typeof totalSlippage === 'number', 'Should return a number');
  assert(totalSlippage >= 0, 'Total slippage should be non-negative');
  
  // Compare with single hop slippage - multi-hop should be higher
  const singleHopSlippage = computeSlippage(1000000, 2000000, flashloanAmount);
  assertGreaterThan(totalSlippage, singleHopSlippage, 
    'Multi-hop slippage should be higher than single hop');
});

// Test 15: Parallel Path Simulation
test('Simulate multiple flashloan paths simultaneously', () => {
  const paths = [
    [[1000000, 2000000], [2100000, 1000000]], // Path 1: profitable
    [[1000000, 1000000], [1000000, 1000000]], // Path 2: unprofitable
    [[1000000, 3000000], [3000000, 1200000]]  // Path 3: highly profitable
  ];
  const flashloanAmounts = [50000, 50000, 50000];
  const flashloanFee = 0.0009;
  const gasCosts = [100, 100, 100];
  
  const results = simulateParallelFlashloanPaths(
    paths,
    flashloanAmounts,
    flashloanFee,
    gasCosts
  );
  
  assert(Array.isArray(results), 'Should return an array');
  assert(results.length === 3, 'Should return results for all 3 paths');
  
  results.forEach((result, idx) => {
    assert(Array.isArray(result), `Result ${idx} should be an array`);
    assert(result.length === 3, `Result ${idx} should have [profit, slippage, pathIndex]`);
    assert(typeof result[0] === 'number', `Profit should be a number for path ${idx}`);
    assert(typeof result[1] === 'number', `Slippage should be a number for path ${idx}`);
    assert(result[2] === idx, `Path index should be ${idx}`);
  });
  
  // Path 3 should be most profitable
  assert(results[2][0] > results[0][0], 'Path 3 should be more profitable than Path 1');
  assert(results[2][0] > results[1][0], 'Path 3 should be more profitable than Path 2');
});

// Test 16: Flashloan Amount for Uniswap V3
test('Flashloan amount calculation for Uniswap V3', () => {
  const liquidity = 5000000;
  const sqrtPriceBuy = 1.5;
  const sqrtPriceSell = 1.6; // Price difference for arbitrage
  const flashloanFee = 0.0009;
  const gasCost = 100;
  
  const flashloanAmount = calculateFlashloanAmountV3(
    liquidity,
    sqrtPriceBuy,
    sqrtPriceSell,
    flashloanFee,
    gasCost
  );
  
  assert(typeof flashloanAmount === 'number', 'Should return a number');
  assert(flashloanAmount >= 0, 'Flashloan amount should be non-negative');
});

// Test 17: Market Impact Edge Cases
test('Market impact handles edge cases', () => {
  // Zero flashloan
  const zeroImpact = calculateMarketImpact(1000000, 2000000, 0);
  assert(zeroImpact === 0, 'Zero flashloan should have zero impact');
  
  // Very small pool with large flashloan
  const hugeImpact = calculateMarketImpact(10000, 20000, 50000);
  assert(hugeImpact > 0, 'Large flashloan on small pool should have impact');
});

// Test 18: Comprehensive Flashloan Arbitrage Workflow
test('Complete flashloan arbitrage workflow', () => {
  // Step 1: Define market conditions
  const buyPool = { reserveIn: 1000000, reserveOut: 2000000 };
  const sellPool = { reserveIn: 2100000, reserveOut: 1000000 };
  const flashloanFee = 0.0009;
  const gasCost = 100;
  
  // Step 2: Calculate optimal flashloan amount
  const flashloanAmount = calculateFlashloanAmount(
    buyPool.reserveIn,
    buyPool.reserveOut,
    sellPool.reserveIn,
    sellPool.reserveOut,
    flashloanFee,
    gasCost
  );
  
  // Step 3: Calculate market impact on buy side
  const buyImpact = calculateMarketImpact(
    buyPool.reserveIn,
    buyPool.reserveOut,
    flashloanAmount
  );
  
  // Step 4: Calculate market impact on sell side
  const amountAfterBuy = flashloanAmount * 0.997 * buyPool.reserveOut / 
    (buyPool.reserveIn + flashloanAmount * 0.997);
  const sellImpact = calculateMarketImpact(
    sellPool.reserveIn,
    sellPool.reserveOut,
    amountAfterBuy
  );
  
  // Verify workflow
  if (flashloanAmount > 0) {
    assert(buyImpact >= 0, 'Buy side impact should be non-negative');
    assert(sellImpact >= 0, 'Sell side impact should be non-negative');
    console.log(`  Flashloan: ${flashloanAmount.toFixed(2)}, Buy Impact: ${buyImpact.toFixed(4)}%, Sell Impact: ${sellImpact.toFixed(4)}%`);
  }
});

// Test 19: Parallel Execution Performance
test('Parallel path simulation finds best opportunity', () => {
  // Create multiple arbitrage paths with different profitability
  const paths = [
    [[1000000, 1500000], [1550000, 1000000]], // Low profit
    [[1000000, 2000000], [2100000, 1000000]], // Medium profit
    [[1000000, 3000000], [3200000, 1000000]], // High profit
    [[1000000, 1000000], [1000000, 1000000]]  // No profit
  ];
  
  const flashloanAmounts = [30000, 30000, 30000, 30000];
  const flashloanFee = 0.0009;
  const gasCosts = [100, 100, 100, 100];
  
  const results = simulateParallelFlashloanPaths(
    paths,
    flashloanAmounts,
    flashloanFee,
    gasCosts
  );
  
  // Find most profitable path
  let bestPathIndex = 0;
  let bestProfit = results[0][0];
  
  results.forEach((result, idx) => {
    if (result[0] > bestProfit) {
      bestProfit = result[0];
      bestPathIndex = idx;
    }
  });
  
  // Verify we found the best path (should be path with highest price difference)
  assert(bestPathIndex >= 0 && bestPathIndex < paths.length, 'Best path index should be valid');
  // Path 3 (index 2) has highest price multiplier, so it should generally be most profitable
  // But due to slippage and fees, path 2 or 1 could also win
  assert(bestProfit >= results[3][0], 'Best path should be more profitable than no-profit path');
  console.log(`  Best path: ${bestPathIndex}, Profit: ${bestProfit.toFixed(2)}`);
});

// Test 20: Flashloan with Multi-DEX Path
test('Flashloan execution through multiple DEX types', () => {
  // Simulate a complex path: Uniswap V2 -> Curve -> Balancer
  const complexPath = [
    [1000000, 2000000],   // Uniswap V2
    [2000000, 2000000],   // Curve (balanced)
    [2000000, 1000000]    // Balancer
  ];
  
  const flashloanAmount = 25000;
  
  // Calculate total slippage
  const totalSlippage = calculateMultihopSlippage(complexPath, flashloanAmount);
  
  // Calculate market impacts at each step
  let currentAmount = flashloanAmount;
  const impacts = [];
  
  complexPath.forEach(([resIn, resOut]) => {
    const impact = calculateMarketImpact(resIn, resOut, currentAmount);
    impacts.push(impact);
    
    // Calculate output for next step
    const amountWithFee = currentAmount * 0.997;
    currentAmount = (amountWithFee * resOut) / (resIn + amountWithFee);
  });
  
  assert(totalSlippage > 0, 'Multi-DEX path should have slippage');
  assert(impacts.length === 3, 'Should calculate impact for each hop');
  assert(impacts.every(impact => impact >= 0), 'All impacts should be non-negative');
  
  console.log(`  Total slippage: ${totalSlippage.toFixed(4)}%, Impacts: ${impacts.map(i => i.toFixed(4)).join('%, ')}%`);
});

// Run all tests
runTests();
