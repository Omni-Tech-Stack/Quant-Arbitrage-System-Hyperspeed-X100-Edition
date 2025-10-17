/**
 * Comprehensive Wallet Manager
 * Supports internal/external wallet management with ethers.js and web3
 */

const { ethers } = require('ethers');
const Web3 = require('web3');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

class WalletManager {
  constructor(options = {}) {
    this.walletsDir = options.walletsDir || path.join(__dirname, 'wallets');
    this.wallets = new Map();
    this.web3 = null;
    this.provider = null;
    
    // Create wallets directory if it doesn't exist
    if (!fs.existsSync(this.walletsDir)) {
      fs.mkdirSync(this.walletsDir, { recursive: true });
    }
  }

  /**
   * Initialize provider for blockchain connectivity
   */
  initializeProvider(rpcUrl) {
    this.provider = new ethers.JsonRpcProvider(rpcUrl);
    this.web3 = new Web3(new Web3.providers.HttpProvider(rpcUrl));
    return { success: true, message: 'Provider initialized' };
  }

  /**
   * Create a new internal wallet
   */
  createWallet(label = 'default') {
    try {
      const wallet = ethers.Wallet.createRandom();
      
      const walletData = {
        address: wallet.address,
        privateKey: wallet.privateKey,
        mnemonic: wallet.mnemonic.phrase,
        label: label,
        type: 'internal',
        createdAt: new Date().toISOString()
      };

      this.wallets.set(wallet.address.toLowerCase(), {
        wallet: wallet,
        data: walletData
      });

      return {
        success: true,
        address: wallet.address,
        mnemonic: wallet.mnemonic.phrase,
        label: label
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Import wallet from private key
   */
  importFromPrivateKey(privateKey, label = 'imported') {
    try {
      const wallet = new ethers.Wallet(privateKey);
      
      const walletData = {
        address: wallet.address,
        privateKey: wallet.privateKey,
        label: label,
        type: 'imported',
        createdAt: new Date().toISOString()
      };

      this.wallets.set(wallet.address.toLowerCase(), {
        wallet: wallet,
        data: walletData
      });

      return {
        success: true,
        address: wallet.address,
        label: label
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Import wallet from mnemonic
   */
  importFromMnemonic(mnemonic, label = 'imported', index = 0) {
    try {
      const wallet = ethers.Wallet.fromPhrase(mnemonic, `m/44'/60'/0'/0/${index}`);
      
      const walletData = {
        address: wallet.address,
        privateKey: wallet.privateKey,
        mnemonic: mnemonic,
        index: index,
        label: label,
        type: 'imported',
        createdAt: new Date().toISOString()
      };

      this.wallets.set(wallet.address.toLowerCase(), {
        wallet: wallet,
        data: walletData
      });

      return {
        success: true,
        address: wallet.address,
        label: label
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Connect external wallet (for read-only or signing via external tools)
   */
  connectExternalWallet(address, label = 'external') {
    try {
      // Validate and convert to checksummed address
      const normalizedAddress = ethers.getAddress(address.toLowerCase());
      
      const walletData = {
        address: normalizedAddress,
        label: label,
        type: 'external',
        createdAt: new Date().toISOString()
      };

      this.wallets.set(normalizedAddress.toLowerCase(), {
        wallet: null,
        data: walletData
      });

      return {
        success: true,
        address: normalizedAddress,
        label: label,
        type: 'external'
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get wallet by address
   */
  getWallet(address) {
    const wallet = this.wallets.get(address.toLowerCase());
    if (!wallet) {
      return { success: false, error: 'Wallet not found' };
    }
    return {
      success: true,
      wallet: wallet.data
    };
  }

  /**
   * List all wallets
   */
  listWallets() {
    const walletList = Array.from(this.wallets.values()).map(w => ({
      address: w.data.address,
      label: w.data.label,
      type: w.data.type,
      createdAt: w.data.createdAt
    }));

    return {
      success: true,
      wallets: walletList,
      count: walletList.length
    };
  }

  /**
   * Get balance for a wallet (supports both internal and external)
   */
  async getBalance(address, token = 'native') {
    try {
      if (!this.provider) {
        return { success: false, error: 'Provider not initialized' };
      }

      const normalizedAddress = ethers.getAddress(address);

      if (token === 'native' || !token) {
        const balance = await this.provider.getBalance(normalizedAddress);
        return {
          success: true,
          address: normalizedAddress,
          balance: balance.toString(),
          balanceFormatted: ethers.formatEther(balance),
          token: 'native'
        };
      } else {
        // ERC20 token balance
        const tokenContract = new ethers.Contract(
          token,
          ['function balanceOf(address) view returns (uint256)'],
          this.provider
        );
        
        const balance = await tokenContract.balanceOf(normalizedAddress);
        return {
          success: true,
          address: normalizedAddress,
          balance: balance.toString(),
          balanceFormatted: ethers.formatEther(balance),
          token: token
        };
      }
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Sign message with wallet (internal wallets only)
   */
  async signMessage(address, message) {
    try {
      const walletData = this.wallets.get(address.toLowerCase());
      
      if (!walletData || !walletData.wallet) {
        return { success: false, error: 'Wallet not found or is external' };
      }

      const signature = await walletData.wallet.signMessage(message);
      
      return {
        success: true,
        signature: signature,
        message: message,
        address: address
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Sign transaction with wallet (internal wallets only)
   */
  async signTransaction(address, transaction) {
    try {
      const walletData = this.wallets.get(address.toLowerCase());
      
      if (!walletData || !walletData.wallet) {
        return { success: false, error: 'Wallet not found or is external' };
      }

      const wallet = walletData.wallet.connect(this.provider);
      const signedTx = await wallet.signTransaction(transaction);
      
      return {
        success: true,
        signedTransaction: signedTx,
        from: address
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Export wallet (private key and mnemonic if available)
   */
  exportWallet(address, includePrivateKey = false) {
    try {
      const walletData = this.wallets.get(address.toLowerCase());
      
      if (!walletData) {
        return { success: false, error: 'Wallet not found' };
      }

      if (walletData.data.type === 'external') {
        return {
          success: true,
          address: walletData.data.address,
          label: walletData.data.label,
          type: 'external'
        };
      }

      const exportData = {
        address: walletData.data.address,
        label: walletData.data.label,
        type: walletData.data.type,
        createdAt: walletData.data.createdAt
      };

      if (includePrivateKey) {
        exportData.privateKey = walletData.data.privateKey;
        if (walletData.data.mnemonic) {
          exportData.mnemonic = walletData.data.mnemonic;
        }
      }

      return {
        success: true,
        wallet: exportData
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Save wallet to encrypted file
   */
  async saveWalletToFile(address, password) {
    try {
      const walletData = this.wallets.get(address.toLowerCase());
      
      if (!walletData || !walletData.wallet) {
        return { success: false, error: 'Wallet not found or is external' };
      }

      const encrypted = await walletData.wallet.encrypt(password);
      
      // Security: Validate address format and sanitize for filename
      const addressLower = address.toLowerCase();
      if (!ethers.isAddress(address)) {
        return { success: false, error: 'Invalid address format' };
      }
      
      // Generate safe filename using only the validated address (no path separators)
      const safeFilename = `wallet-${addressLower.replace(/[^a-z0-9]/g, '')}.json`;
      const walletsDir = path.resolve(this.walletsDir);
      const filepath = path.join(walletsDir, safeFilename);
      
      // Ensure the wallets directory exists
      if (!fs.existsSync(walletsDir)) {
        fs.mkdirSync(walletsDir, { recursive: true });
      }
      
      fs.writeFileSync(filepath, encrypted);

      return {
        success: true,
        filepath: filepath,
        filename: safeFilename
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Load wallet from encrypted file
   */
  async loadWalletFromFile(filepath, password, label = 'loaded') {
    try {
      // Security: Validate filepath to prevent path traversal
      const normalizedPath = path.normalize(filepath);
      const walletsDir = path.resolve(this.walletsDir);
      const resolvedPath = path.resolve(normalizedPath);
      
      // Ensure the file is within the wallets directory
      if (!resolvedPath.startsWith(walletsDir)) {
        return {
          success: false,
          error: 'Invalid file path: must be within wallets directory'
        };
      }
      
      // Check if file exists
      if (!fs.existsSync(resolvedPath)) {
        return {
          success: false,
          error: 'Wallet file not found'
        };
      }
      
      const encrypted = fs.readFileSync(resolvedPath, 'utf8');
      const wallet = await ethers.Wallet.fromEncryptedJson(encrypted, password);
      
      const walletData = {
        address: wallet.address,
        privateKey: wallet.privateKey,
        label: label,
        type: 'loaded',
        createdAt: new Date().toISOString()
      };

      this.wallets.set(wallet.address.toLowerCase(), {
        wallet: wallet,
        data: walletData
      });

      return {
        success: true,
        address: wallet.address,
        label: label
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Remove wallet from memory (does not delete files)
   */
  removeWallet(address) {
    try {
      const deleted = this.wallets.delete(address.toLowerCase());
      
      if (deleted) {
        return {
          success: true,
          message: 'Wallet removed from memory',
          address: address
        };
      } else {
        return {
          success: false,
          error: 'Wallet not found'
        };
      }
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get wallet count
   */
  getWalletCount() {
    return {
      success: true,
      count: this.wallets.size,
      internal: Array.from(this.wallets.values()).filter(w => w.data.type !== 'external').length,
      external: Array.from(this.wallets.values()).filter(w => w.data.type === 'external').length
    };
  }

  /**
   * Verify message signature
   */
  verifySignature(message, signature) {
    try {
      const recoveredAddress = ethers.verifyMessage(message, signature);
      return {
        success: true,
        recoveredAddress: recoveredAddress,
        message: message,
        signature: signature
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }
}

module.exports = WalletManager;
