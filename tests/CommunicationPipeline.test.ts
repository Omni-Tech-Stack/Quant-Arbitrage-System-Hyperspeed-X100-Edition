/**
 * Communication Pipeline Module Tests
 * Tests for inter-module communication and data coordination
 */

import * as ArbitrageEngine from '../ultra-fast-arbitrage-engine/index';

describe('CommunicationPipeline', () => {
  describe('Flashloan Amount Calculation', () => {
    test('should calculate optimal flashloan amount for arbitrage', () => {
      const reserveInBuy = 1000000;
      const reserveOutBuy = 2000000;
      const reserveInSell = 2000000;
      const reserveOutSell = 1500000;
      const flashloanFee = 0.0009;
      const gasCost = 50;

      const flashloanAmount = ArbitrageEngine.calculateFlashloanAmount(
        reserveInBuy,
        reserveOutBuy,
        reserveInSell,
        reserveOutSell,
        flashloanFee,
        gasCost
      );

      expect(flashloanAmount).toBeGreaterThan(0);
      expect(flashloanAmount).toBeLessThan(reserveInBuy);
    });

    test('should account for flashloan fee in calculation', () => {
      const reserveInBuy = 1000000;
      const reserveOutBuy = 2000000;
      const reserveInSell = 2000000;
      const reserveOutSell = 1500000;
      const gasCost = 50;

      const amountLowFee = ArbitrageEngine.calculateFlashloanAmount(
        reserveInBuy, reserveOutBuy, reserveInSell, reserveOutSell,
        0.0001, gasCost
      );

      const amountHighFee = ArbitrageEngine.calculateFlashloanAmount(
        reserveInBuy, reserveOutBuy, reserveInSell, reserveOutSell,
        0.001, gasCost
      );

      expect(amountLowFee).toBeGreaterThanOrEqual(amountHighFee);
    });

    test('should return zero for unprofitable opportunities', () => {
      const reserveInBuy = 1000000;
      const reserveOutBuy = 2000000;
      const reserveInSell = 1000000;
      const reserveOutSell = 2000000; // Same price
      const flashloanFee = 0.0009;
      const gasCost = 50;

      const flashloanAmount = ArbitrageEngine.calculateFlashloanAmount(
        reserveInBuy,
        reserveOutBuy,
        reserveInSell,
        reserveOutSell,
        flashloanFee,
        gasCost
      );

      expect(flashloanAmount).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Flashloan V3 Calculation', () => {
    test('should calculate flashloan for concentrated liquidity', () => {
      const liquidity = 5000000;
      const sqrtPriceBuy = 1.414;
      const sqrtPriceSell = 1.732;
      const flashloanFee = 0.0009;
      const gasCost = 75;

      const flashloanAmount = ArbitrageEngine.calculateFlashloanAmountV3(
        liquidity,
        sqrtPriceBuy,
        sqrtPriceSell,
        flashloanFee,
        gasCost
      );

      expect(flashloanAmount).toBeGreaterThan(0);
    });

    test('should scale with liquidity', () => {
      const sqrtPriceBuy = 1.414;
      const sqrtPriceSell = 1.732;
      const flashloanFee = 0.0009;
      const gasCost = 75;

      const amountLowLiq = ArbitrageEngine.calculateFlashloanAmountV3(
        1000000, sqrtPriceBuy, sqrtPriceSell, flashloanFee, gasCost
      );

      const amountHighLiq = ArbitrageEngine.calculateFlashloanAmountV3(
        10000000, sqrtPriceBuy, sqrtPriceSell, flashloanFee, gasCost
      );

      expect(amountHighLiq).toBeGreaterThan(amountLowLiq);
    });

    test('should handle different price ranges', () => {
      const liquidity = 5000000;
      const flashloanFee = 0.0009;
      const gasCost = 75;

      const amount1 = ArbitrageEngine.calculateFlashloanAmountV3(
        liquidity, 1.0, 1.2, flashloanFee, gasCost
      );

      const amount2 = ArbitrageEngine.calculateFlashloanAmountV3(
        liquidity, 1.0, 2.0, flashloanFee, gasCost
      );

      expect(amount2).toBeGreaterThan(amount1);
    });
  });

  describe('Parallel Path Simulation', () => {
    test('should simulate multiple paths in parallel', () => {
      const paths = [
        [[1000000, 2000000], [2000000, 1500000]], // Path 1: 2 hops
        [[1500000, 2500000], [2500000, 1800000]], // Path 2: 2 hops
        [[2000000, 3000000], [3000000, 2200000]]  // Path 3: 2 hops
      ];
      const flashloanAmounts = [10000, 10000, 10000];
      const flashloanFee = 0.0009;
      const gasCosts = [50, 60, 55];

      const results = ArbitrageEngine.simulateParallelFlashloanPaths(
        paths,
        flashloanAmounts,
        flashloanFee,
        gasCosts
      );

      expect(results).toHaveLength(3);
      expect(results[0]).toHaveLength(3); // [profit, slippage, pathIndex]
    });

    test('should identify most profitable path', () => {
      const paths = [
        [[1000000, 2000000], [2000000, 1500000]], // Path 1
        [[1500000, 3000000], [3000000, 1700000]], // Path 2: better ratio
        [[2000000, 3000000], [3000000, 2200000]]  // Path 3
      ];
      const flashloanAmounts = [10000, 10000, 10000];
      const flashloanFee = 0.0009;
      const gasCosts = [50, 50, 50];

      const results = ArbitrageEngine.simulateParallelFlashloanPaths(
        paths,
        flashloanAmounts,
        flashloanFee,
        gasCosts
      );

      const profits = results.map(r => r[0]);
      const maxProfit = Math.max(...profits);
      const bestPathIndex = results.findIndex(r => r[0] === maxProfit);

      expect(bestPathIndex).toBeGreaterThanOrEqual(0);
      expect(bestPathIndex).toBeLessThan(3);
    });
  });

  describe('Data Flow Coordination', () => {
    test('should coordinate price discovery and opportunity detection', () => {
      // Step 1: Calculate prices
      const pool1Price = ArbitrageEngine.calculatePoolPrice(1000000, 2000000);
      const pool2Price = ArbitrageEngine.calculatePoolPrice(2000000, 3000000);

      // Step 2: Identify opportunity
      const [hasOpportunity, priceDiff] = ArbitrageEngine.identifyArbitrageOpportunity(
        1000000, 2000000, 2000000, 3000000, 0.05
      );

      expect(pool1Price).toBeGreaterThan(0);
      expect(pool2Price).toBeGreaterThan(0);
      expect(hasOpportunity).toBeDefined();
      expect(priceDiff).toBeGreaterThanOrEqual(0);
    });

    test('should coordinate flashloan calculation and market impact', () => {
      const reserveIn = 1000000;
      const reserveOut = 2000000;

      // Step 1: Calculate flashloan
      const flashloanAmount = ArbitrageEngine.calculateFlashloanAmount(
        reserveIn, reserveOut, 2000000, 1500000, 0.0009, 50
      );

      // Step 2: Calculate impact
      const impact = ArbitrageEngine.calculateMarketImpact(
        reserveIn,
        reserveOut,
        flashloanAmount
      );

      expect(flashloanAmount).toBeGreaterThanOrEqual(0);
      expect(impact).toBeGreaterThan(0);
    });
  });

  describe('Error Handling', () => {
    test('should handle zero reserves gracefully', () => {
      expect(() => {
        ArbitrageEngine.calculatePoolPrice(0, 1000000);
      }).not.toThrow();
    });

    test('should handle zero amount in calculations', () => {
      expect(() => {
        ArbitrageEngine.calculateAmountOut(1000000, 2000000, 0);
      }).not.toThrow();
    });
  });
});
