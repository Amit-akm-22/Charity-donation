"""
Unit Tests for RSA Digital Signatures & PKI
--------------------------------------------
Tests:
  - RSA-2048 key generation
  - Donation message canonicalization
  - Signature signing & verification
  - Tamper detection when message is altered
"""
import unittest
from digital_signature import (
    generate_key_pair,
    build_donation_message,
    sign_donation,
    verify_donation_signature,
    get_public_key_pem,
)


class TestDigitalSignature(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.priv_key, cls.pub_key = generate_key_pair()

    def test_key_generation(self):
        self.assertIsNotNone(self.priv_key)
        self.assertIsNotNone(self.pub_key)
        self.assertEqual(self.priv_key.key_size, 2048)
        pem = get_public_key_pem(self.pub_key)
        self.assertTrue(pem.startswith("-----BEGIN PUBLIC KEY-----"))

    def test_canonical_message_format(self):
        msg = build_donation_message(
            donor="Alice",
            recipient="Food Bank",
            amount=150.0,
            tax_amount=7.5,
            net_amount=142.5,
            timestamp="2026-02-01T10:00:00",
            block_index=5,
            block_hash="abc123",
        )
        self.assertIn("donor=Alice", msg)
        self.assertIn("recipient=Food Bank", msg)
        self.assertIn("amount=150.00", msg)
        self.assertIn("block=5", msg)
        self.assertIn("hash=abc123", msg)

    def test_valid_signature_verification(self):
        msg = build_donation_message("Alice", "Food Bank", 100.0, 5.0, 95.0, "2026-01-01", 1, "00abc")
        sig = sign_donation(self.priv_key, msg)
        self.assertTrue(len(sig) > 64)

        result = verify_donation_signature(self.pub_key, msg, sig)
        self.assertTrue(result["valid"])

    def test_tampered_message_fails_verification(self):
        msg = build_donation_message("Alice", "Food Bank", 100.0, 5.0, 95.0, "2026-01-01", 1, "00abc")
        sig = sign_donation(self.priv_key, msg)

        # Altered message: Alice tries to claim she gave $1000
        tampered_msg = build_donation_message("Alice", "Food Bank", 1000.0, 5.0, 95.0, "2026-01-01", 1, "00abc")
        result = verify_donation_signature(self.pub_key, tampered_msg, sig)
        self.assertFalse(result["valid"])

    def test_corrupted_signature_fails_verification(self):
        msg = build_donation_message("Alice", "Food Bank", 100.0, 5.0, 95.0, "2026-01-01", 1, "00abc")
        corrupted_sig = "aW52YWxpZHNpZ25hdHVyZQ=="  # base64 'invalidsignature'
        result = verify_donation_signature(self.pub_key, msg, corrupted_sig)
        self.assertFalse(result["valid"])


if __name__ == "__main__":
    unittest.main()
