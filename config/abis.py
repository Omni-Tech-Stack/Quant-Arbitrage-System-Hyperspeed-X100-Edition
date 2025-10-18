"""Contract ABIs"""

ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], 
     "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
]

ROUTER_ABI = [
    {"constant": False, "inputs": [], "name": "swapExactTokensForTokens", "type": "function"},
]
