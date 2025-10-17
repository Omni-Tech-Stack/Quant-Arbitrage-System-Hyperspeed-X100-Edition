# Quick Start Guide

## Prerequisites

- Node.js v20.x or higher
- Rust 1.90.0 or higher
- Yarn package manager

## Installation

```bash
cd ultra-fast-arbitrage-engine
yarn install
```

## Initial Setup

### Interactive Setup (Recommended)

Run the interactive setup wizard to configure all variables:

```bash
yarn setup
```

This interactive script will:
1. Walk you through all configuration options
2. Create necessary directories and files
3. Generate or update your `.env` file
4. Validate your configuration

Configuration includes:
- Network RPC endpoints
- Wallet/private key setup
- MEV relay configuration (Flashbots, Bloxroute, Eden)
- Pool registry and token equivalence files
- Machine learning model paths
- Monitoring and alerting (Telegram, Slack, Email)
- Database and Redis settings
- Execution parameters and risk management
- Logging configuration

**Security Note:** The setup script handles sensitive data like private keys carefully and reminds you never to commit them to version control.

## Building

### Build Everything (Recommended)

```bash
yarn run build:all
```

This will:
1. Compile the Rust native module with optimizations
2. Build the TypeScript interface
3. Generate type definitions

### Build Components Separately

```bash
# Build Rust native module only
yarn run build:rust

# Build TypeScript only
yarn run build
```

## Testing

Run the complete test suite:

```bash
yarn test
```

Or use the verification script:

```bash
./verify.sh
```

## Expected Test Output

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

## Usage Example

```javascript
const {
  computeSlippage,
  computeUniswapV3Slippage,
  computeCurveSlippage,
  computeBalancerSlippage,
  computeAggregatorSlippage,
  getOptimalTradeSize
} = require('./dist/index.js');

// Calculate Uniswap V2 slippage
const slippage = computeSlippage(
  1000000,  // reserveIn
  2000000,  // reserveOut
  10000     // amountIn
);
console.log('Slippage:', slippage, '%');

// Find optimal trade size
const optimalSize = getOptimalTradeSize(
  1000000,  // reserveIn
  2000000,  // reserveOut
  100,      // gasCost
  50        // minProfit
);
console.log('Optimal trade size:', optimalSize);

// Compare routes and find best
const routes = [
  computeSlippage(1000000, 2000000, 10000),
  computeCurveSlippage(1000000, 1000000, 10000, 100),
  computeBalancerSlippage(1000000, 2000000, 0.5, 0.5, 10000)
];
const bestRoute = computeAggregatorSlippage(routes);
console.log('Best route slippage:', bestRoute, '%');
```

## Architecture Benefits

- **Zero-Copy Performance**: Direct memory access via NAPI bindings
- **Native Speed**: Rust compiled with LTO and opt-level 3
- **Type Safety**: Full TypeScript type definitions
- **Deterministic**: Same inputs always produce same outputs
- **Production Ready**: Optimized for microsecond-latency arbitrage

## Troubleshooting

### Build Issues

If you encounter build issues, ensure:
1. Rust toolchain is installed: `rustc --version`
2. Node.js is v20 or higher: `node --version`
3. Clean build: `rm -rf node_modules dist native/target && yarn install && yarn run build:all`

### Runtime Issues

If the native module fails to load:
1. Verify the build completed: `ls -la native/math_engine.node`
2. Check for platform-specific library: `.so` (Linux), `.dylib` (macOS), `.dll` (Windows)
3. Rebuild: `yarn run build:all`

## Performance Notes

The native module is compiled with:
- **LTO (Link-Time Optimization)**: Enables cross-function optimizations
- **Opt-level 3**: Maximum optimization level
- **Single codegen unit**: Better optimization opportunities

This results in:
- Module size: ~421-441KB (optimized)
- Microsecond-level computation latency
- Zero serialization overhead
