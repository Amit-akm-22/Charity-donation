import hashlib
import time
from datetime import datetime, timezone

DIFFICULTY = 2  # Mining difficulty: hash must start with "00"
DIFFICULTY_PREFIX = "0" * DIFFICULTY


def calculate_hash(
    block_index: int,
    timestamp: str,
    donor: str,
    recipient: str,
    amount: float,
    tax_amount: float,
    net_amount: float,
    previous_hash: str,
    nonce: int,
) -> str:
    payload = f"{block_index}|{timestamp}|{donor}|{recipient}|{float(amount):.2f}|{float(tax_amount):.2f}|{float(net_amount):.2f}|{previous_hash}|{nonce}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def mine_block(
    block_index: int,
    timestamp: str,
    donor: str,
    recipient: str,
    amount: float,
    tax_amount: float,
    net_amount: float,
    previous_hash: str,
    difficulty: int = DIFFICULTY,
):
    prefix = "0" * difficulty
    nonce = 0
    start_time = time.time()
    while True:
        current_hash = calculate_hash(
            block_index,
            timestamp,
            donor,
            recipient,
            amount,
            tax_amount,
            net_amount,
            previous_hash,
            nonce,
        )
        if current_hash.startswith(prefix):
            mining_time_ms = round((time.time() - start_time) * 1000, 2)
            return nonce, current_hash, mining_time_ms
        nonce += 1


def create_genesis_block():
    timestamp = "2026-01-01T00:00:00+00:00"
    prev_hash = "0" * 64
    nonce, block_hash, _ = mine_block(
        block_index=0,
        timestamp=timestamp,
        donor="GENESIS",
        recipient="NETWORK",
        amount=0.0,
        tax_amount=0.0,
        net_amount=0.0,
        previous_hash=prev_hash,
    )
    return {
        "block_index": 0,
        "timestamp": timestamp,
        "donor": "GENESIS",
        "recipient": "NETWORK",
        "amount": 0.0,
        "tax_amount": 0.0,
        "net_amount": 0.0,
        "previous_hash": prev_hash,
        "nonce": nonce,
        "hash": block_hash,
    }


def validate_chain(blocks: list) -> dict:
    if not blocks:
        return {"is_valid": True, "total_blocks": 0, "message": "Blockchain is empty"}

    for i in range(len(blocks)):
        current = blocks[i]
        recorded_hash = current.get("hash") or current.get("block_hash") or ""
        expected_hash = calculate_hash(
            current["block_index"],
            current["timestamp"],
            current["donor"],
            current["recipient"],
            current["amount"],
            current["tax_amount"],
            current["net_amount"],
            current["previous_hash"],
            current["nonce"],
        )

        if recorded_hash != expected_hash:
            return {
                "is_valid": False,
                "tampered_index": current["block_index"],
                "reason": f"Hash mismatch at block #{current['block_index']}: data was altered!",
                "expected_hash": expected_hash,
                "recorded_hash": recorded_hash,
            }

        if not recorded_hash.startswith(DIFFICULTY_PREFIX):
            return {
                "is_valid": False,
                "tampered_index": current["block_index"],
                "reason": f"Proof of work invalid at block #{current['block_index']} (does not start with {DIFFICULTY_PREFIX})",
            }

        if i > 0:
            previous = blocks[i - 1]
            prev_recorded = previous.get("hash") or previous.get("block_hash") or ""
            if current["previous_hash"] != prev_recorded:
                return {
                    "is_valid": False,
                    "tampered_index": current["block_index"],
                    "reason": f"Broken chain link at block #{current['block_index']}: previous_hash does not match block #{previous['block_index']} hash!",
                    "expected_previous_hash": prev_recorded,
                    "recorded_previous_hash": current["previous_hash"],
                }

    return {
        "is_valid": True,
        "total_blocks": len(blocks),
        "difficulty": DIFFICULTY,
        "difficulty_prefix": DIFFICULTY_PREFIX,
        "message": f"All {len(blocks)} blocks are cryptographically verified and intact.",
    }
