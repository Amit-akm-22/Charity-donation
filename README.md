# 🌟 GiveFlow — Blockchain-Verified Charity & Donation Platform

> A full-stack, cryptographically secure, and transparent charity donation platform powered by **Proof-of-Work Blockchain**, **Merkle Trees**, and **RSA-2048 Digital Signatures**.

---

## 📖 Overview

**GiveFlow** solves the core challenge of trust and transparency in charitable giving. Traditional donation platforms operate as opaque black boxes where donors have no cryptographic proof of how their funds were handled or whether records have been altered.

GiveFlow implements a transparent, tamper-evident ledger where:
- Every donation is mined into a **Proof-of-Work (PoW) Blockchain** with cryptographic hash pointers.
- Transactions are anchored into a **Merkle Tree**, providing verifiable cryptographic inclusion proofs.
- Every donation receipt is digitally signed using **RSA-2048 asymmetric encryption** with SHA-256.
- Anyone can audit and verify the entire chain and individual signatures in real time via an interactive dashboard.

---

## ✨ Key Features & Cryptographic Architecture

### 1. ⛓️ Proof-of-Work (PoW) Blockchain
- **Hash Pointer & Immutability:** Each block stores the `previous_hash`, creating an immutable cryptographic chain anchored to a **Genesis Block**.
- **Consensus & Mining:** SHA-256 mining loop iterates nonces to satisfy target difficulty (e.g., hash prefix `0000`).
- **Chain Validation Engine:** Real-time `/api/validate-chain` endpoint traverses every block and verifies hash pointers and PoW difficulty.

### 2. 🌳 Merkle Trees
- Calculates hierarchical SHA-256 Merkle root hashes across batches of donation transactions.
- Provides logarithmic-time cryptographic proofs (`/api/merkle-proof/<id>`) allowing light clients to verify a donation's inclusion without downloading the full ledger.

### 3. 🔐 RSA-2048 Digital Signatures (PKI)
- **Public Key Infrastructure (PKI):** Platform automatically provisions and manages an RSA-2048 keypair.
- **Tamper-Evident Receipts:** Every donation payload is signed with the platform's private key (`RSA-PSS` / `SHA-256`).
- **Independent Verification:** Donors can verify the authenticity of their receipts using the platform's public key (`/api/public-key` & `/api/verify-signature/<id>`).

### 4. 🎨 Next-Generation Cyber Glassmorphic UI
- **Cosmic Starfield & Nebula Canvas:** 200+ particle twinkling background with responsive depth.
- **Live Blockchain Explorer:** Visual chain inspection with hash links, mining stats, and nonce counters.
- **Interactive Merkle Tree Viewer:** Node-by-node visual representation of transaction hashing.
- **Cryptographic Signature Verifier:** One-click verification modal displaying the exact raw message, signature, and public key.

---

## 🛠️ Technology Stack

- **Backend:** Python 3.10+, Flask
- **Cryptography:** `cryptography` (RSA-2048, PSS, PKCS#1 v1.5), `hashlib` (SHA-256)
- **Database:** SQLite3 (zero-configuration, embedded relational store)
- **Frontend:** Vanilla HTML5, Modern CSS3 (Glassmorphism, CSS Custom Properties, Canvas API), JavaScript (ES6+)

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10 or higher
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/Amit-akm-22/Charity-donation.git
cd Charity-donation
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python app.py
```
The application will start on **`http://127.0.0.1:5000`**.

### 5. Run the Test Suite (25 Tests)
```bash
python -m unittest discover tests -v
```

### 6. Interactive CLI & Blockchain Audit
```bash
python cli.py audit          # Full cryptographic chain audit
python cli.py stats          # Platform donation and tax totals
python cli.py keys           # Inspect platform RSA-2048 public key
python cli.py merkle         # Calculate Merkle root and SPV proofs
```

### 7. Run Distributed Network Simulator (P2P Consensus)
```bash
python simulate_network.py   # Multi-node peer-to-peer consensus simulation
```

---

## 📡 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/` | `GET` | Main GiveFlow interactive explorer & donation portal |
| `/user/<name>` | `GET` | Personalized user donation tracking dashboard |
| `/api/donate` | `POST` | Process donation, mine PoW block, sign with RSA |
| `/api/chain` | `GET` | Retrieve the complete blockchain ledger |
| `/api/validate-chain` | `GET` | Validate integrity of all blocks and hash pointers |
| `/api/merkle-proof/<id>` | `GET` | Generate Merkle inclusion proof for a donation |
| `/api/verify-signature/<id>` | `POST` | Verify RSA digital signature for a donation |
| `/api/public-key` | `GET` | Export platform's RSA public key in PEM format |

---

## 📚 Academic Alignment

This project practically demonstrates the core concepts of:
- **Unit I – Fundamentals of Cryptography:**
  - Security Goals (Confidentiality, Integrity, Availability)
  - Symmetric & Asymmetric Encryption (RSA-2048)
  - Cryptographic Hash Functions (SHA-256)
  - Digital Signatures & PKI (Public Key Infrastructure)
  - Merkle Trees & Cryptographic Proofs
- **Unit II – Blockchain Basics & Distributed Ledger:**
  - Blockchain Architecture, Layers & Block Anatomy
  - Hash Pointers & Immutability
  - Mining, Proof of Work (PoW), Nonce & Difficulty
  - Tamper Detection & Trustless Systems

---

## 📄 License
This project is open source and available under the [MIT License](LICENSE).
