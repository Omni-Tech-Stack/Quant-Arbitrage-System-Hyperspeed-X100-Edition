# 🚀 ONE-CLICK INSTALLATION GUIDE

## Quant Arbitrage System: Hyperspeed X100 Edition

This guide will help you install the complete unified system in one command.

---

## ⚡ Quick Install (Recommended)

### Single Command Installation

```bash
./setup.sh
```

That's it! The script will:
- ✅ Check all prerequisites (Node.js, Python, npm, pip)
- ✅ Install all Node.js dependencies (root, backend, frontend, engine)
- ✅ Install all Python dependencies
- ✅ Build all modules (TypeScript, Rust optional)
- ✅ Set up directory structure
- ✅ Verify the installation
- ✅ Display next steps and usage instructions

### First Time Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Omni-Tech-Stack/Quant-Arbitrage-System-Hyperspeed-X100-Edition.git
   cd Quant-Arbitrage-System-Hyperspeed-X100-Edition
   ```

2. **Run the setup script:**
   ```bash
   ./setup.sh
   ```

3. **Follow the on-screen instructions**

---

## 📋 Prerequisites

The setup script will check for these automatically, but you need to have them installed:

### Required
- **Node.js** (v18.0.0 or higher)
  - Download: https://nodejs.org/
  - Verify: `node --version`
- **npm** (comes with Node.js)
  - Verify: `npm --version`
- **Python** (v3.8 or higher)
  - Download: https://www.python.org/
  - Verify: `python --version`
- **pip** (comes with Python)
  - Verify: `pip3 --version`

### Optional
- **Docker** (for containerized deployment)
  - Download: https://docs.docker.com/get-docker/
  - Verify: `docker --version`
- **Git** (for version control)
  - Download: https://git-scm.com/
  - Verify: `git --version`
- **Rust/Cargo** (for native module compilation, optional)
  - Install: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
  - Verify: `cargo --version`

---

## 🔧 Manual Installation

If you prefer to install components manually:

### Step 1: Install Node.js Dependencies

```bash
# Root package
npm install

# Backend
cd backend
npm install
cd ..

# Frontend
cd frontend
npm install
cd ..

# Arbitrage Engine
cd ultra-fast-arbitrage-engine
npm install
cd ..
```

### Step 2: Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

### Step 3: Build Modules

```bash
# Build arbitrage engine
cd ultra-fast-arbitrage-engine
npm run build
cd ..
```

### Step 4: Create Directory Structure

```bash
# Create necessary directories
mkdir -p logs
mkdir -p models
```

### Step 5: Verify Installation

```bash
npm run verify
```

---

## ✅ Verify Installation

After installation, verify everything is working:

```bash
# Comprehensive verification
npm run verify

# Individual component tests
npm run verify:backend      # Backend API tests
npm run test:python         # Python module tests
npm run test:js             # JavaScript module tests
```

**Expected output:**
```
✅ All tests passed!
Backend API: 22/22 tests passed
Python Modules: 6/6 tests passed  
JavaScript Modules: 3/3 tests passed
```

---

## 🎯 Post-Installation Setup

### 1. Configure the System

Edit configuration files as needed:

```bash
# RPC endpoints and trading parameters
vim config/config.py

# Contract addresses
vim config/addresses.py

# Environment variables (copy from examples)
cp ultra-fast-arbitrage-engine/.env.example ultra-fast-arbitrage-engine/.env
vim ultra-fast-arbitrage-engine/.env
```

### 2. Train ML Models (Optional)

```bash
# Train basic ML model
python train_ml_model.py

# Train dual AI models (advanced)
python train_dual_ai_models.py --samples 1000 --validate
```

### 3. Fetch Initial Data

```bash
# Fetch pool data from DEXes
npm run pool:fetch

# Load pools via SDK
npm run pool:sdk

# Fetch TVL data
npm run tvl:fetch
```

---

## 🚀 Start the System

### Development Mode

Start backend and frontend separately for development:

```bash
# Terminal 1 - Start backend API
cd backend
npm start
# Backend running at http://localhost:3001

# Terminal 2 - Start frontend dashboard
cd frontend
python -m http.server 3000
# Dashboard running at http://localhost:3000
```

### Production Mode (Docker)

One-click deployment with Docker Compose:

```bash
./deploy.sh
```

Access your system:
- **Dashboard:** http://localhost:3000
- **Backend API:** http://localhost:3001
- **Health Check:** http://localhost:3001/api/health

---

## 📦 What Gets Installed

### Node.js Packages

**Root:**
- Development and testing utilities
- Verification scripts

**Backend (`backend/`):**
- Express.js web server
- WebSocket support (ws)
- CORS middleware
- Body parser
- UUID generation

**Frontend (`frontend/`):**
- Minimal dependencies (vanilla JS)

**Arbitrage Engine (`ultra-fast-arbitrage-engine/`):**
- TypeScript compiler
- Jest testing framework
- Rust native bindings (optional)

### Python Packages

From `requirements.txt`:
- **Data Processing:** pandas, numpy
- **Machine Learning:** scikit-learn, joblib, xgboost
- **ONNX Runtime:** onnx, onnxruntime, skl2onnx
- **Optional:** web3, eth-account, aiohttp, pytest

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

### Test Individual Components

```bash
# Backend API
cd backend
npm test

# Arbitrage engine
cd ultra-fast-arbitrage-engine
npm test

# Python modules
./test_all_python_modules.sh

# JavaScript modules
./test_all_js_modules.sh
```

---

## 🐛 Troubleshooting

### Installation Issues

**"Command not found: node"**
- Install Node.js from https://nodejs.org/
- Ensure it's in your PATH

**"Command not found: python"**
- Install Python 3.8+ from https://www.python.org/
- On some systems, use `python` instead of `python`

**"Permission denied: ./setup.sh"**
```bash
chmod +x setup.sh
./setup.sh
```

**"npm install fails"**
- Clear npm cache: `npm cache clean --force`
- Delete node_modules: `rm -rf node_modules`
- Try again: `npm install`

**"pip install fails"**
- Upgrade pip: `pip3 install --upgrade pip`
- Use virtual environment:
  ```bash
  python -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
  pip install -r requirements.txt
  ```

**"WARNING: Ignoring invalid distribution ~ympy" (Corrupted Package)**

This warning indicates a corrupted package installation (usually numpy). To fix:

1. **Option 1: Use Virtual Environment (Recommended)**
   ```bash
   # Create clean environment
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   
   # Install in clean environment
   pip install -r requirements.txt
   ```

2. **Option 2: Clean Corrupted Packages**
   ```bash
   # Uninstall corrupted packages
   pip uninstall numpy pandas scikit-learn -y
   
   # Clear cache
   pip cache purge
   
   # Reinstall
   pip install -r requirements.txt
   ```

3. **Option 3: Manual Cleanup (Windows)**
   - Navigate to: `C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python3XX\Lib\site-packages`
   - Delete folders starting with `~` (e.g., `~ympy`, `~andas`)
   - Run: `pip install -r requirements.txt`

**Best Practice:** Always use a virtual environment to avoid package conflicts and corruption.

### Runtime Issues

**"Port 3001 already in use"**
```bash
# Find and kill process using the port
lsof -ti:3001 | xargs kill -9
```

**"Module not found" errors**
```bash
# Reinstall dependencies
npm run install:all
pip3 install -r requirements.txt
```

**"Pool registry not found"**
```bash
# Generate pool registry
npm run pool:fetch
```

---

## 📂 Directory Structure

After installation, your directory structure will be:

```
Quant-Arbitrage-System-Hyperspeed-X100-Edition/
├── setup.sh                          # One-click setup script
├── deploy.sh                         # Docker deployment script
├── package.json                      # Root package configuration
├── requirements.txt                  # Python dependencies
├── docker-compose.yml                # Docker Compose configuration
│
├── backend/                          # Backend API server
│   ├── server.js                    # Express API
│   ├── package.json                 # Backend dependencies
│   ├── tests/                       # API tests
│   └── node_modules/                # Installed packages
│
├── frontend/                         # Frontend dashboard
│   ├── index.html                   # Dashboard UI
│   ├── app.js                       # Frontend logic
│   ├── styles.css                   # Styling
│   └── node_modules/                # Installed packages
│
├── ultra-fast-arbitrage-engine/     # High-performance engine
│   ├── index.ts                     # TypeScript interface
│   ├── native/                      # Rust native module
│   ├── package.json                 # Engine dependencies
│   └── node_modules/                # Installed packages
│
├── config/                           # Configuration files
│   ├── config.py                    # Main configuration
│   ├── addresses.py                 # Contract addresses
│   ├── abis.py                      # Contract ABIs
│   └── pricing.py                   # Pricing configuration
│
├── models/                           # ML models
│   ├── arb_ml_latest.pkl            # Pre-trained model
│   ├── xgboost_primary.pkl          # XGBoost model
│   ├── onnx_model.onnx              # ONNX model
│   └── DUAL_AI_README.md            # ML documentation
│
├── logs/                             # System logs
│   ├── trades.log                   # Trade execution logs
│   ├── system.log                   # System logs
│   └── *.log                        # Other logs
│
├── scripts/                          # Utility scripts
│   ├── test_simulation.py           # Simulation tests
│   ├── backtesting.py               # Backtesting
│   └── monitoring.py                # Monitoring
│
├── tests/                            # Test suites
│   └── *.py                         # Python tests
│
└── node_modules/                     # Root dependencies
```

---

## 🔒 Security Notes

### Development Environment
- ✅ System runs in demo mode by default
- ✅ No real funds at risk
- ✅ Test with simulated data

### Production Environment
Before deploying to production:
- [ ] Configure real RPC endpoints
- [ ] Add private keys securely (use environment variables)
- [ ] Enable authentication/authorization
- [ ] Set up HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Enable rate limiting
- [ ] Set up monitoring and alerts
- [ ] Review and test with small amounts first

---

## 📚 Documentation

After installation, refer to these guides:

- **[README.md](README.md)** - System overview and features
- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment guide
- **[TESTING.md](TESTING.md)** - Testing documentation
- **[WEB3_INTEGRATION.md](WEB3_INTEGRATION.md)** - Web3 integration
- **[SECURITY.md](SECURITY.md)** - Security best practices

---

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs:**
   ```bash
   tail -f logs/*.log
   ```

2. **Review documentation:**
   - Start with [QUICKSTART.md](QUICKSTART.md)
   - Check [DEPLOYMENT.md](DEPLOYMENT.md)
   - Read [TESTING.md](TESTING.md)

3. **Run diagnostics:**
   ```bash
   npm run verify
   ```

4. **Open an issue:**
   - Visit: https://github.com/Omni-Tech-Stack/Quant-Arbitrage-System-Hyperspeed-X100-Edition/issues
   - Provide error messages and logs
   - Describe your environment

---

## 🎉 Next Steps

After successful installation:

1. ✅ **Verify:** `npm run verify`
2. ✅ **Configure:** Edit `config/config.py`
3. ✅ **Train Models:** `python train_ml_model.py`
4. ✅ **Fetch Data:** `npm run pool:fetch`
5. ✅ **Deploy:** `./deploy.sh`
6. ✅ **Monitor:** Open http://localhost:3000

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

**Happy Trading! 🚀**

For the latest updates and documentation, visit:
https://github.com/Omni-Tech-Stack/Quant-Arbitrage-System-Hyperspeed-X100-Edition
