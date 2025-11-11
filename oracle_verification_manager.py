#!/usr/bin/env python3
"""
ORACLE VERIFICATION MANAGER
Manages Chainlink, Uniswap TWAP, and cross-oracle consensus verification
Validates SDK/RPC data against authoritative on-chain oracles
"""

import os
import time
from typing import Dict, Any, Optional, List, Tuple
from web3 import Web3
from web3.contract import Contract
import logging
from dotenv import load_dotenv
from statistics import mean, stdev

load_dotenv('..env')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OracleVerificationManager:
    """
    Manages oracle verification across multiple oracle types
    - Chainlink Price Feeds
    - Uniswap V3 TWAP
    - Cross-Oracle Consensus
    """
    
    # Chainlink Price Feed addresses (Polygon)
    CHAINLINK_FEEDS_POLYGON = {
        'ETH/USD': '0xF9680D99D6C9589e2a93a78A04A279e509205945',
        'BTC/USD': '0xc907E116054Ad103354f2D350FD2514433D57F6f',
        'MATIC/USD': '0xAB594600376Ec9fD91F8e885dADF0CE036862dE0',
        'USDC/USD': '0xfE4A8cc5b5B2366C1B58Bea3858e81843581b2F7',
        'USDT/USD': '0x0A6513e40db6EB1b165753AD52E80663aeA50545',
        'DAI/USD': '0x4746DeC9e833A82EC7C2C1356372CcF2cfcD2F3D',
    }
    
    # Chainlink Price Feed addresses (Ethereum)
    CHAINLINK_FEEDS_ETHEREUM = {
        'ETH/USD': '0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419',
        'BTC/USD': '0xF4030086522a5bEEa4988F8cA5B36dbC97BeE88c',
        'USDC/USD': '0x8fFfFfd4AfB6115b954Bd326cbe7B4BA576818f6',
        'USDT/USD': '0x3E7d1eAB13ad0104d2750B8863b489D65364e32D',
        'DAI/USD': '0xAed0c38402a5d19df6E4c03F4E2DceD6e29c1ee9',
    }
    
    # Chainlink Aggregator ABI (minimal - latestRoundData only)
    CHAINLINK_AGGREGATOR_ABI = [
        {
            "inputs": [],
            "name": "latestRoundData",
            "outputs": [
                {"name": "roundId", "type": "uint80"},
                {"name": "answer", "type": "int256"},
                {"name": "startedAt", "type": "uint256"},
                {"name": "updatedAt", "type": "uint256"},
                {"name": "answeredInRound", "type": "uint80"}
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    # Uniswap V3 Pool ABI (minimal - observe for TWAP)
    UNISWAP_V3_POOL_ABI = [
        {
            "inputs": [{"name": "secondsAgos", "type": "uint32[]"}],
            "name": "observe",
            "outputs": [
                {"name": "tickCumulatives", "type": "int56[]"},
                {"name": "secondsPerLiquidityCumulativeX128s", "type": "uint160[]"}
            ],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    def __init__(
        self,
        deviation_threshold: float = 0.02,  # 2% max deviation
        alert_threshold: float = 0.05,      # 5% triggers alert
        twap_window_seconds: int = 1800,    # 30 minute TWAP
        consensus_min_oracles: int = 2      # Min oracles for consensus
    ):
        """
        Initialize Oracle Verification Manager
        
        Args:
            deviation_threshold: Max % deviation to consider valid (0.02 = 2%)
            alert_threshold: % deviation that triggers alert (0.05 = 5%)
            twap_window_seconds: TWAP time window in seconds
            consensus_min_oracles: Minimum oracles required for consensus
        """
        self.deviation_threshold = deviation_threshold
        self.alert_threshold = alert_threshold
        self.twap_window = twap_window_seconds
        self.consensus_min = consensus_min_oracles
        
        # Initialize Web3 connections
        self.w3_polygon = self._init_web3('POLYGON_RPC_URL', 'Polygon')
        self.w3_ethereum = self._init_web3('ETHEREUM_RPC_URL', 'Ethereum')
        
        # Cache for oracle prices
        self.price_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 12  # 12 seconds = 1 Polygon block
        
        # Statistics
        self.total_verifications = 0
        self.total_passed = 0
        self.total_failed = 0
        self.total_alerts = 0
        
        logger.info("[OracleVerification] ✓ Initialized Oracle Verification Manager")
        logger.info(f"  - Deviation Threshold: {self.deviation_threshold*100}%")
        logger.info(f"  - Alert Threshold: {self.alert_threshold*100}%")
        logger.info(f"  - TWAP Window: {self.twap_window}s")
        logger.info(f"  - Consensus Min: {self.consensus_min} oracles")
    
    def _init_web3(self, env_var: str, chain_name: str) -> Optional[Web3]:
        """Initialize Web3 connection for a chain"""
        rpc_url = os.getenv(env_var)
        if not rpc_url:
            logger.warning(f"[OracleVerification] No RPC URL for {chain_name}")
            return None
        
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if w3.is_connected():
                logger.info(f"[OracleVerification] ✓ Connected to {chain_name}")
                return w3
            else:
                logger.warning(f"[OracleVerification] ✗ Failed to connect to {chain_name}")
                return None
        except Exception as e:
            logger.error(f"[OracleVerification] ✗ {chain_name} connection error: {e}")
            return None
    
    def verify_price_with_chainlink(
        self,
        token_pair: str,
        price: float,
        chain: str = 'polygon'
    ) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Verify a price against Chainlink price feed
        
        Args:
            token_pair: Token pair (e.g., "ETH/USD")
            price: Price to verify
            chain: Blockchain network
        
        Returns:
            (verified, deviation, oracle_data)
        """
        self.total_verifications += 1
        
        # Select Web3 and feed addresses
        if chain == 'polygon':
            w3 = self.w3_polygon
            feeds = self.CHAINLINK_FEEDS_POLYGON
        elif chain == 'ethereum':
            w3 = self.w3_ethereum
            feeds = self.CHAINLINK_FEEDS_ETHEREUM
        else:
            logger.warning(f"[OracleVerification] Unsupported chain: {chain}")
            return False, 0.0, {'error': 'unsupported_chain'}
        
        if not w3:
            logger.warning(f"[OracleVerification] No Web3 connection for {chain}")
            return False, 0.0, {'error': 'no_connection'}
        
        # Check cache
        cache_key = f"{chain}:{token_pair}"
        if cache_key in self.price_cache:
            cached = self.price_cache[cache_key]
            if time.time() - cached['timestamp'] < self.cache_ttl:
                oracle_price = cached['price']
                logger.debug(f"[OracleVerification] Using cached Chainlink price for {token_pair}")
            else:
                # Cache expired, fetch fresh
                oracle_price = self._fetch_chainlink_price(w3, feeds, token_pair)
        else:
            oracle_price = self._fetch_chainlink_price(w3, feeds, token_pair)
        
        if oracle_price is None:
            logger.warning(f"[OracleVerification] Could not fetch Chainlink price for {token_pair}")
            return False, 0.0, {'error': 'oracle_unavailable'}
        
        # Calculate deviation
        deviation = abs(price - oracle_price) / oracle_price
        
        # Determine if verified
        verified = deviation <= self.deviation_threshold
        
        # Alert if high deviation
        if deviation > self.alert_threshold:
            self.total_alerts += 1
            logger.warning(
                f"[OracleVerification] ⚠️ HIGH DEVIATION ALERT: {token_pair} "
                f"SDK: ${price:.2f}, Chainlink: ${oracle_price:.2f}, "
                f"Deviation: {deviation*100:.2f}%"
            )
        
        # Update statistics
        if verified:
            self.total_passed += 1
        else:
            self.total_failed += 1
        
        oracle_data = {
            'oracle_type': 'chainlink',
            'oracle_price': oracle_price,
            'input_price': price,
            'deviation': deviation,
            'deviation_pct': round(deviation * 100, 4),
            'verified': verified,
            'chain': chain,
            'token_pair': token_pair,
            'timestamp': time.time()
        }
        
        logger.info(
            f"[OracleVerification] {token_pair} on {chain}: "
            f"${price:.2f} vs Chainlink ${oracle_price:.2f} "
            f"(deviation: {deviation*100:.2f}%) - {'✓ VERIFIED' if verified else '✗ FAILED'}"
        )
        
        return verified, deviation, oracle_data
    
    def _fetch_chainlink_price(
        self,
        w3: Web3,
        feeds: Dict[str, str],
        token_pair: str
    ) -> Optional[float]:
        """
        Fetch price from Chainlink oracle
        
        Returns:
            float: Price or None if unavailable
        """
        if token_pair not in feeds:
            logger.debug(f"[OracleVerification] No Chainlink feed for {token_pair}")
            return None
        
        feed_address = feeds[token_pair]
        
        try:
            # Create contract instance
            contract = w3.eth.contract(
                address=Web3.to_checksum_address(feed_address),
                abi=self.CHAINLINK_AGGREGATOR_ABI
            )
            
            # Get latest round data
            round_data = contract.functions.latestRoundData().call()
            answer = round_data[1]  # answer is second element
            
            # Get decimals
            decimals = contract.functions.decimals().call()
            
            # Convert to float
            price = float(answer) / (10 ** decimals)
            
            # Update cache
            cache_key = f"{w3.eth.chain_id}:{token_pair}"
            self.price_cache[cache_key] = {
                'price': price,
                'timestamp': time.time()
            }
            
            logger.debug(f"[OracleVerification] Chainlink {token_pair}: ${price:.2f}")
            
            return price
            
        except Exception as e:
            logger.error(f"[OracleVerification] Error fetching Chainlink price: {e}")
            return None
    
    def verify_price_with_uniswap_twap(
        self,
        pool_address: str,
        current_price: float,
        chain: str = 'polygon'
    ) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Verify a price against Uniswap V3 TWAP oracle
        
        Args:
            pool_address: Uniswap V3 pool address
            current_price: Current price to verify
            chain: Blockchain network
        
        Returns:
            (verified, deviation, oracle_data)
        """
        self.total_verifications += 1
        
        # Select Web3
        w3 = self.w3_polygon if chain == 'polygon' else self.w3_ethereum
        
        if not w3:
            return False, 0.0, {'error': 'no_connection'}
        
        try:
            # Create pool contract instance
            pool = w3.eth.contract(
                address=Web3.to_checksum_address(pool_address),
                abi=self.UNISWAP_V3_POOL_ABI
            )
            
            # Query TWAP
            seconds_agos = [self.twap_window, 0]  # [30min ago, now]
            tick_cumulatives, _ = pool.functions.observe(seconds_agos).call()
            
            # Calculate average tick
            tick_cumulative_delta = tick_cumulatives[1] - tick_cumulatives[0]
            time_delta = self.twap_window
            avg_tick = tick_cumulative_delta / time_delta
            
            # Convert tick to price
            twap_price = 1.0001 ** avg_tick
            
            # Calculate deviation
            deviation = abs(current_price - twap_price) / twap_price
            verified = deviation <= self.deviation_threshold
            
            if deviation > self.alert_threshold:
                self.total_alerts += 1
                logger.warning(
                    f"[OracleVerification] ⚠️ TWAP DEVIATION: "
                    f"Current: {current_price:.6f}, TWAP: {twap_price:.6f}, "
                    f"Deviation: {deviation*100:.2f}%"
                )
            
            if verified:
                self.total_passed += 1
            else:
                self.total_failed += 1
            
            oracle_data = {
                'oracle_type': 'uniswap_twap',
                'twap_price': twap_price,
                'input_price': current_price,
                'deviation': deviation,
                'deviation_pct': round(deviation * 100, 4),
                'verified': verified,
                'twap_window': self.twap_window,
                'pool_address': pool_address,
                'timestamp': time.time()
            }
            
            logger.info(
                f"[OracleVerification] TWAP verification: "
                f"{current_price:.6f} vs {twap_price:.6f} "
                f"(deviation: {deviation*100:.2f}%) - {'✓ VERIFIED' if verified else '✗ FAILED'}"
            )
            
            return verified, deviation, oracle_data
            
        except Exception as e:
            logger.error(f"[OracleVerification] Error fetching Uniswap TWAP: {e}")
            return False, 0.0, {'error': str(e)}
    
    def verify_with_consensus(
        self,
        prices: Dict[str, float],
        min_agreement: float = 0.01
    ) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Verify using cross-oracle consensus
        
        Args:
            prices: Dict of {oracle_name: price}
            min_agreement: Max % difference for consensus (0.01 = 1%)
        
        Returns:
            (consensus_reached, avg_price, consensus_data)
        """
        self.total_verifications += 1
        
        if len(prices) < self.consensus_min:
            logger.warning(
                f"[OracleVerification] Insufficient oracles for consensus: "
                f"{len(prices)} < {self.consensus_min}"
            )
            return False, 0.0, {'error': 'insufficient_oracles'}
        
        price_values = list(prices.values())
        avg_price = mean(price_values)
        
        # Check if all prices are within min_agreement of average
        max_deviation = max(abs(p - avg_price) / avg_price for p in price_values)
        
        consensus = max_deviation <= min_agreement
        
        if consensus:
            self.total_passed += 1
        else:
            self.total_failed += 1
        
        if max_deviation > self.alert_threshold:
            self.total_alerts += 1
            logger.warning(
                f"[OracleVerification] ⚠️ CONSENSUS DEVIATION: "
                f"Max deviation {max_deviation*100:.2f}% among oracles"
            )
        
        consensus_data = {
            'oracle_type': 'consensus',
            'oracle_prices': prices,
            'avg_price': avg_price,
            'max_deviation': max_deviation,
            'max_deviation_pct': round(max_deviation * 100, 4),
            'consensus': consensus,
            'num_oracles': len(prices),
            'timestamp': time.time()
        }
        
        logger.info(
            f"[OracleVerification] Consensus: {len(prices)} oracles, "
            f"avg ${avg_price:.2f}, max deviation {max_deviation*100:.2f}% - "
            f"{'✓ CONSENSUS' if consensus else '✗ NO CONSENSUS'}"
        )
        
        return consensus, avg_price, consensus_data
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get verification statistics"""
        total = max(self.total_verifications, 1)
        
        return {
            'total_verifications': self.total_verifications,
            'total_passed': self.total_passed,
            'total_failed': self.total_failed,
            'total_alerts': self.total_alerts,
            'pass_rate': round(self.total_passed / total, 4),
            'fail_rate': round(self.total_failed / total, 4),
            'alert_rate': round(self.total_alerts / total, 4)
        }
    
    def print_statistics(self):
        """Print verification statistics"""
        stats = self.get_statistics()
        
        print("\n" + "="*80)
        print("  ORACLE VERIFICATION STATISTICS")
        print("="*80)
        print(f"Total Verifications: {stats['total_verifications']}")
        print(f"Passed:              {stats['total_passed']} ({stats['pass_rate']*100:.1f}%)")
        print(f"Failed:              {stats['total_failed']} ({stats['fail_rate']*100:.1f}%)")
        print(f"Alerts:              {stats['total_alerts']} ({stats['alert_rate']*100:.1f}%)")
        print("="*80 + "\n")


if __name__ == "__main__":
    # Example usage
    oracle_manager = OracleVerificationManager()
    
    # Test Chainlink verification
    verified, deviation, data = oracle_manager.verify_price_with_chainlink(
        token_pair="ETH/USD",
        price=1850.00,
        chain="polygon"
    )
    
    print(f"\nChainlink Verification: {'✓ PASSED' if verified else '✗ FAILED'}")
    print(f"Deviation: {deviation*100:.2f}%")
    
    # Test consensus
    prices = {
        'chainlink': 1850.00,
        'uniswap': 1851.50,
        'balancer': 1849.00
    }
    
    consensus, avg_price, consensus_data = oracle_manager.verify_with_consensus(prices)
    
    print(f"\nConsensus Verification: {'✓ CONSENSUS' if consensus else '✗ NO CONSENSUS'}")
    print(f"Average Price: ${avg_price:.2f}")
    
    # Print statistics
    oracle_manager.print_statistics()
