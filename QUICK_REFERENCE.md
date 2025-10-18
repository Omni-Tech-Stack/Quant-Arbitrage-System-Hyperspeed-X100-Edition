# ⚡ Quick Reference

Quick command reference for the Quant Arbitrage System: Hyperspeed X100 Edition.

---

## 🚀 Installation & Setup

```bash
# One-click installation
./setup.sh

# Verify system health
./verify-system.sh

# Or using npm
npm run verify:system
```

---

## 🧪 Testing & Verification

```bash
# Complete system verification
npm run verify:all

# Module verification
npm run verify

# Run all tests
npm run test:comprehensive

# Individual test suites
npm run test:python          # Python tests
npm run test:js              # JavaScript tests
npm run verify:backend       # Backend API tests
```

---

## 🚢 Deployment

```bash
# Docker deployment (production)
./deploy.sh

# Or using npm
npm run deploy

# Development mode - Backend
cd backend && npm start

# Development mode - Frontend
cd frontend && python3 -m http.server 3000
```

---

## 📊 Data Fetching

```bash
# Fetch pool data from 30+ DEXes
npm run pool:fetch

# Load pools via SDK (deep pools)
npm run pool:sdk

# Fetch TVL data across chains
npm run tvl:fetch
```

---

## 🎯 Orchestration

```bash
# Test orchestrator
npm run orchestrator:test

# Run orchestrator (production)
python3 main_quant_hybrid_orchestrator.py

# TVL orchestrator (once)
python3 orchestrator_tvl_hyperspeed.py --once --chains ethereum polygon

# TVL orchestrator (continuous)
python3 orchestrator_tvl_hyperspeed.py --interval 60 --chains ethereum polygon bsc
```

---

## 🤖 Machine Learning

```bash
# Train basic ML model
python3 train_ml_model.py

# Train dual AI models
python3 train_dual_ai_models.py --samples 1000 --validate

# Test dual AI system
python3 test_dual_ai_system.py
```

---

## 🔍 Monitoring & Logs

```bash
# View all logs
npm run logs

# Or manually
tail -f logs/*.log

# Backend logs
cd backend && npm run logs

# Check API health
npm run health

# Or manually
curl http://localhost:3001/api/health
```

---

## 🛠️ Development

```bash
# Install all dependencies
npm run install:all

# Build all modules
npm run build:all

# Build Rust module (optional)
npm run build:rust

# Build arbitrage engine
cd ultra-fast-arbitrage-engine && npm run build
```

---

## 📦 Package Management

```bash
# Install Node.js dependencies
npm install                                    # Root
cd backend && npm install                      # Backend
cd frontend && npm install                     # Frontend
cd ultra-fast-arbitrage-engine && npm install  # Engine

# Install Python dependencies
pip3 install -r requirements.txt
```

---

## 🧹 Cleanup

```bash
# Stop Docker containers
docker compose down

# Remove containers and volumes
docker compose down -v

# Clean node_modules
find . -name "node_modules" -type d -prune -exec rm -rf '{}' +

# Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf '{}' +
find . -type f -name "*.pyc" -delete
```

---

## 🔧 Configuration

```bash
# Edit main configuration
vim config/config.py

# Edit contract addresses
vim config/addresses.py

# Edit ABIs
vim config/abis.py

# Edit environment variables
vim ultra-fast-arbitrage-engine/.env
```

---

## 📝 Git Workflow

```bash
# Clone repository
git clone https://github.com/Omni-Tech-Stack/Quant-Arbitrage-System-Hyperspeed-X100-Edition.git
cd Quant-Arbitrage-System-Hyperspeed-X100-Edition

# Create feature branch
git checkout -b feature/your-feature

# Commit changes
git add .
git commit -m "feat: your feature description"

# Push changes
git push origin feature/your-feature
```

---

## 🐛 Troubleshooting

```bash
# Check system health
./verify-system.sh

# Reinstall dependencies
./setup.sh

# Clean and rebuild
npm run install:all
npm run build:all

# Check logs for errors
tail -f logs/system.log

# Test individual components
node dex_pool_fetcher.js
python3 pool_registry_integrator.py pool_registry.json
```

---

## 🌐 API Endpoints

**Backend API (http://localhost:3001):**

```bash
# Health check
curl http://localhost:3001/api/health

# Get statistics
curl http://localhost:3001/api/stats

# Get opportunities
curl http://localhost:3001/api/opportunities

# Get trades
curl http://localhost:3001/api/trades

# Post opportunity
curl -X POST http://localhost:3001/api/opportunities \
  -H "Content-Type: application/json" \
  -d '{"route":["TOKEN_A","TOKEN_B","TOKEN_A"],"profit":100}'

# Calculate flashloan
curl -X POST http://localhost:3001/api/calculate-flashloan \
  -H "Content-Type: application/json" \
  -d '{"targetProfit":100,"gasPrice":50}'

# Calculate market impact
curl -X POST http://localhost:3001/api/calculate-impact \
  -H "Content-Type: application/json" \
  -d '{"amount":1000,"poolDepth":100000}'
```

---

## 🎓 Help & Documentation

```bash
# Show npm commands
npm run help

# View documentation
open README.md                # System overview
open INSTALL.md               # Installation guide
open QUICKSTART.md            # Quick start
open ARCHITECTURE.md          # Architecture
open CONTRIBUTING.md          # Contribution guide

# Or visit docs directory
cd docs
ls -la
```

---

## 🔗 Useful Links

- **Repository:** https://github.com/Omni-Tech-Stack/Quant-Arbitrage-System-Hyperspeed-X100-Edition
- **Issues:** https://github.com/Omni-Tech-Stack/Quant-Arbitrage-System-Hyperspeed-X100-Edition/issues
- **Documentation:** [docs/README.md](docs/README.md)

---

## 📊 System URLs

**Local Development:**
- Dashboard: http://localhost:3000
- Backend API: http://localhost:3001
- API Health: http://localhost:3001/api/health
- API Stats: http://localhost:3001/api/stats

---

## 💡 Tips

1. **Use `npm run help`** to see all available commands
2. **Run `./verify-system.sh`** before deploying
3. **Check logs** when troubleshooting: `npm run logs`
4. **Test locally** before deploying to production
5. **Read INSTALL.md** for detailed setup instructions

---

For complete documentation, see [README.md](README.md) and [docs/README.md](docs/README.md).
