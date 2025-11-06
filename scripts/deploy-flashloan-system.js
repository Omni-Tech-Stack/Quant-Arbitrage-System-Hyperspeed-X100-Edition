const { ethers, network } = require("hardhat");
const fs = require("fs");
const path = require("path");

/**
 * Multi-chain deployment script for Universal Flashloan Arbitrage System
 */

const CHAIN_CONFIGS = {
  // Ethereum Mainnet
  1: {
    name: "ethereum",
    rpc: process.env.ETHEREUM_RPC || "https://eth-mainnet.g.alchemy.com/v2/your-key",
    aaveV3Pool: "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
    balancerVault: "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    dydxSoloMargin: "0x1E0447b19BB6EcFdAe1e4AE1694b0C3659614e4e",
    routers: {
      "UNISWAP_V2": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
      "UNISWAP_V3": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
      "SUSHISWAP": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
      "1INCH": "0x1111111254EEB25477B68fb85Ed929f73A960582",
      "CURVE": "0x8301AE4fc9c624d1D396cbDAa1ed877821D7C511"
    }
  },
  
  // Polygon
  137: {
    name: "polygon",
    rpc: process.env.POLYGON_RPC || "https://polygon-mainnet.g.alchemy.com/v2/your-key",
    aaveV3Pool: "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    balancerVault: "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    dydxSoloMargin: "0x0000000000000000000000000000000000000000", // Not available
    routers: {
      "QUICKSWAP": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
      "UNISWAP_V3": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
      "SUSHISWAP": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
      "1INCH": "0x1111111254EEB25477B68fb85Ed929f73A960582",
      "CURVE": "0x094d12e5b541784701FD8d65F11fc0598FBC6332"
    }
  },
  
  // Arbitrum
  42161: {
    name: "arbitrum",
    rpc: process.env.ARBITRUM_RPC || "https://arb-mainnet.g.alchemy.com/v2/your-key",
    aaveV3Pool: "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    balancerVault: "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    dydxSoloMargin: "0x0000000000000000000000000000000000000000",
    routers: {
      "UNISWAP_V3": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
      "SUSHISWAP": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
      "1INCH": "0x1111111254EEB25477B68fb85Ed929f73A960582",
      "CAMELOT": "0xc873fEcbd354f5A56E00E710B90EF4201db2448d"
    }
  },
  
  // BSC
  56: {
    name: "bsc",
    rpc: process.env.BSC_RPC || "https://bsc-dataseed.binance.org/",
    aaveV3Pool: "0x6807dc923806fE8Fd134338EABCA509979a7e0cB",
    balancerVault: "0x0000000000000000000000000000000000000000", // Not available
    dydxSoloMargin: "0x0000000000000000000000000000000000000000",
    routers: {
      "PANCAKESWAP_V2": "0x10ED43C718714eb63d5aA57B78B54704E256024E",
      "PANCAKESWAP_V3": "0x13f4EA83D0bd40E75C8222255bc855a974568Dd4",
      "1INCH": "0x1111111254EEB25477B68fb85Ed929f73A960582",
      "BISWAP": "0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8"
    }
  },
  
  // Optimism
  10: {
    name: "optimism",
    rpc: process.env.OPTIMISM_RPC || "https://opt-mainnet.g.alchemy.com/v2/your-key",
    aaveV3Pool: "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    balancerVault: "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    dydxSoloMargin: "0x0000000000000000000000000000000000000000",
    routers: {
      "UNISWAP_V3": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
      "1INCH": "0x1111111254EEB25477B68fb85Ed929f73A960582",
      "VELODROME": "0x9c12939390052919aF3155f41Bf4160Fd3666A6f"
    }
  },
  
  // Avalanche
  43114: {
    name: "avalanche",
    rpc: process.env.AVALANCHE_RPC || "https://api.avax.network/ext/bc/C/rpc",
    aaveV3Pool: "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    balancerVault: "0x0000000000000000000000000000000000000000",
    dydxSoloMargin: "0x0000000000000000000000000000000000000000",
    routers: {
      "TRADERJOE": "0x60aE616a2155Ee3d9A68541Ba4544862310933d4",
      "PANGOLIN": "0xE54Ca86531e17Ef3616d22Ca28b0D458b6C89106",
      "1INCH": "0x1111111254EEB25477B68fb85Ed929f73A960582"
    }
  }
};

async function main() {
  const [deployer] = await ethers.getSigners();
  const chainId = network.config.chainId || 1;
  const config = CHAIN_CONFIGS[chainId];
  
  if (!config) {
    throw new Error(`Chain ${chainId} not supported`);
  }
  
  console.log(`\n🚀 Deploying Universal Flashloan Arbitrage System on ${config.name} (Chain ID: ${chainId})`);
  console.log(`📝 Deployer: ${deployer.address}`);
  console.log(`💰 Balance: ${ethers.utils.formatEther(await deployer.getBalance())} ETH\n`);
  
  // Prepare router arrays
  const routerAddresses = Object.values(config.routers);
  const routerNames = Object.keys(config.routers);
  
  console.log(`🔧 Router Configuration:`);
  routerNames.forEach((name, i) => {
    console.log(`   ${name}: ${routerAddresses[i]}`);
  });
  console.log();
  
  // Deploy PayloadEncoder library first
  console.log("📦 Deploying PayloadEncoder library...");
  const PayloadEncoder = await ethers.getContractFactory("PayloadEncoder");
  const payloadEncoder = await PayloadEncoder.deploy();
  await payloadEncoder.deployed();
  console.log(`✅ PayloadEncoder deployed at: ${payloadEncoder.address}`);
  
  // Deploy ArbitrageCallEncoder
  console.log("📦 Deploying ArbitrageCallEncoder...");
  const ArbitrageCallEncoder = await ethers.getContractFactory("ArbitrageCallEncoder");
  const callEncoder = await ArbitrageCallEncoder.deploy();
  await callEncoder.deployed();
  console.log(`✅ ArbitrageCallEncoder deployed at: ${callEncoder.address}`);
  
  // Deploy CrossChainMessenger
  console.log("📦 Deploying CrossChainMessenger...");
  const CrossChainMessenger = await ethers.getContractFactory("CrossChainMessenger");
  const messenger = await CrossChainMessenger.deploy();
  await messenger.deployed();
  console.log(`✅ CrossChainMessenger deployed at: ${messenger.address}`);
  
  // Deploy main UniversalFlashloanArbitrage contract
  console.log("📦 Deploying UniversalFlashloanArbitrage...");
  const UniversalFlashloanArbitrage = await ethers.getContractFactory("UniversalFlashloanArbitrage");
  const arbitrageContract = await UniversalFlashloanArbitrage.deploy(
    config.aaveV3Pool,
    config.balancerVault,
    config.dydxSoloMargin,
    routerAddresses,
    routerNames
  );
  await arbitrageContract.deployed();
  console.log(`✅ UniversalFlashloanArbitrage deployed at: ${arbitrageContract.address}`);
  
  // Deploy FlashloanFactory
  console.log("📦 Deploying FlashloanFactory...");
  const FlashloanFactory = await ethers.getContractFactory("FlashloanFactory");
  const factory = await FlashloanFactory.deploy();
  await factory.deployed();
  console.log(`✅ FlashloanFactory deployed at: ${factory.address}`);
  
  // Set up initial configuration
  console.log("\n⚙️  Setting up initial configuration...");
  
  // Add deployer as authorized caller
  await arbitrageContract.addAuthorizedCaller(deployer.address);
  console.log(`✅ Added ${deployer.address} as authorized caller`);
  
  // Update CrossChainMessenger with contract address
  await messenger.setChainContract(chainId, arbitrageContract.address);
  console.log(`✅ Set chain contract for chain ${chainId}`);
  
  // Verify provider configurations
  console.log("\n🔍 Verifying provider configurations...");
  const providers = await arbitrageContract.getAllProviders();
  for (const provider of providers) {
    console.log(`   ${provider.name}: ${provider.contractAddress} (Fee: ${provider.feeBps}bps, Active: ${provider.isActive})`);
  }
  
  // Create deployment summary
  const deployment = {
    chainId,
    network: config.name,
    timestamp: new Date().toISOString(),
    deployer: deployer.address,
    gasPrice: ethers.utils.formatUnits(await ethers.provider.getGasPrice(), "gwei") + " gwei",
    contracts: {
      PayloadEncoder: payloadEncoder.address,
      ArbitrageCallEncoder: callEncoder.address,
      CrossChainMessenger: messenger.address,
      UniversalFlashloanArbitrage: arbitrageContract.address,
      FlashloanFactory: factory.address
    },
    configuration: {
      aaveV3Pool: config.aaveV3Pool,
      balancerVault: config.balancerVault,
      dydxSoloMargin: config.dydxSoloMargin,
      routers: config.routers
    },
    providers: providers.map(p => ({
      name: p.name,
      address: p.contractAddress,
      feeBps: p.feeBps.toString(),
      active: p.isActive
    }))
  };
  
  // Save deployment info
  const deploymentPath = path.join(__dirname, `../deployments/${config.name}-${chainId}.json`);
  fs.mkdirSync(path.dirname(deploymentPath), { recursive: true });
  fs.writeFileSync(deploymentPath, JSON.stringify(deployment, null, 2));
  
  console.log(`\n📄 Deployment summary saved to: ${deploymentPath}`);
  
  // Generate ABI files
  const abiPath = path.join(__dirname, `../abi/`);
  fs.mkdirSync(abiPath, { recursive: true });
  
  const artifacts = [
    { name: "UniversalFlashloanArbitrage", contract: arbitrageContract },
    { name: "ArbitrageCallEncoder", contract: callEncoder },
    { name: "CrossChainMessenger", contract: messenger },
    { name: "FlashloanFactory", contract: factory }
  ];
  
  for (const artifact of artifacts) {
    const abi = artifact.contract.interface.format(ethers.utils.FormatTypes.json);
    fs.writeFileSync(path.join(abiPath, `${artifact.name}.abi.json`), abi);
  }
  
  console.log(`📄 ABI files saved to: ${abiPath}`);
  
  // Generate interaction examples
  console.log("\n💡 Example usage:");
  console.log(`
// Simple arbitrage example
const provider = ethers.getDefaultProvider("${config.rpc}");
const contract = new ethers.Contract("${arbitrageContract.address}", abi, wallet);

const params = {
  execType: 0, // SIMPLE_ARB
  tokens: ["0xTokenA", "0xTokenB"],
  amounts: [ethers.utils.parseEther("1000")],
  routers: ["${routerAddresses[0]}", "${routerAddresses[1]}"],
  swapData: ["0x", "0x"],
  minProfit: ethers.utils.parseEther("10"),
  maxGasPrice: ethers.utils.parseUnits("50", "gwei"),
  requestId: ethers.utils.id("arbitrage_001")
};

await contract.executeArbitrage("AAVE_V3", params);
  `);
  
  console.log(`\n🎉 Deployment completed successfully!`);
  console.log(`🔗 Main contract: ${arbitrageContract.address}`);
  console.log(`🏭 Factory contract: ${factory.address}`);
  console.log(`📨 Messenger contract: ${messenger.address}`);
  
  return {
    arbitrageContract: arbitrageContract.address,
    factory: factory.address,
    messenger: messenger.address,
    encoder: callEncoder.address,
    chainId,
    network: config.name
  };
}

// Handle deployment
if (require.main === module) {
  main()
    .then((result) => {
      console.log("\n✅ Deployment successful:", result);
      process.exit(0);
    })
    .catch((error) => {
      console.error("\n❌ Deployment failed:", error);
      process.exit(1);
    });
}

module.exports = { main, CHAIN_CONFIGS };