/**
 * Web3 Utilities
 * Helper functions for contract interactions and common blockchain operations
 */

const { ethers } = require('ethers');

class Web3Utilities {
  constructor(provider) {
    this.provider = provider;
  }

  /**
   * Create contract instance
   */
  getContract(address, abi, signerOrProvider = null) {
    try {
      const contractProvider = signerOrProvider || this.provider;
      const contract = new ethers.Contract(address, abi, contractProvider);
      
      return {
        success: true,
        contract
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Encode function call
   */
  encodeFunctionCall(abi, functionName, params) {
    try {
      const iface = new ethers.Interface(abi);
      const encoded = iface.encodeFunctionData(functionName, params);
      
      return {
        success: true,
        encoded,
        functionName,
        params
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Decode function result
   */
  decodeFunctionResult(abi, functionName, data) {
    try {
      const iface = new ethers.Interface(abi);
      const decoded = iface.decodeFunctionResult(functionName, data);
      
      return {
        success: true,
        decoded: Array.from(decoded),
        functionName
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Parse event logs
   */
  parseEventLog(abi, log) {
    try {
      const iface = new ethers.Interface(abi);
      const parsed = iface.parseLog(log);
      
      return {
        success: true,
        event: {
          name: parsed.name,
          signature: parsed.signature,
          args: Object.fromEntries(
            Object.entries(parsed.args).filter(([key]) => isNaN(key))
          )
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
   * Calculate contract address from deployer
   */
  getContractAddress(deployerAddress, nonce) {
    try {
      const address = ethers.getCreateAddress({
        from: deployerAddress,
        nonce: nonce
      });
      
      return {
        success: true,
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
   * Calculate CREATE2 contract address
   */
  getCreate2Address(deployer, salt, bytecode) {
    try {
      const address = ethers.getCreate2Address(deployer, salt, ethers.keccak256(bytecode));
      
      return {
        success: true,
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
   * Format units (wei to ether, etc.)
   */
  formatUnits(value, decimals = 18) {
    try {
      const formatted = ethers.formatUnits(value, decimals);
      
      return {
        success: true,
        value: value.toString(),
        formatted,
        decimals
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Parse units (ether to wei, etc.)
   */
  parseUnits(value, decimals = 18) {
    try {
      const parsed = ethers.parseUnits(value.toString(), decimals);
      
      return {
        success: true,
        value: value.toString(),
        parsed: parsed.toString(),
        decimals
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Keccak256 hash
   */
  keccak256(data) {
    try {
      const hash = ethers.keccak256(
        typeof data === 'string' && !data.startsWith('0x')
          ? ethers.toUtf8Bytes(data)
          : data
      );
      
      return {
        success: true,
        hash,
        input: data
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Solidify packed encoding
   */
  solidityPacked(types, values) {
    try {
      const packed = ethers.solidityPacked(types, values);
      
      return {
        success: true,
        packed,
        types,
        values
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * ABI encode
   */
  abiEncode(types, values) {
    try {
      const encoded = ethers.AbiCoder.defaultAbiCoder().encode(types, values);
      
      return {
        success: true,
        encoded,
        types,
        values
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * ABI decode
   */
  abiDecode(types, data) {
    try {
      const decoded = ethers.AbiCoder.defaultAbiCoder().decode(types, data);
      
      return {
        success: true,
        decoded: Array.from(decoded),
        types
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Check if address is valid
   */
  isAddress(address) {
    try {
      const isValid = ethers.isAddress(address);
      let checksummed = null;
      
      if (isValid) {
        checksummed = ethers.getAddress(address);
      }
      
      return {
        success: true,
        isValid,
        address,
        checksummed
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get function selector
   */
  getFunctionSelector(signature) {
    try {
      const selector = ethers.id(signature).slice(0, 10);
      
      return {
        success: true,
        selector,
        signature
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get event topic
   */
  getEventTopic(signature) {
    try {
      const topic = ethers.id(signature);
      
      return {
        success: true,
        topic,
        signature
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Convert to checksum address
   */
  toChecksumAddress(address) {
    try {
      const checksummed = ethers.getAddress(address);
      
      return {
        success: true,
        address: checksummed,
        original: address
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Generate random bytes
   */
  randomBytes(length) {
    try {
      const bytes = ethers.randomBytes(length);
      const hex = ethers.hexlify(bytes);
      
      return {
        success: true,
        bytes: hex,
        length
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Convert hex to UTF8
   */
  hexToUtf8(hex) {
    try {
      const utf8 = ethers.toUtf8String(hex);
      
      return {
        success: true,
        utf8,
        hex
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Convert UTF8 to hex
   */
  utf8ToHex(text) {
    try {
      const hex = ethers.hexlify(ethers.toUtf8Bytes(text));
      
      return {
        success: true,
        hex,
        text
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Verify typed data signature (EIP-712)
   */
  verifyTypedData(domain, types, value, signature) {
    try {
      const recoveredAddress = ethers.verifyTypedData(domain, types, value, signature);
      
      return {
        success: true,
        recoveredAddress,
        domain,
        types,
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
   * Get typed data hash (EIP-712)
   */
  getTypedDataHash(domain, types, value) {
    try {
      const hash = ethers.TypedDataEncoder.hash(domain, types, value);
      
      return {
        success: true,
        hash,
        domain,
        types,
        value
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }
}

module.exports = Web3Utilities;
