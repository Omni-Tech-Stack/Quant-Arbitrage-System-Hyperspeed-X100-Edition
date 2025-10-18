# ⚡ Quick Start Guide

## 🚀 Get Running in 60 Seconds

### Option 1: Docker (Easiest)

```bash
git clone https://github.com/Omni-Tech-Stack/Quant-Arbitrage-System-Hyperspeed-X100-Edition.git
cd Quant-Arbitrage-System-Hyperspeed-X100-Edition
./deploy.sh
```

**Access:** http://localhost:3000

### Option 2: Live Operations

```bash
git clone https://github.com/Omni-Tech-Stack/Quant-Arbitrage-System-Hyperspeed-X100-Edition.git
cd Quant-Arbitrage-System-Hyperspeed-X100-Edition
./launch-live.sh
```

**Stop:** `./stop-live.sh` or press Ctrl+C

---

## 📦 Pre-Built Package

Using the production tarball:

```bash
tar -xzf quant-arbitrage-system-hyperspeed-x100-v1.0.0.tar.gz
cd production
./install.sh
./deploy.sh
```

---

## 🔧 Quick Commands

```bash
# Deployment
./deploy.sh              # Docker deployment
./launch-live.sh         # Live operations
./stop-live.sh           # Stop system

# Building
./build-production.sh    # Create production package
npm run build:all        # Build all components

# Testing
npm run verify           # Run all tests
npm test                 # Quick test

# Managing
docker-compose ps        # Check status (Docker)
docker-compose logs -f   # View logs (Docker)
```

---

## 🌐 Access Points

- **Dashboard:** http://localhost:3000
- **Backend API:** http://localhost:3001
- **Health Check:** http://localhost:3001/api/health
- **Statistics:** http://localhost:3001/api/stats

---

## 🎯 Configuration (Optional)

**Demo Mode (Default):**
```bash
export DEMO_MODE=true
```

**Live Trading:**
```bash
export ETHEREUM_RPC_URL='https://mainnet.infura.io/v3/YOUR_KEY'
export POLYGON_RPC_URL='https://polygon-rpc.com'
export PRIVATE_KEY='0x...'
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Full system overview |
| [COMPLETE_DEPLOYMENT_GUIDE.md](COMPLETE_DEPLOYMENT_GUIDE.md) | Detailed deployment guide |
| [FINAL_TEST_REPORT.md](FINAL_TEST_REPORT.md) | Test results |
| [FINAL_DEPLOYMENT_SUMMARY.md](FINAL_DEPLOYMENT_SUMMARY.md) | Deployment summary |

---

## ✅ System Status

**Version:** 1.0.0  
**Status:** ✅ Production Ready  
**Test Coverage:** 88%

**Components:**
- ✅ Backend API (22/22 tests passed)
- ✅ Frontend Dashboard (fully functional)
- ✅ Arbitrage Engine (20/20 tests passed)
- ⚠️ Web3 Integration (requires RPC for full functionality)

---

## 🆘 Troubleshooting

**Port in use:**
```bash
lsof -ti:3001 | xargs kill -9
```

**Clean restart:**
```bash
docker-compose down
docker system prune -a
./deploy.sh
```

**View logs:**
```bash
tail -f logs/backend.log    # Live operations
docker-compose logs -f      # Docker deployment
```

---

**Need more info?** See [COMPLETE_DEPLOYMENT_GUIDE.md](COMPLETE_DEPLOYMENT_GUIDE.md)
