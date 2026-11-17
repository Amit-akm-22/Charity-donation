"""Backfill RSA signatures for existing donations that have empty signature field."""
from digital_signature import load_or_create_keys, build_donation_message, sign_donation
import sqlite3

DB = "donations.db"
priv, pub = load_or_create_keys()
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT * FROM donations ORDER BY id ASC").fetchall()
count = 0
for r in rows:
    if not r["signature"] or r["signature"] == "":
        msg = build_donation_message(
            donor=r["donor"], recipient=r["recipient"],
            amount=r["amount"], tax_amount=r["tax_amount"], net_amount=r["net_amount"],
            timestamp=r["timestamp"], block_index=r["block_index"], block_hash=r["block_hash"],
        )
        sig = sign_donation(priv, msg)
        conn.execute("UPDATE donations SET signature=?, signed_message=? WHERE id=?", (sig, msg, r["id"]))
        conn.commit()
        count += 1
        print(f"  Signed id={r['id']} block#{r['block_index']} -> {sig[:30]}...")
print(f"Done. {count} donations signed.")
conn.close()
