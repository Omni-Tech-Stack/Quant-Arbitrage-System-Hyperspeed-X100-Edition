#!/bin/bash

# Installation script for Quant Arbitrage System

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Installing Quant Arbitrage System: Hyperspeed X100 Edition   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Install backend dependencies
echo "Installing backend dependencies..."
cd backend && npm install --production && cd ..

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend && npm install --production && cd ..

# Install engine dependencies (optional)
if [ -d "ultra-fast-arbitrage-engine" ]; then
    echo "Installing arbitrage engine dependencies..."
    cd ultra-fast-arbitrage-engine && npm install && cd ..
fi

echo ""
echo "✓ Installation completed successfully!"
echo ""
echo "Next steps:"
echo "  1. Review DEPLOYMENT.md for configuration options"
echo "  2. Configure your environment variables (RPC endpoints, private keys)"
echo "  3. Run './deploy.sh' to start the system with Docker"
echo "  4. Or run './launch-live.sh' for manual live operations"
echo ""
