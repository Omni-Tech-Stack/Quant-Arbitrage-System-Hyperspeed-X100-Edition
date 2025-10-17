# Flashloan & Market Impact Calculation Features

## Overview

This document describes the flashloan and market impact prediction features added to the Ultra-Fast Arbitrage Engine. These features enable the system to:

1. **Calculate optimal flashloan amounts** for arbitrage opportunities
2. **Predict market impact** (price slippage) caused by large trades
3. **Simulate multiple execution paths simultaneously** to find the best opportunity
4. **Account for flashloan fees** in final profit calculations

## New Functions

### 1. Calculate Flashloan Amount

**Purpose**: Determines the optimal flashloan size for a given arbitrage opportunity.

**TypeScript Interface**:
```typescript
calculateFlashloanAmount(
  reserveInBuy: number,      // Reserve of input token in buy pool
  reserveOutBuy: number,     // Reserve of output token in buy pool
  reserveInSell: number,     // Reserve of input token in sell pool
  reserveOutSell: number,    // Reserve of output token in sell pool
  flashloanFee: number,      // Flashloan fee as decimal (e.g., 0.0009 for 0.09%)
  gasCost: number           // Estimated gas cost in token units
): number
```

**Example**:
```typescript
const flashloanAmount = calculateFlashloanAmount(
  1000000,  // Buy pool: 1M input token
  2000000,  // Buy pool: 2M output token
  1800000,  // Sell pool: 1.8M input token (price difference!)
  1000000,  // Sell pool: 1M output token
  0.0009,   // Aave flashloan fee (0.09%)
  100       // Gas cost
);
// Returns: optimal flashloan amount that maximizes profit
```

**How it works**:
- Uses binary search to find the optimal flashloan amount
- Simulates the entire arbitrage path (buy → sell)
- Accounts for DEX fees (0.3%) and flashloan fees
- Returns 0 if no profitable amount exists

### 2. Calculate Market Impact

**Purpose**: Predicts the percentage price impact of a trade on a pool.

**TypeScript Interface**:
```typescript
calculateMarketImpact(
  reserveIn: number,        // Reserve of input token
  reserveOut: number,       // Reserve of output token
  flashloanAmount: number   // Trade size (flashloan amount)
): number
```

**Example**:
```typescript
const impact = calculateMarketImpact(
  1000000,  // 1M reserve in
  2000000,  // 2M reserve out
  50000     // 50K trade size
);
// Returns: ~4.8% market impact
```

**How it works**:
- Calculates price before and after the trade
- Returns percentage change in price
- Higher trade sizes relative to pool reserves = higher impact

### 3. Calculate Multi-hop Slippage

**Purpose**: Calculates total slippage across a multi-hop arbitrage path.

**TypeScript Interface**:
```typescript
calculateMultihopSlippage(
  reserves: number[][],     // Array of [reserveIn, reserveOut] pairs
  flashloanAmount: number   // Initial flashloan amount
): number
```

**Example**:
```typescript
const path = [
  [1000000, 2000000],  // First hop: Uniswap V2
  [2000000, 2000000],  // Second hop: Curve (balanced)
  [2000000, 1000000]   // Third hop: Balancer
];

const totalSlippage = calculateMultihopSlippage(path, 25000);
// Returns: ~7.98% total slippage across all hops
```

**How it works**:
- Simulates execution through each hop sequentially
- Accumulates slippage at each step
- Accounts for amount reduction at each hop

### 4. Simulate Parallel Flashloan Paths

**Purpose**: Simulates multiple arbitrage paths simultaneously to find the best opportunity.

**TypeScript Interface**:
```typescript
simulateParallelFlashloanPaths(
  paths: number[][][],       // Array of paths (each path is array of reserve pairs)
  flashloanAmounts: number[], // Flashloan amount for each path
  flashloanFee: number,      // Flashloan fee percentage
  gasCosts: number[]         // Gas cost for each path
): number[][]
```

**Example**:
```typescript
const paths = [
  [[1000000, 1500000], [1550000, 1000000]], // Path 1
  [[1000000, 2000000], [2100000, 1000000]], // Path 2
  [[1000000, 3000000], [3200000, 1000000]]  // Path 3
];

const results = simulateParallelFlashloanPaths(
  paths,
  [30000, 30000, 30000],  // Same flashloan amount for all
  0.0009,                 // Aave fee
  [100, 100, 100]         // Same gas cost for all
);

// Returns: [
//   [profit1, slippage1, 0],
//   [profit2, slippage2, 1],
//   [profit3, slippage3, 2]
// ]

// Find best path
const bestPath = results.reduce((best, curr) => 
  curr[0] > best[0] ? curr : best
);
```

**How it works**:
- Calculates profit and slippage for each path in parallel
- Returns array of [profit, slippage, pathIndex] for each path
- Enables quick comparison to find optimal execution route

### 5. Calculate Flashloan Amount V3

**Purpose**: Optimized flashloan calculation for Uniswap V3 concentrated liquidity pools.

**TypeScript Interface**:
```typescript
calculateFlashloanAmountV3(
  liquidity: number,         // Available liquidity
  sqrtPriceBuy: number,      // Square root price in buy pool
  sqrtPriceSell: number,     // Square root price in sell pool
  flashloanFee: number,      // Flashloan fee
  gasCost: number           // Gas cost
): number
```

**Example**:
```typescript
const flashloanAmount = calculateFlashloanAmountV3(
  5000000,  // 5M liquidity
  1.5,      // sqrt price buy
  1.6,      // sqrt price sell (arbitrage opportunity)
  0.0009,   // Aave fee
  100       // Gas cost
);
```

## Integration with Backend API

The backend server now exposes these calculations via REST API:

### POST /api/calculate-flashloan
Calculate optimal flashloan amount for an arbitrage opportunity.

**Request Body**:
```json
{
  "reserveInBuy": 1000000,
  "reserveOutBuy": 2000000,
  "reserveInSell": 1800000,
  "reserveOutSell": 1000000,
  "flashloanFee": 0.0009,
  "gasCost": 100
}
```

**Response**:
```json
{
  "flashloanAmount": 45678.90,
  "flashloanFee": 0.0009,
  "gasCost": 100,
  "timestamp": "2025-10-17T03:00:00.000Z"
}
```

### POST /api/calculate-impact
Calculate market impact for a trade.

**Request Body**:
```json
{
  "reserveIn": 1000000,
  "reserveOut": 2000000,
  "tradeAmount": 50000
}
```

**Response**:
```json
{
  "marketImpact": 4.8116,
  "reserveIn": 1000000,
  "reserveOut": 2000000,
  "tradeAmount": 50000,
  "timestamp": "2025-10-17T03:00:00.000Z"
}
```

### POST /api/simulate-paths
Simulate multiple flashloan paths in parallel.

**Request Body**:
```json
{
  "paths": [
    [[1000000, 2000000], [2100000, 1000000]],
    [[1000000, 3000000], [3200000, 1000000]]
  ],
  "flashloanAmounts": [30000, 30000],
  "flashloanFee": 0.0009,
  "gasCosts": [100, 100]
}
```

**Response**:
```json
{
  "results": [
    [1234.56, 3.45, 0],
    [2345.67, 5.12, 1]
  ],
  "bestPathIndex": 1,
  "timestamp": "2025-10-17T03:00:00.000Z"
}
```

## Frontend Dashboard Updates

The dashboard now displays flashloan-related information:

### Opportunities Table
- **Flashloan**: Shows the optimal flashloan amount for each opportunity
- **Market Impact**: Displays predicted market impact percentage

### Trades Table
- **Flashloan**: Shows the flashloan amount used in executed trades
- **Exec Time**: Shows execution time for transparency

## Usage Examples

### Example 1: Basic Flashloan Arbitrage

```typescript
import {
  calculateFlashloanAmount,
  calculateMarketImpact
} from './dist/index.js';

// Define pools
const uniswapPool = { reserveIn: 1000000, reserveOut: 2000000 };
const sushiswapPool = { reserveIn: 1800000, reserveOut: 1000000 };

// Calculate optimal flashloan
const flashloanAmount = calculateFlashloanAmount(
  uniswapPool.reserveIn,
  uniswapPool.reserveOut,
  sushiswapPool.reserveIn,
  sushiswapPool.reserveOut,
  0.0009,  // Aave fee
  100      // Gas cost
);

if (flashloanAmount > 0) {
  // Calculate market impacts
  const buyImpact = calculateMarketImpact(
    uniswapPool.reserveIn,
    uniswapPool.reserveOut,
    flashloanAmount
  );
  
  const sellImpact = calculateMarketImpact(
    sushiswapPool.reserveIn,
    sushiswapPool.reserveOut,
    flashloanAmount * 2  // Approximate output after first swap
  );
  
  console.log(`Optimal flashloan: ${flashloanAmount}`);
  console.log(`Buy impact: ${buyImpact.toFixed(4)}%`);
  console.log(`Sell impact: ${sellImpact.toFixed(4)}%`);
}
```

### Example 2: Multi-DEX Route Optimization

```typescript
import {
  calculateMultihopSlippage,
  simulateParallelFlashloanPaths
} from './dist/index.js';

// Define multiple routes
const routes = [
  // Route 1: Uniswap -> SushiSwap
  [[1000000, 2000000], [2100000, 1000000]],
  
  // Route 2: Uniswap -> Curve -> Balancer
  [[1000000, 2000000], [2000000, 2000000], [2000000, 1000000]],
  
  // Route 3: Direct large pool
  [[5000000, 10000000], [10500000, 5000000]]
];

// Simulate all routes
const results = simulateParallelFlashloanPaths(
  routes,
  [50000, 50000, 50000],  // Flashloan amounts
  0.0009,                 // Aave fee
  [100, 150, 120]         // Gas costs (multi-hop costs more)
);

// Find best route
let bestRoute = 0;
let bestProfit = results[0][0];

results.forEach(([profit, slippage, index]) => {
  console.log(`Route ${index}: Profit=${profit.toFixed(2)}, Slippage=${slippage.toFixed(4)}%`);
  
  if (profit > bestProfit) {
    bestProfit = profit;
    bestRoute = index;
  }
});

console.log(`\nBest route: ${bestRoute} with profit ${bestProfit.toFixed(2)}`);
```

### Example 3: Risk-Aware Execution

```typescript
import {
  calculateFlashloanAmount,
  calculateMarketImpact,
  calculateMultihopSlippage
} from './dist/index.js';

// Calculate flashloan
const flashloanAmount = calculateFlashloanAmount(
  1000000, 2000000,
  1800000, 1000000,
  0.0009, 100
);

// Define risk thresholds
const MAX_MARKET_IMPACT = 5.0;  // 5% max impact
const MAX_TOTAL_SLIPPAGE = 10.0; // 10% max slippage

// Calculate risks
const buyImpact = calculateMarketImpact(1000000, 2000000, flashloanAmount);
const sellImpact = calculateMarketImpact(1800000, 1000000, flashloanAmount * 2);
const totalSlippage = calculateMultihopSlippage(
  [[1000000, 2000000], [1800000, 1000000]],
  flashloanAmount
);

// Risk checks
if (buyImpact > MAX_MARKET_IMPACT || sellImpact > MAX_MARKET_IMPACT) {
  console.log('⚠️  Market impact too high, reducing trade size...');
  // Reduce flashloan amount
} else if (totalSlippage > MAX_TOTAL_SLIPPAGE) {
  console.log('⚠️  Slippage too high, skipping opportunity...');
} else {
  console.log('✅ Risk checks passed, executing arbitrage...');
  // Execute trade
}
```

## Flashloan Providers

The system supports flashloan calculations for major providers:

| Provider | Fee | Default in Code |
|----------|-----|-----------------|
| **Aave V3** | 0.09% | `0.0009` |
| **dYdX** | 0% | `0.0000` |
| **Balancer** | 0% | `0.0000` |
| **Uniswap V3** | Variable | Check pool |

## Performance Characteristics

All flashloan calculations are implemented in Rust for maximum performance:

- **Flashloan amount calculation**: ~100 iterations, <1ms
- **Market impact calculation**: O(1), <0.1ms
- **Multi-hop slippage**: O(n) where n = hops, <1ms for 5 hops
- **Parallel path simulation**: O(n*m) where n = paths, m = hops per path

## Testing

Comprehensive test suite with 20+ tests covering:

1. ✅ Flashloan amount calculation (profitable/unprofitable scenarios)
2. ✅ Market impact calculation (various trade sizes)
3. ✅ Multi-hop slippage calculation
4. ✅ Parallel path simulation
5. ✅ Uniswap V3 flashloan calculations
6. ✅ Edge case handling
7. ✅ Complete arbitrage workflows
8. ✅ Risk-aware execution

Run tests:
```bash
cd ultra-fast-arbitrage-engine
npm test
```

## Security Considerations

1. **Flashloan Fees**: Always account for provider fees in calculations
2. **Market Impact**: Large trades can cause significant slippage
3. **Front-running**: Use private mempools (Flashbots, etc.) for execution
4. **Gas Costs**: Include gas in profit calculations
5. **Pool Liquidity**: Verify pools have sufficient liquidity before execution
6. **Slippage Tolerance**: Set appropriate slippage limits to prevent failed transactions

## Future Enhancements

Potential improvements for future versions:

1. **Dynamic fee calculation** based on current network conditions
2. **Multi-asset flashloan** optimization
3. **Cross-chain flashloan** routing
4. **Machine learning** for market impact prediction
5. **Real-time liquidity** monitoring integration
6. **Gas price optimization** algorithms
7. **MEV protection** enhancements

## Conclusion

The flashloan and market impact features enable the system to:
- ✅ **Automatically calculate** optimal flashloan amounts
- ✅ **Predict market impact** before execution
- ✅ **Simulate multiple paths** simultaneously
- ✅ **Make risk-aware decisions** based on slippage and impact
- ✅ **Maximize profits** while minimizing execution risk

These features are essential for professional-grade arbitrage trading and MEV extraction strategies.
