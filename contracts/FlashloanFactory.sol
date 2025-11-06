// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title FlashloanFactory
 * @dev Factory contract for deploying UniversalFlashloanArbitrage contracts across multiple chains
 */

import "./UniversalFlashloanArbitrage.sol";

contract FlashloanFactory {
    event ContractDeployed(
        address indexed deployedContract,
        uint256 indexed chainId,
        address indexed deployer,
        string network
    );
    
    struct ChainConfig {
        uint256 chainId;
        string name;
        address aaveV3Pool;
        address balancerVault;
        address dydxSoloMargin;
        address[] routers;
        string[] routerNames;
        bool isActive;
    }
    
    mapping(uint256 => ChainConfig) public chainConfigs;
    mapping(uint256 => address) public deployedContracts;
    address public owner;
    
    // Predefined chain configurations
    constructor() {
        owner = msg.sender;
        _setupChainConfigs();
    }
    
    function _setupChainConfigs() internal {
        // Ethereum Mainnet
        chainConfigs[1] = ChainConfig({
            chainId: 1,
            name: "ethereum",
            aaveV3Pool: 0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2,
            balancerVault: 0xBA12222222228d8Ba445958a75a0704d566BF2C8,
            dydxSoloMargin: 0x1E0447b19BB6EcFdAe1e4AE1694b0C3659614e4e,
            routers: new address[](0),
            routerNames: new string[](0),
            isActive: true
        });
        
        // Polygon
        chainConfigs[137] = ChainConfig({
            chainId: 137,
            name: "polygon",
            aaveV3Pool: 0x794a61358D6845594F94dc1DB02A252b5b4814aD,
            balancerVault: 0xBA12222222228d8Ba445958a75a0704d566BF2C8,
            dydxSoloMargin: address(0), // Not available on Polygon
            routers: new address[](0),
            routerNames: new string[](0),
            isActive: true
        });
        
        // Arbitrum
        chainConfigs[42161] = ChainConfig({
            chainId: 42161,
            name: "arbitrum",
            aaveV3Pool: 0x794a61358D6845594F94dc1DB02A252b5b4814aD,
            balancerVault: 0xBA12222222228d8Ba445958a75a0704d566BF2C8,
            dydxSoloMargin: address(0),
            routers: new address[](0),
            routerNames: new string[](0),
            isActive: true
        });
        
        // BSC
        chainConfigs[56] = ChainConfig({
            chainId: 56,
            name: "bsc",
            aaveV3Pool: 0x6807dc923806fE8Fd134338EABCA509979a7e0cB,
            balancerVault: address(0), // Not available on BSC
            dydxSoloMargin: address(0),
            routers: new address[](0),
            routerNames: new string[](0),
            isActive: true
        });
        
        _setupRouters();
    }
    
    function _setupRouters() internal {
        // Ethereum routers
        chainConfigs[1].routers = [
            0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D, // Uniswap V2
            0xE592427A0AEce92De3Edee1F18E0157C05861564, // Uniswap V3
            0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F, // SushiSwap
            0x1111111254EEB25477B68fb85Ed929f73A960582  // 1inch V5
        ];
        chainConfigs[1].routerNames = ["UNISWAP_V2", "UNISWAP_V3", "SUSHISWAP", "1INCH"];
        
        // Polygon routers
        chainConfigs[137].routers = [
            0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff, // QuickSwap
            0xE592427A0AEce92De3Edee1F18E0157C05861564, // Uniswap V3
            0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506, // SushiSwap
            0x1111111254EEB25477B68fb85Ed929f73A960582  // 1inch V5
        ];
        chainConfigs[137].routerNames = ["QUICKSWAP", "UNISWAP_V3", "SUSHISWAP", "1INCH"];
        
        // Arbitrum routers
        chainConfigs[42161].routers = [
            0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506, // SushiSwap
            0xE592427A0AEce92De3Edee1F18E0157C05861564, // Uniswap V3
            0x1111111254EEB25477B68fb85Ed929f73A960582  // 1inch V5
        ];
        chainConfigs[42161].routerNames = ["SUSHISWAP", "UNISWAP_V3", "1INCH"];
    }
    
    function deployContract() external returns (address) {
        uint256 currentChainId = block.chainid;
        ChainConfig memory config = chainConfigs[currentChainId];
        
        require(config.isActive, "Chain not supported");
        require(deployedContracts[currentChainId] == address(0), "Already deployed on this chain");
        
        UniversalFlashloanArbitrage arbitrageContract = new UniversalFlashloanArbitrage(
            config.aaveV3Pool,
            config.balancerVault,
            config.dydxSoloMargin,
            config.routers,
            config.routerNames
        );
        
        deployedContracts[currentChainId] = address(arbitrageContract);
        
        emit ContractDeployed(
            address(arbitrageContract),
            currentChainId,
            msg.sender,
            config.name
        );
        
        return address(arbitrageContract);
    }
    
    function getChainConfig(uint256 chainId) external view returns (ChainConfig memory) {
        return chainConfigs[chainId];
    }
    
    function updateChainConfig(
        uint256 chainId,
        string memory name,
        address aaveV3Pool,
        address balancerVault,
        address dydxSoloMargin,
        address[] memory routers,
        string[] memory routerNames,
        bool isActive
    ) external {
        require(msg.sender == owner, "Only owner");
        
        chainConfigs[chainId] = ChainConfig({
            chainId: chainId,
            name: name,
            aaveV3Pool: aaveV3Pool,
            balancerVault: balancerVault,
            dydxSoloMargin: dydxSoloMargin,
            routers: routers,
            routerNames: routerNames,
            isActive: isActive
        });
    }
    
    function getDeployedContract(uint256 chainId) external view returns (address) {
        return deployedContracts[chainId];
    }
}