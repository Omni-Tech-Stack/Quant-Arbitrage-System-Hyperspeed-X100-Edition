// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title PayloadEncoder
 * @dev Utility contract for encoding arbitrage payloads that the system can generate
 */

library PayloadEncoder {
    
    struct SimpleArbParams {
        address tokenA;
        address tokenB;
        address routerBuy;
        address routerSell;
        uint24 feeA; // For Uniswap V3
        uint24 feeB; // For Uniswap V3
        uint256 minProfit;
    }
    
    struct MultiHopParams {
        address[] tokens;
        address[] routers;
        uint24[] fees;
        bytes[] customData;
        uint256 minProfit;
    }
    
    struct BalancerBatchParams {
        bytes32[] poolIds;
        address[] tokens;
        uint256[] amounts;
        int256[] limits;
    }
    
    struct CurveParams {
        address pool;
        int128 tokenInIndex;
        int128 tokenOutIndex;
        uint256 minAmountOut;
    }
    
    /**
     * @dev Encode simple arbitrage parameters
     */
    function encodeSimpleArbitrage(
        SimpleArbParams memory params
    ) external pure returns (bytes memory) {
        return abi.encode(
            "SIMPLE_ARB",
            params.tokenA,
            params.tokenB,
            params.routerBuy,
            params.routerSell,
            params.feeA,
            params.feeB,
            params.minProfit
        );
    }
    
    /**
     * @dev Encode multi-hop arbitrage parameters
     */
    function encodeMultiHop(
        MultiHopParams memory params
    ) external pure returns (bytes memory) {
        return abi.encode(
            "MULTI_HOP",
            params.tokens,
            params.routers,
            params.fees,
            params.customData,
            params.minProfit
        );
    }
    
    /**
     * @dev Encode Balancer batch swap parameters
     */
    function encodeBalancerBatch(
        BalancerBatchParams memory params
    ) external pure returns (bytes memory) {
        return abi.encode(
            "BALANCER_BATCH",
            params.poolIds,
            params.tokens,
            params.amounts,
            params.limits
        );
    }
    
    /**
     * @dev Encode Curve exchange parameters
     */
    function encodeCurveExchange(
        CurveParams memory params
    ) external pure returns (bytes memory) {
        return abi.encode(
            "CURVE",
            params.pool,
            params.tokenInIndex,
            params.tokenOutIndex,
            params.minAmountOut
        );
    }
    
    /**
     * @dev Encode Uniswap V3 swap parameters
     */
    function encodeUniswapV3Swap(
        uint24 fee
    ) external pure returns (bytes memory) {
        return abi.encode("UNISWAP_V3", fee);
    }
    
    /**
     * @dev Encode 1inch swap parameters
     */
    function encode1inchSwap(
        bytes memory oneInchData
    ) external pure returns (bytes memory) {
        return abi.encode("1INCH", oneInchData);
    }
    
    /**
     * @dev Encode custom execution parameters
     */
    function encodeCustomExecution(
        address target,
        bytes memory callData
    ) external pure returns (bytes memory) {
        return abi.encode("CUSTOM", target, callData);
    }
    
    /**
     * @dev Encode complete arbitrage execution
     */
    function encodeArbitrageExecution(
        uint8 executionType,
        address[] memory tokens,
        uint256[] memory amounts,
        address[] memory routers,
        bytes[] memory swapData,
        uint256 minProfit,
        uint256 maxGasPrice
    ) external pure returns (bytes memory) {
        return abi.encode(
            executionType,
            tokens,
            amounts,
            routers,
            swapData,
            minProfit,
            maxGasPrice
        );
    }
}

/**
 * @title CrossChainMessenger
 * @dev Handles cross-chain arbitrage coordination
 */
contract CrossChainMessenger {
    
    struct CrossChainArbitrage {
        uint256 sourceChain;
        uint256 destChain;
        address sourceToken;
        address destToken;
        uint256 amount;
        bytes executionData;
        uint256 deadline;
        bool executed;
    }
    
    mapping(bytes32 => CrossChainArbitrage) public arbitrages;
    mapping(uint256 => address) public chainContracts;
    
    event CrossChainArbitrageInitiated(
        bytes32 indexed arbitrageId,
        uint256 indexed sourceChain,
        uint256 indexed destChain,
        uint256 amount
    );
    
    event CrossChainArbitrageCompleted(
        bytes32 indexed arbitrageId,
        bool success,
        uint256 profit
    );
    
    function initiateCrossChainArbitrage(
        uint256 destChain,
        address sourceToken,
        address destToken,
        uint256 amount,
        bytes memory executionData,
        uint256 deadline
    ) external returns (bytes32) {
        bytes32 arbitrageId = keccak256(abi.encodePacked(
            block.chainid,
            destChain,
            sourceToken,
            destToken,
            amount,
            block.timestamp,
            msg.sender
        ));
        
        arbitrages[arbitrageId] = CrossChainArbitrage({
            sourceChain: block.chainid,
            destChain: destChain,
            sourceToken: sourceToken,
            destToken: destToken,
            amount: amount,
            executionData: executionData,
            deadline: deadline,
            executed: false
        });
        
        emit CrossChainArbitrageInitiated(arbitrageId, block.chainid, destChain, amount);
        
        return arbitrageId;
    }
    
    function executeCrossChainArbitrage(
        bytes32 arbitrageId,
        bytes memory proof
    ) external returns (bool success, uint256 profit) {
        CrossChainArbitrage storage arb = arbitrages[arbitrageId];
        require(!arb.executed, "Already executed");
        require(block.timestamp <= arb.deadline, "Expired");
        require(arb.destChain == block.chainid, "Wrong chain");
        
        // Verify cross-chain proof (simplified)
        require(proof.length > 0, "Invalid proof");
        
        arb.executed = true;
        
        // Execute the arbitrage logic
        address destContract = chainContracts[arb.destChain];
        require(destContract != address(0), "No contract on dest chain");
        
        (success, bytes memory result) = destContract.call(arb.executionData);
        
        if (success && result.length >= 32) {
            profit = abi.decode(result, (uint256));
        }
        
        emit CrossChainArbitrageCompleted(arbitrageId, success, profit);
        
        return (success, profit);
    }
    
    function setChainContract(uint256 chainId, address contractAddress) external {
        chainContracts[chainId] = contractAddress;
    }
}

/**
 * @title ArbitrageCallEncoder
 * @dev Encodes function calls for the arbitrage system
 */
contract ArbitrageCallEncoder {
    using PayloadEncoder for *;
    
    /**
     * @dev Encode a complete arbitrage transaction for the system
     */
    function encodeArbitrageTransaction(
        string memory provider,
        uint8 executionType,
        address[] memory tokens,
        uint256[] memory amounts,
        address[] memory routers,
        bytes[] memory swapData,
        uint256 minProfit,
        uint256 maxGasPrice,
        bytes32 requestId
    ) external pure returns (bytes memory) {
        
        // Create ArbitrageParams struct encoding
        bytes memory paramsData = abi.encode(
            executionType,
            tokens,
            amounts,
            routers,
            swapData,
            minProfit,
            maxGasPrice,
            requestId
        );
        
        // Encode the complete function call
        return abi.encodeWithSignature(
            "executeArbitrage(string,(uint8,address[],uint256[],address[],bytes[],uint256,uint256,bytes32))",
            provider,
            abi.decode(paramsData, (uint8, address[], uint256[], address[], bytes[], uint256, uint256, bytes32))
        );
    }
    
    /**
     * @dev Encode simple A->B->A arbitrage
     */
    function encodeSimpleArbitrage(
        string memory provider,
        address tokenA,
        address tokenB,
        address routerBuy,
        address routerSell,
        uint256 amount,
        uint256 minProfit,
        uint256 maxGasPrice
    ) external pure returns (bytes memory) {
        
        address[] memory tokens = new address[](2);
        tokens[0] = tokenA;
        tokens[1] = tokenB;
        
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = amount;
        
        address[] memory routers = new address[](2);
        routers[0] = routerBuy;
        routers[1] = routerSell;
        
        bytes[] memory swapData = new bytes[](2);
        swapData[0] = ""; // Default Uniswap V2
        swapData[1] = ""; // Default Uniswap V2
        
        return abi.encodeWithSignature(
            "executeArbitrage(string,(uint8,address[],uint256[],address[],bytes[],uint256,uint256,bytes32))",
            provider,
            uint8(0), // SIMPLE_ARB
            tokens,
            amounts,
            routers,
            swapData,
            minProfit,
            maxGasPrice,
            keccak256("SIMPLE_ARB")
        );
    }
    
    /**
     * @dev Encode multi-hop arbitrage (up to 4 hops)
     */
    function encodeMultiHopArbitrage(
        string memory provider,
        address[] memory tokens,
        address[] memory routers,
        uint256 amount,
        uint256 minProfit,
        uint256 maxGasPrice,
        bytes[] memory customSwapData
    ) external pure returns (bytes memory) {
        
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = amount;
        
        return abi.encodeWithSignature(
            "executeArbitrage(string,(uint8,address[],uint256[],address[],bytes[],uint256,uint256,bytes32))",
            provider,
            uint8(1), // MULTI_HOP
            tokens,
            amounts,
            routers,
            customSwapData,
            minProfit,
            maxGasPrice,
            keccak256("MULTI_HOP")
        );
    }
    
    /**
     * @dev Encode Balancer batch swap arbitrage
     */
    function encodeBalancerBatchArbitrage(
        string memory provider,
        bytes32[] memory poolIds,
        address[] memory tokens,
        uint256[] memory amounts,
        int256[] memory limits,
        uint256 minProfit,
        uint256 maxGasPrice
    ) external pure returns (bytes memory) {
        
        // Encode Balancer-specific data
        bytes memory balancerData = abi.encode(poolIds, tokens, limits);
        
        bytes[] memory swapData = new bytes[](1);
        swapData[0] = balancerData;
        
        address[] memory routers = new address[](1);
        routers[0] = address(0); // Will use balancerVault from contract
        
        return abi.encodeWithSignature(
            "executeArbitrage(string,(uint8,address[],uint256[],address[],bytes[],uint256,uint256,bytes32))",
            provider,
            uint8(2), // BALANCER_BATCH
            tokens,
            amounts,
            routers,
            swapData,
            minProfit,
            maxGasPrice,
            keccak256("BALANCER_BATCH")
        );
    }
    
    /**
     * @dev Encode Curve exchange arbitrage
     */
    function encodeCurveArbitrage(
        string memory provider,
        address tokenIn,
        address tokenOut,
        address curvePool,
        int128 tokenInIndex,
        int128 tokenOutIndex,
        uint256 amount,
        uint256 minAmountOut,
        uint256 minProfit,
        uint256 maxGasPrice
    ) external pure returns (bytes memory) {
        
        address[] memory tokens = new address[](2);
        tokens[0] = tokenIn;
        tokens[1] = tokenOut;
        
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = amount;
        
        address[] memory routers = new address[](1);
        routers[0] = curvePool;
        
        // Encode Curve-specific data
        bytes memory curveData = abi.encode(curvePool, tokenInIndex, tokenOutIndex, minAmountOut);
        bytes[] memory swapData = new bytes[](1);
        swapData[0] = curveData;
        
        return abi.encodeWithSignature(
            "executeArbitrage(string,(uint8,address[],uint256[],address[],bytes[],uint256,uint256,bytes32))",
            provider,
            uint8(3), // CURVE_EXCHANGE
            tokens,
            amounts,
            routers,
            swapData,
            minProfit,
            maxGasPrice,
            keccak256("CURVE_EXCHANGE")
        );
    }
}