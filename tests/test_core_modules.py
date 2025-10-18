#!/usr/bin/env python3
"""
Unit tests for remaining core modules
Tests MEV relay, Merkle distribution, Analytics, and Protocol precheck
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from arb_request_encoder import encode_arbitrage_request, ArbRequestEncoder
from BillionaireBot_bloxroute_gateway_Version2 import send_private_transaction, MEVRelay
from BillionaireBot_merkle_sender_tree_Version2 import MerkleRewardDistributor
from defi_analytics_ml import MLAnalyticsEngine
from dex_protocol_precheck import DexProtocolPrecheck


class TestArbRequestEncoder(unittest.TestCase):
    """Test suite for Arbitrage Request Encoder"""
    
    def test_encoder_initialization(self):
        """Test encoder initializes"""
        encoder = ArbRequestEncoder()
        self.assertIsNotNone(encoder)
    
    def test_encode_simple_arbitrage(self):
        """Test encoding a simple arbitrage request"""
        opportunity = {
            'path': [
                {'dex': 'uniswap', 'token0': '0xA', 'token1': '0xB'},
                {'dex': 'sushiswap', 'token0': '0xB', 'token1': '0xA'}
            ],
            'initial_amount': 1000
        }
        
        encoded = encode_arbitrage_request(opportunity)
        self.assertIsNotNone(encoded)
        self.assertIsInstance(encoded, (str, bytes, dict))
    
    def test_encode_multi_hop_arbitrage(self):
        """Test encoding multi-hop arbitrage"""
        opportunity = {
            'path': [
                {'dex': 'uniswap', 'token0': '0xA', 'token1': '0xB'},
                {'dex': 'sushiswap', 'token0': '0xB', 'token1': '0xC'},
                {'dex': 'balancer', 'token0': '0xC', 'token1': '0xA'}
            ],
            'initial_amount': 5000
        }
        
        encoded = encode_arbitrage_request(opportunity)
        self.assertIsNotNone(encoded)


class TestMEVRelay(unittest.TestCase):
    """Test suite for MEV Relay Integration"""
    
    def test_relay_initialization(self):
        """Test MEV relay initializes"""
        relay = MEVRelay()
        self.assertIsNotNone(relay)
    
    def test_send_private_transaction(self):
        """Test sending private transaction"""
        calldata = "0x123456789"
        result = send_private_transaction(calldata)
        
        self.assertIsNotNone(result)
        # Should return transaction hash or status
    
    def test_relay_selection(self):
        """Test relay selection logic"""
        relay = MEVRelay()
        selected = relay.select_relay()
        
        self.assertIsNotNone(selected)
        self.assertIn(selected, ['bloxroute', 'flashbots', 'eden'])
    
    def test_transaction_obfuscation(self):
        """Test transaction obfuscation"""
        relay = MEVRelay()
        original_tx = {"to": "0xABC", "data": "0x123"}
        
        obfuscated = relay.obfuscate_transaction(original_tx)
        self.assertIsNotNone(obfuscated)
        self.assertIsInstance(obfuscated, dict)


class TestMerkleRewardDistributor(unittest.TestCase):
    """Test suite for Merkle Reward Distribution"""
    
    def test_distributor_initialization(self):
        """Test distributor initializes"""
        distributor = MerkleRewardDistributor()
        self.assertIsNotNone(distributor)
    
    def test_build_merkle_tree(self):
        """Test building Merkle tree from rewards"""
        rewards = {
            "0xAddress1": 100,
            "0xAddress2": 200,
            "0xAddress3": 150
        }
        
        distributor = MerkleRewardDistributor()
        tree = distributor.build_tree(rewards)
        
        self.assertIsNotNone(tree)
        self.assertIn('root', tree)
        self.assertIn('proofs', tree)
    
    def test_generate_proof(self):
        """Test generating Merkle proof for address"""
        rewards = {
            "0xAddress1": 100,
            "0xAddress2": 200
        }
        
        distributor = MerkleRewardDistributor()
        tree = distributor.build_tree(rewards)
        proof = distributor.get_proof(tree, "0xAddress1")
        
        self.assertIsNotNone(proof)
        self.assertIsInstance(proof, (list, dict))
    
    def test_verify_proof(self):
        """Test verifying Merkle proof"""
        rewards = {"0xAddress1": 100}
        
        distributor = MerkleRewardDistributor()
        tree = distributor.build_tree(rewards)
        proof = distributor.get_proof(tree, "0xAddress1")
        
        is_valid = distributor.verify_proof(tree, "0xAddress1", 100, proof)
        self.assertTrue(is_valid)
    
    def test_distribute_rewards(self):
        """Test reward distribution"""
        rewards = {
            "0xAddress1": 100,
            "0xAddress2": 200
        }
        
        distributor = MerkleRewardDistributor()
        tree = distributor.build_tree(rewards)
        result = distributor.distribute(tree)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)


class TestMLAnalyticsEngine(unittest.TestCase):
    """Test suite for ML Analytics Engine"""
    
    def test_engine_initialization(self):
        """Test ML engine initializes"""
        engine = MLAnalyticsEngine()
        self.assertIsNotNone(engine)
    
    def test_score_opportunities(self):
        """Test scoring opportunities with ML"""
        opportunities = [
            {'estimated_profit': 50, 'confidence': 0.8},
            {'estimated_profit': 100, 'confidence': 0.9}
        ]
        
        engine = MLAnalyticsEngine()
        best = engine.score_opportunities(opportunities)
        
        self.assertIsNotNone(best)
        self.assertIsInstance(best, dict)
    
    def test_add_trade_result(self):
        """Test logging trade results"""
        engine = MLAnalyticsEngine()
        
        opportunity = {'estimated_profit': 50}
        tx_hash = "0x123abc"
        
        engine.add_trade_result(opportunity, tx_hash)
        # Should not raise exception
    
    def test_retrain_model(self):
        """Test model retraining"""
        engine = MLAnalyticsEngine()
        
        # Add some training data
        for i in range(10):
            engine.add_trade_result({'estimated_profit': i * 10}, f"0x{i}")
        
        result = engine.retrain_model()
        self.assertIsNotNone(result)
    
    def test_get_statistics(self):
        """Test getting analytics statistics"""
        engine = MLAnalyticsEngine()
        
        stats = engine.get_statistics()
        self.assertIsInstance(stats, dict)
        self.assertIn('total_trades', stats)


class TestDexProtocolPrecheck(unittest.TestCase):
    """Test suite for DEX Protocol Precheck"""
    
    def test_precheck_initialization(self):
        """Test precheck initializes"""
        precheck = DexProtocolPrecheck(chain="polygon")
        self.assertIsNotNone(precheck)
        self.assertEqual(precheck.chain, "polygon")
    
    def test_run_full_precheck(self):
        """Test running full precheck"""
        precheck = DexProtocolPrecheck(chain="ethereum")
        result = precheck.run_full_precheck()
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
    
    def test_check_contract_validity(self):
        """Test contract validity check"""
        precheck = DexProtocolPrecheck()
        
        is_valid = precheck.check_contract("0x1234567890123456789012345678901234567890")
        self.assertIsInstance(is_valid, bool)
    
    def test_check_router_abi(self):
        """Test router ABI check"""
        precheck = DexProtocolPrecheck()
        
        result = precheck.check_router_abi("uniswap-v2")
        self.assertIsNotNone(result)
    
    def test_get_precheck_report(self):
        """Test getting precheck report"""
        precheck = DexProtocolPrecheck()
        precheck.run_full_precheck()
        
        report = precheck.get_report()
        self.assertIsInstance(report, dict)
        self.assertIn('timestamp', report)
        self.assertIn('chain', report)


def run_tests():
    """Run all tests and display results"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestArbRequestEncoder))
    suite.addTests(loader.loadTestsFromTestCase(TestMEVRelay))
    suite.addTests(loader.loadTestsFromTestCase(TestMerkleRewardDistributor))
    suite.addTests(loader.loadTestsFromTestCase(TestMLAnalyticsEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestDexProtocolPrecheck))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Display summary
    print("\n" + "=" * 80)
    print("CORE MODULES TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ All core module tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
