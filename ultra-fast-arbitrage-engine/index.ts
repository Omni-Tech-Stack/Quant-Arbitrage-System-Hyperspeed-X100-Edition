/**
 * SYMEN-MAX Ultra-Fast Arbitrage Engine
 * TypeScript interface for native Rust math engine with JavaScript fallbacks
 */

import * as path from 'path';

// Try to load native module, fall back to JS implementation if not available
let native: any = null;
try {
  native = require(path.join(__dirname, '..', 'native', 'math_engine.node'));
} catch (e) {
  console.warn('[Ultra-Fast Engine] Native Rust module not available, using JavaScript fallbacks');
}

// JavaScript fallback implementations
const jsFallbacks = {
  computeUniswapV2Slippage(reserveIn: number, reserveOut: number, amountIn: number): number {
    if (amountIn === 0) return 0;
    const k = reserveIn * reserveOut;
    const newReserveIn = reserveIn + amountIn * 0.997; // 0.3% fee
    const newReserveOut = k / newReserveIn;
    const amountOut = reserveOut - newReserveOut;
    const idealAmountOut = (amountIn * reserveOut) / reserveIn;
    return ((idealAmountOut - amountOut) / idealAmountOut) * 100;
  },
  
  computeUniswapV3Slippage(liquidity: number, sqrtPrice: number, amountIn: number): number {
    // Simplified V3 slippage calculation
    return (amountIn / (liquidity * sqrtPrice)) * 100;
  },
  
  computeCurveSlippage(balanceIn: number, balanceOut: number, amountIn: number, amplification: number): number {
    // Simplified Curve slippage
    const totalBalance = balanceIn + balanceOut;
    return (amountIn / totalBalance) * (100 / amplification);
  },
  
  computeBalancerSlippage(balanceIn: number, balanceOut: number, weightIn: number, weightOut: number, amountIn: number): number {
    // Balancer weighted pool formula
    const spotPrice = (balanceIn / weightIn) / (balanceOut / weightOut);
    const effectivePrice = ((balanceIn + amountIn) / weightIn) / (balanceOut / weightOut);
    return ((effectivePrice - spotPrice) / spotPrice) * 100;
  },
  
  computeAggregatorSlippage(slippages: number[]): number {
    return Math.min(...slippages);
  },
  
  optimalTradeSize(reserveIn: number, reserveOut: number, gasCost: number, minProfit: number): number {
    // For a constant product AMM (x * y = k), the optimal trade maximizes profit
    // Binary search for optimal amount considering gas and minProfit
    let low = 0;
    let high = reserveIn * 0.09; // Max 9% of reserve for safety margin
    let best = 0;
    let bestProfit = -Infinity;
    
    for (let i = 0; i < 30; i++) {
      const mid = (low + high) / 2;
      if (mid === 0) break;
      
      const amountOut = (reserveOut * mid * 997) / (reserveIn * 1000 + mid * 997);
      const profit = amountOut - mid - gasCost;
      
      if (profit > bestProfit) {
        bestProfit = profit;
        best = mid;
      }
      
      // Adjust search range
      if (i < 29) {
        const midPlus = mid * 1.01;
        const amountOutPlus = (reserveOut * midPlus * 997) / (reserveIn * 1000 + midPlus * 997);
        const profitPlus = amountOutPlus - midPlus - gasCost;
        
        if (profitPlus > profit) {
          low = mid;
        } else {
          high = mid;
        }
      }
    }
    
    return bestProfit >= minProfit ? best : 0;
  },
  
  calculateFlashloanAmount(reserveInBuy: number, reserveOutBuy: number, reserveInSell: number, reserveOutSell: number, flashloanFee: number, gasCost: number): number {
    // Binary search for optimal amount
    let low = 0;
    let high = Math.min(reserveInBuy, reserveInSell) * 0.3; // Max 30% of pool
    let best = 0;
    let bestProfit = 0;
    
    for (let i = 0; i < 50; i++) {
      const mid = (low + high) / 2;
      const amountOut = (reserveOutBuy * mid * 997) / (reserveInBuy * 1000 + mid * 997);
      const finalOut = (reserveOutSell * amountOut * 997) / (reserveInSell * 1000 + amountOut * 997);
      const profit = finalOut - mid - (mid * flashloanFee) - gasCost;
      
      if (profit > bestProfit) {
        bestProfit = profit;
        best = mid;
      }
      
      if (profit > 0) {
        low = mid;
      } else {
        high = mid;
      }
    }
    
    return bestProfit > 0 ? best : 0;
  },
  
  calculateMarketImpact(reserveIn: number, reserveOut: number, flashloanAmount: number): number {
    const priceBefore = reserveOut / reserveIn;
    const newReserveIn = reserveIn + flashloanAmount;
    const newReserveOut = (reserveIn * reserveOut) / newReserveIn;
    const priceAfter = newReserveOut / newReserveIn;
    return ((priceBefore - priceAfter) / priceBefore) * 100;
  },
  
  calculateMultihopSlippage(reserves: number[][], flashloanAmount: number): number {
    let currentAmount = flashloanAmount;
    let totalSlippage = 0;
    
    for (const [reserveIn, reserveOut] of reserves) {
      const slippage = this.computeUniswapV2Slippage(reserveIn, reserveOut, currentAmount);
      totalSlippage += slippage;
      const amountOut = (reserveOut * currentAmount * 997) / (reserveIn * 1000 + currentAmount * 997);
      currentAmount = amountOut;
    }
    
    return totalSlippage;
  },
  
  simulateParallelFlashloanPaths(paths: number[][][], flashloanAmounts: number[], flashloanFee: number, gasCosts: number[]): number[][] {
    return paths.map((path, idx) => {
      let currentAmount = flashloanAmounts[idx];
      let totalSlippage = 0;
      
      for (const [reserveIn, reserveOut] of path) {
        const amountOut = (reserveOut * currentAmount * 997) / (reserveIn * 1000 + currentAmount * 997);
        const slippage = this.computeUniswapV2Slippage(reserveIn, reserveOut, currentAmount);
        totalSlippage += slippage;
        currentAmount = amountOut;
      }
      
      const profit = currentAmount - flashloanAmounts[idx] * (1 + flashloanFee) - gasCosts[idx];
      return [profit, totalSlippage, idx];
    });
  },
  
  calculateFlashloanAmountV3(liquidity: number, sqrtPriceBuy: number, sqrtPriceSell: number, flashloanFee: number, gasCost: number): number {
    // Simplified V3 calculation
    return liquidity * (sqrtPriceSell - sqrtPriceBuy) / sqrtPriceBuy;
  },
  
  calculatePoolPrice(reserveIn: number, reserveOut: number): number {
    return reserveOut / reserveIn;
  },
  
  identifyArbitrageOpportunity(pool1ReserveIn: number, pool1ReserveOut: number, pool2ReserveIn: number, pool2ReserveOut: number, minPriceDiffPct: number): number[] {
    const price1 = pool1ReserveOut / pool1ReserveIn;
    const price2 = pool2ReserveOut / pool2ReserveIn;
    const priceDiff = Math.abs(price1 - price2) / Math.min(price1, price2) * 100;
    
    if (priceDiff < minPriceDiffPct) {
      return [0, 0, 0];
    }
    
    const direction = price1 < price2 ? 1 : 2;
    return [1, priceDiff, direction];
  },
  
  calculateAmountIn(reserveIn: number, reserveOut: number, amountOut: number): number {
    return ((reserveIn * amountOut * 1000) / ((reserveOut - amountOut) * 997)) + 1;
  },
  
  calculateAmountOut(reserveIn: number, reserveOut: number, amountIn: number): number {
    return (reserveOut * amountIn * 997) / (reserveIn * 1000 + amountIn * 997);
  },
  
  estimateArbitrageProfit(buyReserveIn: number, buyReserveOut: number, sellReserveIn: number, sellReserveOut: number, amountIn: number, gasCost: number, flashloanFeePct: number): number {
    const amountOut = this.calculateAmountOut(buyReserveIn, buyReserveOut, amountIn);
    const finalOut = this.calculateAmountOut(sellReserveIn, sellReserveOut, amountOut);
    return finalOut - amountIn - gasCost - (amountIn * flashloanFeePct);
  },
  
  solveQuadratic(a: number, b: number, c: number): number[] {
    const discriminant = b * b - 4 * a * c;
    if (discriminant < 0) return [0, 0];
    const sqrtDisc = Math.sqrt(discriminant);
    return [(-b + sqrtDisc) / (2 * a), (-b - sqrtDisc) / (2 * a)];
  },
  
  optimizeTradeSizeQuadratic(buyReserveIn: number, buyReserveOut: number, sellReserveIn: number, sellReserveOut: number, gasCost: number, flashloanFeePct: number): number {
    // Simplified optimization using binary search
    let best = 0;
    let bestProfit = -Infinity;
    const maxAmount = Math.min(buyReserveIn, sellReserveIn) * 0.3;
    
    for (let i = 0; i <= 100; i++) {
      const amount = (i / 100) * maxAmount;
      const profit = this.estimateArbitrageProfit(buyReserveIn, buyReserveOut, sellReserveIn, sellReserveOut, amount, gasCost, flashloanFeePct);
      if (profit > bestProfit) {
        bestProfit = profit;
        best = amount;
      }
    }
    
    return best;
  },
  
  calculateTwap(priceSamples: number[][]): number {
    if (priceSamples.length < 2) return 0;
    let sum = 0;
    let totalTime = 0;
    for (let i = 1; i < priceSamples.length; i++) {
      const dt = priceSamples[i][0] - priceSamples[i-1][0];
      sum += priceSamples[i][1] * dt;
      totalTime += dt;
    }
    return totalTime > 0 ? sum / totalTime : 0;
  },
  
  validateWithTwap(currentPrice: number, twap: number, maxDeviationPct: number): boolean {
    const deviation = Math.abs(currentPrice - twap) / twap * 100;
    return deviation <= maxDeviationPct;
  },
  
  executeArbitrageFlow(pool1ReserveIn: number, pool1ReserveOut: number, pool2ReserveIn: number, pool2ReserveOut: number, priceSamplesPool1: number[][], priceSamplesPool2: number[][], config: any): number[] {
    // Step 1: Identify opportunity
    const opportunity = this.identifyArbitrageOpportunity(pool1ReserveIn, pool1ReserveOut, pool2ReserveIn, pool2ReserveOut, config.minPriceDiffPct);
    if (opportunity[0] === 0) return [0, 0, 0];
    
    // Step 2: Calculate optimal amount
    const [buyReserveIn, buyReserveOut, sellReserveIn, sellReserveOut] = opportunity[2] === 1
      ? [pool1ReserveIn, pool1ReserveOut, pool2ReserveIn, pool2ReserveOut]
      : [pool2ReserveIn, pool2ReserveOut, pool1ReserveIn, pool1ReserveOut];
    
    const optimalAmount = this.optimizeTradeSizeQuadratic(buyReserveIn, buyReserveOut, sellReserveIn, sellReserveOut, config.gasCost, config.flashloanFeePct);
    
    // Step 3: Estimate profit
    const profit = this.estimateArbitrageProfit(buyReserveIn, buyReserveOut, sellReserveIn, sellReserveOut, optimalAmount, config.gasCost, config.flashloanFeePct);
    
    // Step 4: Validate with TWAP
    const twap1 = this.calculateTwap(priceSamplesPool1);
    const twap2 = this.calculateTwap(priceSamplesPool2);
    const currentPrice1 = this.calculatePoolPrice(pool1ReserveIn, pool1ReserveOut);
    const currentPrice2 = this.calculatePoolPrice(pool2ReserveIn, pool2ReserveOut);
    const valid1 = this.validateWithTwap(currentPrice1, twap1, config.maxTwapDeviationPct);
    const valid2 = this.validateWithTwap(currentPrice2, twap2, config.maxTwapDeviationPct);
    
    // Step 5: Make decision
    const shouldExecute = valid1 && valid2 && profit >= config.minProfitThreshold ? 1 : 0;
    return [shouldExecute, optimalAmount, profit];
  }
};

// Use native module if available, otherwise use JS fallbacks
if (!native) {
  native = jsFallbacks;
}

/**
 * Compute slippage for Uniswap V2 style constant product pools
 * Formula: x * y = k
 */
export function computeSlippage(
  reserveIn: number,
  reserveOut: number,
  amountIn: number
): number {
  return native.computeUniswapV2Slippage(reserveIn, reserveOut, amountIn);
}

/**
 * Compute slippage for Uniswap V3 concentrated liquidity pools
 */
export function computeUniswapV3Slippage(
  liquidity: number,
  sqrtPrice: number,
  amountIn: number
): number {
  return native.computeUniswapV3Slippage(liquidity, sqrtPrice, amountIn);
}

/**
 * Compute slippage for Curve stableswap pools with amplification
 */
export function computeCurveSlippage(
  balanceIn: number,
  balanceOut: number,
  amountIn: number,
  amplification: number
): number {
  return native.computeCurveSlippage(balanceIn, balanceOut, amountIn, amplification);
}

/**
 * Compute slippage for Balancer weighted pools
 */
export function computeBalancerSlippage(
  balanceIn: number,
  balanceOut: number,
  weightIn: number,
  weightOut: number,
  amountIn: number
): number {
  return native.computeBalancerSlippage(balanceIn, balanceOut, weightIn, weightOut, amountIn);
}

/**
 * Compute best route slippage from aggregator
 * Returns minimum slippage across all routes
 */
export function computeAggregatorSlippage(slippages: number[]): number {
  return native.computeAggregatorSlippage(slippages);
}

/**
 * Calculate optimal trade size for maximum profit
 */
export function getOptimalTradeSize(
  reserveIn: number,
  reserveOut: number,
  gasCost: number,
  minProfit: number
): number {
  return native.optimalTradeSize(reserveIn, reserveOut, gasCost, minProfit);
}

/**
 * Calculate optimal flashloan amount for arbitrage opportunity
 * Determines the best flashloan size based on pool liquidity and expected profit
 */
export function calculateFlashloanAmount(
  reserveInBuy: number,
  reserveOutBuy: number,
  reserveInSell: number,
  reserveOutSell: number,
  flashloanFee: number,
  gasCost: number
): number {
  return native.calculateFlashloanAmount(
    reserveInBuy,
    reserveOutBuy,
    reserveInSell,
    reserveOutSell,
    flashloanFee,
    gasCost
  );
}

/**
 * Calculate market impact (price slippage) from a flashloan-sized trade
 * Returns the percentage price impact on the pool
 */
export function calculateMarketImpact(
  reserveIn: number,
  reserveOut: number,
  flashloanAmount: number
): number {
  return native.calculateMarketImpact(reserveIn, reserveOut, flashloanAmount);
}

/**
 * Calculate total slippage for multi-hop arbitrage path
 * @param reserves - Array of [reserveIn, reserveOut] pairs for each hop
 * @param flashloanAmount - Amount borrowed via flashloan
 */
export function calculateMultihopSlippage(
  reserves: number[][],
  flashloanAmount: number
): number {
  return native.calculateMultihopSlippage(reserves, flashloanAmount);
}

/**
 * Simulate flashloan arbitrage execution across multiple paths in parallel
 * Returns array of [profit, slippage, pathIndex] for each path
 * @param paths - Array of paths, each path is array of [reserveIn, reserveOut] pairs
 * @param flashloanAmounts - Flashloan amount for each path
 * @param flashloanFee - Fee percentage for flashloan (e.g., 0.0009 for 0.09%)
 * @param gasCosts - Gas cost for each path
 */
export function simulateParallelFlashloanPaths(
  paths: number[][][],
  flashloanAmounts: number[],
  flashloanFee: number,
  gasCosts: number[]
): number[][] {
  return native.simulateParallelFlashloanPaths(
    paths,
    flashloanAmounts,
    flashloanFee,
    gasCosts
  );
}

/**
 * Calculate optimal flashloan amount for Uniswap V3 concentrated liquidity
 */
export function calculateFlashloanAmountV3(
  liquidity: number,
  sqrtPriceBuy: number,
  sqrtPriceSell: number,
  flashloanFee: number,
  gasCost: number
): number {
  return native.calculateFlashloanAmountV3(
    liquidity,
    sqrtPriceBuy,
    sqrtPriceSell,
    flashloanFee,
    gasCost
  );
}

// New arbitrage flow functions

/**
 * Step 1: Calculate token price from pool reserves
 * Formula: p_t = reserve_out / reserve_in
 */
export function calculatePoolPrice(
  reserveIn: number,
  reserveOut: number
): number {
  return native.calculatePoolPrice(reserveIn, reserveOut);
}

/**
 * Step 2: Identify arbitrage opportunity by comparing prices across pools
 * Returns [hasOpportunity (0/1), priceDifference%, direction (0/1/2)]
 * direction: 0 = no opportunity, 1 = buy pool1/sell pool2, 2 = buy pool2/sell pool1
 */
export function identifyArbitrageOpportunity(
  pool1ReserveIn: number,
  pool1ReserveOut: number,
  pool2ReserveIn: number,
  pool2ReserveOut: number,
  minPriceDiffPct: number
): number[] {
  return native.identifyArbitrageOpportunity(
    pool1ReserveIn,
    pool1ReserveOut,
    pool2ReserveIn,
    pool2ReserveOut,
    minPriceDiffPct
  );
}

/**
 * Step 3: Calculate input amount needed for desired output
 * Formula: amountIn = (ReserveIn × AmountOut × 1000) / ((ReserveOut - AmountOut) × 997) + 1
 */
export function calculateAmountIn(
  reserveIn: number,
  reserveOut: number,
  amountOut: number
): number {
  return native.calculateAmountIn(reserveIn, reserveOut, amountOut);
}

/**
 * Step 3: Calculate output amount for given input
 * Formula: amountOut = (ReserveOut × AmountIn × 997) / (ReserveIn × 1000 + AmountIn × 997)
 */
export function calculateAmountOut(
  reserveIn: number,
  reserveOut: number,
  amountIn: number
): number {
  return native.calculateAmountOut(reserveIn, reserveOut, amountIn);
}

/**
 * Step 4: Estimate profitability of arbitrage
 * Formula: profit = AmountOut_sell - AmountIn_buy - gas_fees - flashloan_fees
 */
export function estimateArbitrageProfit(
  buyReserveIn: number,
  buyReserveOut: number,
  sellReserveIn: number,
  sellReserveOut: number,
  amountIn: number,
  gasCost: number,
  flashloanFeePct: number
): number {
  return native.estimateArbitrageProfit(
    buyReserveIn,
    buyReserveOut,
    sellReserveIn,
    sellReserveOut,
    amountIn,
    gasCost,
    flashloanFeePct
  );
}

/**
 * Step 5: Solve quadratic equation ax² + bx + c = 0
 * Returns [root1, root2]
 */
export function solveQuadratic(a: number, b: number, c: number): number[] {
  return native.solveQuadratic(a, b, c);
}

/**
 * Step 5: Find optimal trade size using quadratic optimization
 * This finds the trade size that maximizes profit considering slippage
 */
export function optimizeTradeSizeQuadratic(
  buyReserveIn: number,
  buyReserveOut: number,
  sellReserveIn: number,
  sellReserveOut: number,
  gasCost: number,
  flashloanFeePct: number
): number {
  return native.optimizeTradeSizeQuadratic(
    buyReserveIn,
    buyReserveOut,
    sellReserveIn,
    sellReserveOut,
    gasCost,
    flashloanFeePct
  );
}

/**
 * Step 6: Calculate TWAP (Time-Weighted Average Price)
 * Formula: TWAP = (a_t2 - a_t1) / (t2 - t1)
 * @param priceSamples - Array of [timestamp, price] pairs
 */
export function calculateTWAP(priceSamples: number[][]): number {
  return native.calculateTwap(priceSamples);
}

/**
 * Step 6: Validate arbitrage opportunity using TWAP
 * Returns true if current price is close to TWAP (not manipulated)
 */
export function validateWithTWAP(
  currentPrice: number,
  twap: number,
  maxDeviationPct: number
): boolean {
  return native.validateWithTwap(currentPrice, twap, maxDeviationPct);
}

/**
 * Configuration parameters for arbitrage execution
 */
export interface ArbitrageConfig {
  gasCost: number;
  flashloanFeePct: number;
  minPriceDiffPct: number;
  maxTwapDeviationPct: number;
  minProfitThreshold: number;
}

/**
 * Step 7: Complete arbitrage execution flow
 * Returns [shouldExecute (0/1), optimalAmount, expectedProfit]
 * 
 * This function implements the complete logical flow:
 * 1. Identify Arbitrage Opportunities
 * 2. Determine Direction of Arbitrage
 * 3. Calculate Trade Amounts
 * 4. Estimate Profitability
 * 5. Optimize Trade Size
 * 6. Validate Using TWAP
 * 7. Execute Decision
 */
export function executeArbitrageFlow(
  pool1ReserveIn: number,
  pool1ReserveOut: number,
  pool2ReserveIn: number,
  pool2ReserveOut: number,
  priceSamplesPool1: number[][],
  priceSamplesPool2: number[][],
  config: ArbitrageConfig
): number[] {
  return native.executeArbitrageFlow(
    pool1ReserveIn,
    pool1ReserveOut,
    pool2ReserveIn,
    pool2ReserveOut,
    priceSamplesPool1,
    priceSamplesPool2,
    config
  );
}

// Export native module for advanced usage
export { native };
