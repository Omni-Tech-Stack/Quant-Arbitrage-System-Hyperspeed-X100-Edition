/**
 * DEX Protocol Integration Module
 * Implements connections to all DEX protocols defined in .env
 */

const { envConfig } = require('./env-config');
const { multiChainProvider } = require('./multi-chain-provider');

class DEXProtocolIntegration {
  constructor() {
    this.protocols = new Map();
    this.initialized = false;
  }

  /**
   * Initialize all DEX protocol integrations
   */
  initialize() {
    if (this.initialized) {
      return { success: true, message: 'Already initialized' };
    }

    // Load environment config
    if (!envConfig.loaded) {
      envConfig.load();
    }

    const dexEndpoints = envConfig.getDEXProtocolEndpoints();

    // Initialize each protocol
    this._initializeUniswapV2(dexEndpoints.uniswapV2Router);
    this._initializeUniswapV3(dexEndpoints.uniswapV3Router);
    this._initializeSushiSwap(dexEndpoints.sushiswapRouter);
    this._initializeQuickSwap(dexEndpoints.quickswapRouter);
    this._initializeCurve(dexEndpoints.curveRegistry);
    this._initializeBalancer(dexEndpoints.balancerVault);
    this._initializeAAVE(dexEndpoints.aaveV3Pool);
    this._initializeDODO(dexEndpoints.dodoProxy);

    this.initialized = true;

    return {
      success: true,
      protocolCount: this.protocols.size,
      protocols: Array.from(this.protocols.keys())
    };
  }

  /**
   * Initialize Uniswap V2
   */
  _initializeUniswapV2(routerAddress) {
    if (!routerAddress) return;

    const abi = [
      'function swapExactTokensForTokens(uint amountIn, uint amountOutMin, address[] calldata path, address to, uint deadline) external returns (uint[] memory amounts)',
      'function getAmountsOut(uint amountIn, address[] memory path) public view returns (uint[] memory amounts)',
      'function factory() external pure returns (address)',
      'function WETH() external pure returns (address)'
    ];

    this.protocols.set('UNISWAP_V2', {
      name: 'Uniswap V2',
      type: 'AMM',
      router: routerAddress,
      abi,
      getContract: (chainName) => this._getContract(chainName, routerAddress, abi)
    });
  }

  /**
   * Initialize Uniswap V3
   */
  _initializeUniswapV3(routerAddress) {
    if (!routerAddress) return;

    const abi = [
      'function exactInputSingle((address tokenIn, address tokenOut, uint24 fee, address recipient, uint256 deadline, uint256 amountIn, uint256 amountOutMinimum, uint160 sqrtPriceLimitX96)) external payable returns (uint256 amountOut)',
      'function exactInput((bytes path, address recipient, uint256 deadline, uint256 amountIn, uint256 amountOutMinimum)) external payable returns (uint256 amountOut)',
      'function quoteExactInputSingle((address tokenIn, address tokenOut, uint256 amountIn, uint24 fee, uint160 sqrtPriceLimitX96)) external returns (uint256 amountOut)'
    ];

    this.protocols.set('UNISWAP_V3', {
      name: 'Uniswap V3',
      type: 'Concentrated Liquidity AMM',
      router: routerAddress,
      abi,
      getContract: (chainName) => this._getContract(chainName, routerAddress, abi)
    });
  }

  /**
   * Initialize SushiSwap
   */
  _initializeSushiSwap(routerAddress) {
    if (!routerAddress) return;

    const abi = [
      'function swapExactTokensForTokens(uint amountIn, uint amountOutMin, address[] calldata path, address to, uint deadline) external returns (uint[] memory amounts)',
      'function getAmountsOut(uint amountIn, address[] memory path) public view returns (uint[] memory amounts)'
    ];

    this.protocols.set('SUSHISWAP', {
      name: 'SushiSwap',
      type: 'AMM',
      router: routerAddress,
      abi,
      getContract: (chainName) => this._getContract(chainName, routerAddress, abi)
    });
  }

  /**
   * Initialize QuickSwap
   */
  _initializeQuickSwap(routerAddress) {
    if (!routerAddress) return;

    const abi = [
      'function swapExactTokensForTokens(uint amountIn, uint amountOutMin, address[] calldata path, address to, uint deadline) external returns (uint[] memory amounts)',
      'function getAmountsOut(uint amountIn, address[] memory path) public view returns (uint[] memory amounts)'
    ];

    this.protocols.set('QUICKSWAP', {
      name: 'QuickSwap',
      type: 'AMM',
      router: routerAddress,
      abi,
      getContract: (chainName) => this._getContract(chainName, routerAddress, abi)
    });
  }

  /**
   * Initialize Curve
   */
  _initializeCurve(registryAddress) {
    if (!registryAddress) return;

    const abi = [
      'function get_pool_from_lp_token(address lp_token) external view returns (address)',
      'function get_n_coins(address pool) external view returns (uint256)',
      'function get_coins(address pool) external view returns (address[8] memory)',
      'function get_balances(address pool) external view returns (uint256[8] memory)',
      'function get_virtual_price_from_lp_token(address lp_token) external view returns (uint256)'
    ];

    this.protocols.set('CURVE', {
      name: 'Curve Finance',
      type: 'Stableswap AMM',
      registry: registryAddress,
      abi,
      getContract: (chainName) => this._getContract(chainName, registryAddress, abi)
    });
  }

  /**
   * Initialize Balancer
   */
  _initializeBalancer(vaultAddress) {
    if (!vaultAddress) return;

    const abi = [
      'function swap((bytes32 poolId, uint8 kind, address assetIn, address assetOut, uint256 amount, bytes userData), (address sender, bool fromInternalBalance, address recipient, bool toInternalBalance), uint256 limit, uint256 deadline) external returns (uint256)',
      'function getPool(bytes32 poolId) external view returns (address, uint8)',
      'function getPoolTokens(bytes32 poolId) external view returns (address[] memory tokens, uint256[] memory balances, uint256 lastChangeBlock)'
    ];

    this.protocols.set('BALANCER', {
      name: 'Balancer',
      type: 'Weighted Pool AMM',
      vault: vaultAddress,
      abi,
      getContract: (chainName) => this._getContract(chainName, vaultAddress, abi)
    });
  }

  /**
   * Initialize AAVE V3
   */
  _initializeAAVE(poolAddress) {
    if (!poolAddress) return;

    const abi = [
      'function supply(address asset, uint256 amount, address onBehalfOf, uint16 referralCode) external',
      'function withdraw(address asset, uint256 amount, address to) external returns (uint256)',
      'function borrow(address asset, uint256 amount, uint256 interestRateMode, uint16 referralCode, address onBehalfOf) external',
      'function repay(address asset, uint256 amount, uint256 rateMode, address onBehalfOf) external returns (uint256)',
      'function flashLoan(address receiverAddress, address[] calldata assets, uint256[] calldata amounts, uint256[] calldata modes, address onBehalfOf, bytes calldata params, uint16 referralCode) external',
      'function getReserveData(address asset) external view returns (uint256 configuration, uint128 liquidityIndex, uint128 variableBorrowIndex, uint128 currentLiquidityRate, uint128 currentVariableBorrowRate, uint128 currentStableBorrowRate, uint40 lastUpdateTimestamp, address aTokenAddress, address stableDebtTokenAddress, address variableDebtTokenAddress, address interestRateStrategyAddress, uint8 id)'
    ];

    this.protocols.set('AAVE_V3', {
      name: 'AAVE V3',
      type: 'Lending Protocol',
      pool: poolAddress,
      abi,
      getContract: (chainName) => this._getContract(chainName, poolAddress, abi),
      flashloanEnabled: true
    });
  }

  /**
   * Initialize DODO
   */
  _initializeDODO(proxyAddress) {
    if (!proxyAddress) return;

    const abi = [
      'function dodoSwapV2TokenToToken(address fromToken, address toToken, uint256 fromTokenAmount, uint256 minReturnAmount, address[] memory dodoPairs, uint256 directions, bool isIncentive, uint256 deadLine) external returns (uint256 returnAmount)',
      'function dodoSwapV1(address fromToken, address toToken, uint256 fromTokenAmount, uint256 minReturnAmount, address[] memory dodoPairs, uint256 directions, bool isIncentive, uint256 deadLine) external returns (uint256 returnAmount)'
    ];

    this.protocols.set('DODO', {
      name: 'DODO',
      type: 'PMM (Proactive Market Maker)',
      proxy: proxyAddress,
      abi,
      getContract: (chainName) => this._getContract(chainName, proxyAddress, abi)
    });
  }

  /**
   * Get protocol instance
   */
  getProtocol(protocolName) {
    if (!this.initialized) {
      this.initialize();
    }

    const protocol = this.protocols.get(protocolName.toUpperCase());
    
    if (!protocol) {
      return {
        success: false,
        error: `Protocol ${protocolName} not configured`
      };
    }

    return {
      success: true,
      protocol
    };
  }

  /**
   * Get all available protocols
   */
  getAvailableProtocols() {
    if (!this.initialized) {
      this.initialize();
    }

    return Array.from(this.protocols.entries()).map(([key, value]) => ({
      id: key,
      name: value.name,
      type: value.type
    }));
  }

  /**
   * Get contract for protocol on specific chain
   */
  getProtocolContract(protocolName, chainName) {
    const protocolResult = this.getProtocol(protocolName);
    
    if (!protocolResult.success) {
      return protocolResult;
    }

    return protocolResult.protocol.getContract(chainName);
  }

  /**
   * Check if protocol supports flashloans
   */
  supportsFlashloans(protocolName) {
    const protocolResult = this.getProtocol(protocolName);
    
    if (!protocolResult.success) {
      return false;
    }

    return protocolResult.protocol.flashloanEnabled === true;
  }

  /**
   * Private: Get contract instance
   */
  _getContract(chainName, address, abi) {
    // Ensure multi-chain provider is initialized
    if (!multiChainProvider.initialized) {
      multiChainProvider.initialize();
    }

    return multiChainProvider.getContract(chainName, address, abi);
  }

  /**
   * Print summary
   */
  printSummary() {
    console.log('\n╔═══════════════════════════════════════════════════════════╗');
    console.log('║           DEX PROTOCOL INTEGRATION SUMMARY                ║');
    console.log('╚═══════════════════════════════════════════════════════════╝\n');

    if (!this.initialized) {
      console.log('❌ Not initialized. Call initialize() first.\n');
      return;
    }

    console.log(`Total protocols configured: ${this.protocols.size}\n`);

    console.log('Configured Protocols:');
    console.log('─'.repeat(60));
    
    for (const protocol of this.protocols.values()) {
      const flashloan = protocol.flashloanEnabled ? ' (Flashloan ✓)' : '';
      console.log(`  ✓ ${protocol.name.padEnd(20)} ${protocol.type}${flashloan}`);
    }

    console.log('\n');
  }
}

// Export singleton instance
const dexProtocolIntegration = new DEXProtocolIntegration();

module.exports = {
  DEXProtocolIntegration,
  dexProtocolIntegration
};
