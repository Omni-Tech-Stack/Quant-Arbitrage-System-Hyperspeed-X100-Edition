# SYMEN-MAX Ultra-Fast Arbitrage Engine

[![CI](https://github.com/Omni-Tech-Stack/Omni-Defi_Bot/actions/workflows/ci.yml/badge.svg)](https://github.com/Omni-Tech-Stack/Omni-Defi_Bot/actions/workflows/ci.yml)
[![Rust](https://github.com/Omni-Tech-Stack/Omni-Defi_Bot/actions/workflows/rust.yml/badge.svg)](https://github.com/Omni-Tech-Stack/Omni-Defi_Bot/actions/workflows/rust.yml)
[![Lint](https://github.com/Omni-Tech-Stack/Omni-Defi_Bot/actions/workflows/lint.yml/badge.svg)](https://github.com/Omni-Tech-Stack/Omni-Defi_Bot/actions/workflows/lint.yml)

High-performance arbitrage calculation engine with native Rust backend and TypeScript interface.

## Features

- **Zero-Copy NAPI Bindings**: Direct memory access between Rust and Node.js
- **Native Speed**: Rust compiled with LTO and optimization level 3
- **Multi-DEX Support**: Uniswap V2/V3, Curve, Balancer, and aggregator routing
- **Type Safety**: Full TypeScript type definitions
- **Deterministic**: Same inputs always produce same outputs

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

=== TEST SUMMARY ===
Tests passed: 10
Tests failed: 0
Total tests: 10

✓ ALL TESTS PASSED - System integration verified!
```

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

### computeSlippage(reserveIn, reserveOut, amountIn)

Calculate slippage for Uniswap V2 style constant product pools.

**Parameters:**
- `reserveIn` - Input token reserve
- `reserveOut` - Output token reserve
- `amountIn` - Trade amount

**Returns:** Slippage percentage

### computeUniswapV3Slippage(liquidity, sqrtPrice, amountIn)

Calculate slippage for Uniswap V3 concentrated liquidity pools.

### computeCurveSlippage(balanceIn, balanceOut, amountIn, amplification)

Calculate slippage for Curve stableswap pools with amplification coefficient.

### computeBalancerSlippage(balanceIn, balanceOut, weightIn, weightOut, amountIn)

Calculate slippage for Balancer weighted pools.

### computeAggregatorSlippage(slippages)

Find the best route with minimum slippage from multiple options.

### getOptimalTradeSize(reserveIn, reserveOut, gasCost, minProfit)

Calculate the optimal trade size for maximum profit.

## Performance

- **Native Module Size**: ~441KB (optimized)
- **Zero Serialization Overhead**: Direct memory access via NAPI
- **Microsecond Latency**: Suitable for high-frequency arbitrage

## License

MIT
