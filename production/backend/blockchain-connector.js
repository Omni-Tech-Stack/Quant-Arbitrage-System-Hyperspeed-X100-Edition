/**
 * Comprehensive Blockchain Connector
 * Handles multi-chain RPC connections, transactions, and contract interactions
 */

const { ethers } = require('ethers');
const { Web3 } = require('web3');

class BlockchainConnector {
  constructor() {
    this.providers = new Map();
    this.web3Instances = new Map();
    this.defaultChain = null;
    this.chainConfigs = new Map();
  }

  /**
   * Add chain configuration
   */
  addChain(chainId, config) {
    try {
      const { name, rpcUrl, symbol, blockExplorer } = config;
      
      // Initialize ethers provider
      const provider = new ethers.JsonRpcProvider(rpcUrl);
      
      // Initialize web3 instance
      const web3 = new Web3(rpcUrl); // Fixed: Web3 accepts RPC URL directly
      
      this.providers.set(chainId, provider);
      this.web3Instances.set(chainId, web3);
      this.chainConfigs.set(chainId, {
        chainId,
        name,
        rpcUrl,
        symbol: symbol || 'ETH',
        blockExplorer: blockExplorer || ''
      });

      if (!this.defaultChain) {
        this.defaultChain = chainId;
      }

      return {
        success: true,
        chainId,
        name,
        message: 'Chain added successfully'
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get provider for a chain
   */
  getProvider(chainId = null) {
    const chain = chainId || this.defaultChain;
    const provider = this.providers.get(chain);
    
    if (!provider) {
      return { success: false, error: 'Chain not configured' };
    }

    return {
      success: true,
      provider,
      chainId: chain
    };
  }

  /**
   * Get Web3 instance for a chain
   */
  getWeb3(chainId = null) {
    const chain = chainId || this.defaultChain;
    const web3 = this.web3Instances.get(chain);
    
    if (!web3) {
      return { success: false, error: 'Chain not configured' };
    }

    return {
      success: true,
      web3,
      chainId: chain
    };
  }

  /**
   * Set default chain
   */
  setDefaultChain(chainId) {
    if (!this.providers.has(chainId)) {
      return { success: false, error: 'Chain not configured' };
    }

    this.defaultChain = chainId;
    return {
      success: true,
      defaultChain: chainId
    };
  }

  /**
   * Get chain info
   */
  async getChainInfo(chainId = null) {
    try {
      const chain = chainId || this.defaultChain;
      const provider = this.providers.get(chain);
      
      if (!provider) {
        return { success: false, error: 'Chain not configured' };
      }

      const network = await provider.getNetwork();
      const blockNumber = await provider.getBlockNumber();
      const feeData = await provider.getFeeData();
      const config = this.chainConfigs.get(chain);

      return {
        success: true,
        chainId: Number(network.chainId),
        name: config.name,
        symbol: config.symbol,
        blockNumber,
        gasPrice: feeData.gasPrice ? feeData.gasPrice.toString() : null,
        maxFeePerGas: feeData.maxFeePerGas ? feeData.maxFeePerGas.toString() : null,
        maxPriorityFeePerGas: feeData.maxPriorityFeePerGas ? feeData.maxPriorityFeePerGas.toString() : null
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get block information
   */
  async getBlock(blockNumber = 'latest', chainId = null) {
    try {
      const chain = chainId || this.defaultChain;
      const provider = this.providers.get(chain);
      
      if (!provider) {
        return { success: false, error: 'Chain not configured' };
      }

      const block = await provider.getBlock(blockNumber);
      
      return {
        success: true,
        block: {
          number: block.number,
          hash: block.hash,
          timestamp: block.timestamp,
          transactions: block.transactions.length,
          miner: block.miner,
          gasLimit: block.gasLimit.toString(),
          gasUsed: block.gasUsed.toString(),
          baseFeePerGas: block.baseFeePerGas ? block.baseFeePerGas.toString() : null
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get transaction by hash
   */
  async getTransaction(txHash, chainId = null) {
    try {
      const chain = chainId || this.defaultChain;
      const provider = this.providers.get(chain);
      
      if (!provider) {
        return { success: false, error: 'Chain not configured' };
      }

      const tx = await provider.getTransaction(txHash);
      
      if (!tx) {
        return { success: false, error: 'Transaction not found' };
      }

      return {
        success: true,
        transaction: {
          hash: tx.hash,
          from: tx.from,
          to: tx.to,
          value: tx.value.toString(),
          gasLimit: tx.gasLimit.toString(),
          gasPrice: tx.gasPrice ? tx.gasPrice.toString() : null,
          nonce: tx.nonce,
          data: tx.data,
          chainId: tx.chainId
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get transaction receipt
   */
  async getTransactionReceipt(txHash, chainId = null) {
    try {
      const chain = chainId || this.defaultChain;
      const provider = this.providers.get(chain);
      
      if (!provider) {
        return { success: false, error: 'Chain not configured' };
      }

      const receipt = await provider.getTransactionReceipt(txHash);
      
      if (!receipt) {
        return { success: false, error: 'Receipt not found' };
      }

      return {
        success: true,
        receipt: {
          transactionHash: receipt.hash,
          blockNumber: receipt.blockNumber,
          blockHash: receipt.blockHash,
          from: receipt.from,
          to: receipt.to,
          gasUsed: receipt.gasUsed.toString(),
          status: receipt.status,
          logs: receipt.logs.length
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Send transaction
   */
  async sendTransaction(signedTx, chainId = null) {
    try {
      const chain = chainId || this.defaultChain;
      const provider = this.providers.get(chain);
      
      if (!provider) {
        return { success: false, error: 'Chain not configured' };
      }

      const tx = await provider.broadcastTransaction(signedTx);
      
      return {
        success: true,
        hash: tx.hash,
        chainId: chain
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Wait for transaction confirmation
   */
  async waitForTransaction(txHash, confirmations = 1, chainId = null) {
    try {
      const chain = chainId || this.defaultChain;
      const provider = this.providers.get(chain);
      
      if (!provider) {
        return { success: false, error: 'Chain not configured' };
      }

      const receipt = await provider.waitForTransaction(txHash, confirmations);
      
      return {
        success: true,
        receipt: {
          transactionHash: receipt.hash,
          blockNumber: receipt.blockNumber,
          confirmations: receipt.confirmations,
          status: receipt.status,
          gasUsed: receipt.gasUsed.toString()
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Estimate gas for transaction
   */
  async estimateGas(transaction, chainId = null) {
    try {
      const chain = chainId || this.defaultChain;
      const provider = this.providers.get(chain);
      
      if (!provider) {
        return { success: false, error: 'Chain not configured' };
      }

      const gasEstimate = await provider.estimateGas(transaction);
      
      return {
        success: true,
        gasEstimate: gasEstimate.toString(),
        gasEstimateFormatted: gasEstimate.toString()
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Call contract function (read-only)
   */
  async call(transaction, chainId = null) {
    try {
      const chain = chainId || this.defaultChain;
      const provider = this.providers.get(chain);
      
      if (!provider) {
        return { success: false, error: 'Chain not configured' };
      }

      const result = await provider.call(transaction);
      
      return {
        success: true,
        result: result
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get ERC20 token info
   */
  async getTokenInfo(tokenAddress, chainId = null) {
    try {
      const chain = chainId || this.defaultChain;
      const provider = this.providers.get(chain);
      
      if (!provider) {
        return { success: false, error: 'Chain not configured' };
      }

      const tokenContract = new ethers.Contract(
        tokenAddress,
        [
          'function name() view returns (string)',
          'function symbol() view returns (string)',
          'function decimals() view returns (uint8)',
          'function totalSupply() view returns (uint256)'
        ],
        provider
      );

      const [name, symbol, decimals, totalSupply] = await Promise.all([
        tokenContract.name(),
        tokenContract.symbol(),
        tokenContract.decimals(),
        tokenContract.totalSupply()
      ]);

      return {
        success: true,
        token: {
          address: tokenAddress,
          name,
          symbol,
          decimals,
          totalSupply: totalSupply.toString()
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get contract code
   */
  async getCode(address, chainId = null) {
    try {
      const chain = chainId || this.defaultChain;
      const provider = this.providers.get(chain);
      
      if (!provider) {
        return { success: false, error: 'Chain not configured' };
      }

      const code = await provider.getCode(address);
      const isContract = code !== '0x';

      return {
        success: true,
        address,
        code,
        isContract
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get storage at position
   */
  async getStorageAt(address, position, chainId = null) {
    try {
      const chain = chainId || this.defaultChain;
      const provider = this.providers.get(chain);
      
      if (!provider) {
        return { success: false, error: 'Chain not configured' };
      }

      const value = await provider.getStorage(address, position);

      return {
        success: true,
        address,
        position,
        value
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * List all configured chains
   */
  listChains() {
    const chains = Array.from(this.chainConfigs.values());
    
    return {
      success: true,
      chains,
      defaultChain: this.defaultChain,
      count: chains.length
    };
  }

  /**
   * Get current gas price
   */
  async getGasPrice(chainId = null) {
    try {
      const chain = chainId || this.defaultChain;
      const provider = this.providers.get(chain);
      
      if (!provider) {
        return { success: false, error: 'Chain not configured' };
      }

      const feeData = await provider.getFeeData();

      return {
        success: true,
        gasPrice: feeData.gasPrice ? feeData.gasPrice.toString() : null,
        maxFeePerGas: feeData.maxFeePerGas ? feeData.maxFeePerGas.toString() : null,
        maxPriorityFeePerGas: feeData.maxPriorityFeePerGas ? feeData.maxPriorityFeePerGas.toString() : null,
        gasPriceGwei: feeData.gasPrice ? ethers.formatUnits(feeData.gasPrice, 'gwei') : null
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Parse transaction logs
   */
  parseLogs(logs, abi) {
    try {
      const iface = new ethers.Interface(abi);
      const parsedLogs = logs.map(log => {
        try {
          return iface.parseLog(log);
        } catch (e) {
          return null;
        }
      }).filter(log => log !== null);

      return {
        success: true,
        logs: parsedLogs
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }
}

module.exports = BlockchainConnector;
