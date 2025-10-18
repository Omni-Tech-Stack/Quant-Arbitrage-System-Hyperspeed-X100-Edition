# 🚀 Windows Quick Start Guide

## One-Click Installation and Deployment

This guide is specifically for **Windows users** who want to get the Quant Arbitrage System up and running with a single click.

---

## 📋 Prerequisites

Before running the system, ensure you have:

1. **Node.js 18+** installed
   - Download from: https://nodejs.org/
   - Verify: Open Command Prompt and run `node --version`

2. **Python 3.8+** (Optional, for full functionality)
   - Download from: https://www.python.org/
   - During installation, check "Add Python to PATH"
   - Verify: Open Command Prompt and run `python --version`

---

## 🎯 ONE-CLICK INSTALL AND RUN

### Method 1: Complete Installation & Launch (Recommended)

**Double-click:** `install-and-run.bat`

This will:
1. ✅ Check prerequisites
2. ✅ Install all dependencies (backend, frontend, engine)
3. ✅ Build the arbitrage engine
4. ✅ Install Python packages (if Python available)
5. ✅ Start the backend API server
6. ✅ Start the frontend dashboard
7. ✅ Open the dashboard in your browser

**That's it!** Your system will be running at:
- 📊 Dashboard: http://localhost:3000
- 🔌 Backend API: http://localhost:3001

---

## 🔧 Alternative Methods

### Method 2: Separate Installation and Run

**Step 1:** Install dependencies (one time only)
```
Double-click: install-dependencies.bat
```

**Step 2:** Start the system (every time you want to use it)
```
Double-click: run-system.bat
```

---

## 🧪 Verification & Testing

### Verify All Components

```
Double-click: verify-system.bat
```

This runs comprehensive verification including:
- ✅ Directory structure validation
- ✅ File counting and categorization
- ✅ Backend API tests (22 tests)
- ✅ Arbitrage engine tests (20 tests)
- ✅ Build verification

Expected output: "✓ ALL VALIDATIONS PASSED - SYSTEM VERIFIED!"

### Run All Tests

```
Double-click: test-all.bat
```

This runs:
- Backend API test suite
- Arbitrage engine test suite
- Python module tests (if available)

---

## 📊 Available Batch Files

| File | Purpose |
|------|---------|
| `install-and-run.bat` | **ONE-CLICK**: Install everything and start system |
| `install-dependencies.bat` | Install all dependencies only |
| `run-system.bat` | Start the system (after dependencies installed) |
| `verify-system.bat` | Verify all components are working |
| `test-all.bat` | Run all test suites |

---

## 🌐 Access Your System

After running the system:

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard** | http://localhost:3000 | Main trading dashboard with real-time data |
| **Backend API** | http://localhost:3001 | RESTful API and WebSocket server |
| **Health Check** | http://localhost:3001/api/health | System health status |
| **API Docs** | See FLASHLOAN_API_DOCUMENTATION.md | Complete API reference |

---

## 🛑 Stopping the System

To stop the system:

1. **Close the terminal windows** that opened when you started the system
   - "Quant Arbitrage Backend" window
   - "Quant Arbitrage Frontend" window

2. **Or press Ctrl+C** in each window and confirm with 'Y'

---

## 🔍 Troubleshooting

### Issue: "Node.js is not installed"

**Solution:**
1. Download Node.js from https://nodejs.org/
2. Install with default settings
3. Restart Command Prompt
4. Run the batch file again

### Issue: "Port already in use"

**Solution:**
1. Stop any existing Node.js processes
2. Open Task Manager (Ctrl+Shift+Esc)
3. End any "Node.js" processes
4. Run the batch file again

### Issue: "Python not found"

**Solution:**
- Python is optional for basic functionality
- To enable full features:
  1. Install Python from https://www.python.org/
  2. During installation, check "Add Python to PATH"
  3. Run `install-dependencies.bat` again

### Issue: "npm install fails"

**Solution:**
1. Clear npm cache: `npm cache clean --force`
2. Delete `node_modules` folders in backend, frontend, and ultra-fast-arbitrage-engine
3. Run `install-dependencies.bat` again

### Issue: "Tests are failing"

**Solution:**
1. Ensure all dependencies are installed
2. Run `install-dependencies.bat` first
3. Then run `test-all.bat`
4. Check the error messages for specific issues

---

## 📚 Additional Documentation

For detailed information, see:

- **[README.md](README.md)** - Complete system overview
- **[QUICKSTART.md](QUICKSTART.md)** - Cross-platform quick start
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Docker deployment guide
- **[TESTING.md](TESTING.md)** - Testing documentation
- **[FLASHLOAN_API_DOCUMENTATION.md](FLASHLOAN_API_DOCUMENTATION.md)** - API reference

---

## ✅ System Requirements

**Minimum:**
- Windows 10/11
- 2 CPU cores
- 4 GB RAM
- 5 GB free disk space
- Node.js 18+

**Recommended:**
- Windows 10/11
- 4+ CPU cores
- 8+ GB RAM
- 10+ GB free disk space
- Node.js 18+ LTS
- Python 3.8+

---

## 🎉 Quick Test

After installation, verify the system is working:

1. Open browser to http://localhost:3001/api/health
2. You should see: `{"status":"healthy",...}`
3. Open http://localhost:3000
4. You should see the trading dashboard

---

## 🚀 Production Deployment

For production deployment on Windows servers:

1. **Use Docker** (recommended):
   ```
   docker-compose up -d
   ```

2. **Or use PM2** for process management:
   ```
   npm install -g pm2
   pm2 start backend/server.js --name arbitrage-backend
   pm2 start frontend/server.js --name arbitrage-frontend
   ```

3. See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment guide

---

## 💡 Tips

- **First Time Users**: Use `install-and-run.bat` for the easiest experience
- **Daily Use**: Use `run-system.bat` to quickly start the system
- **After Updates**: Run `install-dependencies.bat` to update dependencies
- **Before Deployment**: Run `verify-system.bat` to ensure everything works

---

## 🆘 Support

If you encounter any issues:

1. Check this README's troubleshooting section
2. Review the error messages in the terminal windows
3. Check the [GitHub Issues](https://github.com/Omni-Tech-Stack/Quant-Arbitrage-System-Hyperspeed-X100-Edition/issues)
4. Ensure all prerequisites are correctly installed

---

## 🎊 Success!

If you see:
```
✓ ALL VALIDATIONS PASSED - SYSTEM VERIFIED!
```

And can access the dashboard at http://localhost:3000, then:

**🎉 Congratulations! Your Quant Arbitrage System is ready for use! 🎉**

---

**Happy Trading! 📈**
