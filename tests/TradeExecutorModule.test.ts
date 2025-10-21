/**
 * Trade Executor Module Tests
 * Tests for trade execution, flashloan operations, and transaction handling
 */

import * as ArbitrageEngine from '../ultra-fast-arbitrage-engine/index';

describe('TradeExecutorModule', () => {
  describe('Flashloan Execution', () => {
    test('should calculate flashloan amount for profitable trade', () => {
      const reserveInBuy = 1000000;
      const reserveOutBuy = 2500000; // Better price difference
      const reserveInSell = 2500000;
      const reserveOutSell = 1200000;
      const flashloanFee = 0.0009; // Aave standard
      const gasCost = 100;

      const amount = ArbitrageEngine.calculateFlashloanAmount(
        reserveInBuy,
        reserveOutBuy,
        reserveInSell,
        reserveOutSell,
        flashloanFee,
        gasCost
      );

      expect(amount).toBeGreaterThanOrEqual(0);
    });

    test('should optimize flashloan size to maximize profit', () => {
      const buyReserveIn = 1000000;
      const buyReserveOut = 2000000;
      const sellReserveIn = 2000000;
      const sellReserveOut = 1500000;
      const gasCost = 50;
      const flashloanFee = 0.0009;

      const optimalAmount = ArbitrageEngine.optimizeTradeSizeQuadratic(
        buyReserveIn,
        buyReserveOut,
        sellReserveIn,
        sellReserveOut,
        gasCost,
        flashloanFee
      );

      // Verify this is better than arbitrary amounts
      const profit1k = ArbitrageEngine.estimateArbitrageProfit(
        buyReserveIn, buyReserveOut, sellReserveIn, sellReserveOut,
        1000, gasCost, flashloanFee
      );

      const profit10k = ArbitrageEngine.estimateArbitrageProfit(
        buyReserveIn, buyReserveOut, sellReserveIn, sellReserveOut,
        10000, gasCost, flashloanFee
      );

      const optimalProfit = ArbitrageEngine.estimateArbitrageProfit(
        buyReserveIn, buyReserveOut, sellReserveIn, sellReserveOut,
        optimalAmount, gasCost, flashloanFee
      );

      expect(optimalProfit).toBeGreaterThanOrEqual(profit1k);
      expect(optimalProfit).toBeGreaterThanOrEqual(profit10k);
    });

    test('should handle high flashloan fees', () => {
      const reserveInBuy = 1000000;
      const reserveOutBuy = 2000000;
      const reserveInSell = 2000000;
      const reserveOutSell = 1500000;
      const gasCost = 50;

      const normalFeeAmount = ArbitrageEngine.calculateFlashloanAmount(
        reserveInBuy, reserveOutBuy, reserveInSell, reserveOutSell,
        0.0009, gasCost
      );

      const highFeeAmount = ArbitrageEngine.calculateFlashloanAmount(
        reserveInBuy, reserveOutBuy, reserveInSell, reserveOutSell,
        0.005, gasCost // 0.5% fee
      );

      // Higher fees should result in lower or equal flashloan amounts
      expect(highFeeAmount).toBeLessThanOrEqual(normalFeeAmount);
    });
  });

  describe('Trade Execution Validation', () => {
    test('should validate trade meets minimum profit threshold', () => {
      const buyReserveIn = 1000000;
      const buyReserveOut = 2000000;
      const sellReserveIn = 2000000;
      const sellReserveOut = 1500000;
      const amountIn = 10000;
      const gasCost = 50;
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

      const minProfit = 100;
      expect(profit).toBeGreaterThan(minProfit);
    });

    test('should reject unprofitable trades', () => {
      const buyReserveIn = 1000000;
      const buyReserveOut = 2000000;
      const sellReserveIn = 1000000;
      const sellReserveOut = 2000000; // Same price
      const amountIn = 10000;
      const gasCost = 50000; // High gas cost to ensure unprofitable
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

    test('should account for slippage in execution', () => {
      const reserveIn = 1000000;
      const reserveOut = 2000000;
      const amountIn = 50000; // Large trade

      const slippage = ArbitrageEngine.computeSlippage(
        reserveIn,
        reserveOut,
        amountIn
      );

      expect(slippage).toBeGreaterThan(0);
      expect(slippage).toBeLessThan(100);
    });
  });

  describe('Multi-hop Trade Execution', () => {
    test('should execute two-hop arbitrage', () => {
      const reserves = [
        [1000000, 2000000], // Hop 1: Buy token
        [2000000, 1500000]  // Hop 2: Sell token
      ];
      const flashloanAmount = 10000;

      const totalSlippage = ArbitrageEngine.calculateMultihopSlippage(
        reserves,
        flashloanAmount
      );

      expect(totalSlippage).toBeGreaterThan(0);
    });

    test('should execute three-hop arbitrage', () => {
      const reserves = [
        [1000000, 2000000], // Hop 1
        [2000000, 3000000], // Hop 2
        [3000000, 1200000]  // Hop 3
      ];
      const flashloanAmount = 10000;

      const totalSlippage = ArbitrageEngine.calculateMultihopSlippage(
        reserves,
        flashloanAmount
      );

      expect(totalSlippage).toBeGreaterThan(0);
    });

    test('should prefer paths with lower cumulative slippage', () => {
      const path1 = [
        [1000000, 2000000],
        [2000000, 1500000]
      ];

      const path2 = [
        [500000, 1000000], // Lower liquidity
        [1000000, 700000]
      ];

      const amount = 10000;

      const slippage1 = ArbitrageEngine.calculateMultihopSlippage(path1, amount);
      const slippage2 = ArbitrageEngine.calculateMultihopSlippage(path2, amount);

      expect(slippage1).toBeLessThan(slippage2);
    });
  });

  describe('Gas Cost Management', () => {
    test('should factor gas costs into profitability', () => {
      const buyReserveIn = 1000000;
      const buyReserveOut = 2000000;
      const sellReserveIn = 2000000;
      const sellReserveOut = 1500000;
      const amountIn = 10000;
      const flashloanFee = 0.0009;

      const profitLowGas = ArbitrageEngine.estimateArbitrageProfit(
        buyReserveIn, buyReserveOut, sellReserveIn, sellReserveOut,
        amountIn, 50, flashloanFee
      );

      const profitHighGas = ArbitrageEngine.estimateArbitrageProfit(
        buyReserveIn, buyReserveOut, sellReserveIn, sellReserveOut,
        amountIn, 500, flashloanFee
      );

      expect(profitLowGas).toBeGreaterThan(profitHighGas);
    });

    test('should optimize for net profit after all costs', () => {
      const buyReserveIn = 1000000;
      const buyReserveOut = 2500000;
      const sellReserveIn = 2500000;
      const sellReserveOut = 1200000;
      const gasCost = 100;
      const flashloanFee = 0.0009;

      const optimalAmount = ArbitrageEngine.optimizeTradeSizeQuadratic(
        buyReserveIn,
        buyReserveOut,
        sellReserveIn,
        sellReserveOut,
        gasCost,
        flashloanFee
      );

      const netProfit = ArbitrageEngine.estimateArbitrageProfit(
        buyReserveIn,
        buyReserveOut,
        sellReserveIn,
        sellReserveOut,
        optimalAmount,
        gasCost,
        flashloanFee
      );

      expect(netProfit).toBeGreaterThan(0);
    });
  });

  describe('Market Impact Assessment', () => {
    test('should calculate impact for small trades', () => {
      const reserveIn = 10000000;
      const reserveOut = 20000000;
      const flashloanAmount = 10000; // 0.1% of reserve

      const impact = ArbitrageEngine.calculateMarketImpact(
        reserveIn,
        reserveOut,
        flashloanAmount
      );

      expect(impact).toBeLessThan(1); // Less than 1% impact
    });

    test('should calculate impact for large trades', () => {
      const reserveIn = 1000000;
      const reserveOut = 2000000;
      const flashloanAmount = 200000; // 20% of reserve

      const impact = ArbitrageEngine.calculateMarketImpact(
        reserveIn,
        reserveOut,
        flashloanAmount
      );

      expect(impact).toBeGreaterThan(5);
    });
  });

  describe('DEX-Specific Execution', () => {
    test('should handle Uniswap V2 style execution', () => {
      const reserveIn = 1000000;
      const reserveOut = 2000000;
      const amountIn = 10000;

      const slippage = ArbitrageEngine.computeSlippage(
        reserveIn,
        reserveOut,
        amountIn
      );

      const amountOut = ArbitrageEngine.calculateAmountOut(
        reserveIn,
        reserveOut,
        amountIn
      );

      expect(slippage).toBeGreaterThan(0);
      expect(amountOut).toBeGreaterThan(0);
    });

    test('should handle Curve stableswap execution', () => {
      const balanceIn = 5000000;
      const balanceOut = 5000000;
      const amountIn = 50000;
      const amplification = 2000;

      const slippage = ArbitrageEngine.computeCurveSlippage(
        balanceIn,
        balanceOut,
        amountIn,
        amplification
      );

      expect(slippage).toBeLessThan(1); // Stablecoins have low slippage
    });
  });
});
