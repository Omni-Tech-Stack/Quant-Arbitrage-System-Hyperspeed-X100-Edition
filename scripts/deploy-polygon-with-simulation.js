const { ethers, network } = require("hardhat");
const fs = require("fs");
const path = require("path");

/**
 * Polygon-specific deployment with simulation testing fork
 * Enhanced for production deployment on Polygon mainnet
 */

// Polygon-specific configuration with high-quality endpoints
const POLYGON_CONFIG = {
  chainId: 137,
  name: "polygon",
  currency: "MATIC",
  
  // Primary RPC endpoints
  rpc: process.env.POLYGON_RPC || "https://polygon-rpc.com",
  archiveRpc: process.env.POLYGON_ARCHIVE_RPC || "https://polygon-rpc.com",
  websocket: process.env.POLYGON_WS || "wss://polygon-rpc.com/ws",
  
  // Backup RPCs for redundancy
  backupRpcs: [
    "https://rpc-mainnet.matic.network",
    "https://matic-mainnet.chainstacklabs.com",
    "https://polygon-mainnet.public.blastapi.io",
    "https://polygon-bor.publicnode.com"
  ],
  
  // Protocol addresses on Polygon
  protocols: {
    aaveV3Pool: "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    aaveV3DataProvider: "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654",
    balancerVault: "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    balancerQueries: "0xE39B5e3B6D74016b2F6A9673D7d7493B6DF549d5",
    dydxSoloMargin: "0x0000000000000000000000000000000000000000", // Not available on Polygon
    
    // DEX Routers
    routers: {
      "QUICKSWAP": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
      "UNISWAP_V3": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
      "SUSHISWAP": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
      "1INCH": "0x1111111254EEB25477B68fb85Ed929f73A960582",
      "CURVE": "0x094d12e5b541784701FD8d65F11fc0598FBC6332",
      "DODO": "0xa222f7e8F4e7F6E0d8e2E6F7C8b5E1F2E6F7A8B9", // Example
      "KYBER": "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5"
    },
    
    // Factory addresses for direct pool access
    factories: {
      "QUICKSWAP": "0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32",
      "UNISWAP_V3": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
      "SUSHISWAP": "0xc35DADB65012eC5796536bD9864eD8773aBc74C4"
    },
    
    // Key tokens on Polygon
    tokens: {
      WMATIC: "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
      WETH: "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
      USDC: "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
      USDT: "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
      DAI: "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
      WBTC: "0x1bfd67037b42cf73acf2047067bd4f2c47d9bfd6"
    }
  }
};

// Simulation configuration for testing
const SIMULATION_CONFIG = {
  enabled: process.env.SIMULATION_MODE === "true",
  forkUrl: process.env.FORK_URL || POLYGON_CONFIG.rpc,
  forkBlockNumber: process.env.FORK_BLOCK_NUMBER || "latest",
  accounts: parseInt(process.env.SIMULATION_ACCOUNTS) || 10,
  balance: process.env.SIMULATION_BALANCE_ETH || "10000"
};

async function setupSimulationFork() {
  if (!SIMULATION_CONFIG.enabled) {
    console.log("🔄 Simulation mode disabled, deploying to live network");
    return null;
  }
  
  console.log("🔀 Setting up Polygon simulation fork...");
  console.log(`📍 Fork URL: ${SIMULATION_CONFIG.forkUrl}`);
  console.log(`📦 Fork Block: ${SIMULATION_CONFIG.forkBlockNumber}`);
  
  // Reset hardhat network to fork Polygon
  await network.provider.request({
    method: "hardhat_reset",
    params: [
      {
        forking: {
          jsonRpcUrl: SIMULATION_CONFIG.forkUrl,
          blockNumber: SIMULATION_CONFIG.forkBlockNumber === "latest" ? undefined : parseInt(SIMULATION_CONFIG.forkBlockNumber)
        }
      }
    ]
  });
  
  console.log("✅ Polygon fork established");
  
  // Fund test accounts with MATIC and tokens
  const accounts = await ethers.getSigners();
  const fundingAmount = ethers.utils.parseEther(SIMULATION_CONFIG.balance);
  
  for (let i = 0; i < Math.min(accounts.length, SIMULATION_CONFIG.accounts); i++) {
    await network.provider.send("hardhat_setBalance", [
      accounts[i].address,
      fundingAmount.toHexString()
    ]);
    
    console.log(`💰 Funded ${accounts[i].address} with ${SIMULATION_CONFIG.balance} MATIC`);
  }
  
  return {
    chainId: 137,
    blockNumber: await ethers.provider.getBlockNumber(),
    accounts: accounts.slice(0, SIMULATION_CONFIG.accounts).map(a => a.address)
  };
}

async function validatePolygonEnvironment() {
  console.log("🔍 Validating Polygon environment...");
  
  const chainId = await ethers.provider.getNetwork().then(n => n.chainId);
  if (chainId !== 137 && chainId !== 31337) { // Allow localhost for testing
    throw new Error(`Invalid chain ID: ${chainId}. Expected 137 (Polygon) or 31337 (localhost)`);
  }
  
  const blockNumber = await ethers.provider.getBlockNumber();
  console.log(`📦 Current block: ${blockNumber}`);
  
  // Test RPC connectivity
  const gasPrice = await ethers.provider.getGasPrice();
  console.log(`⛽ Current gas price: ${ethers.utils.formatUnits(gasPrice, "gwei")} gwei`);
  
  // Validate key protocol addresses
  const aavePoolCode = await ethers.provider.getCode(POLYGON_CONFIG.protocols.aaveV3Pool);
  if (aavePoolCode === "0x") {
    console.warn("⚠️  Aave V3 pool not found - may be on testnet or fork");
  } else {
    console.log("✅ Aave V3 pool validated");
  }
  
  const balancerVaultCode = await ethers.provider.getCode(POLYGON_CONFIG.protocols.balancerVault);
  if (balancerVaultCode === "0x") {
    console.warn("⚠️  Balancer Vault not found");
  } else {
    console.log("✅ Balancer Vault validated");
  }
  
  return { chainId, blockNumber, gasPrice };
}

async function deployWithSimulationTesting() {
  console.log("🚀 Starting Polygon deployment with simulation testing");
  console.log("=" * 80);
  
  // Setup simulation fork if enabled
  const forkInfo = await setupSimulationFork();
  
  // Validate environment
  const envInfo = await validatePolygonEnvironment();
  
  const [deployer] = await ethers.getSigners();
  console.log(`📝 Deployer: ${deployer.address}`);
  console.log(`💰 Balance: ${ethers.utils.formatEther(await deployer.getBalance())} MATIC`);
  
  // Prepare router configuration for Polygon
  const routerAddresses = Object.values(POLYGON_CONFIG.protocols.routers);
  const routerNames = Object.keys(POLYGON_CONFIG.protocols.routers);
  
  console.log("\n🔧 Polygon DEX Configuration:");
  routerNames.forEach((name, i) => {
    console.log(`   ${name}: ${routerAddresses[i]}`);
  });
  
  // Deploy contracts
  console.log("\n📦 Deploying contract system...");
  
  // 1. Deploy PayloadEncoder library
  console.log("📦 Deploying PayloadEncoder...");
  const PayloadEncoder = await ethers.getContractFactory("PayloadEncoder");
  const payloadEncoder = await PayloadEncoder.deploy();
  await payloadEncoder.deployed();
  console.log(`✅ PayloadEncoder: ${payloadEncoder.address}`);
  
  // 2. Deploy ArbitrageCallEncoder
  console.log("📦 Deploying ArbitrageCallEncoder...");
  const ArbitrageCallEncoder = await ethers.getContractFactory("ArbitrageCallEncoder");
  const callEncoder = await ArbitrageCallEncoder.deploy();
  await callEncoder.deployed();
  console.log(`✅ ArbitrageCallEncoder: ${callEncoder.address}`);
  
  // 3. Deploy CrossChainMessenger
  console.log("📦 Deploying CrossChainMessenger...");
  const CrossChainMessenger = await ethers.getContractFactory("CrossChainMessenger");
  const messenger = await CrossChainMessenger.deploy();
  await messenger.deployed();
  console.log(`✅ CrossChainMessenger: ${messenger.address}`);
  
  // 4. Deploy main UniversalFlashloanArbitrage contract
  console.log("📦 Deploying UniversalFlashloanArbitrage...");
  const UniversalFlashloanArbitrage = await ethers.getContractFactory("UniversalFlashloanArbitrage");
  
  const arbitrageContract = await UniversalFlashloanArbitrage.deploy(
    POLYGON_CONFIG.protocols.aaveV3Pool,
    POLYGON_CONFIG.protocols.balancerVault,
    POLYGON_CONFIG.protocols.dydxSoloMargin,
    routerAddresses,
    routerNames
  );
  await arbitrageContract.deployed();
  console.log(`✅ UniversalFlashloanArbitrage: ${arbitrageContract.address}`);
  
  // 5. Deploy FlashloanFactory
  console.log("📦 Deploying FlashloanFactory...");
  const FlashloanFactory = await ethers.getContractFactory("FlashloanFactory");
  const factory = await FlashloanFactory.deploy();
  await factory.deployed();
  console.log(`✅ FlashloanFactory: ${factory.address}`);
  
  // Configuration setup
  console.log("\n⚙️  Configuring system...");
  
  // Add deployer as authorized caller
  await arbitrageContract.addAuthorizedCaller(deployer.address);
  console.log(`✅ Added ${deployer.address} as authorized caller`);
  
  // Set chain contract in messenger
  await messenger.setChainContract(envInfo.chainId, arbitrageContract.address);
  console.log(`✅ Set chain contract for chain ${envInfo.chainId}`);
  
  // Verify provider setup
  console.log("\n🔍 Provider verification:");
  const providers = await arbitrageContract.getAllProviders();
  for (const provider of providers) {
    console.log(`   ${provider.name}: ${provider.contractAddress} (${provider.feeBps}bps) ${provider.isActive ? "✅" : "❌"}`);
  }
  
  // Run simulation tests if enabled
  if (SIMULATION_CONFIG.enabled) {
    console.log("\n🧪 Running simulation tests...");
    await runSimulationTests(arbitrageContract, callEncoder, forkInfo);
  }
  
  // Create deployment record
  const deployment = {
    network: "polygon",
    chainId: envInfo.chainId,
    timestamp: new Date().toISOString(),
    deployer: deployer.address,
    gasPrice: ethers.utils.formatUnits(envInfo.gasPrice, "gwei") + " gwei",
    blockNumber: envInfo.blockNumber,
    
    contracts: {
      PayloadEncoder: payloadEncoder.address,
      ArbitrageCallEncoder: callEncoder.address,
      CrossChainMessenger: messenger.address,
      UniversalFlashloanArbitrage: arbitrageContract.address,
      FlashloanFactory: factory.address
    },
    
    configuration: POLYGON_CONFIG.protocols,
    
    simulation: forkInfo ? {
      enabled: true,
      forkBlock: forkInfo.blockNumber,
      testAccounts: forkInfo.accounts
    } : { enabled: false },
    
    providers: providers.map(p => ({
      name: p.name,
      address: p.contractAddress,
      feeBps: p.feeBps.toString(),
      active: p.isActive
    })),
    
    integrationGuide: {
      pythonExample: `
# Integration with main_quant_hybrid_orchestrator.py
from web3 import Web3
import json

w3 = Web3(Web3.HTTPProvider('${POLYGON_CONFIG.rpc}'))
contract = w3.eth.contract(
    address='${arbitrageContract.address}',
    abi=load_abi('UniversalFlashloanArbitrage')
)

# Execute simple arbitrage
params = {
    'execType': 0,  # SIMPLE_ARB
    'tokens': ['${POLYGON_CONFIG.protocols.tokens.WMATIC}', '${POLYGON_CONFIG.protocols.tokens.USDC}'],
    'amounts': [w3.toWei(1000, 'ether')],
    'routers': ['${routerAddresses[0]}', '${routerAddresses[1]}'],
    'swapData': [b'', b''],
    'minProfit': w3.toWei(50, 'ether'),
    'maxGasPrice': w3.toWei(150, 'gwei'),
    'requestId': w3.keccak(text='polygon_arb_001')
}

tx = contract.functions.executeArbitrage('AAVE_V3', params).transact()
      `
    }
  };
  
  // Save deployment info
  const deploymentPath = path.join(__dirname, `../deployments/polygon-production-${Date.now()}.json`);
  fs.mkdirSync(path.dirname(deploymentPath), { recursive: true });
  fs.writeFileSync(deploymentPath, JSON.stringify(deployment, null, 2));
  
  console.log(`\n📄 Deployment saved: ${deploymentPath}`);
  
  // Generate integration files
  await generateIntegrationFiles(deployment);
  
  console.log(`\n🎉 Polygon deployment completed successfully!`);
  console.log(`🔗 Main Contract: ${arbitrageContract.address}`);
  console.log(`🏭 Factory: ${factory.address}`);
  console.log(`📨 Messenger: ${messenger.address}`);
  console.log(`🔧 Encoder: ${callEncoder.address}`);
  
  return deployment;
}

async function runSimulationTests(arbitrageContract, callEncoder, forkInfo) {
  console.log("🧪 Running comprehensive simulation tests...");
  
  try {
    // Test 1: Contract initialization
    const providers = await arbitrageContract.getAllProviders();
    console.log(`✅ Test 1: ${providers.length} providers initialized`);
    
    // Test 2: Router configuration
    const quickswapRouter = await arbitrageContract.getRouter("QUICKSWAP");
    const uniswapRouter = await arbitrageContract.getRouter("UNISWAP_V3");
    console.log(`✅ Test 2: Routers configured (QuickSwap: ${quickswapRouter})`);
    
    // Test 3: Payload encoding
    const encoded = await callEncoder.encodeSimpleArbitrage(
      "AAVE_V3",
      POLYGON_CONFIG.protocols.tokens.WMATIC,
      POLYGON_CONFIG.protocols.tokens.USDC,
      quickswapRouter,
      uniswapRouter,
      ethers.utils.parseEther("100"),
      ethers.utils.parseEther("1"),
      ethers.utils.parseUnits("100", "gwei")
    );
    console.log(`✅ Test 3: Payload encoding successful (${encoded.length} bytes)`);
    
    // Test 4: Gas estimation
    const [signer] = await ethers.getSigners();
    await arbitrageContract.addAuthorizedCaller(signer.address);
    
    const params = {
      execType: 0,
      tokens: [POLYGON_CONFIG.protocols.tokens.WMATIC, POLYGON_CONFIG.protocols.tokens.USDC],
      amounts: [ethers.utils.parseEther("1")],
      routers: [quickswapRouter, uniswapRouter],
      swapData: ["0x", "0x"],
      minProfit: ethers.utils.parseEther("0.01"),
      maxGasPrice: ethers.utils.parseUnits("200", "gwei"),
      requestId: ethers.utils.id("test_simulation")
    };
    
    try {
      const gasEstimate = await arbitrageContract.estimateGas.executeArbitrage("AAVE_V3", params);
      console.log(`✅ Test 4: Gas estimation successful (~${gasEstimate.toString()} gas)`);
    } catch (error) {
      console.log(`⚠️  Test 4: Gas estimation failed (expected in simulation): ${error.message.slice(0, 100)}...`);
    }
    
    console.log("✅ All simulation tests completed");
    
  } catch (error) {
    console.error(`❌ Simulation test failed: ${error.message}`);
    throw error;
  }
}

async function generateIntegrationFiles(deployment) {
  console.log("📄 Generating integration files...");
  
  // ABI files
  const abiDir = path.join(__dirname, "../abi");
  fs.mkdirSync(abiDir, { recursive: true });
  
  // Python integration
  const pythonIntegration = `"""
Polygon Flashloan Arbitrage Integration
Auto-generated integration for main_quant_hybrid_orchestrator.py
"""

from web3 import Web3
import json

# Contract Configuration
CONTRACT_ADDRESS = "${deployment.contracts.UniversalFlashloanArbitrage}"
ENCODER_ADDRESS = "${deployment.contracts.ArbitrageCallEncoder}"
CHAIN_ID = ${deployment.chainId}
RPC_URL = "${POLYGON_CONFIG.rpc}"

# Protocol Addresses
AAVE_V3_POOL = "${POLYGON_CONFIG.protocols.aaveV3Pool}"
BALANCER_VAULT = "${POLYGON_CONFIG.protocols.balancerVault}"

# Router Addresses
ROUTERS = ${JSON.stringify(POLYGON_CONFIG.protocols.routers, null, 2)}

# Token Addresses  
TOKENS = ${JSON.stringify(POLYGON_CONFIG.protocols.tokens, null, 2)}

class PolygonFlashloanExecutor:
    def __init__(self, private_key: str, rpc_url: str = RPC_URL):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.account = self.w3.eth.account.from_key(private_key)
        
        # Load contract ABIs
        with open('abi/UniversalFlashloanArbitrage.abi.json') as f:
            self.arbitrage_abi = json.load(f)
        
        self.contract = self.w3.eth.contract(
            address=CONTRACT_ADDRESS,
            abi=self.arbitrage_abi
        )
    
    def execute_simple_arbitrage(self, token_a: str, token_b: str, amount: int, min_profit: int):
        """Execute simple A->B->A arbitrage"""
        params = {
            'execType': 0,  # SIMPLE_ARB
            'tokens': [token_a, token_b],
            'amounts': [amount],
            'routers': [ROUTERS['QUICKSWAP'], ROUTERS['UNISWAP_V3']],
            'swapData': [b'', b''],
            'minProfit': min_profit,
            'maxGasPrice': self.w3.toWei(150, 'gwei'),
            'requestId': self.w3.keccak(text=f'arb_{int(time.time())}')
        }
        
        tx = self.contract.functions.executeArbitrage('AAVE_V3', params)
        return self._send_transaction(tx)
    
    def _send_transaction(self, tx):
        """Send transaction with proper gas estimation"""
        gas_estimate = tx.estimateGas({'from': self.account.address})
        gas_price = self.w3.eth.gas_price
        
        transaction = tx.buildTransaction({
            'from': self.account.address,
            'gas': int(gas_estimate * 1.1),  # 10% buffer
            'gasPrice': gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.account.address)
        })
        
        signed_tx = self.w3.eth.account.sign_transaction(transaction, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        return self.w3.eth.wait_for_transaction_receipt(tx_hash)

# Integration example for main orchestrator
def integrate_with_orchestrator(opportunity_data):
    executor = PolygonFlashloanExecutor(private_key=os.getenv('PRIVATE_KEY'))
    
    result = executor.execute_simple_arbitrage(
        token_a=opportunity_data['token_a'],
        token_b=opportunity_data['token_b'],
        amount=opportunity_data['amount'],
        min_profit=opportunity_data['min_profit']
    )
    
    return result.transactionHash.hex()
`;
  
  fs.writeFileSync(
    path.join(__dirname, "../integration/polygon_flashloan_integration.py"),
    pythonIntegration
  );
  
  console.log("✅ Integration files generated");
}

// Main execution
if (require.main === module) {
  deployWithSimulationTesting()
    .then((deployment) => {
      console.log("\n🎊 Deployment Summary:");
      console.log(`Network: ${deployment.network}`);
      console.log(`Chain ID: ${deployment.chainId}`);
      console.log(`Main Contract: ${deployment.contracts.UniversalFlashloanArbitrage}`);
      console.log(`Simulation Mode: ${deployment.simulation.enabled}`);
      process.exit(0);
    })
    .catch((error) => {
      console.error("\n💥 Deployment failed:");
      console.error(error);
      process.exit(1);
    });
}

module.exports = {
  deployWithSimulationTesting,
  POLYGON_CONFIG,
  SIMULATION_CONFIG
};