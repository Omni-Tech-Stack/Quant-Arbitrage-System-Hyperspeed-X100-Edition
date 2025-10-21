#!/usr/bin/env python
"""
Merkle Reward Distributor
Batch reward/airdrop distribution using Merkle proofs
"""

import hashlib


class MerkleRewardDistributor:
    """Distribute rewards using Merkle trees for efficient on-chain verification"""
    
    def __init__(self):
        self.trees = {}
    
    def _hash(self, data: str) -> str:
        """Hash data for Merkle tree"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def build_tree(self, rewards: dict) -> dict:
        """Build Merkle tree from reward mappings"""
        # Simplified Merkle tree construction
        leaves = []
        for address, amount in rewards.items():
            leaf = self._hash(f"{address}:{amount}")
            leaves.append({"address": address, "amount": amount, "hash": leaf})
        
        # Build tree layers (simplified - single root)
        if not leaves:
            root = "0x" + "0" * 64
        else:
            # Combine all leaf hashes
            combined = "".join(leaf["hash"] for leaf in leaves)
            root = "0x" + self._hash(combined)
        
        tree = {
            "root": root,
            "leaves": leaves,
            "proofs": self._generate_proofs(leaves, root)
        }
        
        return tree
    
    def _generate_proofs(self, leaves: list, root: str) -> dict:
        """Generate Merkle proofs for each leaf"""
        proofs = {}
        for leaf in leaves:
            # Simplified proof - would be actual Merkle path in production
            proofs[leaf["address"]] = [root, leaf["hash"]]
        return proofs
    
    def get_proof(self, tree: dict, address: str) -> list:
        """Get Merkle proof for specific address"""
        return tree["proofs"].get(address, [])
    
    def verify_proof(self, tree: dict, address: str, amount: int, proof: list) -> bool:
        """Verify Merkle proof"""
        # Simplified verification
        expected_leaf = self._hash(f"{address}:{amount}")
        return expected_leaf in proof
    
    def distribute(self, merkle_tree: dict) -> dict:
        """Distribute rewards using Merkle tree"""
        root = merkle_tree['root']
        leaf_count = len(merkle_tree.get('leaves', []))
        
        print(f"[Merkle] Distributing rewards to {leaf_count} addresses")
        print(f"[Merkle] Root: {root[:16]}...")
        
        return {
            "status": "success",
            "root": root,
            "recipients": leaf_count,
            "tx_hash": "0x" + "a" * 64  # Simulated transaction hash
        }


if __name__ == "__main__":
    print("Merkle Reward Distributor - Ready")
