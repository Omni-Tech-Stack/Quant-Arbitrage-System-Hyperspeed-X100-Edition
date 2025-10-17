#!/usr/bin/env node

/**
 * Arbitrage Flow Demonstration
 * Visual demonstration of the complete 7-step arbitrage workflow
 */

const {
  calculatePoolPrice,
  identifyArbitrageOpportunity,
  calculateAmountIn,
  calculateAmountOut,
  estimateArbitrageProfit,
  solveQuadratic,
  optimizeTradeSizeQuadratic,
  calculateTWAP,
  validateWithTWAP,
  executeArbitrageFlow
} = require('./dist/index.js');

console.log('\n╔════════════════════════════════════════════════════════════════╗');
console.log('║     ARBITRAGE FLOW DEMONSTRATION - 7-Step Equation System     ║');
console.log('╚════════════════════════════════════════════════════════════════╝\n');

// Market Setup
console.log('📊 MARKET SETUP');
console.log('═══════════════════════════════════════════════════════════════════\n');

const pool1 = { name: 'Uniswap', reserveIn: 1000000, reserveOut: 2000000 };
const pool2 = { name: 'SushiSwap', reserveIn: 1000000, reserveOut: 2600000 };

console.log(`Pool 1 (${pool1.name}):     ReserveIn: ${pool1.reserveIn.toLocaleString()}, ReserveOut: ${pool1.reserveOut.toLocaleString()}`);
console.log(`Pool 2 (${pool2.name}): ReserveIn: ${pool2.reserveIn.toLocaleString()}, ReserveOut: ${pool2.reserveOut.toLocaleString()}\n`);

// Historical price data for TWAP
const history1 = [
  [0, 1.95],
  [10, 2.0],
  [20, 2.05]
];

const history2 = [
  [0, 2.55],
  [10, 2.6],
  [20, 2.65]
];

console.log('Historical Prices for TWAP:');
console.log(`Pool 1: ${history1.map(h => h[1]).join(', ')}`);
console.log(`Pool 2: ${history2.map(h => h[1]).join(', ')}\n`);

// Step 1: Identify Arbitrage Opportunities
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
console.log('STEP 1: IDENTIFY ARBITRAGE OPPORTUNITIES');
console.log('Formula: p_t = reserveOut / reserveIn\n');

const price1 = calculatePoolPrice(pool1.reserveIn, pool1.reserveOut);
const price2 = calculatePoolPrice(pool2.reserveIn, pool2.reserveOut);

console.log(`Pool 1 Price: ${price1.toFixed(4)}`);
console.log(`Pool 2 Price: ${price2.toFixed(4)}`);
console.log(`Price Difference: ${((price2 - price1) / price1 * 100).toFixed(2)}%\n`);

// Step 2: Determine Direction of Arbitrage
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
console.log('STEP 2: DETERMINE DIRECTION OF ARBITRAGE');
console.log('Formula: P_tokenX = poolReserveOut / poolReserveIn\n');

const [hasOpp, priceDiff, direction] = identifyArbitrageOpportunity(
  pool1.reserveIn, pool1.reserveOut,
  pool2.reserveIn, pool2.reserveOut,
  5.0
);

console.log(`Has Opportunity: ${hasOpp === 1 ? '✅ YES' : '❌ NO'}`);
console.log(`Price Difference: ${priceDiff.toFixed(2)}%`);
console.log(`Direction: ${direction === 1 ? 'Buy Pool 1, Sell Pool 2' : direction === 2 ? 'Buy Pool 2, Sell Pool 1' : 'None'}\n`);

// Step 3: Calculate Trade Amounts
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
console.log('STEP 3: CALCULATE TRADE AMOUNTS');
console.log('Input Formula:  amountIn = (ReserveIn × AmountOut × 1000) / ((ReserveOut - AmountOut) × 997) + 1');
console.log('Output Formula: amountOut = (ReserveOut × AmountIn × 997) / (ReserveIn × 1000 + AmountIn × 997)\n');

const testAmount = 50000;
const amountOut = calculateAmountOut(pool1.reserveIn, pool1.reserveOut, testAmount);
const requiredInput = calculateAmountIn(pool1.reserveIn, pool1.reserveOut, amountOut);

console.log(`For ${testAmount.toLocaleString()} input:`);
console.log(`  → Output: ${amountOut.toFixed(2)}`);
console.log(`  → Required input for same output: ${requiredInput.toFixed(2)}`);
console.log(`  → Round-trip accuracy: ${((requiredInput / testAmount - 1) * 100).toFixed(4)}%\n`);

// Step 4: Estimate Profitability
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
console.log('STEP 4: ESTIMATE PROFITABILITY');
console.log('Formula: profit = AmountOut_sell - AmountIn_buy - gas_fees - flashloan_fees\n');

const gasCost = 100;
const flashloanFee = 0.0009; // 0.09%

const profit = estimateArbitrageProfit(
  pool1.reserveIn, pool1.reserveOut,
  pool2.reserveIn, pool2.reserveOut,
  testAmount,
  gasCost,
  flashloanFee
);

console.log(`Trade Amount: ${testAmount.toLocaleString()}`);
console.log(`Gas Cost: $${gasCost}`);
console.log(`Flashloan Fee: ${(flashloanFee * 100).toFixed(2)}%`);
console.log(`Estimated Profit: $${profit.toFixed(2)}\n`);

// Step 5: Optimize Trade Size
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
console.log('STEP 5: OPTIMIZE TRADE SIZE');
console.log('Using quadratic optimization to find maximum profit\n');

const optimalSize = optimizeTradeSizeQuadratic(
  pool1.reserveIn, pool1.reserveOut,
  pool2.reserveIn, pool2.reserveOut,
  gasCost,
  flashloanFee
);

const optimalProfit = estimateArbitrageProfit(
  pool1.reserveIn, pool1.reserveOut,
  pool2.reserveIn, pool2.reserveOut,
  optimalSize,
  gasCost,
  flashloanFee
);

console.log(`Original Amount: ${testAmount.toLocaleString()} → Profit: $${profit.toFixed(2)}`);
console.log(`Optimal Amount:  ${optimalSize.toFixed(0).padStart(7)} → Profit: $${optimalProfit.toFixed(2)}`);
console.log(`Improvement: ${((optimalProfit / profit - 1) * 100).toFixed(2)}%\n`);

// Demonstrate quadratic solver
console.log('Quadratic Equation Example: x² - 5x + 6 = 0');
const [root1, root2] = solveQuadratic(1, -5, 6);
console.log(`Solutions: x = ${root1}, x = ${root2}\n`);

// Step 6: Validate Using TWAP
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
console.log('STEP 6: VALIDATE USING TWAP');
console.log('Formula: TWAP = Σ(p_i × Δt_i) / Σ(Δt_i)\n');

const twap1 = calculateTWAP(history1);
const twap2 = calculateTWAP(history2);

const isValid1 = validateWithTWAP(price1, twap1, 10);
const isValid2 = validateWithTWAP(price2, twap2, 10);

console.log(`Pool 1:`);
console.log(`  Current Price: ${price1.toFixed(4)}`);
console.log(`  TWAP: ${twap1.toFixed(4)}`);
console.log(`  Deviation: ${Math.abs((price1 - twap1) / twap1 * 100).toFixed(2)}%`);
console.log(`  Valid: ${isValid1 ? '✅ YES' : '❌ NO'}\n`);

console.log(`Pool 2:`);
console.log(`  Current Price: ${price2.toFixed(4)}`);
console.log(`  TWAP: ${twap2.toFixed(4)}`);
console.log(`  Deviation: ${Math.abs((price2 - twap2) / twap2 * 100).toFixed(2)}%`);
console.log(`  Valid: ${isValid2 ? '✅ YES' : '❌ NO'}\n`);

// Step 7: Execute the Trade
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
console.log('STEP 7: EXECUTE THE TRADE (Complete Flow)\n');

const [shouldExecute, finalAmount, finalProfit] = executeArbitrageFlow(
  pool1.reserveIn, pool1.reserveOut,
  pool2.reserveIn, pool2.reserveOut,
  history1,
  history2,
  gasCost,
  flashloanFee,
  5.0,   // Min price diff %
  10.0,  // Max TWAP deviation %
  50.0   // Min profit threshold
);

console.log('EXECUTION DECISION:');
console.log('═══════════════════════════════════════════════════════════════════\n');

if (shouldExecute === 1) {
  console.log('✅ EXECUTE ARBITRAGE\n');
  console.log(`📊 Trade Parameters:`);
  console.log(`   Amount to borrow (flashloan): ${finalAmount.toFixed(2)}`);
  console.log(`   Expected profit: $${finalProfit.toFixed(2)}`);
  console.log(`   ROI: ${(finalProfit / finalAmount * 100).toFixed(2)}%\n`);
  
  console.log(`🔄 Execution Steps:`);
  console.log(`   1. Borrow ${finalAmount.toFixed(2)} via flashloan`);
  console.log(`   2. Buy tokens on ${pool1.name} (lower price)`);
  console.log(`   3. Sell tokens on ${pool2.name} (higher price)`);
  console.log(`   4. Repay flashloan with fee`);
  console.log(`   5. Keep profit: $${finalProfit.toFixed(2)}\n`);
} else {
  console.log('❌ DO NOT EXECUTE\n');
  console.log(`Reason: Conditions not met`);
  console.log(`  - TWAP validation may have failed`);
  console.log(`  - Profit below minimum threshold`);
  console.log(`  - Price difference too small\n`);
}

console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

console.log('✨ SUMMARY\n');
console.log('The 7-step arbitrage flow successfully:');
console.log('  ✓ Identified price discrepancy between pools');
console.log('  ✓ Determined optimal arbitrage direction');
console.log('  ✓ Calculated precise trade amounts');
console.log('  ✓ Estimated profitability after all fees');
console.log('  ✓ Optimized trade size for maximum profit');
console.log('  ✓ Validated prices using TWAP');
console.log(`  ${shouldExecute === 1 ? '✓' : '✗'} Made informed execution decision\n`);

console.log('╔════════════════════════════════════════════════════════════════╗');
console.log('║                    DEMONSTRATION COMPLETE                      ║');
console.log('╚════════════════════════════════════════════════════════════════╝\n');
