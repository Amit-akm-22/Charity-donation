"""
Backfill script: assign block_index, nonce, block_hash, previous_hash
to all existing donations that were inserted before the blockchain was added.
Run once: python backfill_blockchain.py
"""
import sqlite3
from blockchain import mine_block

DB = "donations.db"

def get_genesis_hash():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT block_hash FROM genesis WHERE id=0").fetchone()
    conn.close()
    return row["block_hash"] if row else "0" * 64


def backfill():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # Get all donations ordered by id
    rows = conn.execute("SELECT * FROM donations ORDER BY id ASC").fetchall()

    # Determine which ones already have a valid block_hash
    already_done = [r for r in rows if r["block_hash"] and r["block_hash"] != ""]
    to_backfill = [r for r in rows if not r["block_hash"] or r["block_hash"] == ""]

    print(f"Total donations: {len(rows)}")
    print(f"Already have blockchain data: {len(already_done)}")
    print(f"Need backfilling: {len(to_backfill)}")

    if not to_backfill:
        print("Nothing to backfill. All good!")
        conn.close()
        return

    # Determine previous hash and index starting point
    if already_done:
        last_done = max(already_done, key=lambda r: r["block_index"])
        prev_hash = last_done["block_hash"]
        next_index = last_done["block_index"] + 1
    else:
        prev_hash = get_genesis_hash()
        next_index = 1

    print(f"\nStarting from block_index={next_index}, prev_hash={prev_hash[:16]}...")

    for i, row in enumerate(to_backfill):
        blk = next_index + i
        nonce, block_hash, mining_time_ms = mine_block(
            block_index=blk,
            timestamp=row["timestamp"],
            donor=row["donor"],
            recipient=row["recipient"],
            amount=row["amount"],
            tax_amount=row["tax_amount"],
            net_amount=row["net_amount"],
            previous_hash=prev_hash,
        )
        conn.execute(
            """UPDATE donations
               SET block_index=?, block_hash=?, previous_hash=?, nonce=?, mining_time_ms=?
               WHERE id=?""",
            (blk, block_hash, prev_hash, nonce, mining_time_ms, row["id"]),
        )
        conn.commit()
        prev_hash = block_hash
        print(f"  Block #{blk} mined | id={row['id']} | hash={block_hash[:16]}... | nonce={nonce} | {mining_time_ms}ms")

    print(f"\nDone! {len(to_backfill)} blocks backfilled.")
    conn.close()


if __name__ == "__main__":
    backfill()
