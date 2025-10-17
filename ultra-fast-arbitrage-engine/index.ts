/**
 * SYMEN-MAX Ultra-Fast Arbitrage Engine
 * TypeScript interface for native Rust math engine
 */

import * as path from 'path';

const native = require(path.join(__dirname, '..', 'native', 'math_engine.node'));

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

// Export native module for advanced usage
export { native };
