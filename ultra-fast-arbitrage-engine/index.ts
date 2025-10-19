/**
 * SYMEN-MAX Ultra-Fast Arbitrage Engine
 * TypeScript interface for native Rust math engine
 */

import * as path from 'path';
import * as fs from 'fs';

// Try to load native module, fall back to JavaScript implementation if not available
let native: any;
const nativePath = path.join(__dirname, '..', 'native', 'math_engine.node');

if (fs.existsSync(nativePath)) {
  native = require(nativePath);
} else {
  // Fallback JavaScript implementation for when Rust native module is not built.
  // WARNING: This fallback is 10-100x slower than the native Rust implementation.
  native = require(path.join(__dirname, '..', 'native', 'math_engine_fallback.js'));
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
