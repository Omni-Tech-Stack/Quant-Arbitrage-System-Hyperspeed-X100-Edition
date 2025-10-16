/**
 * SYMEN-MAX Ultra-Fast Arbitrage Engine
 * TypeScript interface for native Rust math engine
 */

const native = require('../native/math_engine.node');

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

// Export native module for advanced usage
export { native };
