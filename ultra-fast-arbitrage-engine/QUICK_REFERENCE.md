# Quick Reference - Arbitrage Flow Functions

## 🚀 Quick Start

```bash
# Install and build
npm install
npm run build:all

# Run tests
npm run test:all

# See demonstration
npm run demo
```

## 📋 Function Reference

### Step 1: Price Calculation
```typescript
const price = calculatePoolPrice(reserveIn, reserveOut);
// Example: calculatePoolPrice(1000000, 2000000) → 2.0
```

### Step 2: Identify Opportunity
```typescript
const [hasOpp, priceDiff, direction] = identifyArbitrageOpportunity(
  pool1ReserveIn, pool1ReserveOut,
  pool2ReserveIn, pool2ReserveOut,
  minPriceDiffPct
);
// Returns: [1/0, percentage, 0/1/2]
```

### Step 3: Calculate Amounts
```typescript
// Calculate output for given input
const amountOut = calculateAmountOut(reserveIn, reserveOut, amountIn);

// Calculate input needed for desired output
const amountIn = calculateAmountIn(reserveIn, reserveOut, amountOut);
```

### Step 4: Estimate Profit
```typescript
const profit = estimateArbitrageProfit(
  buyReserveIn, buyReserveOut,
  sellReserveIn, sellReserveOut,
  amountIn,
  gasCost,
  flashloanFeePct
);
```

### Step 5: Optimize Size
```typescript
// Solve quadratic equation
const [root1, root2] = solveQuadratic(a, b, c);

// Find optimal trade size
const optimalSize = optimizeTradeSizeQuadratic(
  buyReserveIn, buyReserveOut,
  sellReserveIn, sellReserveOut,
  gasCost,
  flashloanFeePct
);
```

### Step 6: TWAP Validation
```typescript
// Calculate TWAP from price samples
const priceSamples = [[0, 100], [10, 110], [20, 105]]; // [timestamp, price]
const twap = calculateTWAP(priceSamples);

// Validate current price
const isValid = validateWithTWAP(currentPrice, twap, maxDeviationPct);
```

### Step 7: Complete Flow
```typescript
const [shouldExecute, optimalAmount, expectedProfit] = executeArbitrageFlow(
  pool1ReserveIn,
  pool1ReserveOut,
  pool2ReserveIn,
  pool2ReserveOut,
  priceSamplesPool1,
  priceSamplesPool2,
  gasCost,
  flashloanFeePct,
  minPriceDiffPct,
  maxTwapDeviationPct,
  minProfitThreshold
);

if (shouldExecute === 1) {
  // Execute the arbitrage
  console.log(`Amount: ${optimalAmount}, Profit: ${expectedProfit}`);
}
```

## 📊 Complete Example

```typescript
import {
  identifyArbitrageOpportunity,
  executeArbitrageFlow
} from './index';

// Market data
const pool1 = { reserveIn: 1000000, reserveOut: 2000000 };
const pool2 = { reserveIn: 1000000, reserveOut: 2600000 };

// Price history for TWAP
const history = [[0, 2.0], [10, 2.05], [20, 2.1]];

// Step 1 & 2: Check opportunity
const [hasOpp, priceDiff, direction] = identifyArbitrageOpportunity(
  pool1.reserveIn, pool1.reserveOut,
  pool2.reserveIn, pool2.reserveOut,
  5.0  // Min 5% price difference
);

if (hasOpp === 1) {
  // Steps 3-7: Complete execution flow
  const [shouldExecute, amount, profit] = executeArbitrageFlow(
    pool1.reserveIn, pool1.reserveOut,
    pool2.reserveIn, pool2.reserveOut,
    history, history,
    100,    // Gas cost
    0.0009, // Flashloan fee (0.09%)
    5.0,    // Min price diff
    10.0,   // Max TWAP deviation
    50.0    // Min profit threshold
  );

  if (shouldExecute === 1) {
    console.log('Execute arbitrage!');
    console.log(`Borrow: ${amount}`);
    console.log(`Profit: ${profit}`);
    // Execute trade...
  }
}
```

## 🧪 Testing

```bash
# Run all tests
npm run test:all

# Run specific test suites
npm run test        # Integration tests
npm run test:flow   # Arbitrage flow tests

# Interactive demo
npm run demo
```

## 📖 Documentation

- **[ARBITRAGE_FLOW.md](./ARBITRAGE_FLOW.md)** - Complete API documentation
- **[IMPLEMENTATION_SUMMARY_FLOW.md](./IMPLEMENTATION_SUMMARY_FLOW.md)** - Implementation details
- **[README.md](./README.md)** - Main documentation

## ⚡ Performance

All operations run in native Rust:
- Complete flow: < 200μs
- Throughput: 5,000+ opportunities/second
- Zero serialization overhead (NAPI direct access)

## 🔑 Key Formulas

| Step | Formula |
|------|---------|
| 1 | `p_t = reserveOut / reserveIn` |
| 2 | `PriceDiff = \|P1 - P2\| / min(P1, P2) * 100%` |
| 3 (in) | `amountIn = (ReserveIn × AmountOut × 1000) / ((ReserveOut - AmountOut) × 997) + 1` |
| 3 (out) | `amountOut = (ReserveOut × AmountIn × 997) / (ReserveIn × 1000 + AmountIn × 997)` |
| 4 | `profit = AmountOut_sell - AmountIn_buy - gas - fees` |
| 5 | `ax² + bx + c = 0` |
| 6 | `TWAP = Σ(p_i × Δt_i) / Σ(Δt_i)` |
| 7 | Complete integration of steps 1-6 |

## 🎯 Use Cases

1. **DEX Arbitrage**: Trade between Uniswap, SushiSwap, etc.
2. **Price Discovery**: Identify market inefficiencies
3. **Risk Management**: TWAP validation prevents manipulation
4. **Profit Optimization**: Find optimal trade sizes
5. **High-Frequency Trading**: Sub-millisecond execution decisions

## 🛠️ Troubleshooting

**Build fails?**
```bash
npm run build:rust  # Rebuild Rust module
npm run build       # Rebuild TypeScript
```

**Tests fail?**
```bash
npm install         # Reinstall dependencies
npm run build:all   # Full rebuild
```

**Need help?**
- See [ARBITRAGE_FLOW.md](./ARBITRAGE_FLOW.md) for detailed docs
- Run `npm run demo` for interactive examples
- Check test files for usage patterns
