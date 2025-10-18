/**
 * JavaScript Fallback for Ultra-Fast Arbitrage Engine
 * Used when native Rust module is not available
 * Provides the same API but with JavaScript implementations
 */

// Uniswap V2 Slippage Calculation
// Formula: amountOut = (reserveOut * amountIn * 997) / (reserveIn * 1000 + amountIn * 997)
function computeUniswapV2Slippage(reserveIn, reserveOut, amountIn) {
  if (amountIn === 0) return 0;
  
  const amountInWithFee = amountIn * 997;
  const numerator = amountInWithFee * reserveOut;
  const denominator = reserveIn * 1000 + amountInWithFee;
  const amountOut = numerator / denominator;
  const idealAmountOut = (amountIn * reserveOut) / reserveIn;
  return ((idealAmountOut - amountOut) / idealAmountOut) * 100;
}

// Uniswap V3 Slippage (Simplified)
function computeUniswapV3Slippage(liquidity, sqrtPrice, amountIn) {
  // Simplified calculation for V3
  const priceImpact = amountIn / (liquidity * sqrtPrice);
  return priceImpact * 100;
}

// Curve Slippage (Simplified stableswap)
function computeCurveSlippage(balanceIn, balanceOut, amountIn, amplification) {
  // Simplified Curve calculation
  const totalBalance = balanceIn + balanceOut;
  const priceImpact = (amountIn / totalBalance) * (1 / Math.sqrt(amplification));
  return priceImpact * 100;
}

// Balancer Weighted Pool Slippage
function computeBalancerSlippage(balanceIn, balanceOut, weightIn, weightOut, amountIn) {
  // Balancer formula: amountOut = balanceOut * (1 - (balanceIn / (balanceIn + amountIn))^(weightIn/weightOut))
  const ratio = balanceIn / (balanceIn + amountIn);
  const exponent = weightIn / weightOut;
  const amountOut = balanceOut * (1 - Math.pow(ratio, exponent));
  const idealAmountOut = (amountIn * balanceOut * weightOut) / (balanceIn * weightIn);
  return ((idealAmountOut - amountOut) / idealAmountOut) * 100;
}

// Aggregator Slippage (minimum across routes)
function computeAggregatorSlippage(slippages) {
  return Math.min(...slippages);
}

// Optimal Trade Size
function optimalTradeSize(reserveIn, reserveOut, gasCost, minProfit) {
  // Calculate theoretical max profit: assume 10% of pool can generate some profit
  // But need to account for slippage
  const maxTrade = reserveIn * 0.1;
  const amountOut = (reserveOut * maxTrade * 997) / (reserveIn * 1000 + maxTrade * 997);
  const grossProfit = amountOut - maxTrade;
  const netProfit = grossProfit - gasCost;
  
  // If even the theoretical max can't meet minimum profit, return 0
  if (netProfit < minProfit) {
    return 0;
  }
  
  // Calculate optimal size (simplified formula)
  // For Uniswap V2: optimal is around sqrt(k) / 2 where k = reserveIn * reserveOut
  const k = reserveIn * reserveOut;
  const optimalBase = Math.sqrt(k) * 0.05; // 5% of sqrt(k)
  
  // Ensure it's reasonable (max 10% of reserve)
  const optimal = Math.min(optimalBase, maxTrade);
  
  // Ensure it meets minimum profit
  return Math.max(minProfit, optimal);
}

// Calculate Flashloan Amount
function calculateFlashloanAmount(reserveInBuy, reserveOutBuy, reserveInSell, reserveOutSell, flashloanFee, gasCost) {
  // Calculate price difference to see if arbitrage is profitable
  const priceBuy = reserveOutBuy / reserveInBuy;
  const priceSell = reserveOutSell / reserveInSell;
  
  // If no arbitrage opportunity, return 0
  if (Math.abs(priceBuy - priceSell) < 0.01) {
    return 0;
  }
  
  // Optimal flashloan is typically around sqrt(k) for AMM pools
  // But we want to limit to 30% of reserves to avoid excessive slippage
  const optimalBuy = Math.sqrt(reserveInBuy * reserveOutBuy) * 0.15;
  const optimalSell = Math.sqrt(reserveInSell * reserveOutSell) * 0.15;
  const maxReserveBuy = reserveInBuy * 0.3;
  const maxReserveSell = reserveInSell * 0.3;
  
  // Take minimum to ensure we don't exceed limits
  return Math.min(optimalBuy, optimalSell, maxReserveBuy, maxReserveSell);
}

// Market Impact
function calculateMarketImpact(reserveIn, reserveOut, flashloanAmount) {
  return (flashloanAmount / reserveIn) * 100;
}

// Multihop Slippage
function calculateMultihopSlippage(reserves, flashloanAmount) {
  let totalSlippage = 0;
  let currentAmount = flashloanAmount;
  
  for (const [reserveIn, reserveOut] of reserves) {
    const slippage = computeUniswapV2Slippage(reserveIn, reserveOut, currentAmount);
    totalSlippage += slippage;
    currentAmount = currentAmount * (1 - slippage / 100);
  }
  
  return totalSlippage;
}

// Simulate Parallel Flashloan Paths
function simulateParallelFlashloanPaths(paths, flashloanAmounts, flashloanFee, gasCosts) {
  return paths.map((path, i) => {
    const amount = flashloanAmounts[i];
    const gasCost = gasCosts[i];
    const slippage = calculateMultihopSlippage(path, amount);
    const profit = amount * (1 - slippage / 100) - amount - (amount * flashloanFee) - gasCost;
    return [profit, slippage, i];
  });
}

// Flashloan Amount V3
function calculateFlashloanAmountV3(liquidity, sqrtPriceBuy, sqrtPriceSell, flashloanFee, gasCost) {
  const priceDiff = Math.abs(sqrtPriceBuy - sqrtPriceSell);
  return liquidity * priceDiff * 0.5;
}

// Pool Price
function calculatePoolPrice(reserveIn, reserveOut) {
  return reserveOut / reserveIn;
}

// Identify Arbitrage Opportunity
function identifyArbitrageOpportunity(pool1ReserveIn, pool1ReserveOut, pool2ReserveIn, pool2ReserveOut, minPriceDiffPct) {
  const price1 = calculatePoolPrice(pool1ReserveIn, pool1ReserveOut);
  const price2 = calculatePoolPrice(pool2ReserveIn, pool2ReserveOut);
  const priceDiff = Math.abs(price1 - price2);
  const priceDiffPct = (priceDiff / Math.min(price1, price2)) * 100;
  
  if (priceDiffPct >= minPriceDiffPct) {
    const direction = price1 < price2 ? 1 : 2;
    return [1, priceDiffPct, direction];
  }
  
  return [0, 0, 0];
}

// Calculate Amount In (Uniswap V2 formula)
function calculateAmountIn(reserveIn, reserveOut, amountOut) {
  const numerator = reserveIn * amountOut * 1000;
  const denominator = (reserveOut - amountOut) * 997;
  return Math.floor(numerator / denominator) + 1;
}

// Calculate Amount Out (Uniswap V2 formula)
function calculateAmountOut(reserveIn, reserveOut, amountIn) {
  const amountInWithFee = amountIn * 997;
  const numerator = amountInWithFee * reserveOut;
  const denominator = reserveIn * 1000 + amountInWithFee;
  return Math.floor(numerator / denominator);
}

// Estimate Arbitrage Profit
function estimateArbitrageProfit(buyReserveIn, buyReserveOut, sellReserveIn, sellReserveOut, amountIn, gasCost, flashloanFeePct) {
  const amountOut = calculateAmountOut(buyReserveIn, buyReserveOut, amountIn);
  const finalAmount = calculateAmountOut(sellReserveOut, sellReserveIn, amountOut);
  const flashloanFee = amountIn * flashloanFeePct;
  return finalAmount - amountIn - flashloanFee - gasCost;
}

// Solve Quadratic Equation
function solveQuadratic(a, b, c) {
  const discriminant = b * b - 4 * a * c;
  if (discriminant < 0) return [0, 0];
  
  const sqrtD = Math.sqrt(discriminant);
  const root1 = (-b + sqrtD) / (2 * a);
  const root2 = (-b - sqrtD) / (2 * a);
  
  return [root1, root2];
}

// Optimize Trade Size using Quadratic

// Binary search bounds for optimizeTradeSizeQuadratic
const BINARY_SEARCH_INITIAL_LOW = 100;
const BINARY_SEARCH_INITIAL_HIGH_FACTOR = 0.1;

function optimizeTradeSizeQuadratic(buyReserveIn, buyReserveOut, sellReserveIn, sellReserveOut, gasCost, flashloanFeePct) {
  // Simplified: use binary search for optimal amount
  let low = BINARY_SEARCH_INITIAL_LOW;
  let high = Math.min(buyReserveIn, sellReserveIn) * BINARY_SEARCH_INITIAL_HIGH_FACTOR;
  let bestAmount = 0;
  let bestProfit = -Infinity;
  
  for (let i = 0; i < 20; i++) {
    const mid = (low + high) / 2;
    const profit = estimateArbitrageProfit(buyReserveIn, buyReserveOut, sellReserveIn, sellReserveOut, mid, gasCost, flashloanFeePct);
    
    if (profit > bestProfit) {
      bestProfit = profit;
      bestAmount = mid;
    }
    
    const profitLow = estimateArbitrageProfit(buyReserveIn, buyReserveOut, sellReserveIn, sellReserveOut, low, gasCost, flashloanFeePct);
    const profitHigh = estimateArbitrageProfit(buyReserveIn, buyReserveOut, sellReserveIn, sellReserveOut, high, gasCost, flashloanFeePct);
    
    if (profitLow > profitHigh) {
      high = mid;
    } else {
      low = mid;
    }
  }
  
  return bestAmount;
}

// Calculate TWAP
function calculateTwap(priceSamples) {
  if (priceSamples.length < 2) return 0;
  
  let weightedSum = 0;
  let totalTime = 0;
  
  for (let i = 1; i < priceSamples.length; i++) {
    const [t1, p1] = priceSamples[i - 1];
    const [t2, p2] = priceSamples[i];
    const timeDiff = t2 - t1;
    weightedSum += p1 * timeDiff;
    totalTime += timeDiff;
  }
  
  return totalTime > 0 ? weightedSum / totalTime : 0;
}

// Validate with TWAP
function validateWithTwap(currentPrice, twap, maxDeviationPct) {
  const deviation = Math.abs(currentPrice - twap) / twap * 100;
  return deviation <= maxDeviationPct;
}

// Execute Complete Arbitrage Flow
function executeArbitrageFlow(
  pool1ReserveIn,
  pool1ReserveOut,
  pool2ReserveIn,
  pool2ReserveOut,
  priceSamplesPool1,
  priceSamplesPool2,
  config
) {
  // Step 1: Identify opportunity
  const [hasOpp, priceDiff, direction] = identifyArbitrageOpportunity(
    pool1ReserveIn,
    pool1ReserveOut,
    pool2ReserveIn,
    pool2ReserveOut,
    config.minPriceDiffPct
  );
  
  if (!hasOpp) return [0, 0, 0];
  
  // Step 2: Calculate TWAP for both pools
  const twap1 = calculateTwap(priceSamplesPool1);
  const twap2 = calculateTwap(priceSamplesPool2);
  const price1 = calculatePoolPrice(pool1ReserveIn, pool1ReserveOut);
  const price2 = calculatePoolPrice(pool2ReserveIn, pool2ReserveOut);
  
  // Step 3: Validate with TWAP
  const valid1 = validateWithTwap(price1, twap1, config.maxTwapDeviationPct);
  const valid2 = validateWithTwap(price2, twap2, config.maxTwapDeviationPct);
  
  if (!valid1 || !valid2) return [0, 0, 0];
  
  // Step 4: Optimize trade size based on direction
  let optimalAmount, expectedProfit;
  
  if (direction === 1) {
    // Buy from pool1, sell to pool2
    optimalAmount = optimizeTradeSizeQuadratic(
      pool1ReserveIn,
      pool1ReserveOut,
      pool2ReserveOut,
      pool2ReserveIn,
      config.gasCost,
      config.flashloanFeePct
    );
    expectedProfit = estimateArbitrageProfit(
      pool1ReserveIn,
      pool1ReserveOut,
      pool2ReserveOut,
      pool2ReserveIn,
      optimalAmount,
      config.gasCost,
      config.flashloanFeePct
    );
  } else {
    // Buy from pool2, sell to pool1
    optimalAmount = optimizeTradeSizeQuadratic(
      pool2ReserveIn,
      pool2ReserveOut,
      pool1ReserveOut,
      pool1ReserveIn,
      config.gasCost,
      config.flashloanFeePct
    );
    expectedProfit = estimateArbitrageProfit(
      pool2ReserveIn,
      pool2ReserveOut,
      pool1ReserveOut,
      pool1ReserveIn,
      optimalAmount,
      config.gasCost,
      config.flashloanFeePct
    );
  }
  
  // Step 5: Check if profit meets minimum threshold
  const shouldExecute = expectedProfit >= config.minProfitThreshold ? 1 : 0;
  
  return [shouldExecute, optimalAmount, expectedProfit];
}

// Export all functions
module.exports = {
  computeUniswapV2Slippage,
  computeUniswapV3Slippage,
  computeCurveSlippage,
  computeBalancerSlippage,
  computeAggregatorSlippage,
  optimalTradeSize,
  calculateFlashloanAmount,
  calculateMarketImpact,
  calculateMultihopSlippage,
  simulateParallelFlashloanPaths,
  calculateFlashloanAmountV3,
  calculatePoolPrice,
  identifyArbitrageOpportunity,
  calculateAmountIn,
  calculateAmountOut,
  estimateArbitrageProfit,
  solveQuadratic,
  optimizeTradeSizeQuadratic,
  calculateTwap,
  validateWithTwap,
  executeArbitrageFlow,
};
