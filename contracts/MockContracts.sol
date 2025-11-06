// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

/**
 * @title Mock contracts for testing
 */

contract MockERC20 is ERC20 {
    uint8 private _decimals;
    
    constructor(
        string memory name,
        string memory symbol,
        uint8 __decimals
    ) ERC20(name, symbol) {
        _decimals = __decimals;
    }
    
    function decimals() public view override returns (uint8) {
        return _decimals;
    }
    
    function mint(address to, uint256 amount) external {
        _mint(to, amount);
    }
    
    function burn(address from, uint256 amount) external {
        _burn(from, amount);
    }
}

contract MockUniswapRouter {
    mapping(address => mapping(address => uint256)) public exchangeRates;
    
    constructor() {
        // Set some default exchange rates for testing
        // 1 Token A = 2 Token B
        // 1 Token B = 0.5 Token A
    }
    
    function setExchangeRate(address tokenA, address tokenB, uint256 rate) external {
        exchangeRates[tokenA][tokenB] = rate;
    }
    
    function swapExactTokensForTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external returns (uint[] memory amounts) {
        require(path.length >= 2, "Invalid path");
        require(block.timestamp <= deadline, "Expired");
        
        amounts = new uint[](path.length);
        amounts[0] = amountIn;
        
        // Simple mock: each hop has 1% fee
        uint256 currentAmount = amountIn;
        for (uint256 i = 1; i < path.length; i++) {
            uint256 rate = exchangeRates[path[i-1]][path[i]];
            if (rate == 0) rate = 1e18; // 1:1 if no rate set
            
            currentAmount = (currentAmount * rate * 99) / (100 * 1e18); // 1% fee
            amounts[i] = currentAmount;
        }
        
        require(amounts[amounts.length - 1] >= amountOutMin, "Insufficient output");
        
        // Transfer tokens (simplified - in real router this would be more complex)
        MockERC20(path[0]).transferFrom(msg.sender, address(this), amountIn);
        MockERC20(path[path.length - 1]).transfer(to, amounts[amounts.length - 1]);
        
        return amounts;
    }
    
    function getAmountsOut(uint amountIn, address[] calldata path)
        external view returns (uint[] memory amounts) {
        amounts = new uint[](path.length);
        amounts[0] = amountIn;
        
        uint256 currentAmount = amountIn;
        for (uint256 i = 1; i < path.length; i++) {
            uint256 rate = exchangeRates[path[i-1]][path[i]];
            if (rate == 0) rate = 1e18;
            
            currentAmount = (currentAmount * rate * 99) / (100 * 1e18);
            amounts[i] = currentAmount;
        }
    }
}

contract MockAavePool {
    mapping(address => uint256) public availableLiquidity;
    uint256 public flashLoanFee = 9; // 0.09%
    
    function setAvailableLiquidity(address asset, uint256 amount) external {
        availableLiquidity[asset] = amount;
    }
    
    function flashLoan(
        address receiverAddress,
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata modes,
        address onBehalfOf,
        bytes calldata params,
        uint16 referralCode
    ) external {
        require(assets.length == amounts.length, "Mismatched arrays");
        
        // Check liquidity availability
        for (uint256 i = 0; i < assets.length; i++) {
            require(amounts[i] <= availableLiquidity[assets[i]], "Insufficient liquidity");
        }
        
        // Calculate premiums
        uint256[] memory premiums = new uint256[](amounts.length);
        for (uint256 i = 0; i < amounts.length; i++) {
            premiums[i] = (amounts[i] * flashLoanFee) / 10000;
            // Transfer tokens to receiver
            MockERC20(assets[i]).transfer(receiverAddress, amounts[i]);
        }
        
        // Call the receiver
        (bool success, ) = receiverAddress.call(
            abi.encodeWithSignature(
                "executeOperation(address[],uint256[],uint256[],address,bytes)",
                assets,
                amounts,
                premiums,
                msg.sender,
                params
            )
        );
        require(success, "Flashloan execution failed");
        
        // Collect repayment
        for (uint256 i = 0; i < assets.length; i++) {
            uint256 amountToReturn = amounts[i] + premiums[i];
            MockERC20(assets[i]).transferFrom(receiverAddress, address(this), amountToReturn);
        }
    }
}

contract MockBalancerVault {
    mapping(address => uint256) public poolBalances;
    
    function setPoolBalance(address token, uint256 balance) external {
        poolBalances[token] = balance;
    }
    
    function flashLoan(
        address recipient,
        address[] memory tokens,
        uint256[] memory amounts,
        bytes memory userData
    ) external {
        // Check availability
        for (uint256 i = 0; i < tokens.length; i++) {
            require(amounts[i] <= poolBalances[tokens[i]], "Insufficient balance");
            // Transfer tokens
            MockERC20(tokens[i]).transfer(recipient, amounts[i]);
        }
        
        // Zero fees for Balancer flashloans
        uint256[] memory feeAmounts = new uint256[](tokens.length);
        
        // Call recipient
        (bool success, ) = recipient.call(
            abi.encodeWithSignature(
                "receiveFlashLoan(address[],uint256[],uint256[],bytes)",
                tokens,
                amounts,
                feeAmounts,
                userData
            )
        );
        require(success, "Flashloan callback failed");
        
        // Collect repayment (no fees)
        for (uint256 i = 0; i < tokens.length; i++) {
            MockERC20(tokens[i]).transferFrom(recipient, address(this), amounts[i]);
        }
    }
    
    function batchSwap(
        SwapKind kind,
        BatchSwapStep[] memory swaps,
        address[] memory assets,
        FundManagement memory funds,
        int256[] memory limits,
        uint256 deadline
    ) external payable returns (int256[] memory) {
        // Simplified mock implementation
        int256[] memory deltas = new int256[](assets.length);
        
        // Mock some swaps
        for (uint256 i = 0; i < swaps.length; i++) {
            if (i < deltas.length) {
                deltas[i] = int256(swaps[i].amount);
            }
        }
        
        return deltas;
    }
    
    enum SwapKind { GIVEN_IN, GIVEN_OUT }
    
    struct BatchSwapStep {
        bytes32 poolId;
        uint256 assetInIndex;
        uint256 assetOutIndex;
        uint256 amount;
        bytes userData;
    }
    
    struct FundManagement {
        address sender;
        bool fromInternalBalance;
        address payable recipient;
        bool toInternalBalance;
    }
}

contract MockCurvePool {
    mapping(int128 => address) public coins;
    mapping(int128 => uint256) public balances;
    
    function setCoin(int128 index, address token, uint256 balance) external {
        coins[index] = token;
        balances[index] = balance;
    }
    
    function exchange(
        int128 i,
        int128 j,
        uint256 dx,
        uint256 min_dy
    ) external returns (uint256) {
        require(coins[i] != address(0) && coins[j] != address(0), "Invalid coins");
        require(dx <= balances[i], "Insufficient balance");
        
        // Simple 1:1 exchange with 0.3% fee
        uint256 dy = (dx * 997) / 1000;
        require(dy >= min_dy, "Slippage too high");
        
        MockERC20(coins[i]).transferFrom(msg.sender, address(this), dx);
        MockERC20(coins[j]).transfer(msg.sender, dy);
        
        balances[i] += dx;
        balances[j] -= dy;
        
        return dy;
    }
    
    function get_dy(
        int128 i,
        int128 j,
        uint256 dx
    ) external view returns (uint256) {
        return (dx * 997) / 1000;
    }
}