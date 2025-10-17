# SYMEN-MAX Ultra-Fast Arbitrage Engine

[![CI](https://github.com/Omni-Tech-Stack/Omni-Defi_Bot/actions/workflows/ci.yml/badge.svg)](https://github.com/Omni-Tech-Stack/Omni-Defi_Bot/actions/workflows/ci.yml)
[![Rust](https://github.com/Omni-Tech-Stack/Omni-Defi_Bot/actions/workflows/rust.yml/badge.svg)](https://github.com/Omni-Tech-Stack/Omni-Defi_Bot/actions/workflows/rust.yml)
[![Lint](https://github.com/Omni-Tech-Stack/Omni-Defi_Bot/actions/workflows/lint.yml/badge.svg)](https://github.com/Omni-Tech-Stack/Omni-Defi_Bot/actions/workflows/lint.yml)

High-performance arbitrage calculation engine with native Rust backend and TypeScript interface.

## 📊 Test Validation & Transparency

**All calculations, formulas, and data sources are fully documented and verifiable:**

- **[TEST_VALIDATION_SUMMARY.md](./TEST_VALIDATION_SUMMARY.md)** - Quick overview and navigation
- **[MATH_FORMULAS.md](./MATH_FORMULAS.md)** - All formulas with whitepaper sources
- **[TEST_DATA_SOURCES.md](./TEST_DATA_SOURCES.md)** - Test data justification and sources
- **[VALIDATION_GUIDE.md](./VALIDATION_GUIDE.md)** - How to validate everything yourself

Run `yarn test:verbose` to see step-by-step calculations with sources.

---

## Features

- **Zero-Copy NAPI Bindings**: Direct memory access between Rust and Node.js
- **Native Speed**: Rust compiled with LTO and optimization level 3
- **Multi-DEX Support**: Uniswap V2/V3, Curve, Balancer, and aggregator routing
- **Complete Arbitrage Flow**: 7-step logical flow for opportunity detection and execution
- **TWAP Validation**: Time-weighted average price validation to prevent manipulation
- **Quadratic Optimization**: Advanced trade size optimization for maximum profit
- **Type Safety**: Full TypeScript type definitions
- **Deterministic**: Same inputs always produce same outputs

## 🚀 New: Complete Arbitrage Flow System

The engine now implements a complete 7-step logical flow for arbitrage:

1. **Identify Arbitrage Opportunities** - Calculate and compare prices
2. **Determine Direction** - Confirm buy/sell pools
3. **Calculate Trade Amounts** - Input/output calculations
4. **Estimate Profitability** - Profit after all fees
5. **Optimize Trade Size** - Quadratic optimization
6. **Validate Using TWAP** - Prevent price manipulation
7. **Execute Decision** - Complete workflow

📖 **[See ARBITRAGE_FLOW.md for complete documentation](./ARBITRAGE_FLOW.md)**

### Quick Example

```typescript
import { executeArbitrageFlow } from './index';

const priceSamples = [[0, 2.0], [10, 2.05], [20, 2.1]];

const [shouldExecute, optimalAmount, expectedProfit] = executeArbitrageFlow(
  1000000, 2000000,   // Pool 1 reserves
  1000000, 2500000,   // Pool 2 reserves (25% price difference)
  priceSamples,       // TWAP validation data
  priceSamples,
  100,                // Gas cost
  0.0009,             // Flashloan fee (0.09%)
  5.0,                // Min 5% price difference
  10.0,               // Max 10% TWAP deviation
  50.0                // Min $50 profit
);

if (shouldExecute === 1) {
  console.log(`Execute: Amount ${optimalAmount}, Profit ${expectedProfit}`);
}
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   TypeScript/JavaScript                  │
│  (index.ts → dist/index.js)                             │
│  - computeSlippage()                                     │
│  - computeUniswapV3Slippage()                           │
│  - computeCurveSlippage()                               │
│  - computeBalancerSlippage()                            │
│  - computeAggregatorSlippage()                          │
│  - getOptimalTradeSize()                                │
└────────────────────┬────────────────────────────────────┘
                     │ NAPI-RS Bindings
                     │ (Zero-copy, direct function calls)
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    Rust Native Module                    │
│  (native/src/lib.rs + math.rs)                          │
│  - compute_uniswap_v2_slippage()                        │
│  - compute_uniswap_v3_slippage()                        │
│  - compute_curve_slippage()                             │
│  - compute_balancer_slippage()                          │
│  - compute_aggregator_slippage()                        │
│  - optimal_trade_size()                                 │
│                                                          │
│  Optimizations:                                         │
│  - LTO (Link-Time Optimization)                         │
│  - Opt-level 3                                          │
│  - Single codegen unit                                  │
└─────────────────────────────────────────────────────────┘
```

## Installation

```bash
cd ultra-fast-arbitrage-engine
yarn install
```

## Setup

### Interactive Setup (Recommended)

Run the interactive setup script to configure all variables:

```bash
yarn setup
# or
node setup.js
```

This will guide you through configuring:
- RPC Endpoint
- Pool Registry Path
- Token Equivalence Path
- Arbitrage Contract ABI
- Private Key (securely)
- MEV Relays (Bloxroute, Flashbots, Eden)
- ML Model configuration
- Monitoring & Alerts (Slack, Email, Telegram)
- Log Directory
- Automation settings
- Execution parameters
- Risk management
- Database connection

The script will:
1. Prompt for each configuration item
2. Create necessary directories and files
3. Update or create the `.env` file
4. Validate the configuration

### Manual Setup

Alternatively, copy `.env.example` (if exists) or manually create `.env` with required variables.

## Building

Build both Rust native module and TypeScript interface:

```bash
yarn run build:all
```

Or build separately:

```bash
# Build Rust module only
yarn run build:rust

# Build TypeScript only
yarn run build
```

## Testing

### Quick Test (Standard Output)

Run the complete integration test suite:

```bash
yarn test
```

Expected output:
```
=== SYSTEM INTEGRATION TEST ===
✓ Uniswap V2 slippage calculation
✓ Uniswap V3 slippage calculation
✓ Curve slippage calculation
✓ Balancer slippage calculation
✓ Aggregator returns minimum slippage
✓ Optimal trade size for profitable scenario
✓ Optimal trade size for unprofitable scenario
✓ Large trade shows higher slippage than small trade
✓ Functions handle zero trade size
✓ Full arbitrage workflow integration
...and 10 more tests

=== TEST SUMMARY ===
Tests passed: 20
Tests failed: 0
Total tests: 20

✓ ALL TESTS PASSED - System integration verified!
```

### Verbose Test (Detailed Calculations)

Run tests with detailed mathematical calculations and data sources:

```bash
yarn test:verbose
```

This shows:
- **Input parameters** with context and sources
- **Step-by-step calculations** for each formula
- **Intermediate values** in each computation
- **Final results** with explanations
- **Source references** to protocol documentation

### Arbitrage Flow Testing

Run the complete arbitrage flow test suite:

```bash
yarn test:flow
```

This tests all 7 steps of the arbitrage workflow:
- ✓ Price calculation and opportunity identification
- ✓ Direction determination
- ✓ Trade amount calculations
- ✓ Profitability estimation
- ✓ Quadratic optimization
- ✓ TWAP validation
- ✓ Complete execution flow

Run all tests:

```bash
yarn test:all
```

### Test Validation Documentation

For complete transparency on test mathematics and data sources:

1. **[VALIDATION_GUIDE.md](./VALIDATION_GUIDE.md)** - How to validate all calculations
2. **[MATH_FORMULAS.md](./MATH_FORMULAS.md)** - All formulas with sources and examples
3. **[ARBITRAGE_FLOW.md](./ARBITRAGE_FLOW.md)** - Complete arbitrage flow documentation
4. **[TEST_DATA_SOURCES.md](./TEST_DATA_SOURCES.md)** - Test data justification and sources

These documents provide:
- ✓ Mathematical formula derivations with whitepaper references
- ✓ Complete arbitrage workflow with equations
- ✓ Test data sources and rationale
- ✓ Manual calculation examples you can verify
- ✓ Protocol fee sources (Uniswap, Curve, Aave, etc.)
- ✓ Links to on-chain analytics and contract code
- ✓ Step-by-step validation instructions

## Variable Verification

Run comprehensive variable verification (80+ automated checks):

```bash
node verify-variables.js
```

This validates:
- All module files exist
- Build artifacts are present and valid
- All functions are properly exported
- All parameters are correctly typed
- Test suite completeness
- Rust NAPI bindings
- Configuration integrity
- Module loading and functionality

For detailed documentation of all 200+ variables, see [MODULE_VERIFICATION.md](./MODULE_VERIFICATION.md).

## API Reference

### Core Slippage Functions

#### computeSlippage(reserveIn, reserveOut, amountIn)

Calculate slippage for Uniswap V2 style constant product pools.

**Parameters:**
- `reserveIn` - Input token reserve
- `reserveOut` - Output token reserve
- `amountIn` - Trade amount

**Returns:** Slippage percentage

#### computeUniswapV3Slippage(liquidity, sqrtPrice, amountIn)

Calculate slippage for Uniswap V3 concentrated liquidity pools.

#### computeCurveSlippage(balanceIn, balanceOut, amountIn, amplification)

Calculate slippage for Curve stableswap pools with amplification coefficient.

#### computeBalancerSlippage(balanceIn, balanceOut, weightIn, weightOut, amountIn)

Calculate slippage for Balancer weighted pools.

#### computeAggregatorSlippage(slippages)

Find the best route with minimum slippage from multiple options.

#### getOptimalTradeSize(reserveIn, reserveOut, gasCost, minProfit)

Calculate the optimal trade size for maximum profit.

### Arbitrage Flow Functions

#### calculatePoolPrice(reserveIn, reserveOut)
**Step 1**: Calculate token price from pool reserves.

#### identifyArbitrageOpportunity(pool1ReserveIn, pool1ReserveOut, pool2ReserveIn, pool2ReserveOut, minPriceDiffPct)
**Step 2**: Identify arbitrage opportunity and determine direction.

**Returns:** `[hasOpportunity, priceDifference%, direction]`

#### calculateAmountIn(reserveIn, reserveOut, amountOut)
**Step 3**: Calculate input amount needed for desired output.

#### calculateAmountOut(reserveIn, reserveOut, amountIn)
**Step 3**: Calculate output amount for given input.

#### estimateArbitrageProfit(buyReserveIn, buyReserveOut, sellReserveIn, sellReserveOut, amountIn, gasCost, flashloanFeePct)
**Step 4**: Estimate net profit after all fees.

#### solveQuadratic(a, b, c)
**Step 5**: Solve quadratic equation ax² + bx + c = 0.

**Returns:** `[root1, root2]`

#### optimizeTradeSizeQuadratic(buyReserveIn, buyReserveOut, sellReserveIn, sellReserveOut, gasCost, flashloanFeePct)
**Step 5**: Find optimal trade size for maximum profit.

#### calculateTWAP(priceSamples)
**Step 6**: Calculate time-weighted average price from historical samples.

**Parameters:**
- `priceSamples` - Array of `[timestamp, price]` pairs

#### validateWithTWAP(currentPrice, twap, maxDeviationPct)
**Step 6**: Validate current price against TWAP to detect manipulation.

#### executeArbitrageFlow(...)
**Step 7**: Complete arbitrage workflow integrating all steps.

**Returns:** `[shouldExecute, optimalAmount, expectedProfit]`

📖 **See [ARBITRAGE_FLOW.md](./ARBITRAGE_FLOW.md) for detailed API documentation and examples.**

## Performance

- **Native Module Size**: ~441KB (optimized)
- **Zero Serialization Overhead**: Direct memory access via NAPI
- **Microsecond Latency**: Suitable for high-frequency arbitrage
- **Arbitrage Flow**: < 200μs for complete 7-step workflow

## License

MIT
