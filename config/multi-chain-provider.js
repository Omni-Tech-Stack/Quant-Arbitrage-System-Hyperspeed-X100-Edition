/**
 * Multi-Chain RPC Provider System
 * Manages RPC connections across all supported chains using .env configuration
 */

const { ethers } = require('ethers');
const { envConfig } = require('./env-config');

class MultiChainProvider {
  constructor() {
    this.providers = new Map();
    this.chainMetadata = new Map();
    this.initialized = false;
  }

  /**
   * Initialize all chain providers from environment configuration
   */
  initialize() {
    if (this.initialized) {
      return { success: true, message: 'Already initialized' };
    }

    // Load environment config
    if (!envConfig.loaded) {
      envConfig.load();
    }

    const chainEndpoints = envConfig.getChainEndpoints();
    const enabledChains = [];
    const failedChains = [];

    // Chain ID mapping (defaults, can be overridden)
    const chainIdMap = {
      'ETHEREUM': 1,
      'POLYGON': 137,
      'BSC': 56,
      'ARBITRUM': 42161,
      'OPTIMISM': 10,
      'BASE': 8453,
      'AVALANCHE': 43114,
      'FANTOM': 250,
      'CELO': 42220,
      'MOONBEAM': 1284,
      'GNOSIS': 100,
      'POLYGON_ZKEVM': 1101,
      'ZKSYNC': 324,
      'LINEA': 59144,
      'SCROLL': 534352,
      'MANTLE': 5000,
      'BLAST': 81457,
      'FRAX': 252,
      'MODE': 34443
    };

    // Process each chain
    for (const [chainName, chainData] of Object.entries(chainEndpoints)) {
      if (chainName === 'GENERAL') continue;

      // Skip if chain has no endpoints
      if (!chainData.endpoints || Object.keys(chainData.endpoints).length === 0) {
        continue;
      }

      // Only initialize enabled chains for EVM chains
      if (chainData.enabled === false) {
        continue;
      }

      try {
        // Get primary RPC endpoint (prefer HTTPS)
        const rpcUrl = this._selectBestEndpoint(chainData.endpoints);
        
        if (!rpcUrl) {
          failedChains.push({ chain: chainName, reason: 'No valid RPC endpoint' });
          continue;
        }

        // Create provider
        const provider = new ethers.JsonRpcProvider(rpcUrl);
        const chainId = chainIdMap[chainName] || 1;

        this.providers.set(chainName, provider);
        this.chainMetadata.set(chainName, {
          chainId,
          name: chainName,
          rpcUrl,
          endpoints: chainData.endpoints,
          enabled: chainData.enabled !== false
        });

        enabledChains.push(chainName);
      } catch (error) {
        failedChains.push({ chain: chainName, reason: error.message });
      }
    }

    this.initialized = true;

    return {
      success: true,
      enabledChains,
      failedChains,
      totalChains: enabledChains.length,
      message: `Initialized ${enabledChains.length} chains`
    };
  }

  /**
   * Get provider for a specific chain
   */
  getProvider(chainName) {
    if (!this.initialized) {
      this.initialize();
    }

    const provider = this.providers.get(chainName.toUpperCase());
    
    if (!provider) {
      return { 
        success: false, 
        error: `Chain ${chainName} not available or not enabled` 
      };
    }

    return {
      success: true,
      provider,
      chainId: this.chainMetadata.get(chainName.toUpperCase())?.chainId
    };
  }

  /**
   * Get all available chains
   */
  getAvailableChains() {
    if (!this.initialized) {
      this.initialize();
    }

    return Array.from(this.chainMetadata.keys());
  }

  /**
   * Get chain metadata
   */
  getChainMetadata(chainName) {
    return this.chainMetadata.get(chainName.toUpperCase()) || null;
  }

  /**
   * Test connection to a chain
   */
  async testConnection(chainName) {
    const result = this.getProvider(chainName);
    
    if (!result.success) {
      return result;
    }

    try {
      const blockNumber = await result.provider.getBlockNumber();
      return {
        success: true,
        chainName,
        blockNumber,
        connected: true
      };
    } catch (error) {
      return {
        success: false,
        chainName,
        error: error.message,
        connected: false
      };
    }
  }

  /**
   * Test all connections
   */
  async testAllConnections() {
    const results = [];
    
    for (const chainName of this.getAvailableChains()) {
      const result = await this.testConnection(chainName);
      results.push(result);
    }

    const successful = results.filter(r => r.success).length;
    const failed = results.length - successful;

    return {
      results,
      summary: {
        total: results.length,
        successful,
        failed,
        successRate: ((successful / results.length) * 100).toFixed(1) + '%'
      }
    };
  }

  /**
   * Get block number for a chain
   */
  async getBlockNumber(chainName) {
    const result = this.getProvider(chainName);
    
    if (!result.success) {
      return result;
    }

    try {
      const blockNumber = await result.provider.getBlockNumber();
      return {
        success: true,
        chainName,
        blockNumber
      };
    } catch (error) {
      return {
        success: false,
        chainName,
        error: error.message
      };
    }
  }

  /**
   * Get gas price for a chain
   */
  async getGasPrice(chainName) {
    const result = this.getProvider(chainName);
    
    if (!result.success) {
      return result;
    }

    try {
      const feeData = await result.provider.getFeeData();
      return {
        success: true,
        chainName,
        gasPrice: feeData.gasPrice ? ethers.formatUnits(feeData.gasPrice, 'gwei') : null,
        maxFeePerGas: feeData.maxFeePerGas ? ethers.formatUnits(feeData.maxFeePerGas, 'gwei') : null,
        maxPriorityFeePerGas: feeData.maxPriorityFeePerGas ? ethers.formatUnits(feeData.maxPriorityFeePerGas, 'gwei') : null
      };
    } catch (error) {
      return {
        success: false,
        chainName,
        error: error.message
      };
    }
  }

  /**
   * Get contract instance
   */
  getContract(chainName, address, abi) {
    const result = this.getProvider(chainName);
    
    if (!result.success) {
      return result;
    }

    try {
      const contract = new ethers.Contract(address, abi, result.provider);
      return {
        success: true,
        contract,
        chainName,
        address
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Private: Select best endpoint from available options
   * Priority can be configured via RPC_PROVIDER_PRIORITY env variable
   * Default: "infura,alchemy,quicknode,https,wss"
   */
  _selectBestEndpoint(endpoints) {
    // Get provider priority from environment or use default
    const priorityConfig = process.env.RPC_PROVIDER_PRIORITY || 'infura,alchemy,quicknode,https,wss';
    const priorityList = priorityConfig.split(',').map(p => p.trim().toLowerCase());
    
    // Build priority regex patterns based on configuration
    const priorities = priorityList.map(provider => {
      switch(provider) {
        case 'infura':
          return /mainnet\.https\.infura$/i;
        case 'alchemy':
          return /mainnet\.https\.alchemy$/i;
        case 'quicknode':
          return /mainnet\.https\.quicknode$/i;
        case 'https':
          return /https/i;
        case 'wss':
          return /wss/i;
        default:
          return new RegExp(provider, 'i'); // Custom pattern
      }
    });

    for (const priority of priorities) {
      for (const [key, url] of Object.entries(endpoints)) {
        if (priority.test(key) && url && url.length > 0) {
          return url;
        }
      }
    }

    // Fallback to first available endpoint
    const firstEndpoint = Object.values(endpoints).find(url => url && url.length > 0);
    return firstEndpoint || null;
  }

  /**
   * Print summary of initialized chains
   */
  printSummary() {
    console.log('\n╔═══════════════════════════════════════════════════════════╗');
    console.log('║          MULTI-CHAIN PROVIDER INITIALIZATION              ║');
    console.log('╚═══════════════════════════════════════════════════════════╝\n');

    if (!this.initialized) {
      console.log('❌ Not initialized. Call initialize() first.\n');
      return;
    }

    console.log(`Total chains configured: ${this.providers.size}\n`);

    console.log('Enabled Chains:');
    console.log('─'.repeat(60));
    
    for (const [chainName, metadata] of this.chainMetadata) {
      console.log(`  ✓ ${chainName.padEnd(20)} Chain ID: ${metadata.chainId}`);
    }

    console.log('\n');
  }
}

// Export singleton instance
const multiChainProvider = new MultiChainProvider();

module.exports = {
  MultiChainProvider,
  multiChainProvider
};
