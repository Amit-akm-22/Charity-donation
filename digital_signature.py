"""
Digital Signatures using RSA (PKCS#1 v1.5 / PSS)
--------------------------------------------------
Implements RSA key generation, signing, and verification.
Every donation is signed with the platform's private key so anyone
can verify the donation was genuinely issued by this server.

Syllabus: Unit I – Cryptography Fundamentals → Digital Signatures
"""
import os
import base64
import hashlib

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature

PRIVATE_KEY_FILE = "platform_private.pem"
PUBLIC_KEY_FILE  = "platform_public.pem"


# ── Key Generation ──────────────────────────────────────────────────────────

def generate_key_pair():
    """Generate a 2048-bit RSA key pair and save to PEM files."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )
    # Save private key
    with open(PRIVATE_KEY_FILE, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    # Save public key
    with open(PUBLIC_KEY_FILE, "wb") as f:
        f.write(
            private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
    return private_key, private_key.public_key()


def load_or_create_keys():
    """Load existing keys from disk, or generate a new pair."""
    if os.path.exists(PRIVATE_KEY_FILE) and os.path.exists(PUBLIC_KEY_FILE):
        with open(PRIVATE_KEY_FILE, "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
        with open(PUBLIC_KEY_FILE, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())
        return private_key, public_key
    return generate_key_pair()


# ── Signing & Verification ──────────────────────────────────────────────────

def build_donation_message(
    donor: str, recipient: str, amount: float, tax_amount: float,
    net_amount: float, timestamp: str, block_index: int, block_hash: str,
) -> str:
    """Build the canonical message string that gets signed."""
    return (
        f"donor={donor}|recipient={recipient}|amount={float(amount):.2f}"
        f"|tax={float(tax_amount):.2f}|net={float(net_amount):.2f}"
        f"|ts={timestamp}|block={block_index}|hash={block_hash}"
    )


def sign_donation(private_key, message: str) -> str:
    """
    Sign the donation message with RSA-PSS + SHA-256.
    Returns a base64-encoded signature string.
    """
    signature_bytes = private_key.sign(
        message.encode("utf-8"),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    return base64.b64encode(signature_bytes).decode("utf-8")


def verify_donation_signature(
    public_key,
    message: str,
    signature_b64: str,
) -> dict:
    """
    Verify an RSA-PSS signature against the donation message.
    Returns {"valid": True/False, "reason": str}.
    """
    try:
        signature_bytes = base64.b64decode(signature_b64)
        public_key.verify(
            signature_bytes,
            message.encode("utf-8"),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        return {"valid": True, "reason": "Signature is authentic — message was signed by the platform's private key."}
    except InvalidSignature:
        return {"valid": False, "reason": "⚠ Invalid signature — message may have been tampered!"}
    except Exception as e:
        return {"valid": False, "reason": f"Verification error: {str(e)}"}


def get_public_key_pem(public_key) -> str:
    """Return the public key as a PEM string."""
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
