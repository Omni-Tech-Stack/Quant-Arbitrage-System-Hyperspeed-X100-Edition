/**
 * Market Data Module Tests
 * Tests for handling market data, reserves, and pool calculations
 */

import * as ArbitrageEngine from '../ultra-fast-arbitrage-engine/index';

describe('MarketDataModule', () => {
  describe('Amount Calculations', () => {
    test('should calculate amount out for given input', () => {
      const reserveIn = 1000000;
      const reserveOut = 2000000;
      const amountIn = 10000;

      const amountOut = ArbitrageEngine.calculateAmountOut(
        reserveIn,
        reserveOut,
        amountIn
      );

      expect(amountOut).toBeGreaterThan(0);
      expect(amountOut).toBeLessThan(amountIn * 2); // Should be less than 2x due to fees
    });

    test('should calculate amount in for desired output', () => {
      const reserveIn = 1000000;
      const reserveOut = 2000000;
      const amountOut = 10000;

      const amountIn = ArbitrageEngine.calculateAmountIn(
        reserveIn,
        reserveOut,
        amountOut
      );

      expect(amountIn).toBeGreaterThan(0);
      expect(amountIn).toBeGreaterThan(amountOut / 2); // Should account for fees
    });
  });

  describe('Slippage Calculations - Uniswap V2', () => {
    test('should compute slippage for small trades', () => {
      const reserveIn = 1000000;
      const reserveOut = 2000000;
      const amountIn = 1000; // 0.1% of reserve

      const slippage = ArbitrageEngine.computeSlippage(
        reserveIn,
        reserveOut,
        amountIn
      );

      expect(slippage).toBeGreaterThan(0);
      expect(slippage).toBeLessThan(1); // Should be less than 1% for small trade
    });

    test('should compute higher slippage for large trades', () => {
      const reserveIn = 1000000;
      const reserveOut = 2000000;
      
      const smallTrade = 1000;
      const largeTrade = 100000; // 10% of reserve

      const smallSlippage = ArbitrageEngine.computeSlippage(
        reserveIn,
        reserveOut,
        smallTrade
      );

      const largeSlippage = ArbitrageEngine.computeSlippage(
        reserveIn,
        reserveOut,
        largeTrade
      );

      expect(largeSlippage).toBeGreaterThan(smallSlippage);
    });
  });

  describe('Slippage Calculations - Uniswap V3', () => {
    test('should compute V3 slippage with concentrated liquidity', () => {
      const liquidity = 5000000;
      const sqrtPrice = 1.414; // sqrt(2)
      const amountIn = 1000;

      const slippage = ArbitrageEngine.computeUniswapV3Slippage(
        liquidity,
        sqrtPrice,
        amountIn
      );

      expect(slippage).toBeGreaterThan(0);
    });
  });

  describe('Slippage Calculations - Curve', () => {
    test('should compute Curve slippage for stableswap', () => {
      const balanceIn = 5000000;
      const balanceOut = 5000000;
      const amountIn = 10000;
      const amplification = 2000;

      const slippage = ArbitrageEngine.computeCurveSlippage(
        balanceIn,
        balanceOut,
        amountIn,
        amplification
      );

      expect(slippage).toBeGreaterThan(0);
      expect(slippage).toBeLessThan(1); // Stablecoins should have low slippage
    });
  });

  describe('Slippage Calculations - Balancer', () => {
    test('should compute Balancer weighted pool slippage', () => {
      const balanceIn = 100;
      const balanceOut = 1000;
      const weightIn = 0.4;
      const weightOut = 0.6;
      const amountIn = 1;

      const slippage = ArbitrageEngine.computeBalancerSlippage(
        balanceIn,
        balanceOut,
        weightIn,
        weightOut,
        amountIn
      );

      expect(slippage).toBeGreaterThan(0);
    });
  });

  describe('Aggregator Routing', () => {
    test('should select best route from multiple options', () => {
      const slippages = [2.5, 1.8, 3.2, 2.1];

      const bestSlippage = ArbitrageEngine.computeAggregatorSlippage(slippages);

      expect(bestSlippage).toBe(Math.min(...slippages));
    });

    test('should handle many routes', () => {
      const slippages = [5.2, 3.8, 2.1, 4.5, 6.7, 1.9, 3.3];

      const bestSlippage = ArbitrageEngine.computeAggregatorSlippage(slippages);

      expect(bestSlippage).toBe(1.9);
    });
  });

  describe('Market Impact', () => {
    test('should calculate market impact for trade', () => {
      const reserveIn = 1000000;
      const reserveOut = 2000000;
      const flashloanAmount = 50000;

      const impact = ArbitrageEngine.calculateMarketImpact(
        reserveIn,
        reserveOut,
        flashloanAmount
      );

      expect(impact).toBeGreaterThan(0);
      expect(impact).toBeLessThan(100);
    });
  });

  describe('Multi-hop Slippage', () => {
    test('should calculate slippage for multi-hop path', () => {
      const reserves = [
        [1000000, 2000000], // Hop 1
        [2000000, 3000000], // Hop 2
        [3000000, 1500000]  // Hop 3
      ];
      const flashloanAmount = 10000;

      const totalSlippage = ArbitrageEngine.calculateMultihopSlippage(
        reserves,
        flashloanAmount
      );

      expect(totalSlippage).toBeGreaterThan(0);
    });
  });
});
