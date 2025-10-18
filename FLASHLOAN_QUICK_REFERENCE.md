# Flashloan Integration Quick Reference

## 🚀 Quick Start

### 1. Start the System

```bash
# Terminal 1: Build and test the engine
cd ultra-fast-arbitrage-engine
npm install
cd native && cargo build --release && cd ..
cp native/target/release/libmath_engine.so native/math_engine.node
npm run build
npm test

# Terminal 2: Start the backend API
cd backend
npm install
DEMO_MODE=true npm start
```

### 2. Test the API

```bash
curl http://localhost:3001/api/health
```

## 📊 Common Use Cases

### Calculate Flashloan for Arbitrage

**JavaScript/Node.js:**
```javascript
const axios = require('axios');

const result = await axios.post('http://localhost:3001/api/calculate-flashloan', {
  reserveInBuy: 1000000,
  reserveOutBuy: 2000000,
  reserveInSell: 1800000,
  reserveOutSell: 1000000,
  flashloanFee: 0.0009,  // Aave V3: 0.09%
  gasCost: 100
});

console.log('Flashloan amount:', result.data.flashloanAmount);
console.log('Profitable:', result.data.profitable);
```

**Python:**
```python
import requests

response = requests.post('http://localhost:3001/api/calculate-flashloan', json={
    'reserveInBuy': 1000000,
    'reserveOutBuy': 2000000,
    'reserveInSell': 1800000,
    'reserveOutSell': 1000000,
    'flashloanFee': 0.0009,
    'gasCost': 100
})

data = response.json()
print(f"Flashloan amount: ${data['flashloanAmount']:.2f}")
print(f"Profitable: {data['profitable']}")
```

**cURL:**
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

### Check Market Impact

**JavaScript/Node.js:**
```javascript
const impact = await axios.post('http://localhost:3001/api/calculate-impact', {
  reserveIn: 1000000,
  reserveOut: 2000000,
  tradeAmount: 50000
});

console.log('Market impact:', impact.data.marketImpactPct);

if (impact.data.marketImpact > 5) {
  console.log('⚠️ WARNING: High market impact!');
}
```

**cURL:**
```bash
curl -X POST http://localhost:3001/api/calculate-impact \
  -H "Content-Type: application/json" \
  -d '{
    "reserveIn": 1000000,
    "reserveOut": 2000000,
    "tradeAmount": 50000
  }'
```

### Multi-hop Path Analysis

**JavaScript/Node.js:**
```javascript
const slippage = await axios.post('http://localhost:3001/api/calculate-multihop-slippage', {
  path: [
    [1000000, 2000000],  // Uniswap
    [2000000, 2000000],  // Curve
    [2000000, 1000000]   // Balancer
  ],
  flashloanAmount: 25000
});

console.log('Total slippage:', slippage.data.totalSlippagePct);
console.log('Number of hops:', slippage.data.hops);
```

**cURL:**
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

### Find Best Route

**JavaScript/Node.js:**
```javascript
const simulation = await axios.post('http://localhost:3001/api/simulate-paths', {
  paths: [
    [[1000000, 2000000], [2100000, 1000000]],
    [[1000000, 3000000], [3200000, 1000000]],
    [[5000000, 10000000], [10500000, 5000000]]
  ],
  flashloanAmounts: [50000, 50000, 50000],
  flashloanFee: 0.0009,
  gasCosts: [100, 100, 120]
});

const bestRoute = simulation.data.results.find(r => r.isBest);
console.log(`Best route: Path ${bestRoute.pathIndex}`);
console.log(`Profit: $${bestRoute.profit.toFixed(2)}`);
console.log(`Slippage: ${bestRoute.slippagePct}`);
```

**cURL:**
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

## 🔧 Using TypeScript/JavaScript Directly

You can also use the engine directly without the API:

```javascript
const {
  calculateFlashloanAmount,
  calculateMarketImpact,
  calculateMultihopSlippage,
  simulateParallelFlashloanPaths
} = require('./ultra-fast-arbitrage-engine/dist/index.js');

// Calculate flashloan
const flashloan = calculateFlashloanAmount(
  1000000, 2000000,  // Buy pool
  1800000, 1000000,  // Sell pool
  0.0009,            // Flashloan fee
  100                // Gas cost
);

// Calculate market impact
const impact = calculateMarketImpact(1000000, 2000000, 50000);

// Multi-hop slippage
const slippage = calculateMultihopSlippage([
  [1000000, 2000000],
  [2000000, 1000000]
], 25000);

// Parallel paths
const results = simulateParallelFlashloanPaths(
  [
    [[1000000, 2000000], [2100000, 1000000]],
    [[1000000, 3000000], [3200000, 1000000]]
  ],
  [50000, 50000],
  0.0009,
  [100, 100]
);
```

## 💡 Flashloan Provider Fees

| Provider | Fee | Fee Decimal | Use Case |
|----------|-----|-------------|----------|
| **Aave V3** | 0.09% | 0.0009 | Most popular, reliable |
| **dYdX** | 0% | 0 | Best for high-frequency |
| **Balancer** | 0% | 0 | No fees on flashloans |
| **Uniswap V3** | Variable | Varies | Check contract |

## ⚡ Performance Tips

1. **Batch Calculations**: Use parallel path simulation for multiple routes
2. **Cache Results**: Cache pool reserves if they don't change frequently
3. **Set Thresholds**: Define max slippage and min profit early
4. **Monitor Gas**: Include realistic gas costs in calculations

## 🎯 Decision Flow

```
1. Identify price difference between DEXs
   ↓
2. Calculate optimal flashloan amount
   ↓
3. Check if flashloan > 0 (profitable?)
   ↓ YES
4. Calculate market impact
   ↓
5. Check if impact < 5% threshold?
   ↓ YES
6. Calculate multi-hop slippage (if applicable)
   ↓
7. Verify total slippage < 10% threshold?
   ↓ YES
8. Execute arbitrage with flashloan
```

## 📈 Real-World Example

```javascript
// Complete arbitrage workflow
async function executeArbitrage() {
  // 1. Define pools (from blockchain data)
  const uniswapPool = { reserveIn: 1000000, reserveOut: 2000000 };
  const sushiswapPool = { reserveIn: 1800000, reserveOut: 1000000 };
  
  // 2. Calculate optimal flashloan
  const flashloanResult = await axios.post('http://localhost:3001/api/calculate-flashloan', {
    reserveInBuy: uniswapPool.reserveIn,
    reserveOutBuy: uniswapPool.reserveOut,
    reserveInSell: sushiswapPool.reserveIn,
    reserveOutSell: sushiswapPool.reserveOut,
    flashloanFee: 0.0009,
    gasCost: 150
  });
  
  if (!flashloanResult.data.profitable) {
    console.log('❌ Not profitable');
    return;
  }
  
  const flashloan = flashloanResult.data.flashloanAmount;
  console.log(`✅ Profitable! Flashloan: $${flashloan.toFixed(2)}`);
  
  // 3. Check market impact
  const impactResult = await axios.post('http://localhost:3001/api/calculate-impact', {
    reserveIn: uniswapPool.reserveIn,
    reserveOut: uniswapPool.reserveOut,
    tradeAmount: flashloan
  });
  
  if (impactResult.data.marketImpact > 5) {
    console.log(`⚠️ High impact: ${impactResult.data.marketImpactPct}`);
    return;
  }
  
  console.log(`✅ Market impact acceptable: ${impactResult.data.marketImpactPct}`);
  
  // 4. Calculate path slippage
  const slippageResult = await axios.post('http://localhost:3001/api/calculate-multihop-slippage', {
    path: [
      [uniswapPool.reserveIn, uniswapPool.reserveOut],
      [sushiswapPool.reserveIn, sushiswapPool.reserveOut]
    ],
    flashloanAmount: flashloan
  });
  
  if (slippageResult.data.totalSlippage > 10) {
    console.log(`⚠️ High slippage: ${slippageResult.data.totalSlippagePct}`);
    return;
  }
  
  console.log(`✅ Slippage acceptable: ${slippageResult.data.totalSlippagePct}`);
  console.log('🚀 Ready to execute!');
  
  // 5. Execute flashloan arbitrage (implementation depends on your setup)
  // executeFlashloanTrade(flashloan, ...);
}

executeArbitrage().catch(console.error);
```

## 🧪 Testing

```bash
# Test the engine
cd ultra-fast-arbitrage-engine
npm test

# Test API endpoints
cd backend
node tests/flashloan-api.test.js

# Run all tests
npm test
```

## 📚 More Information

- **Full API Documentation**: See [FLASHLOAN_API_DOCUMENTATION.md](./FLASHLOAN_API_DOCUMENTATION.md)
- **Architecture Details**: See [README.md](./README.md)
- **Deployment Guide**: See [DEPLOYMENT.md](./DEPLOYMENT.md)

## 🔒 Security Checklist

- [ ] Verify flashloan provider contract addresses
- [ ] Set maximum slippage tolerance
- [ ] Set minimum profit threshold
- [ ] Include realistic gas costs
- [ ] Monitor pool liquidity limits
- [ ] Use private mempools for large trades
- [ ] Implement circuit breakers
- [ ] Set maximum trade size limits

## ⚙️ Configuration

Default values (can be overridden):

```javascript
const DEFAULT_CONFIG = {
  flashloanFee: 0.0009,     // Aave V3: 0.09%
  gasCost: 100,             // Base gas cost in USDC
  maxSlippage: 5.0,         // 5% maximum acceptable slippage
  minProfit: 50,            // Minimum $50 profit threshold
  maxPoolImpact: 30         // Maximum 30% of pool reserves
};
```

## 🆘 Troubleshooting

**Issue**: "Cannot find module 'math_engine.node'"
```bash
cd ultra-fast-arbitrage-engine/native
cargo build --release
cp target/release/libmath_engine.so ../native/math_engine.node
```

**Issue**: "TypeError: Cannot read property 'flashloanAmount'"
- Check that all required parameters are provided
- Verify parameter types (numbers, not strings)
- Check API endpoint URL

**Issue**: "Server not responding"
```bash
# Check if server is running
curl http://localhost:3001/api/health

# Start server in demo mode
cd backend
DEMO_MODE=true npm start
```

## 📞 Support

For issues or questions:
1. Check this quick reference first
2. Review [FLASHLOAN_API_DOCUMENTATION.md](./FLASHLOAN_API_DOCUMENTATION.md)
3. Run test suite to verify installation
4. Check logs for detailed error messages
