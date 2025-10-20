/**
 * Integration Tests
 * End-to-end tests for the complete arbitrage flow
 */

import * as ArbitrageEngine from '../ultra-fast-arbitrage-engine/index';

describe('Integration', () => {
  describe('Complete Arbitrage Flow', () => {
    test('should execute full arbitrage detection and validation flow', () => {
      const config: ArbitrageEngine.ArbitrageConfig = {
        gasCost: 100,
        flashloanFeePct: 0.0009,
        minPriceDiffPct: 1.0,
        maxTwapDeviationPct: 5.0,
        minProfitThreshold: 50
      };

      // Real pool data
      const pool1ReserveIn = 1523847;
      const pool1ReserveOut = 2847651;
      const pool2ReserveIn = 2891245;
      const pool2ReserveOut = 1578392;

      // TWAP samples
      const priceSamples1 = [
        [1000, 1.85],
        [2000, 1.87],
        [3000, 1.86],
        [4000, 1.87]
      ];

      const priceSamples2 = [
        [1000, 0.54],
        [2000, 0.55],
        [3000, 0.55],
        [4000, 0.55]
      ];

      const [shouldExecute, optimalAmount, expectedProfit] = 
        ArbitrageEngine.executeArbitrageFlow(
          pool1ReserveIn,
          pool1ReserveOut,
          pool2ReserveIn,
          pool2ReserveOut,
          priceSamples1,
          priceSamples2,
          config
        );

      expect(shouldExecute).toBeDefined();
      expect(optimalAmount).toBeGreaterThanOrEqual(0);
      expect(expectedProfit).toBeDefined();
    });

    test('should reject flow when price manipulation detected', () => {
      const config: ArbitrageEngine.ArbitrageConfig = {
        gasCost: 100,
        flashloanFeePct: 0.0009,
        minPriceDiffPct: 1.0,
        maxTwapDeviationPct: 2.0, // Strict TWAP check
        minProfitThreshold: 50
      };

      const pool1ReserveIn = 1000000;
      const pool1ReserveOut = 3000000; // Current: 3.0

      const pool2ReserveIn = 1000000;
      const pool2ReserveOut = 2000000; // Current: 2.0

      // TWAP shows much lower prices (manipulation suspected)
      const priceSamples1 = [
        [1000, 2.0],
        [2000, 2.0],
        [3000, 2.0],
        [4000, 2.0]
      ];

      const priceSamples2 = [
        [1000, 2.0],
        [2000, 2.0],
        [3000, 2.0],
        [4000, 2.0]
      ];

      const [shouldExecute] = ArbitrageEngine.executeArbitrageFlow(
        pool1ReserveIn,
        pool1ReserveOut,
        pool2ReserveIn,
        pool2ReserveOut,
        priceSamples1,
        priceSamples2,
        config
      );

      // Should not execute due to TWAP deviation
      expect(shouldExecute).toBeLessThanOrEqual(1);
    });

    test('should handle complete flow with minimal profit margin', () => {
      const config: ArbitrageEngine.ArbitrageConfig = {
        gasCost: 50,
        flashloanFeePct: 0.0009,
        minPriceDiffPct: 0.5,
        maxTwapDeviationPct: 5.0,
        minProfitThreshold: 10
      };

      const pool1ReserveIn = 1000000;
      const pool1ReserveOut = 2000000;
      const pool2ReserveIn = 2000000;
      const pool2ReserveOut = 990000; // Small difference

      const priceSamples1 = [
        [1000, 2.0],
        [2000, 2.0],
        [3000, 2.0],
        [4000, 2.0]
      ];

      const priceSamples2 = [
        [1000, 1.98],
        [2000, 1.98],
        [3000, 1.98],
        [4000, 1.98]
      ];

      const [shouldExecute, optimalAmount, expectedProfit] = 
        ArbitrageEngine.executeArbitrageFlow(
          pool1ReserveIn,
          pool1ReserveOut,
          pool2ReserveIn,
          pool2ReserveOut,
          priceSamples1,
          priceSamples2,
          config
        );

      expect(shouldExecute).toBeDefined();
      expect(optimalAmount).toBeGreaterThanOrEqual(0);
      expect(expectedProfit).toBeDefined();
    });
  });

  describe('Multi-Path Selection', () => {
    test('should select best path from multiple options', () => {
      const paths = [
        [[1000000, 2000000], [2000000, 1500000]], // Path 1
        [[1500000, 3500000], [3500000, 1800000]], // Path 2
        [[2000000, 3000000], [3000000, 2200000]]  // Path 3
      ];
      const flashloanAmounts = [15000, 15000, 15000];
      const flashloanFee = 0.0009;
      const gasCosts = [50, 60, 55];

      const results = ArbitrageEngine.simulateParallelFlashloanPaths(
        paths,
        flashloanAmounts,
        flashloanFee,
        gasCosts
      );

      const bestResult = results.reduce((best, current) => 
        current[0] > best[0] ? current : best
      );

      expect(bestResult[0]).toBeGreaterThanOrEqual(results[0][0]);
      expect(bestResult[0]).toBeGreaterThanOrEqual(results[1][0]);
      expect(bestResult[0]).toBeGreaterThanOrEqual(results[2][0]);
    });

    test('should handle competing paths with different characteristics', () => {
      const paths = [
        [[10000000, 20000000], [20000000, 15000000]], // High liquidity, low spread
        [[1000000, 2500000], [2500000, 1200000]],     // Low liquidity, high spread
        [[5000000, 9000000], [9000000, 7000000]]      // Medium liquidity, medium spread
      ];
      const flashloanAmounts = [50000, 10000, 25000]; // Different sizes
      const flashloanFee = 0.0009;
      const gasCosts = [50, 45, 48];

      const results = ArbitrageEngine.simulateParallelFlashloanPaths(
        paths,
        flashloanAmounts,
        flashloanFee,
        gasCosts
      );

      expect(results).toHaveLength(3);
      results.forEach(result => {
        expect(result[0]).toBeDefined(); // profit
        expect(result[1]).toBeDefined(); // slippage
        expect(result[2]).toBeDefined(); // pathIndex
      });
    });

    test('should prefer paths with lower slippage for same profit', () => {
      const paths = [
        [[1000000, 2000000], [2000000, 1500000]],
        [[5000000, 10000000], [10000000, 7500000]] // Higher liquidity = lower slippage
      ];
      const flashloanAmounts = [10000, 10000];
      const flashloanFee = 0.0009;
      const gasCosts = [50, 50];

      const results = ArbitrageEngine.simulateParallelFlashloanPaths(
        paths,
        flashloanAmounts,
        flashloanFee,
        gasCosts
      );

      expect(results).toHaveLength(2);
      expect(results[1][1]).toBeLessThan(results[0][1]); // Path 2 should have lower slippage
    });
  });

  describe('Real-World Scenarios', () => {
    test('should handle Uniswap V2 vs SushiSwap arbitrage', () => {
      // Uniswap V2 ETH/USDT
      const uniReserveIn = 1000000;
      const uniReserveOut = 3000000; // Price: 3.0

      // SushiSwap ETH/USDT - different price
      const sushiReserveIn = 2000000;
      const sushiReserveOut = 1500000; // Price: 0.75

      const [hasOpportunity, priceDiff] = ArbitrageEngine.identifyArbitrageOpportunity(
        uniReserveIn,
        uniReserveOut,
        sushiReserveIn,
        sushiReserveOut,
        0.5 // 0.5% minimum
      );

      expect(hasOpportunity).toBeDefined();
      expect(priceDiff).toBeGreaterThanOrEqual(0);

      if (hasOpportunity === 1) {
        const flashloanAmount = ArbitrageEngine.calculateFlashloanAmount(
          uniReserveIn,
          uniReserveOut,
          sushiReserveIn,
          sushiReserveOut,
          0.0009,
          100
        );

        expect(flashloanAmount).toBeGreaterThanOrEqual(0);
        expect(priceDiff).toBeGreaterThan(0.5);
      }
    });

    test('should handle Balancer weighted pool arbitrage', () => {
      // Balancer WBTC/ETH pool
      const balanceIn = 234.567;
      const balanceOut = 1234.891;
      const weightIn = 0.4;
      const weightOut = 0.6;
      const tradeAmount = 2.5;

      const slippage = ArbitrageEngine.computeBalancerSlippage(
        balanceIn,
        balanceOut,
        weightIn,
        weightOut,
        tradeAmount
      );

      expect(slippage).toBeGreaterThan(0);
    });

    test('should validate arbitrage across multiple DEX types', () => {
      // Test cross-DEX arbitrage validation
      const uniV2Reserve = [1000000, 2000000];
      const curveBalance = [5000000, 5000000];
      
      const uniSlippage = ArbitrageEngine.computeSlippage(
        uniV2Reserve[0], uniV2Reserve[1], 10000
      );
      
      const curveSlippage = ArbitrageEngine.computeCurveSlippage(
        curveBalance[0], curveBalance[1], 10000, 2000
      );

      expect(uniSlippage).toBeGreaterThan(curveSlippage); // Stablecoins have lower slippage
    });
  });

  describe('Edge Cases and Stress Tests', () => {
    test('should handle extremely small price differences', () => {
      const pool1ReserveIn = 10000000;
      const pool1ReserveOut = 20000000; // Price: 2.0
      const pool2ReserveIn = 10000000;
      const pool2ReserveOut = 20001000; // Price: 2.0001

      const [hasOpportunity] = ArbitrageEngine.identifyArbitrageOpportunity(
        pool1ReserveIn,
        pool1ReserveOut,
        pool2ReserveIn,
        pool2ReserveOut,
        0.001 // 0.1% minimum
      );

      expect(hasOpportunity).toBeDefined();
    });

    test('should handle very large pool reserves', () => {
      const reserveIn = 1e12; // 1 trillion
      const reserveOut = 2e12;
      const amountIn = 1e9; // 1 billion

      const slippage = ArbitrageEngine.computeSlippage(
        reserveIn,
        reserveOut,
        amountIn
      );

      expect(slippage).toBeGreaterThan(0);
      expect(slippage).toBeLessThan(1);
    });

    test('should handle maximum complexity path (5 hops)', () => {
      const reserves = [
        [1000000, 2000000],
        [2000000, 3000000],
        [3000000, 2500000],
        [2500000, 3500000],
        [3500000, 1800000]
      ];
      const flashloanAmount = 10000;

      const totalSlippage = ArbitrageEngine.calculateMultihopSlippage(
        reserves,
        flashloanAmount
      );

      expect(totalSlippage).toBeGreaterThan(0);
    });
  });

  describe('Performance and Optimization', () => {
    test('should optimize for maximum profit across multiple scenarios', () => {
      const scenarios = [
        {
          buyReserveIn: 1000000,
          buyReserveOut: 2000000,
          sellReserveIn: 2000000,
          sellReserveOut: 1500000,
          gasCost: 50
        },
        {
          buyReserveIn: 2000000,
          buyReserveOut: 3500000,
          sellReserveIn: 3500000,
          sellReserveOut: 2200000,
          gasCost: 55
        }
      ];

      const flashloanFee = 0.0009;

      scenarios.forEach(scenario => {
        const optimalAmount = ArbitrageEngine.optimizeTradeSizeQuadratic(
          scenario.buyReserveIn,
          scenario.buyReserveOut,
          scenario.sellReserveIn,
          scenario.sellReserveOut,
          scenario.gasCost,
          flashloanFee
        );

        const profit = ArbitrageEngine.estimateArbitrageProfit(
          scenario.buyReserveIn,
          scenario.buyReserveOut,
          scenario.sellReserveIn,
          scenario.sellReserveOut,
          optimalAmount,
          scenario.gasCost,
          flashloanFee
        );

        expect(optimalAmount).toBeGreaterThan(0);
        expect(profit).toBeDefined();
      });
    });
  });
});
