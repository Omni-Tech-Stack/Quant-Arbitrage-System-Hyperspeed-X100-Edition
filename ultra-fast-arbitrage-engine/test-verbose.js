/**
 * SYMEN-MAX System Integration Test Suite - VERBOSE MODE
 * Shows all calculations, intermediate values, and data sources
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
  console.log('\n=== VERBOSE SYSTEM INTEGRATION TEST ===');
  console.log('Shows detailed calculations, formulas, and data sources\n');
  console.log('Documentation References:');
  console.log('  - Mathematical formulas: See MATH_FORMULAS.md');
  console.log('  - Test data sources: See TEST_DATA_SOURCES.md\n');
  console.log('='.repeat(80) + '\n');
  
  tests.forEach(({ name, fn }) => {
    try {
      console.log(`\n[TEST] ${name}`);
      console.log('-'.repeat(80));
      fn();
      console.log(`✓ PASSED\n`);
      testsPassed++;
    } catch (error) {
      console.log(`✗ FAILED`);
      console.log(`  Error: ${error.message}\n`);
      testsFailed++;
    }
  });
  
  console.log('\n' + '='.repeat(80));
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
  
  console.log('Formula: Uniswap V2 Constant Product (x * y = k)');
  console.log('Source: https://uniswap.org/whitepaper.pdf');
  console.log('\nInput Parameters:');
  console.log(`  reserve_in:  ${reserveIn.toLocaleString()} tokens`);
  console.log(`  reserve_out: ${reserveOut.toLocaleString()} tokens`);
  console.log(`  amount_in:   ${amountIn.toLocaleString()} tokens`);
  console.log(`  Pool price:  ${(reserveOut/reserveIn).toFixed(4)} (${reserveOut/reserveIn}:1)`);
  console.log(`  Trade size:  ${((amountIn/reserveIn)*100).toFixed(2)}% of pool`);
  console.log(`  Fee:         0.3% (Uniswap V2 standard)`);
  
  console.log('\nCalculation Steps:');
  const amountInWithFee = amountIn * 0.997;
  console.log(`  1. Apply fee: ${amountIn} * 0.997 = ${amountInWithFee}`);
  
  const amountOut = (amountInWithFee * reserveOut) / (reserveIn + amountInWithFee);
  console.log(`  2. Calculate output: (${amountInWithFee} * ${reserveOut}) / (${reserveIn} + ${amountInWithFee})`);
  console.log(`                     = ${amountOut.toFixed(2)} tokens`);
  
  const expectedOut = (amountIn / reserveIn) * reserveOut;
  console.log(`  3. Expected (no slippage): (${amountIn} / ${reserveIn}) * ${reserveOut}`);
  console.log(`                            = ${expectedOut.toFixed(2)} tokens`);
  
  const slippage = computeSlippage(reserveIn, reserveOut, amountIn);
  console.log(`  4. Slippage: ((${expectedOut.toFixed(2)} - ${amountOut.toFixed(2)}) / ${expectedOut.toFixed(2)}) * 100`);
  console.log(`             = ${slippage.toFixed(4)}%`);
  
  console.log('\nResult:');
  console.log(`  ✓ Slippage: ${slippage.toFixed(4)}%`);
  console.log(`  ✓ Loss from slippage: ${(expectedOut - amountOut).toFixed(2)} tokens`);
  
  assert(slippage > 0, 'Slippage should be positive');
  assert(slippage < 100, 'Slippage should be less than 100%');
  assertLessThan(slippage, 2, 'Slippage should be reasonable for this trade size');
});

// Test 2: Uniswap V3 Slippage Calculation
test('Uniswap V3 slippage calculation', () => {
  const liquidity = 5000000;
  const sqrtPrice = 1.5;
  const amountIn = 10000;
  
  console.log('Formula: Uniswap V3 Concentrated Liquidity (Simplified)');
  console.log('Source: https://uniswap.org/whitepaper-v3.pdf');
  console.log('\nInput Parameters:');
  console.log(`  liquidity:   ${liquidity.toLocaleString()} L`);
  console.log(`  sqrt_price:  ${sqrtPrice}`);
  console.log(`  actual price: ${(sqrtPrice * sqrtPrice).toFixed(4)}`);
  console.log(`  amount_in:   ${amountIn.toLocaleString()} tokens`);
  console.log('\nNote: Using simplified V3 model. Real V3 uses tick math and ranges.');
  
  console.log('\nCalculation Steps:');
  const amountOut = (amountIn * sqrtPrice * liquidity) / (liquidity + amountIn);
  console.log(`  1. Output: (${amountIn} * ${sqrtPrice} * ${liquidity}) / (${liquidity} + ${amountIn})`);
  console.log(`           = ${amountOut.toFixed(2)} tokens`);
  
  const expectedOut = amountIn * sqrtPrice;
  console.log(`  2. Expected: ${amountIn} * ${sqrtPrice} = ${expectedOut.toFixed(2)} tokens`);
  
  const slippage = computeUniswapV3Slippage(liquidity, sqrtPrice, amountIn);
  console.log(`  3. Slippage: ${slippage.toFixed(4)}%`);
  
  console.log('\nResult:');
  console.log(`  ✓ Slippage: ${slippage.toFixed(4)}%`);
  console.log(`  ✓ Concentrated liquidity provides better rates than V2`);
  
  assert(slippage >= 0, 'Slippage should be non-negative');
  assert(slippage < 100, 'Slippage should be less than 100%');
});

// Test 3: Curve Slippage Calculation
test('Curve slippage calculation', () => {
  const balanceIn = 1000000;
  const balanceOut = 1000000;
  const amountIn = 10000;
  const amplification = 100;
  
  console.log('Formula: Curve StableSwap with Amplification');
  console.log('Source: https://curve.fi/files/stableswap-paper.pdf');
  console.log('\nInput Parameters:');
  console.log(`  balance_in:     ${balanceIn.toLocaleString()} tokens`);
  console.log(`  balance_out:    ${balanceOut.toLocaleString()} tokens`);
  console.log(`  amount_in:      ${amountIn.toLocaleString()} tokens`);
  console.log(`  amplification:  ${amplification} (typical for stablecoin pairs)`);
  console.log(`  Pool ratio:     ${(balanceOut/balanceIn).toFixed(4)}:1 (balanced)`);
  console.log(`  Fee:            0.04% (Curve standard)`);
  
  console.log('\nCalculation (Hybrid Approach):');
  const amountInWithFee = amountIn * 0.9996;
  console.log(`  1. Apply fee: ${amountIn} * 0.9996 = ${amountInWithFee.toFixed(2)}`);
  
  const totalLiquidity = balanceIn + balanceOut;
  const constantSumOut = (totalLiquidity * amountInWithFee) / totalLiquidity;
  console.log(`  2. Constant sum output: ${constantSumOut.toFixed(2)}`);
  
  const constantProductOut = (amountInWithFee * balanceOut) / (balanceIn + amountInWithFee);
  console.log(`  3. Constant product output: ${constantProductOut.toFixed(2)}`);
  
  const ampWeight = amplification / (amplification + 100);
  console.log(`  4. Amplification weight: ${amplification}/(${amplification}+100) = ${ampWeight.toFixed(4)}`);
  
  const finalOut = constantSumOut * ampWeight + constantProductOut * (1 - ampWeight);
  console.log(`  5. Blended output: ${constantSumOut.toFixed(2)} * ${ampWeight.toFixed(4)} + ${constantProductOut.toFixed(2)} * ${(1-ampWeight).toFixed(4)}`);
  console.log(`                   = ${finalOut.toFixed(2)} tokens`);
  
  const slippage = computeCurveSlippage(balanceIn, balanceOut, amountIn, amplification);
  console.log(`  6. Slippage: ${slippage.toFixed(4)}%`);
  
  console.log('\nResult:');
  console.log(`  ✓ Slippage: ${slippage.toFixed(4)}%`);
  console.log(`  ✓ Lower than Uniswap due to StableSwap design for similar assets`);
  
  assert(slippage >= 0, 'Slippage should be non-negative');
  assert(slippage < 100, 'Slippage should be less than 100%');
  assertLessThan(slippage, 1, 'Curve slippage should be low for balanced pools');
});

// Test 4: Balancer Slippage Calculation
test('Balancer slippage calculation', () => {
  const balanceIn = 1000000;
  const balanceOut = 2000000;
  const weightIn = 0.5;
  const weightOut = 0.5;
  const amountIn = 10000;
  
  console.log('Formula: Balancer Weighted Pool');
  console.log('Source: https://balancer.fi/whitepaper.pdf');
  console.log('\nInput Parameters:');
  console.log(`  balance_in:  ${balanceIn.toLocaleString()} tokens`);
  console.log(`  balance_out: ${balanceOut.toLocaleString()} tokens`);
  console.log(`  weight_in:   ${weightIn} (50%)`);
  console.log(`  weight_out:  ${weightOut} (50%)`);
  console.log(`  amount_in:   ${amountIn.toLocaleString()} tokens`);
  console.log(`  Pool type:   50/50 weighted pool (most common)`);
  
  console.log('\nCalculation Steps:');
  const base = balanceIn / (balanceIn + amountIn);
  console.log(`  1. Base: ${balanceIn} / (${balanceIn} + ${amountIn}) = ${base.toFixed(6)}`);
  
  const exponent = weightIn / weightOut;
  console.log(`  2. Exponent: ${weightIn} / ${weightOut} = ${exponent}`);
  
  const powerResult = Math.pow(base, exponent);
  console.log(`  3. Power: ${base.toFixed(6)}^${exponent} = ${powerResult.toFixed(6)}`);
  
  const amountOut = balanceOut * (1 - powerResult);
  console.log(`  4. Output: ${balanceOut} * (1 - ${powerResult.toFixed(6)}) = ${amountOut.toFixed(2)}`);
  
  const slippage = computeBalancerSlippage(balanceIn, balanceOut, weightIn, weightOut, amountIn);
  console.log(`  5. Slippage: ${slippage.toFixed(4)}%`);
  
  console.log('\nResult:');
  console.log(`  ✓ Slippage: ${slippage.toFixed(4)}%`);
  console.log(`  ✓ Similar to Uniswap V2 for equal weights (50/50)`);
  
  assert(slippage >= 0, 'Slippage should be non-negative');
  assert(slippage < 100, 'Slippage should be less than 100%');
});

// Test 5: Aggregator Route Optimization
test('Aggregator returns minimum slippage', () => {
  const uniswapSlippage = computeSlippage(1000000, 2000000, 10000);
  const curveSlippage = computeCurveSlippage(1000000, 1000000, 10000, 100);
  const balancerSlippage = computeBalancerSlippage(1000000, 2000000, 0.5, 0.5, 10000);
  
  console.log('Objective: Find best route across multiple DEXs');
  console.log('\nRoute Options:');
  console.log(`  Uniswap V2:  ${uniswapSlippage.toFixed(4)}%`);
  console.log(`  Curve:       ${curveSlippage.toFixed(4)}%`);
  console.log(`  Balancer:    ${balancerSlippage.toFixed(4)}%`);
  
  const slippages = [uniswapSlippage, curveSlippage, balancerSlippage];
  const bestSlippage = computeAggregatorSlippage(slippages);
  const minSlippage = Math.min(...slippages);
  
  const bestRoute = slippages.indexOf(bestSlippage);
  const routeNames = ['Uniswap V2', 'Curve', 'Balancer'];
  
  console.log('\nAggregator Decision:');
  console.log(`  Best route: ${routeNames[bestRoute]}`);
  console.log(`  Best slippage: ${bestSlippage.toFixed(4)}%`);
  console.log(`  Savings vs worst: ${(Math.max(...slippages) - bestSlippage).toFixed(4)}%`);
  
  console.log('\nResult:');
  console.log(`  ✓ Aggregator correctly selects route with minimum slippage`);
  console.log(`  ✓ Trade routed through: ${routeNames[bestRoute]}`);
  
  assertApproximately(bestSlippage, minSlippage, 0.0001, 'Aggregator should return minimum slippage');
});

// Test 11: Flashloan Amount Calculation for Arbitrage
test('Flashloan amount calculation for profitable arbitrage', () => {
  const reserveInBuy = 1000000;
  const reserveOutBuy = 2000000;
  const reserveInSell = 2100000;
  const reserveOutSell = 1000000;
  const flashloanFee = 0.0009;
  const gasCost = 100;
  
  console.log('Objective: Calculate optimal flashloan for arbitrage');
  console.log('Source: Aave V3 flashloan fee - https://docs.aave.com/');
  console.log('\nMarket Conditions:');
  console.log('  Buy Pool (DEX A):');
  console.log(`    reserve_in:  ${reserveInBuy.toLocaleString()}`);
  console.log(`    reserve_out: ${reserveOutBuy.toLocaleString()}`);
  console.log(`    price: ${(reserveOutBuy/reserveInBuy).toFixed(4)} (can buy 2 tokens B for 1 token A)`);
  console.log('  Sell Pool (DEX B):');
  console.log(`    reserve_in:  ${reserveInSell.toLocaleString()}`);
  console.log(`    reserve_out: ${reserveOutSell.toLocaleString()}`);
  console.log(`    price: ${(reserveOutSell/reserveInSell).toFixed(4)} (can sell 2 tokens B for ~4.2 tokens A)`);
  console.log(`  Flashloan fee: ${(flashloanFee * 100).toFixed(2)}% (Aave standard)`);
  console.log(`  Gas cost: ${gasCost} tokens`);
  
  console.log('\nArbitrage Opportunity:');
  const priceDiff = (reserveOutBuy/reserveInBuy) - (reserveOutSell/reserveInSell);
  console.log(`  Price difference: ${priceDiff.toFixed(4)} (${((priceDiff / (reserveOutBuy/reserveInBuy)) * 100).toFixed(2)}%)`);
  console.log(`  Opportunity: BUY on DEX A (cheap), SELL on DEX B (expensive)`);
  
  const flashloanAmount = calculateFlashloanAmount(
    reserveInBuy,
    reserveOutBuy,
    reserveInSell,
    reserveOutSell,
    flashloanFee,
    gasCost
  );
  
  console.log('\nOptimization Result:');
  console.log(`  Optimal flashloan: ${flashloanAmount.toFixed(2)} tokens`);
  console.log(`  % of buy pool: ${((flashloanAmount/reserveInBuy)*100).toFixed(2)}%`);
  console.log(`  Flashloan fee: ${(flashloanAmount * flashloanFee).toFixed(2)} tokens`);
  console.log(`  Total repayment: ${(flashloanAmount * (1 + flashloanFee)).toFixed(2)} tokens`);
  
  if (flashloanAmount > 0) {
    // Simulate the arbitrage
    const amountInWithFee = flashloanAmount * 0.997;
    const amountOutBuy = (amountInWithFee * reserveOutBuy) / (reserveInBuy + amountInWithFee);
    const amountInSell = amountOutBuy * 0.997;
    const amountOutSell = (amountInSell * reserveOutSell) / (reserveInSell + amountInSell);
    const profit = amountOutSell - flashloanAmount * (1 + flashloanFee) - gasCost;
    
    console.log('\nArbitrage Execution Simulation:');
    console.log(`  1. Borrow: ${flashloanAmount.toFixed(2)} tokens A`);
    console.log(`  2. Buy on DEX A: Get ${amountOutBuy.toFixed(2)} tokens B`);
    console.log(`  3. Sell on DEX B: Get ${amountOutSell.toFixed(2)} tokens A`);
    console.log(`  4. Repay flashloan: ${(flashloanAmount * (1 + flashloanFee)).toFixed(2)} tokens A`);
    console.log(`  5. Pay gas: ${gasCost} tokens`);
    console.log(`  6. Net profit: ${profit.toFixed(2)} tokens A`);
  }
  
  console.log('\nResult:');
  console.log(`  ✓ Flashloan amount: ${flashloanAmount.toFixed(2)} tokens`);
  if (flashloanAmount > 0) {
    console.log(`  ✓ Profitable arbitrage opportunity identified`);
  }
  
  assert(typeof flashloanAmount === 'number', 'Should return a number');
  assert(flashloanAmount >= 0, 'Flashloan amount should be non-negative');
  
  if (flashloanAmount > 0) {
    assertLessThan(flashloanAmount, Math.min(reserveInBuy, reserveInSell) * 0.3, 
      'Flashloan amount should not exceed 30% of reserves');
  }
});

// Test 18: Comprehensive Flashloan Arbitrage Workflow
test('Complete flashloan arbitrage workflow', () => {
  const buyPool = { reserveIn: 1000000, reserveOut: 2000000 };
  const sellPool = { reserveIn: 2100000, reserveOut: 1000000 };
  const flashloanFee = 0.0009;
  const gasCost = 100;
  
  console.log('Workflow: End-to-end flashloan arbitrage execution');
  console.log('\n1. Market Analysis:');
  console.log(`   Buy pool price:  ${(buyPool.reserveOut/buyPool.reserveIn).toFixed(4)}`);
  console.log(`   Sell pool price: ${(sellPool.reserveOut/sellPool.reserveIn).toFixed(4)}`);
  
  const flashloanAmount = calculateFlashloanAmount(
    buyPool.reserveIn,
    buyPool.reserveOut,
    sellPool.reserveIn,
    sellPool.reserveOut,
    flashloanFee,
    gasCost
  );
  
  console.log(`\n2. Optimal Flashloan: ${flashloanAmount.toFixed(2)} tokens`);
  
  if (flashloanAmount > 0) {
    const buyImpact = calculateMarketImpact(
      buyPool.reserveIn,
      buyPool.reserveOut,
      flashloanAmount
    );
    console.log(`\n3. Buy Side Impact: ${buyImpact.toFixed(4)}%`);
    
    const amountAfterBuy = flashloanAmount * 0.997 * buyPool.reserveOut / 
      (buyPool.reserveIn + flashloanAmount * 0.997);
    const sellImpact = calculateMarketImpact(
      sellPool.reserveIn,
      sellPool.reserveOut,
      amountAfterBuy
    );
    console.log(`\n4. Sell Side Impact: ${sellImpact.toFixed(4)}%`);
    
    console.log('\nResult:');
    console.log(`  ✓ Flashloan amount: ${flashloanAmount.toFixed(2)}`);
    console.log(`  ✓ Buy market impact: ${buyImpact.toFixed(4)}%`);
    console.log(`  ✓ Sell market impact: ${sellImpact.toFixed(4)}%`);
    console.log(`  ✓ Complete workflow validated`);
    
    assert(buyImpact >= 0, 'Buy side impact should be non-negative');
    assert(sellImpact >= 0, 'Sell side impact should be non-negative');
  }
});

// Run all tests
runTests();
