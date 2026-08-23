import base64
import secrets
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def generate_rsa_key_pair(key_size: int = 2048) -> tuple[bytes, bytes]:
    """Generate RSA keypair, serialize to PEM. Returns (private_key_pem, public_key_pem)."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
    )
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_key = private_key.public_key()
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return private_key_pem, public_key_pem

def derive_key_from_password(password: str, salt: bytes) -> bytes:
    """Use PBKDF2HMAC with SHA256 to derive key."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return kdf.derive(password.encode())

def encrypt_private_key(private_key_pem: bytes, password: str) -> dict:
    """Encrypt private key with password-derived key."""
    salt = secrets.token_bytes(32)
    nonce = secrets.token_bytes(12)
    derived_key = derive_key_from_password(password, salt)
    aesgcm = AESGCM(derived_key)
    ciphertext = aesgcm.encrypt(nonce, private_key_pem, None)
    return {
        'encrypted_key': base64.b64encode(ciphertext).decode(),
        'salt': salt.hex(),
        'nonce': nonce.hex()
    }

def decrypt_private_key(encrypted_key_b64: str, password: str, salt_hex: str, nonce_hex: str) -> bytes:
    """Decrypt private key using password."""
    salt = bytes.fromhex(salt_hex)
    nonce = bytes.fromhex(nonce_hex)
    ciphertext = base64.b64decode(encrypted_key_b64)
    derived_key = derive_key_from_password(password, salt)
    aesgcm = AESGCM(derived_key)
    return aesgcm.decrypt(nonce, ciphertext, None)

def decrypt_private_key_with_derived_key(encrypted_key_b64: str, derived_key: bytes, nonce_hex: str) -> bytes:
    """Decrypt private key using pre-derived key."""
    nonce = bytes.fromhex(nonce_hex)
    ciphertext = base64.b64decode(encrypted_key_b64)
    aesgcm = AESGCM(derived_key)
    return aesgcm.decrypt(nonce, ciphertext, None)

def encrypt_aes_key_for_recipient(aes_key: bytes, recipient_public_key_pem: bytes) -> str:
    """Encrypt AES key using recipient's RSA public key."""
    public_key = serialization.load_pem_public_key(recipient_public_key_pem)
    ciphertext = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return base64.b64encode(ciphertext).decode()

def decrypt_aes_key(encrypted_aes_key_b64: str, private_key_pem: bytes) -> bytes:
    """Decrypt AES key using private RSA key."""
    private_key = serialization.load_pem_private_key(private_key_pem, password=None)
    ciphertext = base64.b64decode(encrypted_aes_key_b64)
    return private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
