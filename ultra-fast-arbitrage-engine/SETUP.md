# Setup Guide - Ultra-Fast Arbitrage Engine

This guide explains how to configure the Ultra-Fast Arbitrage Engine using the interactive setup script.

## Table of Contents

- [Quick Start](#quick-start)
- [Interactive Setup](#interactive-setup)
- [Configuration Options](#configuration-options)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)
- [Manual Configuration](#manual-configuration)

## Quick Start

The easiest way to configure the arbitrage engine is using the interactive setup script:

```bash
cd ultra-fast-arbitrage-engine
yarn setup
```

Or directly with Node.js:

```bash
node setup.js
```

The script will guide you through all configuration options with helpful prompts and default values.

## Interactive Setup

### What the Setup Script Does

The interactive setup script:

1. **Walks through all configuration options** - Step-by-step prompts for each setting
2. **Provides intelligent defaults** - Common values are pre-filled
3. **Creates necessary files and directories** - Automatically creates missing files
4. **Validates input** - Ensures required fields are properly configured
5. **Generates .env file** - Creates or updates your environment configuration
6. **Provides security warnings** - Reminds you about sensitive data handling
7. **Shows a summary** - Displays what was configured and next steps

### Setup Flow

The script goes through these sections in order:

#### 1. RPC Endpoint Configuration
- Primary RPC endpoint URL
- Chain ID

**Example:**
```
Primary RPC Endpoint: https://polygon-rpc.com
Chain ID: 137
```

#### 2. Pool Registry Configuration
- Path to pool registry JSON file
- Automatically creates file if it doesn't exist

**Default:** `./pool_registry.json`

#### 3. Token Equivalence Configuration
- Path to token equivalence mapping file
- Automatically creates file if it doesn't exist

**Default:** `./token_equivalence.json`

#### 4. Arbitrage Contract ABI
- Path to your arbitrage contract ABI file
- Creates template if it doesn't exist

**Default:** `./MultiDEXArbitrageCore.abi.json`

#### 5. Wallet Configuration
- Private key for transaction execution (optional, can be set later)
- Executor wallet address

**Security:** Private keys are never displayed and script warns about security

#### 6. MEV Relay Configuration
Configure MEV relays for enhanced transaction submission:
- **Flashbots** - For MEV protection and private transactions
- **Bloxroute** - For fast transaction propagation
- **Eden Network** - Alternative private relay

#### 7. Machine Learning Model
- Path to ML model file for profit prediction
- Retrain interval (number of transactions)
- TAR threshold
- Minimum training samples

**Default:** `./models/arb_ml_latest.pkl`

#### 8. Monitoring & Alerts
Configure notification channels:
- **Telegram** - Bot token and chat ID
- **Slack** - Webhook URL
- **Email** - SMTP configuration
- **Metrics** - Prometheus and health check endpoints

#### 9. Logging Configuration
- Log directory path
- Log level (debug/info/warn/error)
- Maximum log file size
- Maximum number of log files

**Default:** `./logs/`

#### 10. Automation & Scheduling
- Automated pool fetching configuration
- SDK pool loader setup

#### 11. Execution Parameters
- Minimum profit threshold (USD)
- Maximum gas price (Gwei)
- Slippage tolerance (%)
- Simulation requirement
- Maximum position size (USD)

#### 12. Risk Management
- Maximum bundle age (ms)
- Maximum retry attempts
- Token blacklist

#### 13. Database Configuration
- PostgreSQL connection settings
- Redis configuration

#### 14. Multi-Chain Configuration
- Enable/disable multi-chain support
- Individual chain endpoints (preserved from existing .env)

## Configuration Options

### Required Configuration

These settings are **required** for the arbitrage engine to function:

- `PRIMARY_RPC_ENDPOINT` or chain-specific RPC endpoints
- `CHAIN_ID` - Network chain ID
- `EXECUTOR_ADDRESS` - Your wallet address
- `EXECUTOR_PRIVATE_KEY` - Your private key (for production use)

### Optional Configuration

These settings enhance functionality but are not required:

- MEV relay configurations
- Monitoring and alerting
- Machine learning model
- Multi-chain support

### Recommended Configuration

For production use, we recommend configuring:

- At least one MEV relay (Flashbots or Bloxroute)
- Monitoring (Telegram or Slack)
- Database (PostgreSQL and Redis)
- Proper risk management parameters

## Security Considerations

### Private Keys

**NEVER commit your private key to version control!**

The setup script:
- Warns you about private key security
- Allows you to skip private key entry and set it manually later
- Recommends adding `.env` to `.gitignore`

Best practices:
1. Use environment variables for production
2. Use hardware wallets when possible
3. Regularly rotate keys
4. Use different keys for testing and production

### .env File

The `.env` file contains sensitive information. Ensure it's in your `.gitignore`:

```bash
# Add to .gitignore
.env
.env.*
!.env.example
```

### API Keys and Tokens

- Keep all API keys and tokens secure
- Use read-only keys where possible
- Regularly audit access and rotate keys

## Troubleshooting

### Setup Script Won't Run

**Problem:** `Error: Cannot find module 'readline'`
**Solution:** Update Node.js to version 20.x or higher

**Problem:** Permission denied
**Solution:** Make script executable: `chmod +x setup.js`

### Configuration Issues

**Problem:** "File not found" errors after setup
**Solution:** Run setup script again, it will create missing files

**Problem:** RPC endpoint not working
**Solution:** Verify the endpoint URL and ensure you have internet connectivity

### Build Issues After Setup

**Problem:** Build fails with missing dependencies
**Solution:** Run `yarn install` to install dependencies

**Problem:** Rust compilation errors
**Solution:** Ensure Rust 1.90.0+ is installed: `rustc --version`

## Manual Configuration

If you prefer to configure manually, create a `.env` file with these variables:

```env
# Network Configuration
PRIMARY_RPC_ENDPOINT=https://polygon-rpc.com
CHAIN_ID=137

# Wallet Configuration
EXECUTOR_PRIVATE_KEY=your_private_key_here
EXECUTOR_ADDRESS=0xYourAddress

# MEV Configuration
FLASHBOTS_RELAY_URL=https://relay.flashbots.net
BLOXROUTE_AUTH_HEADER=
EDEN_ENDPOINT=
MEV_SHARE_ENABLED=true

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=omtegrate
POSTGRES_USER=omtegrate_user
POSTGRES_PASSWORD=your_db_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Monitoring
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
ENABLE_METRICS=true
PROMETHEUS_PORT=9090
HEALTH_CHECK_PORT=8080

# ML Configuration
ML_MODEL_PATH=./models/arb_ml_latest.pkl
ML_RETRAIN_INTERVAL=100
TAR_THRESHOLD=0.4
MIN_TRAINING_SAMPLES=1000

# Execution Parameters
MIN_PROFIT_USD=10.00
MAX_GAS_PRICE_GWEI=2100
SLIPPAGE_TOLERANCE=0.5
SIMULATION_REQUIRED=true
MAX_POSITION_SIZE_USD=100000

# Risk Management
MAX_BUNDLE_AGE_MS=12000
MAX_RETRY_ATTEMPTS=3
BLACKLIST_TOKENS=

# Logging
LOG_LEVEL=info
LOG_FILE_PATH=./logs/omtegrate.log
LOG_MAX_SIZE=100M
LOG_MAX_FILES=30

# Multi-Chain Configuration
MULTI_CHAIN_ENABLED=true
```

## Next Steps

After running the setup:

1. **Verify Configuration**
   ```bash
   node verify-variables.js
   ```

2. **Build the Project**
   ```bash
   yarn run build:all
   ```

3. **Run Tests**
   ```bash
   yarn test
   ```

4. **Start the Engine**
   Follow instructions in the main README for starting the arbitrage engine.

## Getting Help

- Check the [README.md](./README.md) for general information
- See [QUICKSTART.md](./QUICKSTART.md) for quick start guide
- Review [MODULE_VERIFICATION.md](./MODULE_VERIFICATION.md) for detailed variable documentation

## Example Session

Here's what a typical setup session looks like:

```
╔══════════════════════════════════════════════════════════════╗
║  Ultra-Fast Arbitrage Engine - Interactive Setup             ║
╚══════════════════════════════════════════════════════════════╝

Welcome! This script will guide you through configuring the arbitrage engine.
Press Ctrl+C at any time to exit.

Ready to begin setup? [Y/n]: y

▶ 1. RPC Endpoint Configuration
──────────────────────────────────────────────────────────────
Configure your primary RPC endpoint for blockchain connectivity.
Use Polygon RPC (https://polygon-rpc.com)? [Y/n]: y
✓ Using default Polygon RPC endpoint
Enter Chain ID [137]: 

▶ 2. Pool Registry Configuration
──────────────────────────────────────────────────────────────
Pool registry contains DEX pool information for arbitrage detection.
Pool Registry Path [./pool_registry.json]: 
File does not exist. Create it? [Y/n]: y
✓ Created pool registry at ./pool_registry.json

[... continues through all sections ...]

▶ Writing Configuration
──────────────────────────────────────────────────────────────
✓ Configuration saved to /path/to/.env

╔══════════════════════════════════════════════════════════════╗
║  Setup Complete!                                             ║
╚══════════════════════════════════════════════════════════════╝

Configuration Summary:
──────────────────────────────────────────────────────────────

  ✓ RPC Endpoint:           https://polygon-rpc.com
  ✓ Pool Registry:          ./pool_registry.json
  ✓ Token Equivalence:      ./token_equivalence.json
  ✓ Arbitrage ABI:          ./MultiDEXArbitrageCore.abi.json
  ✓ Private Key:            Configured
  ✓ MEV Relays:             Flashbots, Bloxroute, Eden
  ✓ ML Model:               ./models/arb_ml_latest.pkl
  ✓ Monitoring:             Telegram + Slack
  ✓ Log Directory:          ./logs/
  ✓ Automation:             SDK Pool Loader

Next Steps:
──────────────────────────────────────────────────────────────

  1. Review and verify .env file for any sensitive information
  2. Run verification: node verify-variables.js
  3. Build the project: yarn run build:all
  4. Run tests: yarn test
  5. Start the arbitrage engine
```

## Advanced Topics

### Using Environment Variables Instead of .env

For production deployments, you may want to use environment variables directly:

```bash
export EXECUTOR_PRIVATE_KEY="your_key"
export PRIMARY_RPC_ENDPOINT="https://your-rpc-endpoint"
# ... other variables
```

### Docker Setup

When using Docker, pass environment variables through docker-compose.yml or docker run:

```yaml
# docker-compose.yml
services:
  arbitrage-engine:
    environment:
      - EXECUTOR_PRIVATE_KEY=${EXECUTOR_PRIVATE_KEY}
      - PRIMARY_RPC_ENDPOINT=${PRIMARY_RPC_ENDPOINT}
      # ... other variables
```

### Multiple Environments

For different environments (dev, staging, production), use separate .env files:

```bash
.env.development
.env.staging
.env.production
```

Load the appropriate file based on your environment.
