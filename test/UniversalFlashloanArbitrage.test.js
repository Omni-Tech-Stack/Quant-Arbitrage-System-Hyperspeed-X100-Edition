const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("UniversalFlashloanArbitrage", function () {
  let arbitrageContract;
  let payloadEncoder;
  let callEncoder;
  let messenger;
  let factory;
  let owner;
  let user;
  let mockToken;
  let mockRouter;

  // Mock addresses for testing
  const MOCK_AAVE_POOL = "0x1111111111111111111111111111111111111111";
  const MOCK_BALANCER_VAULT = "0x2222222222222222222222222222222222222222";
  const MOCK_DYDX_MARGIN = "0x3333333333333333333333333333333333333333";

  beforeEach(async function () {
    [owner, user] = await ethers.getSigners();

    // Deploy mock ERC20 token
    const MockToken = await ethers.getContractFactory("MockERC20");
    mockToken = await MockToken.deploy("Test Token", "TEST", 18);
    await mockToken.deployed();

    // Deploy mock router
    const MockRouter = await ethers.getContractFactory("MockUniswapRouter");
    mockRouter = await MockRouter.deploy();
    await mockRouter.deployed();

    // Deploy PayloadEncoder
    const PayloadEncoder = await ethers.getContractFactory("PayloadEncoder");
    payloadEncoder = await PayloadEncoder.deploy();
    await payloadEncoder.deployed();

    // Deploy ArbitrageCallEncoder
    const ArbitrageCallEncoder = await ethers.getContractFactory("ArbitrageCallEncoder");
    callEncoder = await ArbitrageCallEncoder.deploy();
    await callEncoder.deployed();

    // Deploy CrossChainMessenger
    const CrossChainMessenger = await ethers.getContractFactory("CrossChainMessenger");
    messenger = await CrossChainMessenger.deploy();
    await messenger.deployed();

    // Deploy main contract
    const UniversalFlashloanArbitrage = await ethers.getContractFactory("UniversalFlashloanArbitrage");
    arbitrageContract = await UniversalFlashloanArbitrage.deploy(
      MOCK_AAVE_POOL,
      MOCK_BALANCER_VAULT,
      MOCK_DYDX_MARGIN,
      [mockRouter.address],
      ["MOCK_ROUTER"]
    );
    await arbitrageContract.deployed();

    // Deploy factory
    const FlashloanFactory = await ethers.getContractFactory("FlashloanFactory");
    factory = await FlashloanFactory.deploy();
    await factory.deployed();
  });

  describe("Deployment", function () {
    it("Should set the correct owner", async function () {
      expect(await arbitrageContract.owner()).to.equal(owner.address);
    });

    it("Should initialize providers correctly", async function () {
      const aaveProvider = await arbitrageContract.getProviderInfo("AAVE_V3");
      expect(aaveProvider.name).to.equal("AAVE_V3");
      expect(aaveProvider.contractAddress).to.equal(MOCK_AAVE_POOL);
      expect(aaveProvider.feeBps).to.equal(9); // 0.09%
      expect(aaveProvider.isActive).to.be.true;
    });

    it("Should set router addresses correctly", async function () {
      const routerAddress = await arbitrageContract.getRouter("MOCK_ROUTER");
      expect(routerAddress).to.equal(mockRouter.address);
    });
  });

  describe("Authorization", function () {
    it("Should allow owner to add authorized callers", async function () {
      await arbitrageContract.addAuthorizedCaller(user.address);
      expect(await arbitrageContract.authorizedCallers(user.address)).to.be.true;
    });

    it("Should allow owner to remove authorized callers", async function () {
      await arbitrageContract.addAuthorizedCaller(user.address);
      await arbitrageContract.removeAuthorizedCaller(user.address);
      expect(await arbitrageContract.authorizedCallers(user.address)).to.be.false;
    });

    it("Should not allow non-owner to add authorized callers", async function () {
      await expect(
        arbitrageContract.connect(user).addAuthorizedCaller(user.address)
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });
  });

  describe("Provider Management", function () {
    it("Should allow owner to update provider", async function () {
      const newAddress = "0x4444444444444444444444444444444444444444";
      await arbitrageContract.updateProvider("TEST_PROVIDER", newAddress, 10, true);
      
      const provider = await arbitrageContract.getProviderInfo("TEST_PROVIDER");
      expect(provider.contractAddress).to.equal(newAddress);
      expect(provider.feeBps).to.equal(10);
    });

    it("Should return all providers", async function () {
      const providers = await arbitrageContract.getAllProviders();
      expect(providers.length).to.be.at.least(3); // AAVE_V3, BALANCER, DYDX
    });
  });

  describe("Payload Encoding", function () {
    it("Should encode simple arbitrage correctly", async function () {
      const encoded = await callEncoder.encodeSimpleArbitrage(
        "AAVE_V3",
        mockToken.address,
        mockToken.address,
        mockRouter.address,
        mockRouter.address,
        ethers.utils.parseEther("1000"),
        ethers.utils.parseEther("10"),
        ethers.utils.parseUnits("50", "gwei")
      );
      
      expect(encoded).to.be.a("string");
      expect(encoded.length).to.be.greaterThan(2); // More than "0x"
    });

    it("Should encode multi-hop arbitrage correctly", async function () {
      const tokens = [mockToken.address, mockToken.address, mockToken.address];
      const routers = [mockRouter.address, mockRouter.address];
      const swapData = ["0x", "0x"];
      
      const encoded = await callEncoder.encodeMultiHopArbitrage(
        "BALANCER",
        tokens,
        routers,
        ethers.utils.parseEther("1000"),
        ethers.utils.parseEther("10"),
        ethers.utils.parseUnits("50", "gwei"),
        swapData
      );
      
      expect(encoded).to.be.a("string");
      expect(encoded.length).to.be.greaterThan(2);
    });
  });

  describe("Cross-Chain Functionality", function () {
    it("Should initiate cross-chain arbitrage", async function () {
      const executionData = "0x1234";
      const deadline = Math.floor(Date.now() / 1000) + 3600; // 1 hour from now
      
      const tx = await messenger.initiateCrossChainArbitrage(
        137, // Polygon
        mockToken.address,
        mockToken.address,
        ethers.utils.parseEther("1000"),
        executionData,
        deadline
      );
      
      const receipt = await tx.wait();
      const event = receipt.events.find(e => e.event === "CrossChainArbitrageInitiated");
      expect(event).to.not.be.undefined;
    });

    it("Should set chain contract address", async function () {
      await messenger.setChainContract(1, arbitrageContract.address);
      expect(await messenger.chainContracts(1)).to.equal(arbitrageContract.address);
    });
  });

  describe("Factory Functionality", function () {
    it("Should return correct chain config", async function () {
      const config = await factory.getChainConfig(1);
      expect(config.chainId).to.equal(1);
      expect(config.name).to.equal("ethereum");
      expect(config.isActive).to.be.true;
    });

    it("Should allow owner to update chain config", async function () {
      await factory.updateChainConfig(
        999,
        "test-chain",
        MOCK_AAVE_POOL,
        MOCK_BALANCER_VAULT,
        MOCK_DYDX_MARGIN,
        [mockRouter.address],
        ["TEST_ROUTER"],
        true
      );
      
      const config = await factory.getChainConfig(999);
      expect(config.name).to.equal("test-chain");
      expect(config.isActive).to.be.true;
    });
  });

  describe("Emergency Functions", function () {
    it("Should allow owner to emergency withdraw ETH", async function () {
      // Send some ETH to the contract
      await owner.sendTransaction({
        to: arbitrageContract.address,
        value: ethers.utils.parseEther("1")
      });
      
      const initialBalance = await owner.getBalance();
      const tx = await arbitrageContract.emergencyWithdraw(
        ethers.constants.AddressZero,
        ethers.utils.parseEther("0.5")
      );
      
      // Check that transaction succeeded
      expect(tx).to.not.be.reverted;
    });

    it("Should allow owner to emergency withdraw tokens", async function () {
      // Mint tokens to the contract
      await mockToken.mint(arbitrageContract.address, ethers.utils.parseEther("1000"));
      
      await arbitrageContract.emergencyWithdraw(
        mockToken.address,
        ethers.utils.parseEther("500")
      );
      
      const ownerBalance = await mockToken.balanceOf(owner.address);
      expect(ownerBalance).to.equal(ethers.utils.parseEther("500"));
    });

    it("Should not allow non-owner to emergency withdraw", async function () {
      await expect(
        arbitrageContract.connect(user).emergencyWithdraw(
          ethers.constants.AddressZero,
          ethers.utils.parseEther("1")
        )
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });
  });

  describe("Gas Optimization", function () {
    it("Should reject transactions with high gas price", async function () {
      await arbitrageContract.addAuthorizedCaller(owner.address);
      
      const params = {
        execType: 0, // SIMPLE_ARB
        tokens: [mockToken.address, mockToken.address],
        amounts: [ethers.utils.parseEther("1000")],
        routers: [mockRouter.address, mockRouter.address],
        swapData: ["0x", "0x"],
        minProfit: ethers.utils.parseEther("10"),
        maxGasPrice: ethers.utils.parseUnits("1", "gwei"), // Very low gas price
        requestId: ethers.utils.id("test")
      };
      
      // This should fail due to gas price check
      await expect(
        arbitrageContract.executeArbitrage("AAVE_V3", params, {
          gasPrice: ethers.utils.parseUnits("100", "gwei") // Higher than maxGasPrice
        })
      ).to.be.revertedWith("Gas price too high");
    });
  });
});

// Mock contracts for testing

contract("MockERC20", function () {
  const MockERC20 = artifacts.require("MockERC20");
  
  beforeEach(async function () {
    this.token = await MockERC20.new("Mock Token", "MOCK", 18);
  });
});

contract("MockUniswapRouter", function () {
  const MockRouter = artifacts.require("MockUniswapRouter");
  
  beforeEach(async function () {
    this.router = await MockRouter.new();
  });
});