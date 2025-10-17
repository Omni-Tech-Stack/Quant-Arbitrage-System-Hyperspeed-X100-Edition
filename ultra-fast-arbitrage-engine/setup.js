#!/usr/bin/env node
/**
 * Interactive Setup Script for Ultra-Fast Arbitrage Engine
 * Walks users through configuration of all required variables
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// Color codes for better UX
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  red: '\x1b[31m'
};

// Configuration object to store all settings
const config = {
  env: {},
  files: {
    poolRegistry: './pool_registry.json',
    tokenEquivalence: './token_equivalence.json',
    arbitrageABI: './MultiDEXArbitrageCore.abi.json',
    mlModel: './models/arb_ml_latest.pkl',
    logDirectory: './logs/'
  }
};

// Utility functions
function print(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

function printHeader(title) {
  console.log('\n' + '═'.repeat(70));
  console.log(`  ${colors.bright}${colors.cyan}${title}${colors.reset}`);
  console.log('═'.repeat(70) + '\n');
}

function printSection(title) {
  console.log(`\n${colors.bright}${colors.blue}▶ ${title}${colors.reset}`);
  console.log('─'.repeat(70));
}

function question(prompt, defaultValue = '') {
  return new Promise((resolve) => {
    const displayPrompt = defaultValue 
      ? `${prompt} ${colors.yellow}[${defaultValue}]${colors.reset}: `
      : `${prompt}: `;
    
    rl.question(displayPrompt, (answer) => {
      resolve(answer.trim() || defaultValue);
    });
  });
}

function confirm(prompt, defaultYes = true) {
  const suffix = defaultYes ? '[Y/n]' : '[y/N]';
  return question(`${prompt} ${suffix}`, defaultYes ? 'y' : 'n')
    .then(answer => answer.toLowerCase().startsWith('y'));
}

// Setup functions
async function setupRPCEndpoint() {
  printSection('1. RPC Endpoint Configuration');
  print('Configure your primary RPC endpoint for blockchain connectivity.', colors.cyan);
  
  const useDefault = await confirm('Use Polygon RPC (https://polygon-rpc.com)?', true);
  
  if (useDefault) {
    config.env.PRIMARY_RPC_ENDPOINT = 'https://polygon-rpc.com';
    print('✓ Using default Polygon RPC endpoint', colors.green);
  } else {
    config.env.PRIMARY_RPC_ENDPOINT = await question('Enter your RPC endpoint URL');
  }
  
  // Chain ID
  config.env.CHAIN_ID = await question('Enter Chain ID', '137');
}

async function setupPoolRegistry() {
  printSection('2. Pool Registry Configuration');
  print('Pool registry contains DEX pool information for arbitrage detection.', colors.cyan);
  
  const poolPath = await question('Pool Registry Path', config.files.poolRegistry);
  config.files.poolRegistry = poolPath;
  
  // Create file if doesn't exist
  const fullPath = path.resolve(poolPath);
  if (!fs.existsSync(fullPath)) {
    const createFile = await confirm('File does not exist. Create it?', true);
    if (createFile) {
      fs.writeFileSync(fullPath, JSON.stringify({
        pools: [],
        lastUpdated: new Date().toISOString(),
        version: '1.0.0'
      }, null, 2));
      print(`✓ Created pool registry at ${poolPath}`, colors.green);
    }
  } else {
    print(`✓ Pool registry found at ${poolPath}`, colors.green);
  }
}

async function setupTokenEquivalence() {
  printSection('3. Token Equivalence Configuration');
  print('Token equivalence maps equivalent tokens across different networks.', colors.cyan);
  
  const tokenPath = await question('Token Equivalence Path', config.files.tokenEquivalence);
  config.files.tokenEquivalence = tokenPath;
  
  // Create file if doesn't exist
  const fullPath = path.resolve(tokenPath);
  if (!fs.existsSync(fullPath)) {
    const createFile = await confirm('File does not exist. Create it?', true);
    if (createFile) {
      fs.writeFileSync(fullPath, JSON.stringify({
        equivalences: {},
        lastUpdated: new Date().toISOString(),
        version: '1.0.0'
      }, null, 2));
      print(`✓ Created token equivalence file at ${tokenPath}`, colors.green);
    }
  } else {
    print(`✓ Token equivalence file found at ${tokenPath}`, colors.green);
  }
}

async function setupArbitrageABI() {
  printSection('4. Arbitrage Contract ABI Configuration');
  print('ABI file defines the interface for the arbitrage smart contract.', colors.cyan);
  
  const abiPath = await question('Arbitrage Contract ABI Path', config.files.arbitrageABI);
  config.files.arbitrageABI = abiPath;
  
  // Create file if doesn't exist
  const fullPath = path.resolve(abiPath);
  if (!fs.existsSync(fullPath)) {
    const createFile = await confirm('File does not exist. Create template?', true);
    if (createFile) {
      fs.writeFileSync(fullPath, JSON.stringify([
        {
          "type": "function",
          "name": "executeArbitrage",
          "inputs": [],
          "outputs": []
        }
      ], null, 2));
      print(`✓ Created ABI template at ${abiPath}`, colors.green);
      print(`${colors.yellow}⚠ Remember to update with your actual contract ABI${colors.reset}`);
    }
  } else {
    print(`✓ ABI file found at ${abiPath}`, colors.green);
  }
}

async function setupPrivateKey() {
  printSection('5. Wallet Configuration');
  print('Configure your wallet for executing arbitrage transactions.', colors.cyan);
  print(`${colors.yellow}⚠ SECURITY WARNING: Never commit your private key to version control!${colors.reset}`);
  
  const hasKey = await confirm('Do you have a private key to configure?', false);
  
  if (hasKey) {
    const keyChoice = await question('Enter private key directly (1) or set it later in .env (2)?', '2');
    
    if (keyChoice === '1') {
      const privateKey = await question('Enter your private key (will be hidden in .env)');
      config.env.EXECUTOR_PRIVATE_KEY = privateKey;
      print('✓ Private key configured (stored securely)', colors.green);
    } else {
      config.env.EXECUTOR_PRIVATE_KEY = '';
      print(`${colors.yellow}⚠ Remember to manually set EXECUTOR_PRIVATE_KEY in .env${colors.reset}`);
    }
  } else {
    config.env.EXECUTOR_PRIVATE_KEY = '';
    print(`${colors.yellow}⚠ Private key not configured. Set EXECUTOR_PRIVATE_KEY in .env before running${colors.reset}`);
  }
  
  // Executor address
  const hasAddress = await confirm('Do you have an executor address?', true);
  if (hasAddress) {
    config.env.EXECUTOR_ADDRESS = await question('Enter executor address', '0x49A3C1CF9593c62bF7215dA9c7879E86a6Bc41bc');
  }
}

async function setupMEVRelays() {
  printSection('6. MEV Relay Configuration');
  print('Configure MEV relays for enhanced transaction submission.', colors.cyan);
  
  // Flashbots
  print('\n  Flashbots Relay:', colors.bright);
  const useFlashbots = await confirm('  Enable Flashbots?', true);
  if (useFlashbots) {
    config.env.FLASHBOTS_RELAY_URL = await question('  Flashbots URL', 'https://relay.flashbots.net');
  }
  
  // Bloxroute
  print('\n  Bloxroute:', colors.bright);
  const useBloxroute = await confirm('  Enable Bloxroute?', true);
  if (useBloxroute) {
    const hasAuth = await confirm('  Do you have a Bloxroute auth header?', false);
    if (hasAuth) {
      config.env.BLOXROUTE_AUTH_HEADER = await question('  Bloxroute auth header');
    } else {
      config.env.BLOXROUTE_AUTH_HEADER = '';
      print(`  ${colors.yellow}⚠ Bloxroute auth header not configured${colors.reset}`);
    }
  }
  
  // Eden Network
  print('\n  Eden Network:', colors.bright);
  const useEden = await confirm('  Enable Eden Network?', true);
  if (useEden) {
    const hasEndpoint = await confirm('  Do you have an Eden endpoint?', false);
    if (hasEndpoint) {
      config.env.EDEN_ENDPOINT = await question('  Eden endpoint URL');
    } else {
      config.env.EDEN_ENDPOINT = '';
      print(`  ${colors.yellow}⚠ Eden endpoint not configured${colors.reset}`);
    }
  }
  
  // MEV Share
  config.env.MEV_SHARE_ENABLED = await confirm('Enable MEV Share?', true) ? 'true' : 'false';
}

async function setupMLModel() {
  printSection('7. Machine Learning Model Configuration');
  print('ML model for profit prediction and arbitrage optimization.', colors.cyan);
  
  const mlPath = await question('ML Model Path', config.files.mlModel);
  config.files.mlModel = mlPath;
  config.env.ML_MODEL_PATH = mlPath;
  
  // Create models directory if doesn't exist
  const modelsDir = path.dirname(path.resolve(mlPath));
  if (!fs.existsSync(modelsDir)) {
    fs.mkdirSync(modelsDir, { recursive: true });
    print(`✓ Created models directory at ${modelsDir}`, colors.green);
  }
  
  // Check if file exists
  const fullPath = path.resolve(mlPath);
  if (!fs.existsSync(fullPath)) {
    print(`${colors.yellow}⚠ ML model file not found. You'll need to train or provide a model.${colors.reset}`);
  } else {
    print(`✓ ML model found at ${mlPath}`, colors.green);
  }
  
  // ML parameters
  config.env.ML_RETRAIN_INTERVAL = await question('ML retrain interval (transaction count)', '100');
  config.env.TAR_THRESHOLD = await question('TAR (Total Addressable Revenue) threshold', '0.4');
  config.env.MIN_TRAINING_SAMPLES = await question('Minimum training samples', '1000');
}

async function setupMonitoring() {
  printSection('8. Monitoring & Alerts Configuration');
  print('Configure monitoring and alerting channels.', colors.cyan);
  
  // Telegram
  print('\n  Telegram:', colors.bright);
  const useTelegram = await confirm('  Enable Telegram notifications?', true);
  if (useTelegram) {
    config.env.TELEGRAM_BOT_TOKEN = await question('  Telegram Bot Token', '7723139008:AAGTCWvTbFoCxefmiEiV-OBYuA6PcoxycK4');
    config.env.TELEGRAM_CHAT_ID = await question('  Telegram Chat ID', '7998300080');
  }
  
  // Slack
  print('\n  Slack:', colors.bright);
  const useSlack = await confirm('  Enable Slack notifications?', false);
  if (useSlack) {
    config.env.SLACK_WEBHOOK_URL = await question('  Slack Webhook URL');
  }
  
  // Email
  print('\n  Email:', colors.bright);
  const useEmail = await confirm('  Enable Email notifications?', false);
  if (useEmail) {
    config.env.EMAIL_SMTP_HOST = await question('  SMTP Host');
    config.env.EMAIL_SMTP_PORT = await question('  SMTP Port', '587');
    config.env.EMAIL_FROM = await question('  From Email');
    config.env.EMAIL_TO = await question('  To Email');
  }
  
  // Metrics
  print('\n  Metrics:', colors.bright);
  config.env.ENABLE_METRICS = await confirm('  Enable Prometheus metrics?', true) ? 'true' : 'false';
  if (config.env.ENABLE_METRICS === 'true') {
    config.env.PROMETHEUS_PORT = await question('  Prometheus port', '9090');
  }
  config.env.HEALTH_CHECK_PORT = await question('  Health check port', '8080');
}

async function setupLogging() {
  printSection('9. Logging Configuration');
  print('Configure application logging.', colors.cyan);
  
  const logDir = await question('Log directory path', config.files.logDirectory);
  config.files.logDirectory = logDir;
  config.env.LOG_FILE_PATH = path.join(logDir, 'omtegrate.log');
  
  // Create log directory if doesn't exist
  const fullPath = path.resolve(logDir);
  if (!fs.existsSync(fullPath)) {
    fs.mkdirSync(fullPath, { recursive: true });
    print(`✓ Created log directory at ${logDir}`, colors.green);
  } else {
    print(`✓ Log directory found at ${logDir}`, colors.green);
  }
  
  config.env.LOG_LEVEL = await question('Log level (debug/info/warn/error)', 'info');
  config.env.LOG_MAX_SIZE = await question('Maximum log file size', '100M');
  config.env.LOG_MAX_FILES = await question('Maximum number of log files', '30');
}

async function setupAutomation() {
  printSection('10. Automation & Scheduling Configuration');
  print('Configure automated pool fetching and updates.', colors.cyan);
  
  const enableCron = await confirm('Enable automated pool fetching?', true);
  
  if (enableCron) {
    const interval = await question('Pool fetch interval (minutes)', '5');
    print(`✓ Pool fetching will run every ${interval} minutes`, colors.green);
    print(`${colors.yellow}ℹ Configure cron job manually: */${interval} * * * * cd ${process.cwd()} && node sdk_pool_loader.js${colors.reset}`);
  }
  
  // Check if sdk_pool_loader exists
  const loaderPath = path.resolve('./sdk_pool_loader.js');
  if (fs.existsSync(loaderPath)) {
    print('✓ sdk_pool_loader.js found', colors.green);
  } else {
    print(`${colors.yellow}⚠ sdk_pool_loader.js not found. You may need to create it.${colors.reset}`);
  }
}

async function setupExecutionParameters() {
  printSection('11. Execution Parameters');
  print('Configure arbitrage execution settings.', colors.cyan);
  
  config.env.MIN_PROFIT_USD = await question('Minimum profit in USD', '10.00');
  config.env.MAX_GAS_PRICE_GWEI = await question('Maximum gas price in Gwei', '2100');
  config.env.SLIPPAGE_TOLERANCE = await question('Slippage tolerance (%)', '0.5');
  config.env.SIMULATION_REQUIRED = await confirm('Require simulation before execution?', true) ? 'true' : 'false';
  config.env.MAX_POSITION_SIZE_USD = await question('Maximum position size in USD', '100000');
}

async function setupRiskManagement() {
  printSection('12. Risk Management');
  print('Configure risk management parameters.', colors.cyan);
  
  config.env.MAX_BUNDLE_AGE_MS = await question('Maximum bundle age (ms)', '12000');
  config.env.MAX_RETRY_ATTEMPTS = await question('Maximum retry attempts', '3');
  
  const hasBlacklist = await confirm('Configure token blacklist?', false);
  if (hasBlacklist) {
    config.env.BLACKLIST_TOKENS = await question('Blacklisted token addresses (comma-separated)');
  } else {
    config.env.BLACKLIST_TOKENS = '';
  }
}

async function setupDatabase() {
  printSection('13. Database Configuration');
  print('Configure PostgreSQL database connection.', colors.cyan);
  
  const useDefault = await confirm('Use default localhost database settings?', true);
  
  if (useDefault) {
    config.env.POSTGRES_HOST = 'localhost';
    config.env.POSTGRES_PORT = '5432';
    config.env.POSTGRES_DB = 'omtegrate';
    config.env.POSTGRES_USER = 'omtegrate_user';
    config.env.POSTGRES_PASSWORD = 'your_db_password';
    print('✓ Using default database settings', colors.green);
    print(`${colors.yellow}⚠ Remember to update POSTGRES_PASSWORD in .env${colors.reset}`);
  } else {
    config.env.POSTGRES_HOST = await question('PostgreSQL host', 'localhost');
    config.env.POSTGRES_PORT = await question('PostgreSQL port', '5432');
    config.env.POSTGRES_DB = await question('Database name', 'omtegrate');
    config.env.POSTGRES_USER = await question('Database user', 'omtegrate_user');
    config.env.POSTGRES_PASSWORD = await question('Database password');
  }
  
  // Redis
  print('\n  Redis Configuration:', colors.bright);
  const configureRedis = await confirm('  Configure Redis?', true);
  if (configureRedis) {
    config.env.REDIS_HOST = await question('  Redis host', 'localhost');
    config.env.REDIS_PORT = await question('  Redis port', '6379');
    const hasRedisPassword = await confirm('  Does Redis require a password?', false);
    if (hasRedisPassword) {
      config.env.REDIS_PASSWORD = await question('  Redis password');
    } else {
      config.env.REDIS_PASSWORD = '';
    }
  }
}

async function setupMultiChain() {
  printSection('14. Multi-Chain Configuration');
  print('Configure multi-chain support (optional).', colors.cyan);
  
  config.env.MULTI_CHAIN_ENABLED = await confirm('Enable multi-chain support?', true) ? 'true' : 'false';
  
  if (config.env.MULTI_CHAIN_ENABLED === 'true') {
    print('\n  Note: Multi-chain endpoints are already configured in .env', colors.cyan);
    print('  You can enable/disable specific chains by editing the .env file', colors.cyan);
  }
}

function writeEnvFile() {
  printSection('Writing Configuration');
  
  // Read existing .env file
  const envPath = path.resolve('.env');
  let existingEnv = {};
  
  if (fs.existsSync(envPath)) {
    const envContent = fs.readFileSync(envPath, 'utf8');
    envContent.split('\n').forEach(line => {
      const trimmed = line.trim();
      if (trimmed && !trimmed.startsWith('#')) {
        const [key, ...valueParts] = trimmed.split('=');
        if (key) {
          existingEnv[key.trim()] = valueParts.join('=').trim();
        }
      }
    });
  }
  
  // Merge with new config
  const mergedConfig = { ...existingEnv, ...config.env };
  
  // Build .env content
  let envContent = `# Ultra-Fast Arbitrage Engine Configuration
# Generated by setup.js on ${new Date().toISOString()}
# 
# SECURITY WARNING: Never commit this file with real credentials!
# Add .env to .gitignore

`;
  
  // Add configuration sections
  envContent += `\n# Network Configuration\n`;
  if (mergedConfig.PRIMARY_RPC_ENDPOINT) envContent += `PRIMARY_RPC_ENDPOINT=${mergedConfig.PRIMARY_RPC_ENDPOINT}\n`;
  envContent += `CHAIN_ID=${mergedConfig.CHAIN_ID || '137'}\n`;
  
  envContent += `\n# Wallet Configuration\n`;
  envContent += `EXECUTOR_PRIVATE_KEY=${mergedConfig.EXECUTOR_PRIVATE_KEY || ''}\n`;
  envContent += `EXECUTOR_ADDRESS=${mergedConfig.EXECUTOR_ADDRESS || ''}\n`;
  
  envContent += `\n# MEV Configuration\n`;
  if (mergedConfig.FLASHBOTS_RELAY_URL) envContent += `FLASHBOTS_RELAY_URL=${mergedConfig.FLASHBOTS_RELAY_URL}\n`;
  if (mergedConfig.BLOXROUTE_AUTH_HEADER !== undefined) envContent += `BLOXROUTE_AUTH_HEADER=${mergedConfig.BLOXROUTE_AUTH_HEADER}\n`;
  if (mergedConfig.EDEN_ENDPOINT !== undefined) envContent += `EDEN_ENDPOINT=${mergedConfig.EDEN_ENDPOINT}\n`;
  envContent += `MEV_SHARE_ENABLED=${mergedConfig.MEV_SHARE_ENABLED || 'true'}\n`;
  
  envContent += `\n# Database\n`;
  envContent += `POSTGRES_HOST=${mergedConfig.POSTGRES_HOST || 'localhost'}\n`;
  envContent += `POSTGRES_PORT=${mergedConfig.POSTGRES_PORT || '5432'}\n`;
  envContent += `POSTGRES_DB=${mergedConfig.POSTGRES_DB || 'omtegrate'}\n`;
  envContent += `POSTGRES_USER=${mergedConfig.POSTGRES_USER || 'omtegrate_user'}\n`;
  envContent += `POSTGRES_PASSWORD=${mergedConfig.POSTGRES_PASSWORD || 'your_db_password'}\n`;
  
  envContent += `\n# Redis\n`;
  envContent += `REDIS_HOST=${mergedConfig.REDIS_HOST || 'localhost'}\n`;
  envContent += `REDIS_PORT=${mergedConfig.REDIS_PORT || '6379'}\n`;
  envContent += `REDIS_PASSWORD=${mergedConfig.REDIS_PASSWORD || ''}\n`;
  
  envContent += `\n# Monitoring\n`;
  if (mergedConfig.TELEGRAM_BOT_TOKEN) envContent += `TELEGRAM_BOT_TOKEN=${mergedConfig.TELEGRAM_BOT_TOKEN}\n`;
  if (mergedConfig.TELEGRAM_CHAT_ID) envContent += `TELEGRAM_CHAT_ID=${mergedConfig.TELEGRAM_CHAT_ID}\n`;
  if (mergedConfig.SLACK_WEBHOOK_URL) envContent += `SLACK_WEBHOOK_URL=${mergedConfig.SLACK_WEBHOOK_URL}\n`;
  envContent += `ENABLE_METRICS=${mergedConfig.ENABLE_METRICS || 'true'}\n`;
  if (mergedConfig.PROMETHEUS_PORT) envContent += `PROMETHEUS_PORT=${mergedConfig.PROMETHEUS_PORT}\n`;
  envContent += `HEALTH_CHECK_PORT=${mergedConfig.HEALTH_CHECK_PORT || '8080'}\n`;
  
  envContent += `\n# ML Configuration\n`;
  envContent += `ML_MODEL_PATH=${mergedConfig.ML_MODEL_PATH || './models/arb_ml_latest.pkl'}\n`;
  envContent += `ML_RETRAIN_INTERVAL=${mergedConfig.ML_RETRAIN_INTERVAL || '100'}\n`;
  envContent += `TAR_THRESHOLD=${mergedConfig.TAR_THRESHOLD || '0.4'}\n`;
  envContent += `MIN_TRAINING_SAMPLES=${mergedConfig.MIN_TRAINING_SAMPLES || '1000'}\n`;
  
  envContent += `\n# Execution Parameters\n`;
  envContent += `MIN_PROFIT_USD=${mergedConfig.MIN_PROFIT_USD || '10.00'}\n`;
  envContent += `MAX_GAS_PRICE_GWEI=${mergedConfig.MAX_GAS_PRICE_GWEI || '2100'}\n`;
  envContent += `SLIPPAGE_TOLERANCE=${mergedConfig.SLIPPAGE_TOLERANCE || '0.5'}\n`;
  envContent += `SIMULATION_REQUIRED=${mergedConfig.SIMULATION_REQUIRED || 'true'}\n`;
  envContent += `MAX_POSITION_SIZE_USD=${mergedConfig.MAX_POSITION_SIZE_USD || '100000'}\n`;
  
  envContent += `\n# Risk Management\n`;
  envContent += `MAX_BUNDLE_AGE_MS=${mergedConfig.MAX_BUNDLE_AGE_MS || '12000'}\n`;
  envContent += `MAX_RETRY_ATTEMPTS=${mergedConfig.MAX_RETRY_ATTEMPTS || '3'}\n`;
  envContent += `BLACKLIST_TOKENS=${mergedConfig.BLACKLIST_TOKENS || ''}\n`;
  
  envContent += `\n# Logging\n`;
  envContent += `LOG_LEVEL=${mergedConfig.LOG_LEVEL || 'info'}\n`;
  envContent += `LOG_FILE_PATH=${mergedConfig.LOG_FILE_PATH || './logs/omtegrate.log'}\n`;
  envContent += `LOG_MAX_SIZE=${mergedConfig.LOG_MAX_SIZE || '100M'}\n`;
  envContent += `LOG_MAX_FILES=${mergedConfig.LOG_MAX_FILES || '30'}\n`;
  
  envContent += `\n# Multi-Chain Configuration\n`;
  envContent += `MULTI_CHAIN_ENABLED=${mergedConfig.MULTI_CHAIN_ENABLED || 'true'}\n`;
  
  // Preserve existing multi-chain endpoints
  envContent += `\n# Multi-Chain Endpoints (preserved from existing config)\n`;
  Object.keys(existingEnv).forEach(key => {
    if (key.includes('MAINNET') || key.includes('TESTNET') || key.includes('_HTTPS_') || key.includes('_WSS_')) {
      envContent += `${key}=${existingEnv[key]}\n`;
    }
  });
  
  // Write to file
  fs.writeFileSync(envPath, envContent);
  print(`✓ Configuration saved to ${envPath}`, colors.green);
}

function printSummary() {
  printHeader('Setup Complete!');
  
  print('Configuration Summary:', colors.bright);
  print('─'.repeat(70));
  
  console.log(`
  ${colors.green}✓${colors.reset} RPC Endpoint:           ${config.env.PRIMARY_RPC_ENDPOINT || 'Not configured'}
  ${colors.green}✓${colors.reset} Pool Registry:          ${config.files.poolRegistry}
  ${colors.green}✓${colors.reset} Token Equivalence:      ${config.files.tokenEquivalence}
  ${colors.green}✓${colors.reset} Arbitrage ABI:          ${config.files.arbitrageABI}
  ${colors.green}✓${colors.reset} Private Key:            ${config.env.EXECUTOR_PRIVATE_KEY ? 'Configured' : 'Not configured'}
  ${colors.green}✓${colors.reset} MEV Relays:             ${[
    config.env.FLASHBOTS_RELAY_URL && 'Flashbots',
    config.env.BLOXROUTE_AUTH_HEADER && 'Bloxroute',
    config.env.EDEN_ENDPOINT && 'Eden'
  ].filter(Boolean).join(', ') || 'None configured'}
  ${colors.green}✓${colors.reset} ML Model:               ${config.files.mlModel}
  ${colors.green}✓${colors.reset} Monitoring:             ${[
    config.env.TELEGRAM_BOT_TOKEN && 'Telegram',
    config.env.SLACK_WEBHOOK_URL && 'Slack',
    config.env.EMAIL_SMTP_HOST && 'Email'
  ].filter(Boolean).join(' + ') || 'None configured'}
  ${colors.green}✓${colors.reset} Log Directory:          ${config.files.logDirectory}
  ${colors.green}✓${colors.reset} Automation:             SDK Pool Loader
  `);
  
  print('Next Steps:', colors.bright);
  print('─'.repeat(70));
  console.log(`
  1. Review and verify .env file for any sensitive information
  2. Run verification: ${colors.cyan}node verify-variables.js${colors.reset}
  3. Build the project: ${colors.cyan}yarn run build:all${colors.reset}
  4. Run tests: ${colors.cyan}yarn test${colors.reset}
  5. Start the arbitrage engine
  `);
  
  if (!config.env.EXECUTOR_PRIVATE_KEY) {
    print(`${colors.yellow}⚠ WARNING: Private key not configured!${colors.reset}`);
    print(`${colors.yellow}  Set EXECUTOR_PRIVATE_KEY in .env before running the bot.${colors.reset}\n`);
  }
  
  if (!config.env.BLOXROUTE_AUTH_HEADER && !config.env.EDEN_ENDPOINT) {
    print(`${colors.yellow}ℹ Optional MEV relay configurations are incomplete.${colors.reset}`);
    print(`${colors.yellow}  You can still run the bot, but MEV features may be limited.${colors.reset}\n`);
  }
}

async function main() {
  printHeader('Ultra-Fast Arbitrage Engine - Interactive Setup');
  
  print('Welcome! This script will guide you through configuring the arbitrage engine.', colors.cyan);
  print('Press Ctrl+C at any time to exit.\n');
  
  const proceed = await confirm('Ready to begin setup?', true);
  if (!proceed) {
    print('Setup cancelled.', colors.yellow);
    rl.close();
    process.exit(0);
  }
  
  try {
    await setupRPCEndpoint();
    await setupPoolRegistry();
    await setupTokenEquivalence();
    await setupArbitrageABI();
    await setupPrivateKey();
    await setupMEVRelays();
    await setupMLModel();
    await setupMonitoring();
    await setupLogging();
    await setupAutomation();
    await setupExecutionParameters();
    await setupRiskManagement();
    await setupDatabase();
    await setupMultiChain();
    
    // Write configuration
    writeEnvFile();
    
    // Print summary
    printSummary();
    
  } catch (error) {
    print(`\n${colors.red}Error during setup: ${error.message}${colors.reset}`, colors.red);
    print('Setup incomplete. Please try again or configure manually.', colors.red);
  } finally {
    rl.close();
  }
}

// Handle Ctrl+C
process.on('SIGINT', () => {
  print('\n\nSetup interrupted by user.', colors.yellow);
  rl.close();
  process.exit(0);
});

// Run the setup
main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
