"""
Merkle Tree Implementation
--------------------------
Builds a binary Merkle Tree from a list of block hashes.
Used in Bitcoin/blockchain to efficiently verify transaction integrity.

Syllabus: Unit I – Cryptography Fundamentals → Merkle Tree
"""
import hashlib


def sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def merkle_hash_pair(left: str, right: str) -> str:
    """Hash two sibling nodes together (left + right concatenation)."""
    return sha256(left + right)


def build_merkle_tree(leaves: list[str]) -> dict:
    """
    Build a complete Merkle Tree from a list of leaf hashes.

    Returns a dict with:
      - root: the Merkle Root hash
      - levels: list of levels (bottom = leaves, top = root)
      - leaf_count: number of original leaves
    """
    if not leaves:
        return {"root": sha256("EMPTY_TREE"), "levels": [], "leaf_count": 0}

    # Work with a copy; duplicate last leaf if odd number (Bitcoin convention)
    current_level = list(leaves)
    levels = [list(current_level)]  # Store each level for visualization

    while len(current_level) > 1:
        # Duplicate last element if odd number of nodes
        if len(current_level) % 2 == 1:
            current_level.append(current_level[-1])

        next_level = []
        for i in range(0, len(current_level), 2):
            parent = merkle_hash_pair(current_level[i], current_level[i + 1])
            next_level.append(parent)

        current_level = next_level
        levels.append(list(current_level))

    root = current_level[0]
    return {
        "root": root,
        "levels": levels,  # levels[0] = leaves, levels[-1] = [root]
        "leaf_count": len(leaves),
    }


def get_merkle_proof(leaves: list[str], target_index: int) -> list[dict]:
    """
    Generate a Merkle Proof for a specific leaf index.
    Proof = list of sibling hashes needed to recompute the root.
    This is how Bitcoin SPV (Simplified Payment Verification) works.
    """
    if not leaves or target_index >= len(leaves):
        return []

    proof = []
    current_level = list(leaves)
    idx = target_index

    while len(current_level) > 1:
        if len(current_level) % 2 == 1:
            current_level.append(current_level[-1])

        # Determine sibling
        if idx % 2 == 0:
            sibling_idx = idx + 1
            proof.append({"hash": current_level[sibling_idx], "position": "right"})
        else:
            sibling_idx = idx - 1
            proof.append({"hash": current_level[sibling_idx], "position": "left"})

        # Move up the tree
        next_level = []
        for i in range(0, len(current_level), 2):
            next_level.append(merkle_hash_pair(current_level[i], current_level[i + 1]))

        current_level = next_level
        idx = idx // 2

    return proof


def verify_merkle_proof(leaf_hash: str, proof: list[dict], root: str) -> bool:
    """Verify a leaf belongs to the Merkle tree using its proof."""
    current = leaf_hash
    for step in proof:
        if step["position"] == "right":
            current = merkle_hash_pair(current, step["hash"])
        else:
            current = merkle_hash_pair(step["hash"], current)
    return current == root
