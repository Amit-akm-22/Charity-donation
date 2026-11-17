#!/usr/bin/env python3
"""
GiveFlow CLI — Blockchain & Cryptography Management Utility
------------------------------------------------------------
Provides administrative and auditing capabilities for the GiveFlow
charity donation platform:
  - Blockchain integrity audit
  - Proof-of-Work manual mining
  - Merkle tree calculations & proofs
  - RSA-2048 digital signature generation and verification
  - Platform key inspection
"""
import sys
import argparse
import sqlite3
import json
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from blockchain import (
    calculate_hash,
    mine_block,
    validate_chain,
    create_genesis_block,
    DIFFICULTY,
)
from merkle import build_merkle_tree, get_merkle_proof, verify_merkle_proof
from digital_signature import (
    load_or_create_keys,
    build_donation_message,
    sign_donation,
    verify_donation_signature,
    get_public_key_pem,
)

DB_PATH = "donations.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def command_audit(args):
    """Audit the complete blockchain stored in SQLite."""
    print("=" * 60)
    print("🔍 GIVINGFLOW BLOCKCHAIN AUDIT")
    print("=" * 60)

    try:
        conn = get_db_connection()
    except Exception as e:
        print(f"[-] Could not connect to database {DB_PATH}: {e}")
        return 1

    genesis_row = conn.execute("SELECT * FROM genesis WHERE id=0").fetchone()
    if not genesis_row:
        print("[-] Genesis block not found in database!")
        conn.close()
        return 1

    donations = conn.execute("SELECT * FROM donations ORDER BY block_index ASC").fetchall()
    conn.close()

    chain = [
        {
            "block_index": 0,
            "block_hash": genesis_row["block_hash"],
            "previous_hash": "0" * 64,
            "timestamp": genesis_row["timestamp"],
            "nonce": genesis_row["nonce"],
            "donor": "GENESIS",
            "recipient": "NETWORK",
            "amount": 0.0,
            "tax_amount": 0.0,
            "net_amount": 0.0,
            "mining_time_ms": 0.0,
        }
    ]

    for d in donations:
        chain.append({
            "block_index": d["block_index"],
            "block_hash": d["block_hash"],
            "previous_hash": d["previous_hash"],
            "timestamp": d["timestamp"],
            "nonce": d["nonce"],
            "donor": d["donor"],
            "recipient": d["recipient"],
            "amount": d["amount"],
            "tax_amount": d["tax_amount"],
            "net_amount": d["net_amount"],
            "mining_time_ms": d["mining_time_ms"],
        })

    report = validate_chain(chain)
    is_valid = report["is_valid"]

    print(f"Total Blocks in Chain : {report.get('total_blocks', len(chain))}")
    print(f"Mining Difficulty     : {DIFFICULTY} leading zeros")
    print(f"Chain Integrity Status: {'✅ VALID' if is_valid else '❌ CORRUPTED'}")

    if not is_valid:
        print("\nAudit Failure:")
        print(f"  • Block #{report.get('tampered_index')}: {report.get('reason')}")
        return 1
    else:
        print("\nAll hash pointers, PoW nonces, and block transitions verified successfully.")
        return 0


def command_keys(args):
    """Display or regenerate RSA platform keys."""
    print("=" * 60)
    print("🔐 RSA-2048 PLATFORM PUBLIC KEY")
    print("=" * 60)
    priv_key, pub_key = load_or_create_keys()
    pem = get_public_key_pem(pub_key)
    print(pem)


def command_merkle(args):
    """Compute Merkle Tree for current donations or given list."""
    print("=" * 60)
    print("🌳 MERKLE TREE CALCULATION")
    print("=" * 60)

    conn = get_db_connection()
    rows = conn.execute("SELECT id, donor, recipient, amount, timestamp FROM donations ORDER BY id ASC").fetchall()
    conn.close()

    if not rows:
        print("No transactions found in database.")
        return 0

    leaf_hashes = [
        f"{r['id']}_{r['donor']}_{r['amount']}_{r['timestamp']}"
        for r in rows
    ]
    from merkle import sha256
    leaves = [sha256(h) for h in leaf_hashes]

    tree = build_merkle_tree(leaves)
    print(f"Transaction Count: {len(leaves)}")
    print(f"Tree Levels      : {len(tree['levels'])}")
    print(f"Merkle Root Hash : {tree['root']}")

    if args.proof_id is not None:
        target_idx = None
        for i, r in enumerate(rows):
            if r["id"] == args.proof_id:
                target_idx = i
                break

        if target_idx is None:
            print(f"[-] Donation ID #{args.proof_id} not found in tree.")
        else:
            print(f"\nGenerating Proof for Donation ID #{args.proof_id} (Leaf #{target_idx})...")
            proof = get_merkle_proof(leaves, target_idx)
            print(json.dumps(proof, indent=2))
            is_valid = verify_merkle_proof(leaves[target_idx], proof, tree["root"])
            print(f"Verification Result: {'✅ VERIFIED' if is_valid else '❌ INVALID'}")


def command_stats(args):
    """Show platform statistics and totals."""
    conn = get_db_connection()
    donations = conn.execute("SELECT * FROM donations").fetchall()
    conn.close()

    total_donated = sum(d["amount"] for d in donations)
    total_tax = sum(d["tax_amount"] for d in donations)
    total_net = sum(d["net_amount"] for d in donations)

    print("=" * 60)
    print("📊 GIVEFLOW PLATFORM METRICS")
    print("=" * 60)
    print(f"Total Transactions : {len(donations)}")
    print(f"Total Volume       : ${total_donated:,.2f}")
    print(f"Platform Tax (5%)  : ${total_tax:,.2f}")
    print(f"Charity Distributed: ${total_net:,.2f}")


def main():
    parser = argparse.ArgumentParser(
        description="GiveFlow Blockchain & Cryptography Management CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Audit command
    subparsers.add_parser("audit", help="Verify cryptographic integrity of the blockchain")

    # Keys command
    subparsers.add_parser("keys", help="Inspect platform RSA-2048 public key")

    # Merkle command
    merkle_parser = subparsers.add_parser("merkle", help="Compute Merkle root and proofs")
    merkle_parser.add_argument("--proof-id", type=int, help="Donation ID to generate inclusion proof for")

    # Stats command
    subparsers.add_parser("stats", help="Display platform and financial metrics")

    args = parser.parse_args()

    if args.command == "audit":
        sys.exit(command_audit(args))
    elif args.command == "keys":
        command_keys(args)
    elif args.command == "merkle":
        command_merkle(args)
    elif args.command == "stats":
        command_stats(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
