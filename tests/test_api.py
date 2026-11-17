"""
Unit & Integration Tests for GiveFlow Flask Endpoints
------------------------------------------------------
Tests:
  - Homepage GET /
  - User portal GET /user/<name>
  - Blockchain query GET /api/chain
  - Chain validation GET /api/chain/validate
  - Merkle tree GET /api/merkle
  - Merkle proof GET /api/merkle/proof/<block_index>
  - Public key retrieval GET /api/signature/public-key
  - Signature verification POST /api/signature/verify
  - Donation submission and block mining POST /api/donations
"""
import unittest
import json
from app import app, init_db


class TestGiveFlowAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        init_db()
        cls.client = app.test_client()

    def test_homepage_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"GiveFlow", response.data)

    def test_get_public_key(self):
        response = self.client.get("/api/signature/public-key")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("public_key_pem", data)
        self.assertTrue(data["public_key_pem"].startswith("-----BEGIN PUBLIC KEY-----"))

    def test_get_chain(self):
        response = self.client.get("/api/chain")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)  # At least genesis

    def test_validate_chain(self):
        response = self.client.get("/api/chain/validate")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("is_valid", data)
        self.assertTrue(data["is_valid"])

    def test_get_merkle(self):
        response = self.client.get("/api/merkle")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("root", data)
        self.assertIn("levels", data)
        self.assertIn("leaf_count", data)

    def test_get_merkle_proof_genesis(self):
        response = self.client.get("/api/merkle/proof/0")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["block_index"], 0)
        self.assertTrue(data["is_valid"])

    def test_donate_endpoint(self):
        payload = {
            "donor": "TestDonor",
            "recipient": "Clean Water Initiative",
            "amount": 75.0,
        }
        response = self.client.post(
            "/api/donations",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["donor"], "TestDonor")
        self.assertEqual(data["recipient"], "Clean Water Initiative")
        self.assertEqual(data["amount"], 75.0)
        self.assertIn("signature", data)
        self.assertIn("block_hash", data)
        self.assertTrue(data["block_hash"].startswith("00"))

        # Verify signature via the verify endpoint
        verify_resp = self.client.post(
            "/api/signature/verify",
            data=json.dumps({
                "signed_message": data["signed_message"],
                "signature": data["signature"],
            }),
            content_type="application/json",
        )
        self.assertEqual(verify_resp.status_code, 200)
        verify_data = verify_resp.get_json()
        self.assertTrue(verify_data["valid"])

    def test_user_portal(self):
        response = self.client.get("/user/TestDonor")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
