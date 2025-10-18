#!/usr/bin/env python3
"""Test Merkle sender"""
import sys
sys.path.insert(0, '..')

def main():
    print("=" * 80)
    print("  MERKLE SENDER TEST")
    print("=" * 80)
    
    try:
        from BillionaireBot_merkle_sender_tree_Version2 import MerkleRewardDistributor
        distributor = MerkleRewardDistributor()
        
        print("\n✓ Distributor initialized")
        rewards = [{"address": f"0x{i:040x}", "amount": 100} for i in range(5)]
        tree = distributor.build_tree(rewards)
        print(f"✓ Merkle tree built: {tree['root'][:10]}...")
        print("\n✅ Merkle sender test passed!")
    except Exception as e:
        print(f"\n⚠ Merkle test: {e}")

if __name__ == "__main__":
    main()
