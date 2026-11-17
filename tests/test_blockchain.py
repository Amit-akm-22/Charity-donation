"""
Unit Tests for GiveFlow Blockchain Engine
------------------------------------------
Tests:
  - Hash calculation determinism
  - Proof-of-Work mining difficulty compliance
  - Genesis block creation
  - Chain validation with valid blocks
  - Tamper detection (modified amounts, broken previous_hash)
"""
import unittest
from blockchain import (
    calculate_hash,
    mine_block,
    create_genesis_block,
    validate_chain,
    DIFFICULTY,
)


class TestBlockchain(unittest.TestCase):

    def setUp(self):
        self.genesis = create_genesis_block()

    def test_genesis_block_structure(self):
        self.assertEqual(self.genesis["block_index"], 0)
        self.assertEqual(self.genesis["previous_hash"], "0" * 64)
        self.assertTrue(self.genesis["hash"].startswith("0" * DIFFICULTY))
        self.assertGreaterEqual(self.genesis["nonce"], 0)

    def test_calculate_hash_deterministic(self):
        h1 = calculate_hash(1, "2026-01-01T00:00:00", "Alice", "Charity A", 100.0, 5.0, 95.0, "0"*64, 42)
        h2 = calculate_hash(1, "2026-01-01T00:00:00", "Alice", "Charity A", 100.0, 5.0, 95.0, "0"*64, 42)
        self.assertEqual(h1, h2)

    def test_calculate_hash_avalanche_effect(self):
        """Even 1 cent difference should drastically change the hash (SHA-256 property)."""
        h1 = calculate_hash(1, "2026-01-01T00:00:00", "Alice", "Charity A", 100.00, 5.0, 95.0, "0"*64, 1)
        h2 = calculate_hash(1, "2026-01-01T00:00:00", "Alice", "Charity A", 100.01, 5.0, 95.0, "0"*64, 1)
        self.assertNotEqual(h1, h2)

    def test_mine_block_difficulty(self):
        nonce, block_hash, time_ms = mine_block(
            block_index=1,
            timestamp="2026-01-01T12:00:00",
            donor="Bob",
            recipient="Save Wildlife",
            amount=50.0,
            tax_amount=2.5,
            net_amount=47.5,
            previous_hash=self.genesis["hash"],
            difficulty=2,
        )
        self.assertTrue(block_hash.startswith("00"))
        self.assertGreaterEqual(time_ms, 0)

    def test_validate_valid_chain(self):
        nonce, hash_1, _ = mine_block(
            1, "2026-01-01T12:00:00", "Bob", "Charity", 50.0, 2.5, 47.5, self.genesis["hash"]
        )
        chain = [
            {
                "block_index": 0,
                "block_hash": self.genesis["hash"],
                "previous_hash": "0" * 64,
                "timestamp": self.genesis["timestamp"],
                "nonce": self.genesis["nonce"],
                "donor": "GENESIS",
                "recipient": "NETWORK",
                "amount": 0.0,
                "tax_amount": 0.0,
                "net_amount": 0.0,
            },
            {
                "block_index": 1,
                "block_hash": hash_1,
                "previous_hash": self.genesis["hash"],
                "timestamp": "2026-01-01T12:00:00",
                "nonce": nonce,
                "donor": "Bob",
                "recipient": "Charity",
                "amount": 50.0,
                "tax_amount": 2.5,
                "net_amount": 47.5,
            },
        ]
        report = validate_chain(chain)
        self.assertTrue(report["is_valid"])

    def test_detect_tampered_chain(self):
        nonce, hash_1, _ = mine_block(
            1, "2026-01-01T12:00:00", "Bob", "Charity", 50.0, 2.5, 47.5, self.genesis["hash"]
        )
        tampered_chain = [
            {
                "block_index": 0,
                "block_hash": self.genesis["hash"],
                "previous_hash": "0" * 64,
                "timestamp": self.genesis["timestamp"],
                "nonce": self.genesis["nonce"],
                "donor": "GENESIS",
                "recipient": "NETWORK",
                "amount": 0.0,
                "tax_amount": 0.0,
                "net_amount": 0.0,
            },
            {
                "block_index": 1,
                "block_hash": hash_1,
                "previous_hash": self.genesis["hash"],
                "timestamp": "2026-01-01T12:00:00",
                "nonce": nonce,
                "donor": "Bob",
                "recipient": "Charity",
                "amount": 50000.0,  # TAMPERED
                "tax_amount": 2.5,
                "net_amount": 47.5,
            },
        ]
        report = validate_chain(tampered_chain)
        self.assertFalse(report["is_valid"])
        self.assertIn("reason", report)


if __name__ == "__main__":
    unittest.main()
