/**
 * Environment Configuration Module
 * Centralizes all environment variable loading and validation
 * Implements support for all .env variables defined in the system
 */

const fs = require('fs');
const path = require('path');

class EnvironmentConfig {
  constructor(envPath = null) {
    this.envPath = envPath || path.join(__dirname, '..', 'ultra-fast-arbitrage-engine', '.env');
    this.config = {};
    this.loaded = false;
  }

  /**
   * Load environment variables from .env file
   */
  load() {
    try {
      if (!fs.existsSync(this.envPath)) {
        console.warn(`⚠️  .env file not found at ${this.envPath}`);
        return false;
      }

      const envContent = fs.readFileSync(this.envPath, 'utf8');
      const lines = envContent.split('\n');

      for (const line of lines) {
        // Skip comments and empty lines
        if (line.trim().startsWith('#') || !line.trim()) continue;

        // Match VAR_NAME=value or ## VAR_NAME=value
        // Note: The .env file contains escaped underscores (e.g., ETHEREUM\_MAINNET)
        // due to markdown formatting. We need to unescape them for proper variable names.
        const match = line.match(/^#*\s*([A-Z][A-Z0-9_\\]*)\s*=\s*(.*)$/);
        if (match) {
          const key = match[1].replace(/\\_/g, '_'); // Unescape markdown underscores
          const value = match[2].trim();
          
          // Don't override existing environment variables
          if (!process.env[key]) {
            process.env[key] = value;
          }
          
          this.config[key] = process.env[key];
        }
      }

      this.loaded = true;
      return true;
    } catch (error) {
      console.error(`Error loading .env file: ${error.message}`);
      return false;
    }
  }

  /**
   * Get network and chain configuration
   */
  getNetworkConfig() {
    return {
      chainId: parseInt(this.config.CHAIN_ID || '137'),
      multiChainEnabled: this.config.MULTI_CHAIN_ENABLED === 'true',
      enabledChains: this._getEnabledChains()
    };
  }

  /**
   * Get wallet and execution configuration
   */
  getWalletConfig() {
    return {
      executorPrivateKey: this.config.EXECUTOR_PRIVATE_KEY || '',
      executorAddress: this.config.EXECUTOR_ADDRESS || ''
    };
  }

  /**
   * Get DEX protocol endpoints
   */
  getDEXProtocolEndpoints() {
    return {
      uniswapV2Router: this.config.UNISWAP_V2_ROUTER || '',
      uniswapV3Router: this.config.UNISWAP_V3_ROUTER || '',
      sushiswapRouter: this.config.SUSHISWAP_ROUTER || '',
      quickswapRouter: this.config.QUICKSWAP_ROUTER || '',
      curveRegistry: this.config.CURVE_REGISTRY || '',
      balancerVault: this.config.BALANCER_VAULT || '',
      aaveV3Pool: this.config.AAVE_V3_POOL || '',
      dodoProxy: this.config.DODO_PROXY || ''
    };
  }

  /**
   * Get MEV and flashloan configuration
   */
  getMEVConfig() {
    return {
      flashbotsRelayUrl: this.config.FLASHBOTS_RELAY_URL || '',
      bloxrouteAuthHeader: this.config.BLOXROUTE_AUTH_HEADER || '',
      merkleApiKey: this.config.MERKLE_API_KEY || '',
      edenEndpoint: this.config.EDEN_ENDPOINT || '',
      privateMempoolUrls: this._parseCommaSeparated(this.config.PRIVATE_MEMPOOL_URLS),
      mevShareEnabled: this.config.MEV_SHARE_ENABLED === 'true'
    };
  }

  /**
   * Get database configuration
   */
  getDatabaseConfig() {
    return {
      postgres: {
        host: this.config.POSTGRES_HOST || 'localhost',
        port: parseInt(this.config.POSTGRES_PORT || '5432'),
        database: this.config.POSTGRES_DB || 'omtegrate',
        user: this.config.POSTGRES_USER || 'omtegrate_user',
        password: this.config.POSTGRES_PASSWORD || ''
      },
      redis: {
        host: this.config.REDIS_HOST || 'localhost',
        port: parseInt(this.config.REDIS_PORT || '6379'),
        password: this.config.REDIS_PASSWORD || ''
      }
    };
  }

  /**
   * Get notification configuration
   */
  getNotificationConfig() {
    return {
      telegram: {
        botToken: this.config.TELEGRAM_BOT_TOKEN || '',
        chatId: this.config.TELEGRAM_CHAT_ID || ''
      },
      discord: {
        webhookUrl: this.config.DISCORD_WEBHOOK_URL || ''
      }
    };
  }

  /**
   * Get ML and AI configuration
   */
  getMLConfig() {
    return {
      modelPath: this.config.ML_MODEL_PATH || './models/profit_predictor.json',
      retrainInterval: parseInt(this.config.ML_RETRAIN_INTERVAL || '100'),
      tarThreshold: parseFloat(this.config.TAR_THRESHOLD || '0.4'),
      minTrainingSamples: parseInt(this.config.MIN_TRAINING_SAMPLES || '1000')
    };
  }

  /**
   * Get execution and risk parameters
   */
  getExecutionConfig() {
    return {
      minProfitUSD: parseFloat(this.config.MIN_PROFIT_USD || '10.00'),
      maxGasPriceGwei: parseFloat(this.config.MAX_GAS_PRICE_GWEI || '2100'),
      slippageTolerance: parseFloat(this.config.SLIPPAGE_TOLERANCE || '0.5'),
      simulationRequired: this.config.SIMULATION_REQUIRED === 'true',
      maxPositionSizeUSD: parseFloat(this.config.MAX_POSITION_SIZE_USD || '100000'),
      maxBundleAgeMs: parseInt(this.config.MAX_BUNDLE_AGE_MS || '12000'),
      maxRetryAttempts: parseInt(this.config.MAX_RETRY_ATTEMPTS || '3'),
      blacklistTokens: this._parseCommaSeparated(this.config.BLACKLIST_TOKENS)
    };
  }

  /**
   * Get monitoring and logging configuration
   */
  getMonitoringConfig() {
    return {
      prometheusPort: parseInt(this.config.PROMETHEUS_PORT || '9090'),
      enableMetrics: this.config.ENABLE_METRICS === 'true',
      healthCheckPort: parseInt(this.config.HEALTH_CHECK_PORT || '8080'),
      logLevel: this.config.LOG_LEVEL || 'info',
      logFilePath: this.config.LOG_FILE_PATH || './logs/omtegrate.log',
      logMaxSize: this.config.LOG_MAX_SIZE || '100M',
      logMaxFiles: parseInt(this.config.LOG_MAX_FILES || '30')
    };
  }

  /**
   * Get swarm configuration
   */
  getSwarmConfig() {
    return {
      enabled: this.config.SWARM_ENABLED === 'true',
      redisUrl: this.config.SWARM_REDIS_URL || 'redis://localhost:6379',
      instanceId: this.config.SWARM_INSTANCE_ID || 'default',
      region: this.config.SWARM_REGION || 'us-east'
    };
  }

  /**
   * Get all chain RPC endpoints
   */
  getChainEndpoints() {
    const chains = {};
    const chainNames = [
      'ETHEREUM', 'LINEA', 'POLYGON', 'BASE', 'BLAST', 'OPTIMISM',
      'ARBITRUM', 'UNICHAIN', 'AVALANCHE', 'STARKNET', 'CELO', 'ZKSYNC',
      'BSC', 'MANTLE', 'OPBNB', 'SCROLL', 'SWELLCHAIN', 'PALM',
      'SOLANA', 'POLKADOT', 'BITCOIN', 'ABSTRACT', 'WORLD', 'SHAPE',
      'ASTAR', 'POLYGON_ZKEVM', 'ZETACHAIN', 'BERACHAIN', 'ZORA',
      'RONIN', 'PLASMA', 'SETTLUS', 'BOB', 'ROOTSTOCK', 'CLANKERMON',
      'STORY', 'HUMANITY', 'HYPEREVM', 'GALACTICA', 'LENS',
      'WORLD_MOBILE_CHAIN', 'FRAX', 'INK', 'BOTANIX', 'GNOSIS',
      'BOBA', 'SYNDICATE', 'SUPERSEED', 'FLOW_EVM', 'DEGEN',
      'POLYNOMIAL', 'MODE', 'MOONBEAM', 'APECHAIN', 'ANIME',
      'METIS', 'SONIC', 'SEI', 'SONEIUM', 'LUMIA_PRISM'
    ];

    for (const chainName of chainNames) {
      const chainData = this._getChainData(chainName);
      if (chainData.enabled !== undefined || Object.keys(chainData.endpoints).length > 0) {
        chains[chainName] = chainData;
      }
    }

    // Add general/unmapped endpoints
    chains.GENERAL = {
      endpoints: {
        httpsQuicknode: this.config.GENERAL_ENDPOINT_HTTPS_QUICKNODE || '',
        wssQuicknode: this.config.GENERAL_ENDPOINT_WSS_QUICKNODE || ''
      }
    };

    return chains;
  }

  /**
   * Get RPC endpoints for a specific chain
   */
  getChainRPCEndpoints(chainName) {
    const chainData = this._getChainData(chainName);
    return chainData.endpoints;
  }

  /**
   * Check if a chain is enabled
   */
  isChainEnabled(chainName) {
    const enabledKey = `${chainName}_MAINNET`;
    return this.config[enabledKey] === 'true';
  }

  /**
   * Get all configuration at once
   */
  getAllConfig() {
    return {
      network: this.getNetworkConfig(),
      wallet: this.getWalletConfig(),
      dexProtocols: this.getDEXProtocolEndpoints(),
      mev: this.getMEVConfig(),
      database: this.getDatabaseConfig(),
      notifications: this.getNotificationConfig(),
      ml: this.getMLConfig(),
      execution: this.getExecutionConfig(),
      monitoring: this.getMonitoringConfig(),
      swarm: this.getSwarmConfig(),
      chains: this.getChainEndpoints()
    };
  }

  /**
   * Validate required configuration
   */
  validate() {
    const errors = [];
    const warnings = [];

    // Check critical variables
    if (!this.config.EXECUTOR_ADDRESS) {
      warnings.push('EXECUTOR_ADDRESS not set');
    }

    if (!this.config.EXECUTOR_PRIVATE_KEY) {
      warnings.push('EXECUTOR_PRIVATE_KEY not set (required for transaction signing)');
    }

    // Check at least one chain is enabled
    const enabledChains = this._getEnabledChains();
    if (enabledChains.length === 0) {
      warnings.push('No chains enabled - set at least one chain to true');
    }

    // Check MEV configuration
    if (!this.config.FLASHBOTS_RELAY_URL) {
      warnings.push('FLASHBOTS_RELAY_URL not set');
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Private helper: Get enabled chains
   */
  _getEnabledChains() {
    const enabled = [];
    for (const [key, value] of Object.entries(this.config)) {
      if (key.endsWith('_MAINNET') && value === 'true') {
        enabled.push(key.replace('_MAINNET', ''));
      }
    }
    return enabled;
  }

  /**
   * Private helper: Parse comma-separated values
   */
  _parseCommaSeparated(value) {
    if (!value) return [];
    return value.split(',').map(v => v.trim()).filter(v => v);
  }

  /**
   * Private helper: Get chain data
   */
  _getChainData(chainName) {
    const data = {
      enabled: undefined,
      endpoints: {}
    };

    // Check if chain is enabled
    const enabledKey = `${chainName}_MAINNET`;
    if (this.config[enabledKey] !== undefined) {
      data.enabled = this.config[enabledKey] === 'true';
    }

    // Get endpoints for mainnet
    const endpointPrefixes = [
      `${chainName}_MAINNET_HTTPS_INFURA`,
      `${chainName}_MAINNET_WSS_INFURA`,
      `${chainName}_MAINNET_HTTPS_ALCHEMY`,
      `${chainName}_MAINNET_HTTPS_QUICKNODE`,
      `${chainName}_MAINNET_WSS_QUICKNODE`
    ];

    // Get testnet endpoints
    const testnetPrefixes = [
      `${chainName}_SEPOLIA_HTTPS_INFURA`,
      `${chainName}_SEPOLIA_WSS_INFURA`,
      `${chainName}_TESTNET_HTTPS_INFURA`,
      `${chainName}_FUJI_HTTPS_INFURA`,
      `${chainName}_FUJI_WSS_INFURA`,
      `${chainName}_ALFAJORES_HTTPS_INFURA`,
      `${chainName}_AMOY_HTTPS_INFURA`,
      `${chainName}_AMOY_WSS_INFURA`
    ];

    const allPrefixes = [...endpointPrefixes, ...testnetPrefixes];

    for (const prefix of allPrefixes) {
      if (this.config[prefix]) {
        const key = prefix.toLowerCase().replace(/_/g, '.');
        data.endpoints[key] = this.config[prefix];
      }
    }

    return data;
  }

  /**
   * Print configuration summary
   */
  printSummary() {
    console.log('\n╔═══════════════════════════════════════════════════════════╗');
    console.log('║           ENVIRONMENT CONFIGURATION SUMMARY               ║');
    console.log('╚═══════════════════════════════════════════════════════════╝\n');

    const network = this.getNetworkConfig();
    console.log('Network Configuration:');
    console.log(`  Chain ID: ${network.chainId}`);
    console.log(`  Multi-chain enabled: ${network.multiChainEnabled}`);
    console.log(`  Enabled chains: ${network.enabledChains.join(', ') || 'none'}\n`);

    const execution = this.getExecutionConfig();
    console.log('Execution Parameters:');
    console.log(`  Min Profit: $${execution.minProfitUSD}`);
    console.log(`  Max Gas Price: ${execution.maxGasPriceGwei} Gwei`);
    console.log(`  Slippage Tolerance: ${execution.slippageTolerance}%`);
    console.log(`  Simulation Required: ${execution.simulationRequired}\n`);

    const mev = this.getMEVConfig();
    console.log('MEV Configuration:');
    console.log(`  Flashbots: ${mev.flashbotsRelayUrl ? '✓' : '✗'}`);
    console.log(`  Bloxroute: ${mev.bloxrouteAuthHeader ? '✓' : '✗'}`);
    console.log(`  Merkle: ${mev.merkleApiKey ? '✓' : '✗'}`);
    console.log(`  MEV-Share: ${mev.mevShareEnabled ? '✓' : '✗'}\n`);

    const validation = this.validate();
    if (validation.warnings.length > 0) {
      console.log('⚠️  Warnings:');
      validation.warnings.forEach(w => console.log(`  - ${w}`));
    }

    console.log('\n');
  }
}

// Export singleton instance
const envConfig = new EnvironmentConfig();

module.exports = {
  EnvironmentConfig,
  envConfig
};
