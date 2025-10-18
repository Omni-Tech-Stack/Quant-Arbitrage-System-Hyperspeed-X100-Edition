# Flashloan Features API Documentation

## Overview

The Quant Arbitrage System Hyperspeed X100 Edition now includes advanced flashloan calculation and market impact prediction capabilities through a high-performance Rust-powered backend.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                Ultra-Fast Arbitrage Engine               │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │       Rust Math Engine (Native)                 │    │
│  │                                                  │    │
│  │  • calculate_flashloan_amount()                 │    │
│  │  • calculate_market_impact()                    │    │
│  │  • calculate_multihop_slippage()               │    │
│  │  • simulate_parallel_flashloan_paths()         │    │
│  │                                                  │    │
│  │  Performance: <1ms per calculation              │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────┐
│                  Backend API (Express)                   │
│                                                          │
│  POST /api/calculate-flashloan                          │
│  POST /api/calculate-impact                             │
│  POST /api/calculate-multihop-slippage                  │
│  POST /api/simulate-paths                               │
└─────────────────────────────────────────────────────────┘
```

## Features

### 1. Automatic Flashloan Amount Calculation

Automatically calculates the optimal flashloan amount for arbitrage opportunities using binary search optimization.

**Key Points:**
- Accounts for DEX fees (0.3%), flashloan fees, and gas costs
- Returns 0 for unprofitable opportunities
- Considers pool liquidity limits (max 30% of reserve)
- Sub-millisecond calculation time

**Supported Flashloan Providers:**
- **Aave V3**: 0.09% fee (0.0009)
- **dYdX**: 0% fee (0)
- **Balancer**: 0% fee (0)
- **Uniswap V3**: Variable fee

### 2. Market Impact Prediction

Predicts price slippage caused by flashloan-sized trades before execution.

**Key Points:**
- Calculates price change in the pool
- Returns percentage impact
- Essential for large trades
- Helps assess execution risk

### 3. Multi-hop Slippage Calculation

Calculates total slippage across complex arbitrage paths.

**Key Points:**
- Supports multi-DEX routes
- Accumulates slippage at each hop
- Accounts for amount reduction through path
- Enables risk-aware route selection

### 4. Parallel Path Simulation

Simulates multiple execution paths simultaneously.

**Key Points:**
- Tests different routes in parallel
- Calculates profit and slippage for each
- Returns ranked results
- Supports complex multi-hop paths

## API Endpoints

### POST /api/calculate-flashloan

Calculate the optimal flashloan amount for an arbitrage opportunity.

**Request Body:**
```json
{
  "reserveInBuy": 1000000,
  "reserveOutBuy": 2000000,
  "reserveInSell": 1800000,
  "reserveOutSell": 1000000,
  "flashloanFee": 0.0009,  // Optional, default: 0.0009 (Aave V3)
  "gasCost": 100           // Optional, default: 100
}
```

**Response:**
```json
{
  "success": true,
  "flashloanAmount": 45678.90,
  "flashloanFee": 0.0009,
  "gasCost": 100,
  "profitable": true,
  "timestamp": "2025-10-18T17:00:00.000Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:3001/api/calculate-flashloan \
  -H "Content-Type: application/json" \
  -d '{
    "reserveInBuy": 1000000,
    "reserveOutBuy": 2000000,
    "reserveInSell": 1800000,
    "reserveOutSell": 1000000,
    "flashloanFee": 0.0009,
    "gasCost": 100
  }'
```

### POST /api/calculate-impact

Calculate market impact (price slippage) for a trade.

**Request Body:**
```json
{
  "reserveIn": 1000000,
  "reserveOut": 2000000,
  "tradeAmount": 50000
}
```

**Response:**
```json
{
  "success": true,
  "marketImpact": 4.8116,
  "marketImpactPct": "4.8116%",
  "reserveIn": 1000000,
  "reserveOut": 2000000,
  "tradeAmount": 50000,
  "timestamp": "2025-10-18T17:00:00.000Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:3001/api/calculate-impact \
  -H "Content-Type: application/json" \
  -d '{
    "reserveIn": 1000000,
    "reserveOut": 2000000,
    "tradeAmount": 50000
  }'
```

### POST /api/calculate-multihop-slippage

Calculate total slippage across a multi-hop arbitrage path.

**Request Body:**
```json
{
  "path": [
    [1000000, 2000000],  // Hop 1: Uniswap V2
    [2000000, 2000000],  // Hop 2: Curve
    [2000000, 1000000]   // Hop 3: Balancer
  ],
  "flashloanAmount": 25000
}
```

**Response:**
```json
{
  "success": true,
  "totalSlippage": 7.9834,
  "totalSlippagePct": "7.9834%",
  "hops": 3,
  "flashloanAmount": 25000,
  "timestamp": "2025-10-18T17:00:00.000Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:3001/api/calculate-multihop-slippage \
  -H "Content-Type: application/json" \
  -d '{
    "path": [
      [1000000, 2000000],
      [2000000, 2000000],
      [2000000, 1000000]
    ],
    "flashloanAmount": 25000
  }'
```

### POST /api/simulate-paths

Simulate multiple flashloan arbitrage paths in parallel.

**Request Body:**
```json
{
  "paths": [
    [[1000000, 2000000], [2100000, 1000000]],  // Route 1
    [[1000000, 3000000], [3200000, 1000000]],  // Route 2
    [[5000000, 10000000], [10500000, 5000000]] // Route 3
  ],
  "flashloanAmounts": [50000, 50000, 50000],
  "flashloanFee": 0.0009,
  "gasCosts": [100, 100, 120]
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "pathIndex": 0,
      "profit": 1234.56,
      "slippage": 3.45,
      "slippagePct": "3.4500%",
      "isBest": false
    },
    {
      "pathIndex": 1,
      "profit": 2345.67,
      "slippage": 2.34,
      "slippagePct": "2.3400%",
      "isBest": true
    },
    {
      "pathIndex": 2,
      "profit": 987.65,
      "slippage": 1.23,
      "slippagePct": "1.2300%",
      "isBest": false
    }
  ],
  "bestPathIndex": 1,
  "bestProfit": 2345.67,
  "totalPathsSimulated": 3,
  "timestamp": "2025-10-18T17:00:00.000Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:3001/api/simulate-paths \
  -H "Content-Type: application/json" \
  -d '{
    "paths": [
      [[1000000, 2000000], [2100000, 1000000]],
      [[1000000, 3000000], [3200000, 1000000]]
    ],
    "flashloanAmounts": [30000, 30000],
    "flashloanFee": 0.0009,
    "gasCosts": [100, 100]
  }'
```

## Usage Examples

### Example 1: Calculate Optimal Flashloan

```javascript
const axios = require('axios');

async function calculateFlashloan() {
  const response = await axios.post('http://localhost:3001/api/calculate-flashloan', {
    reserveInBuy: 1000000,   // 1M USDC
    reserveOutBuy: 2000000,  // 2M ETH
    reserveInSell: 1800000,  // 1.8M USDC (price difference!)
    reserveOutSell: 1000000, // 1M ETH
    flashloanFee: 0.0009,    // Aave V3 fee
    gasCost: 100             // Gas cost in USDC
  });

  console.log(`Optimal flashloan: $${response.data.flashloanAmount.toFixed(2)}`);
  console.log(`Profitable: ${response.data.profitable}`);
}

calculateFlashloan();
```

### Example 2: Predict Market Impact

```javascript
async function predictImpact() {
  const response = await axios.post('http://localhost:3001/api/calculate-impact', {
    reserveIn: 1000000,
    reserveOut: 2000000,
    tradeAmount: 50000
  });

  console.log(`Market impact: ${response.data.marketImpactPct}`);
  
  if (response.data.marketImpact > 5) {
    console.log('⚠️ High impact - consider reducing trade size');
  }
}

predictImpact();
```

### Example 3: Multi-hop Arbitrage

```javascript
async function calculateMultihopSlippage() {
  const response = await axios.post('http://localhost:3001/api/calculate-multihop-slippage', {
    path: [
      [1000000, 2000000],  // Uniswap V2
      [2000000, 2000000],  // Curve
      [2000000, 1000000]   // Balancer
    ],
    flashloanAmount: 25000
  });

  console.log(`Total slippage across ${response.data.hops} hops: ${response.data.totalSlippagePct}`);
}

calculateMultihopSlippage();
```

### Example 4: Find Best Route

```javascript
async function findBestRoute() {
  const response = await axios.post('http://localhost:3001/api/simulate-paths', {
    paths: [
      [[1000000, 2000000], [2100000, 1000000]],  // Route 1
      [[1000000, 3000000], [3200000, 1000000]],  // Route 2
      [[5000000, 10000000], [10500000, 5000000]] // Route 3
    ],
    flashloanAmounts: [50000, 50000, 50000],
    flashloanFee: 0.0009,
    gasCosts: [100, 100, 120]
  });

  const bestRoute = response.data.results.find(r => r.isBest);
  console.log(`Best route: Path ${bestRoute.pathIndex}`);
  console.log(`Expected profit: $${bestRoute.profit.toFixed(2)}`);
  console.log(`Slippage: ${bestRoute.slippagePct}`);
}

findBestRoute();
```

## Performance

All calculations run in native Rust code for maximum performance:

| Operation | Time Complexity | Typical Runtime |
|-----------|----------------|-----------------|
| Flashloan amount calculation | O(log n) | <1ms |
| Market impact calculation | O(1) | <0.1ms |
| Multi-hop slippage | O(n) | <1ms (5 hops) |
| Parallel path simulation | O(n×m) | <5ms (10 paths × 3 hops) |

## Error Handling

All endpoints return appropriate HTTP status codes:

- **200 OK**: Successful calculation
- **400 Bad Request**: Invalid or missing parameters
- **500 Internal Server Error**: Server-side error

Error response format:
```json
{
  "success": false,
  "error": "Error message description"
}
```

## Security Considerations

### 1. Flashloan Provider Risks
- Always verify provider contract addresses
- Check flashloan fees before execution
- Monitor provider liquidity

### 2. Market Impact Risks
- Large trades can cause significant slippage
- Set maximum impact thresholds (e.g., 5%)
- Use private mempools to prevent front-running

### 3. Gas Cost Management
- Include gas in profit calculations
- Monitor network congestion
- Set gas price limits

### 4. Slippage Protection
- Set slippage tolerance limits
- Use multi-path routing for better execution
- Monitor pool liquidity in real-time

## Testing

Comprehensive test suite included:

```bash
# Test the arbitrage engine
cd ultra-fast-arbitrage-engine
npm test

# Test API endpoints
cd backend
node tests/flashloan-api.test.js
```

Test coverage:
- ✅ 20 engine tests (all passing)
- ✅ 15 API integration tests (all passing)

## Quick Start

1. **Build the Engine**
```bash
cd ultra-fast-arbitrage-engine
npm install
cd native && cargo build --release && cd ..
cp native/target/release/libmath_engine.so native/math_engine.node
npm run build
```

2. **Run Tests**
```bash
npm test
```

3. **Start Backend**
```bash
cd ../backend
npm install
DEMO_MODE=true npm start
```

4. **Test API**
```bash
curl http://localhost:3001/api/health
```

## Integration with Frontend

The API is designed to work with the existing frontend dashboard. New flashloan metrics are automatically displayed:

- **Opportunities Table**: Shows optimal flashloan amounts
- **Trades Table**: Displays flashloan execution details
- **Market Impact**: Visual indicators for trade impact

## Support

For issues or questions:
- Check test files for usage examples
- Review API endpoint documentation above
- Ensure all dependencies are installed
- Verify Rust toolchain is available

## License

MIT
