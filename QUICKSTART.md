# Quick Start Guide

Welcome to the Quant Arbitrage System: Hyperspeed X100 Edition! This guide will help you get started quickly.

---

## 🚀 One-Click Setup

### Prerequisites
- Node.js 18+ and npm/yarn
- Python 3.8+
- Docker (optional, for deployment)

### Installation

```bash
# Clone the repository
git clone https://github.com/Omni-Tech-Stack/Quant-Arbitrage-System-Hyperspeed-X100-Edition.git
cd Quant-Arbitrage-System-Hyperspeed-X100-Edition

# Install all dependencies
npm run install:all

# For Python dependencies (optional)
pip install -r requirements.txt
```

---

## ✅ Verify Installation

Run comprehensive verification to ensure everything works:

```bash
# Full system verification
npm run verify

# Or test individual components
npm run verify:backend      # Backend API tests (22 tests)
npm run test:python        # Python module tests (6 tests)
npm run test:js           # JavaScript module tests (3 tests)
```

**Expected Output:**
```
✅ All tests passed!
Backend API: 22/22 tests passed
Python Modules: 6/6 tests passed
JavaScript Modules: 3/3 tests passed
```

---

## 🎯 Quick Commands

### Pool Discovery & Analytics

```bash
# Fetch pools from 30+ DEXes across 6 chains
npm run pool:fetch

# Load deep pools via SDK (ultra-low-latency)
npm run pool:sdk

# Fetch TVL data across multiple chains
npm run tvl:fetch
```

### Orchestration & Testing

```bash
# Test the main hybrid orchestrator
npm run orchestrator:test

# Run TVL orchestrator (one-time fetch)
python3 orchestrator_tvl_hyperspeed.py --once --chains ethereum polygon

# Run TVL orchestrator (continuous mode)
python3 orchestrator_tvl_hyperspeed.py --interval 60 --chains ethereum polygon bsc
```

### Test Scripts

```bash
# Run all test scripts
python3 scripts/test_simulation.py
python3 scripts/backtesting.py
python3 scripts/monitoring.py
python3 scripts/test_registry_integrity.py
python3 scripts/test_opportunity_detector.py
python3 scripts/test_merkle_sender.py
```

---

## 🖥️ Start the System

### Development Mode

```bash
# Start backend API server
cd backend
npm start
# API available at http://localhost:3001

# In another terminal, start frontend dashboard
cd frontend
python3 -m http.server 3000
# Dashboard available at http://localhost:3000
```

### Production Deployment

```bash
# One-click deployment with Docker
./deploy.sh

# Access your system:
# Dashboard: http://localhost:3000
# Backend API: http://localhost:3001
# API Health: http://localhost:3001/api/health
```

---

## 📊 Main Components

### 1. Backend API Server

**Location:** `backend/`

The REST API with WebSocket support for real-time arbitrage data.

**Key Endpoints:**
- `GET /api/health` - System health check
- `GET /api/opportunities` - Get arbitrage opportunities
- `POST /api/opportunities` - Post new opportunity
- `GET /api/trades` - Get executed trades
- `POST /api/trades` - Record trade execution
- `POST /api/calculate-flashloan` - Calculate optimal flashloan amount
- `POST /api/calculate-impact` - Calculate market impact
- `POST /api/simulate-paths` - Simulate parallel arbitrage paths

**Start Server:**
```bash
cd backend
npm start
```

### 2. Frontend Dashboard

**Location:** `frontend/`

Real-time dashboard displaying opportunities, trades, and statistics.

**Features:**
- Live opportunity feed
- Trade history
- Performance metrics
- WebSocket real-time updates

**Start Dashboard:**
```bash
cd frontend
# Serve with any HTTP server
python3 -m http.server 3000
```

### 3. Ultra-Fast Arbitrage Engine

**Location:** `ultra-fast-arbitrage-engine/`

TypeScript + Rust engine for high-performance arbitrage calculations.

**Features:**
- Flashloan amount optimization
- Market impact prediction
- Multi-hop slippage calculation
- Parallel path simulation

**Build & Test:**
```bash
cd ultra-fast-arbitrage-engine
npm run build
npm test
```

### 4. Python Orchestration System

**Location:** Root directory + `scripts/`

Hybrid Python + Node.js orchestrator for complete arbitrage workflow.

**Main Components:**
- `main_quant_hybrid_orchestrator.py` - Main orchestrator
- `orchestrator_tvl_hyperspeed.py` - TVL fetching orchestrator
- `pool_registry_integrator.py` - Pool registry and pathfinding
- `advanced_opportunity_detection_Version1.py` - Opportunity detector
- `dex_pool_fetcher.js` - DEX pool aggregator
- `sdk_pool_loader.js` - Deep pool loader

**Run Orchestrator:**
```bash
# Test mode (validate all components)
python3 main_quant_hybrid_orchestrator.py --test

# Production mode (requires configuration)
python3 main_quant_hybrid_orchestrator.py
```

---

## 🔧 Configuration

### RPC Endpoints

Edit `config/config.py`:

```python
RPC_ENDPOINTS = {
    "ethereum": "https://eth.llamarpc.com",
    "polygon": "https://polygon-rpc.com",
    "bsc": "https://bsc-dataseed.binance.org",
    "arbitrum": "https://arb1.arbitrum.io/rpc",
}
```

### Trading Parameters

Edit `config/config.py`:

```python
MIN_PROFIT_USD = 10         # Minimum profit threshold
MAX_GAS_PRICE_GWEI = 100    # Maximum gas price
SLIPPAGE_TOLERANCE = 0.01   # 1% slippage tolerance
```

### Contract Addresses

Edit `config/addresses.py`:

```python
# Add your contract addresses
UNISWAP_V2_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
CUSTOM_ARB_CONTRACT = "0x..."
```

---

## 📈 Monitoring

### View Logs

```bash
# Trade logs
tail -f logs/trades.log

# System logs
tail -f logs/system.log

# All logs
tail -f logs/*.log
```

### Health Check

```bash
# Python monitoring script
python3 scripts/monitoring.py

# Backend API health
curl http://localhost:3001/api/health

# Check statistics
curl http://localhost:3001/api/stats
```

---

## 🧪 Testing

### Run All Tests

```bash
# Comprehensive test suite
npm run test:comprehensive

# Individual test suites
npm run test:python          # Python modules
npm run test:js             # JavaScript modules
npm run verify:backend      # Backend API
```

### Backtesting

```bash
# Run backtest on historical data
python3 scripts/backtesting.py
```

### Simulation

```bash
# Run full pipeline simulation
python3 scripts/test_simulation.py
```

---

## 📚 Documentation

- **[README.md](README.md)** - Complete system overview
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment guide
- **[TESTING.md](TESTING.md)** - Testing documentation
- **[IMPLEMENTATION_VERIFICATION.md](IMPLEMENTATION_VERIFICATION.md)** - Verification report
- **[WEB3_INTEGRATION.md](WEB3_INTEGRATION.md)** - Web3 integration guide
- **[QUICKSTART_WEB3.md](QUICKSTART_WEB3.md)** - Web3 quick start
- **[SECURITY.md](SECURITY.md)** - Security best practices

---

## 🆘 Common Issues

### Pool Registry Not Found

If you see "Registry file not found":

```bash
# Generate pool registry
npm run pool:fetch
```

### Python Module Import Errors

Ensure you're running from the root directory:

```bash
cd /path/to/Quant-Arbitrage-System-Hyperspeed-X100-Edition
python3 main_quant_hybrid_orchestrator.py --test
```

### Backend Test Failures

Ensure no other process is using port 3001:

```bash
# Check port usage
lsof -i :3001

# Kill process if needed
kill -9 <PID>
```

### Rust Module Build Errors

The Rust native module is optional. If you need it:

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Build Rust module
cd ultra-fast-arbitrage-engine
npm run build:rust
```

---

## 🤝 Support

- **GitHub Issues:** [Report bugs or request features](https://github.com/Omni-Tech-Stack/Quant-Arbitrage-System-Hyperspeed-X100-Edition/issues)
- **Documentation:** Check the `/docs` directory for detailed guides
- **Examples:** See `scripts/` directory for usage examples

---

## 🎉 Next Steps

1. ✅ Verify installation: `npm run verify`
2. ✅ Fetch pool data: `npm run pool:fetch`
3. ✅ Test orchestrator: `npm run orchestrator:test`
4. ✅ Start backend: `cd backend && npm start`
5. ✅ Start frontend: `cd frontend && python3 -m http.server 3000`
6. ✅ Deploy: `./deploy.sh`

**Happy Trading! 🚀**
