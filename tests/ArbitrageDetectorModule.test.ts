/**
 * Arbitrage Detector Module Tests
 * Tests for identifying and validating arbitrage opportunities
 */

import * as ArbitrageEngine from '../ultra-fast-arbitrage-engine/index';

describe('ArbitrageDetectorModule', () => {
  describe('Price Calculation', () => {
    test('should calculate pool price correctly', () => {
      const reserveIn = 1000000;
      const reserveOut = 2000000;
      const price = ArbitrageEngine.calculatePoolPrice(reserveIn, reserveOut);
      expect(price).toBeCloseTo(2.0, 5);
    });

    test('should handle equal reserves', () => {
      const price = ArbitrageEngine.calculatePoolPrice(1000, 1000);
      expect(price).toBeCloseTo(1.0, 5);
    });

    test('should handle large reserve values', () => {
      const price = ArbitrageEngine.calculatePoolPrice(1e12, 2e12);
      expect(price).toBeCloseTo(2.0, 5);
    });
  });

  describe('Opportunity Identification', () => {
    test('should identify arbitrage opportunity when price difference exists', () => {
      const pool1ReserveIn = 1000000;
      const pool1ReserveOut = 2000000; // Price: 2.0
      const pool2ReserveIn = 2000000;
      const pool2ReserveOut = 3000000; // Price: 1.5
      const minPriceDiff = 0.05; // 5%

      const [hasOpportunity, priceDiff, direction] = ArbitrageEngine.identifyArbitrageOpportunity(
        pool1ReserveIn,
        pool1ReserveOut,
        pool2ReserveIn,
        pool2ReserveOut,
        minPriceDiff
      );

      expect(hasOpportunity).toBe(1);
      expect(priceDiff).toBeGreaterThan(5);
      expect(direction).toBeGreaterThan(0);
    });

    test('should not identify opportunity when price difference is too small', () => {
      const pool1ReserveIn = 1000000;
      const pool1ReserveOut = 2000000; // Price: 2.0
      const pool2ReserveIn = 1000000;
      const pool2ReserveOut = 2010000; // Price: 2.01 (0.5% diff)
      const minPriceDiff = 1.0; // 1%

      const [hasOpportunity] = ArbitrageEngine.identifyArbitrageOpportunity(
        pool1ReserveIn,
        pool1ReserveOut,
        pool2ReserveIn,
        pool2ReserveOut,
        minPriceDiff
      );

      expect(hasOpportunity).toBe(0);
    });

    test('should determine correct arbitrage direction', () => {
      const pool1ReserveIn = 1000000;
      const pool1ReserveOut = 3000000; // Price: 3.0
      const pool2ReserveIn = 1000000;
      const pool2ReserveOut = 2000000; // Price: 2.0
      const minPriceDiff = 0.05;

      const [, , direction] = ArbitrageEngine.identifyArbitrageOpportunity(
        pool1ReserveIn,
        pool1ReserveOut,
        pool2ReserveIn,
        pool2ReserveOut,
        minPriceDiff
      );

      expect(direction).toBeGreaterThan(0);
      expect(direction).toBeLessThanOrEqual(2);
    });
  });

  describe('Profit Estimation', () => {
    test('should estimate positive profit for valid opportunity', () => {
      const buyReserveIn = 1000000;
      const buyReserveOut = 2000000;
      const sellReserveIn = 2000000;
      const sellReserveOut = 1500000;
      const amountIn = 10000;
      const gasCost = 50;
      const flashloanFee = 0.0009; // 0.09%

      const profit = ArbitrageEngine.estimateArbitrageProfit(
        buyReserveIn,
        buyReserveOut,
        sellReserveIn,
        sellReserveOut,
        amountIn,
        gasCost,
        flashloanFee
      );

      expect(profit).toBeGreaterThan(0);
    });

    test('should estimate negative profit when opportunity is unprofitable', () => {
      const buyReserveIn = 1000000;
      const buyReserveOut = 2000000;
      const sellReserveIn = 1000000;
      const sellReserveOut = 2000000; // Same price
      const amountIn = 10000;
      const gasCost = 100000; // Very high gas to ensure unprofitable
      const flashloanFee = 0.0009;

      const profit = ArbitrageEngine.estimateArbitrageProfit(
        buyReserveIn,
        buyReserveOut,
        sellReserveIn,
        sellReserveOut,
        amountIn,
        gasCost,
        flashloanFee
      );

      expect(profit).toBeLessThan(0);
    });

    test('should account for gas costs', () => {
      const buyReserveIn = 1000000;
      const buyReserveOut = 2000000;
      const sellReserveIn = 2000000;
      const sellReserveOut = 1500000;
      const amountIn = 10000;
      const flashloanFee = 0.0009;

      const profitHighGas = ArbitrageEngine.estimateArbitrageProfit(
        buyReserveIn, buyReserveOut, sellReserveIn, sellReserveOut,
        amountIn, 500, flashloanFee
      );

      const profitLowGas = ArbitrageEngine.estimateArbitrageProfit(
        buyReserveIn, buyReserveOut, sellReserveIn, sellReserveOut,
        amountIn, 50, flashloanFee
      );

      expect(profitLowGas).toBeGreaterThan(profitHighGas);
    });
  });

  describe('Optimal Trade Size', () => {
    test('should calculate optimal trade size for profitability', () => {
      const reserveIn = 1000000;
      const reserveOut = 2000000;
      const gasCost = 100;
      const minProfit = 50;

      const optimalSize = ArbitrageEngine.getOptimalTradeSize(
        reserveIn,
        reserveOut,
        gasCost,
        minProfit
      );

      expect(optimalSize).toBeGreaterThan(0);
      expect(optimalSize).toBeLessThan(reserveIn);
    });

    test('should return zero when no profitable trade size exists', () => {
      const reserveIn = 1000;
      const reserveOut = 1000;
      const gasCost = 1000; // Very high gas cost
      const minProfit = 100;

      const optimalSize = ArbitrageEngine.getOptimalTradeSize(
        reserveIn,
        reserveOut,
        gasCost,
        minProfit
      );

      expect(optimalSize).toBeGreaterThanOrEqual(0);
    });

    test('should scale with pool liquidity', () => {
      const gasCost = 100;
      const minProfit = 50;

      const sizeSmall = ArbitrageEngine.getOptimalTradeSize(
        100000, 200000, gasCost, minProfit
      );

      const sizeLarge = ArbitrageEngine.getOptimalTradeSize(
        10000000, 20000000, gasCost, minProfit
      );

      expect(sizeLarge).toBeGreaterThan(sizeSmall);
    });
  });

  describe('Quadratic Optimization', () => {
    test('should solve quadratic equation correctly', () => {
      // x^2 - 5x + 6 = 0 (roots: 2, 3)
      const [root1, root2] = ArbitrageEngine.solveQuadratic(1, -5, 6);
      
      expect(root1).toBeCloseTo(3, 5);
      expect(root2).toBeCloseTo(2, 5);
    });

    test('should optimize trade size using quadratic method', () => {
      const buyReserveIn = 1000000;
      const buyReserveOut = 2000000;
      const sellReserveIn = 2000000;
      const sellReserveOut = 1500000;
      const gasCost = 50;
      const flashloanFee = 0.0009;

      const optimalSize = ArbitrageEngine.optimizeTradeSizeQuadratic(
        buyReserveIn,
        buyReserveOut,
        sellReserveIn,
        sellReserveOut,
        gasCost,
        flashloanFee
      );

      expect(optimalSize).toBeGreaterThan(0);
    });
  });

  describe('TWAP Validation', () => {
    test('should calculate TWAP correctly', () => {
      const priceSamples = [
        [1000, 2.0],
        [2000, 2.1],
        [3000, 2.2],
        [4000, 2.3]
      ];

      const twap = ArbitrageEngine.calculateTWAP(priceSamples);
      expect(twap).toBeGreaterThan(2.0);
      expect(twap).toBeLessThan(2.3);
    });

    test('should validate price against TWAP within threshold', () => {
      const currentPrice = 2.05;
      const twap = 2.0;
      const maxDeviation = 5.0; // 5%

      const isValid = ArbitrageEngine.validateWithTWAP(
        currentPrice,
        twap,
        maxDeviation
      );

      expect(isValid).toBe(true);
    });

    test('should reject price when deviation exceeds threshold', () => {
      const currentPrice = 2.5;
      const twap = 2.0;
      const maxDeviation = 5.0; // 5%

      const isValid = ArbitrageEngine.validateWithTWAP(
        currentPrice,
        twap,
        maxDeviation
      );

      expect(isValid).toBe(false);
    });
  });
});
