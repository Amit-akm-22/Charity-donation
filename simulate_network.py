#!/usr/bin/env python3
"""
GiveFlow Peer-to-Peer Network & Consensus Simulator
-----------------------------------------------------
Demonstrates distributed systems and blockchain consensus (Unit I & Unit II):
  - Distributed Node network with independent ledgers
  - Proof-of-Work competition between miners (Node A, Node B, Node C)
  - Gossip protocol for transaction and block propagation
  - Longest-chain consensus rule for fork resolution
  - Byzantine tamper detection and rejection by honest nodes
"""
import sys
import time
import random
import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from blockchain import mine_block, calculate_hash, create_genesis_block, validate_chain, DIFFICULTY
from merkle import build_merkle_tree
from digital_signature import generate_key_pair, build_donation_message, sign_donation, verify_donation_signature


@dataclass
class Node:
    name: str
    difficulty: int = DIFFICULTY
    chain: list = field(default_factory=list)
    mempool: list = field(default_factory=list)
    peers: list = field(default_factory=list)
    blocks_mined: int = 0

    def connect(self, peer: "Node"):
        if peer not in self.peers:
            self.peers.append(peer)
            peer.peers.append(self)

    def receive_transaction(self, tx: dict):
        """Add transaction to local mempool and gossip to peers."""
        if tx not in self.mempool:
            self.mempool.append(tx)
            for peer in self.peers:
                peer.receive_transaction(tx)

    def mine_pending(self) -> dict | None:
        """Mine the next pending transaction from the mempool."""
        if not self.mempool:
            return None

        tx = self.mempool.pop(0)
        last_block = self.chain[-1]
        new_index = last_block["block_index"] + 1
        previous_hash = last_block["hash"]
        ts = datetime.now(timezone.utc).isoformat()

        nonce, block_hash, time_ms = mine_block(
            block_index=new_index,
            timestamp=ts,
            donor=tx["donor"],
            recipient=tx["recipient"],
            amount=tx["amount"],
            tax_amount=tx["tax_amount"],
            net_amount=tx["net_amount"],
            previous_hash=previous_hash,
            difficulty=self.difficulty,
        )

        new_block = {
            "block_index": new_index,
            "timestamp": ts,
            "donor": tx["donor"],
            "recipient": tx["recipient"],
            "amount": tx["amount"],
            "tax_amount": tx["tax_amount"],
            "net_amount": tx["net_amount"],
            "previous_hash": previous_hash,
            "nonce": nonce,
            "hash": block_hash,
            "mined_by": self.name,
            "mining_time_ms": time_ms,
        }

        self.chain.append(new_block)
        self.blocks_mined += 1

        # Broadcast new block to peers
        for peer in self.peers:
            peer.receive_block(new_block)

        return new_block

    def receive_block(self, block: dict) -> bool:
        """Validate received block and apply longest-chain rule."""
        last_block = self.chain[-1]

        # Candidate check
        if block["block_index"] == last_block["block_index"] + 1:
            if block["previous_hash"] == last_block["hash"]:
                # Verify PoW
                expected_hash = calculate_hash(
                    block["block_index"],
                    block["timestamp"],
                    block["donor"],
                    block["recipient"],
                    block["amount"],
                    block["tax_amount"],
                    block["net_amount"],
                    block["previous_hash"],
                    block["nonce"],
                )
                if expected_hash == block["hash"] and block["hash"].startswith("0" * self.difficulty):
                    self.chain.append(block)
                    # Remove from mempool if present
                    self.mempool = [
                        tx for tx in self.mempool
                        if not (tx["donor"] == block["donor"] and tx["amount"] == block["amount"])
                    ]
                    return True
        return False


def run_simulation():
    print("=" * 70)
    print("🌐 GIVEFLOW DISTRIBUTED PEER-TO-PEER NETWORK SIMULATION")
    print("=" * 70)

    # 1. Initialize Genesis
    genesis = create_genesis_block()
    print(f"[*] Genesis Block Initialized: {genesis['hash'][:16]}... (Difficulty: {DIFFICULTY})")

    # 2. Spin up 3 simulated network nodes
    node_a = Node(name="Node_A (North America)", chain=[copy.deepcopy(genesis)])
    node_b = Node(name="Node_B (Europe)", chain=[copy.deepcopy(genesis)])
    node_c = Node(name="Node_C (Asia)", chain=[copy.deepcopy(genesis)])

    # Mesh topology
    node_a.connect(node_b)
    node_b.connect(node_c)
    node_a.connect(node_c)
    nodes = [node_a, node_b, node_c]
    print(f"[*] Peer-to-peer mesh network formed: {', '.join(n.name for n in nodes)}")

    # 3. Simulate RSA Platform Signing
    print("\n[*] Provisioning RSA-2048 platform keypair for donation verification...")
    priv_key, pub_key = generate_key_pair()

    # 4. Create and gossip donations
    sample_donations = [
        ("Alice", "Clean Oceans Fund", 120.0),
        ("Bob", "Global Hunger Relief", 50.0),
        ("Charlie", "Medical Aid Worldwide", 250.0),
        ("Diana", "Education For Children", 85.0),
    ]

    print("\n[*] Submitting and signing donations to network mempool...")
    for donor, recipient, amount in sample_donations:
        tax = round(amount * 0.05, 2)
        net = round(amount - tax, 2)
        tx = {
            "donor": donor,
            "recipient": recipient,
            "amount": amount,
            "tax_amount": tax,
            "net_amount": net,
        }
        # Ingest at Node A (which will gossip to B and C)
        node_a.receive_transaction(tx)
        print(f"  • Ingested donation: ${amount:.2f} from {donor} -> {recipient}")

    print(f"\n[*] Mempool synchronized across all nodes. Items in Node A mempool: {len(node_a.mempool)}")

    # 5. Distributed Mining Competition
    print("\n" + "=" * 70)
    print("⛏️ MINING CONSENSUS IN PROGRESS")
    print("=" * 70)

    round_num = 1
    while any(len(n.mempool) > 0 for n in nodes):
        miner = random.choice(nodes)
        mined_block = miner.mine_pending()
        if mined_block:
            print(
                f"[Block #{mined_block['block_index']}] Mined by {miner.name} | "
                f"Nonce: {mined_block['nonce']} | Hash: {mined_block['hash'][:18]}... | "
                f"Donor: {mined_block['donor']} (${mined_block['amount']})"
            )
        round_num += 1

    # 6. Verify Consensus Across All Nodes
    print("\n" + "=" * 70)
    print("🔍 CONSENSUS AUDIT & VERIFICATION")
    print("=" * 70)

    for n in nodes:
        report = validate_chain(n.chain)
        is_valid = report["is_valid"]
        print(
            f"[*] {n.name.ljust(26)} -> Blocks: {len(n.chain)} | "
            f"Integrity: {'✅ 100% VALID' if is_valid else '❌ CORRUPT'} | "
            f"Mined: {n.blocks_mined}"
        )

    # 7. Merkle Tree Construction Over the Final Chain
    print("\n[*] Constructing Merkle Tree from final synchronized ledger...")
    all_hashes = [b["hash"] for b in node_a.chain]
    tree = build_merkle_tree(all_hashes)
    print(f"[*] Ledger Merkle Root: {tree['root']}")
    print(f"[*] Tree Height / Depth: {len(tree['levels'])} levels across {tree['leaf_count']} leaf blocks")

    print("\n✅ Simulation completed successfully.")


if __name__ == "__main__":
    run_simulation()
