import sqlite3
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify
from blockchain import mine_block, calculate_hash, create_genesis_block, validate_chain
from merkle import build_merkle_tree, get_merkle_proof, verify_merkle_proof
from digital_signature import (
    load_or_create_keys,
    build_donation_message,
    sign_donation,
    verify_donation_signature,
    get_public_key_pem,
)

app = Flask(__name__)
DB = "donations.db"
TAX_RATE = 0.05  # 5% platform tax

# Load / create RSA key pair at startup
_private_key, _public_key = load_or_create_keys()


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS donations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                donor TEXT NOT NULL,
                recipient TEXT NOT NULL,
                amount REAL NOT NULL,
                tax_amount REAL NOT NULL,
                net_amount REAL NOT NULL,
                timestamp TEXT NOT NULL,
                block_index INTEGER NOT NULL DEFAULT 0,
                block_hash TEXT NOT NULL DEFAULT '',
                previous_hash TEXT NOT NULL DEFAULT '',
                nonce INTEGER NOT NULL DEFAULT 0,
                mining_time_ms REAL NOT NULL DEFAULT 0,
                signature TEXT NOT NULL DEFAULT '',
                signed_message TEXT NOT NULL DEFAULT ''
            )
            """
        )
        # Migrate existing DB if columns are missing
        existing = [col[1] for col in conn.execute("PRAGMA table_info(donations)").fetchall()]
        for col, typedef in [
            ("block_index",    "INTEGER NOT NULL DEFAULT 0"),
            ("block_hash",     "TEXT NOT NULL DEFAULT ''"),
            ("previous_hash",  "TEXT NOT NULL DEFAULT ''"),
            ("nonce",          "INTEGER NOT NULL DEFAULT 0"),
            ("mining_time_ms", "REAL NOT NULL DEFAULT 0"),
            ("signature",      "TEXT NOT NULL DEFAULT ''"),
            ("signed_message", "TEXT NOT NULL DEFAULT ''"),
        ]:
            if col not in existing:
                conn.execute(f"ALTER TABLE donations ADD COLUMN {col} {typedef}")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS genesis (
                id INTEGER PRIMARY KEY,
                block_hash TEXT NOT NULL,
                nonce INTEGER NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )
        genesis_exists = conn.execute("SELECT COUNT(*) FROM genesis").fetchone()[0]
        if genesis_exists == 0:
            g = create_genesis_block()
            conn.execute(
                "INSERT INTO genesis (id, block_hash, nonce, timestamp) VALUES (0, ?, ?, ?)",
                (g["hash"], g["nonce"], g["timestamp"]),
            )


init_db()


def get_genesis_hash() -> str:
    with get_db() as conn:
        row = conn.execute("SELECT block_hash FROM genesis WHERE id=0").fetchone()
        return row["block_hash"] if row else "0" * 64


def get_last_block_hash() -> tuple[int, str]:
    with get_db() as conn:
        row = conn.execute(
            "SELECT block_index, block_hash FROM donations ORDER BY block_index DESC LIMIT 1"
        ).fetchone()
    if row:
        return row["block_index"], row["block_hash"]
    return 0, get_genesis_hash()


def get_full_chain() -> list[dict]:
    with get_db() as conn:
        g_row = conn.execute("SELECT * FROM genesis WHERE id=0").fetchone()
        d_rows = conn.execute(
            "SELECT * FROM donations ORDER BY block_index ASC"
        ).fetchall()
    chain = []
    if g_row:
        chain.append({
            "block_index": 0,
            "timestamp": g_row["timestamp"],
            "donor": "GENESIS",
            "recipient": "NETWORK",
            "amount": 0.0,
            "tax_amount": 0.0,
            "net_amount": 0.0,
            "previous_hash": "0" * 64,
            "nonce": g_row["nonce"],
            "hash": g_row["block_hash"],
        })
    for r in d_rows:
        chain.append({
            "block_index": r["block_index"],
            "timestamp": r["timestamp"],
            "donor": r["donor"],
            "recipient": r["recipient"],
            "amount": r["amount"],
            "tax_amount": r["tax_amount"],
            "net_amount": r["net_amount"],
            "previous_hash": r["previous_hash"],
            "nonce": r["nonce"],
            "hash": r["block_hash"],
            "signature": r["signature"] if "signature" in r.keys() else "",
            "signed_message": r["signed_message"] if "signed_message" in r.keys() else "",
        })
    return chain


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def index():
    return render_template("index.html", tax_rate=int(TAX_RATE * 100))


@app.get("/api/donations")
def list_donations():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM donations ORDER BY id DESC").fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/api/donations")
def create_donation():
    data = request.get_json(force=True) or {}
    donor     = (data.get("donor") or "").strip()
    recipient = (data.get("recipient") or "").strip()
    try:
        amount = float(data.get("amount", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "invalid amount"}), 400

    if not donor or not recipient:
        return jsonify({"error": "donor and recipient are required"}), 400
    if amount <= 0:
        return jsonify({"error": "amount must be positive"}), 400

    tax = round(amount * TAX_RATE, 2)
    net = round(amount - tax, 2)
    ts  = datetime.now(timezone.utc).isoformat()

    # Blockchain: mine block
    last_index, last_hash = get_last_block_hash()
    new_index = last_index + 1
    nonce, block_hash, mining_time_ms = mine_block(
        block_index=new_index, timestamp=ts, donor=donor, recipient=recipient,
        amount=amount, tax_amount=tax, net_amount=net, previous_hash=last_hash,
    )

    # Digital Signature: sign the donation
    signed_msg = build_donation_message(
        donor=donor, recipient=recipient, amount=amount,
        tax_amount=tax, net_amount=net, timestamp=ts,
        block_index=new_index, block_hash=block_hash,
    )
    signature = sign_donation(_private_key, signed_msg)

    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO donations
                (donor, recipient, amount, tax_amount, net_amount, timestamp,
                 block_index, block_hash, previous_hash, nonce, mining_time_ms,
                 signature, signed_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (donor, recipient, amount, tax, net, ts,
             new_index, block_hash, last_hash, nonce, mining_time_ms,
             signature, signed_msg),
        )
        donation_id = cur.lastrowid

    return jsonify({
        "id": donation_id,
        "donor": donor,
        "recipient": recipient,
        "amount": amount,
        "tax_amount": tax,
        "net_amount": net,
        "timestamp": ts,
        "block_index": new_index,
        "block_hash": block_hash,
        "previous_hash": last_hash,
        "nonce": nonce,
        "mining_time_ms": mining_time_ms,
        "signature": signature,
        "signed_message": signed_msg,
    }), 201


# ── Blockchain endpoints ───────────────────────────────────────────────────────

@app.get("/api/chain")
def get_chain():
    return jsonify(get_full_chain())


@app.get("/api/chain/validate")
def validate_blockchain():
    chain = get_full_chain()
    result = validate_chain(chain)
    return jsonify(result)


# ── Merkle Tree endpoints ──────────────────────────────────────────────────────

@app.get("/api/merkle")
def get_merkle():
    """
    Build a Merkle Tree from all block hashes in the chain.
    Returns the Merkle Root and all tree levels for visualization.
    """
    chain = get_full_chain()
    leaf_hashes = [b["hash"] for b in chain]
    tree = build_merkle_tree(leaf_hashes)
    return jsonify({
        "root": tree["root"],
        "leaf_count": tree["leaf_count"],
        "levels": tree["levels"],
        "leaves": leaf_hashes,
    })


@app.get("/api/merkle/proof/<int:block_index>")
def get_merkle_proof_for_block(block_index: int):
    """
    Get the Merkle Proof for a specific block.
    Proof lets anyone verify a block belongs to the chain without downloading all blocks.
    """
    chain = get_full_chain()
    leaf_hashes = [b["hash"] for b in chain]
    tree = build_merkle_tree(leaf_hashes)

    if block_index >= len(leaf_hashes):
        return jsonify({"error": "block_index out of range"}), 404

    proof = get_merkle_proof(leaf_hashes, block_index)
    is_valid = verify_merkle_proof(leaf_hashes[block_index], proof, tree["root"])

    return jsonify({
        "block_index": block_index,
        "leaf_hash": leaf_hashes[block_index],
        "merkle_root": tree["root"],
        "proof": proof,
        "is_valid": is_valid,
    })


# ── Digital Signature endpoints ────────────────────────────────────────────────

@app.get("/api/signature/public-key")
def get_public_key():
    """Return the platform's RSA public key (PEM format)."""
    return jsonify({"public_key_pem": get_public_key_pem(_public_key)})


@app.post("/api/signature/verify")
def verify_signature():
    """
    Verify a donation's digital signature.
    Body: { "signed_message": "...", "signature": "..." }
    """
    data = request.get_json(force=True) or {}
    message   = data.get("signed_message", "")
    signature = data.get("signature", "")
    if not message or not signature:
        return jsonify({"error": "signed_message and signature are required"}), 400
    result = verify_donation_signature(_public_key, message, signature)
    return jsonify(result)


# ── User page ──────────────────────────────────────────────────────────────────

@app.get("/user/<name>")
def user_page(name):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM donations WHERE donor=? OR recipient=? ORDER BY id DESC",
            (name, name),
        ).fetchall()
    return render_template("user.html", name=name, donations=[dict(r) for r in rows])


if __name__ == "__main__":
    app.run(debug=True)
