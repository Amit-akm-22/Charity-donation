"""
Unit Tests for Merkle Tree Implementation
------------------------------------------
Tests:
  - Empty tree handling
  - Single leaf tree
  - Odd vs even leaf count balancing
  - Merkle inclusion proof generation
  - Proof verification succeeds for valid leaf
  - Proof verification fails for altered leaf or invalid root
"""
import unittest
from merkle import (
    sha256,
    merkle_hash_pair,
    build_merkle_tree,
    get_merkle_proof,
    verify_merkle_proof,
)


class TestMerkleTree(unittest.TestCase):

    def setUp(self):
        self.sample_leaves = [
            sha256(f"donation_tx_{i}") for i in range(1, 5)
        ]

    def test_empty_tree(self):
        tree = build_merkle_tree([])
        self.assertEqual(tree["leaf_count"], 0)
        self.assertEqual(tree["levels"], [])
        self.assertIn("root", tree)

    def test_single_leaf_tree(self):
        leaf = sha256("single_tx")
        tree = build_merkle_tree([leaf])
        self.assertEqual(tree["root"], leaf)
        self.assertEqual(tree["leaf_count"], 1)

    def test_even_leaves_merkle_root(self):
        # 4 leaves -> level 0 (4), level 1 (2), level 2 (1 root)
        tree = build_merkle_tree(self.sample_leaves)
        self.assertEqual(len(tree["levels"]), 3)
        self.assertEqual(tree["leaf_count"], 4)

        # Manually compute root
        h01 = merkle_hash_pair(self.sample_leaves[0], self.sample_leaves[1])
        h23 = merkle_hash_pair(self.sample_leaves[2], self.sample_leaves[3])
        expected_root = merkle_hash_pair(h01, h23)
        self.assertEqual(tree["root"], expected_root)

    def test_odd_leaves_handling(self):
        # 3 leaves -> 3rd leaf is duplicated
        leaves_3 = self.sample_leaves[:3]
        tree = build_merkle_tree(leaves_3)
        self.assertEqual(tree["leaf_count"], 3)
        self.assertIsNotNone(tree["root"])

    def test_merkle_proof_verification(self):
        tree = build_merkle_tree(self.sample_leaves)
        root = tree["root"]

        for idx, leaf in enumerate(self.sample_leaves):
            proof = get_merkle_proof(self.sample_leaves, idx)
            is_valid = verify_merkle_proof(leaf, proof, root)
            self.assertTrue(is_valid, f"Proof failed for leaf index {idx}")

    def test_merkle_proof_detects_tampering(self):
        tree = build_merkle_tree(self.sample_leaves)
        root = tree["root"]

        # Valid proof for leaf 0
        proof = get_merkle_proof(self.sample_leaves, 0)

        # Attacker tries to verify a fabricated transaction with leaf 0's proof
        fake_leaf = sha256("fake_fraudulent_tx")
        is_valid = verify_merkle_proof(fake_leaf, proof, root)
        self.assertFalse(is_valid)


if __name__ == "__main__":
    unittest.main()
