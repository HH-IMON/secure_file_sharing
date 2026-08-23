import secrets
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

def generate_aes_key() -> bytes:
    """Generate 256-bit random key using secrets.token_bytes(32)"""
    return secrets.token_bytes(32)

def generate_nonce() -> bytes:
    """Generate 96-bit nonce using secrets.token_bytes(12)"""
    return secrets.token_bytes(12)

def encrypt_file(file_data: bytes) -> dict:
    """Encrypt file using AES-256-GCM."""
    key = generate_aes_key()
    nonce = generate_nonce()
        
    aesgcm = AESGCM(key)
    ct_with_tag = aesgcm.encrypt(nonce, file_data, None)
    
    tag = ct_with_tag[-16:]
    ciphertext = ct_with_tag[:-16]
    
    return {
        'ciphertext': ciphertext,
        'key': key,
        'nonce': nonce,
        'tag': tag
    }

def decrypt_file(ciphertext: bytes, key: bytes, nonce: bytes, tag: bytes) -> bytes:
    """Decrypt file using AES-256-GCM."""
    aesgcm = AESGCM(key)
    ct_with_tag = ciphertext + tag
    return aesgcm.decrypt(nonce, ct_with_tag, None)

def calculate_hash(data: bytes, algorithm: str = 'sha256') -> str:
    """Returns hex digest using hashlib."""
    h = hashlib.new(algorithm)
    h.update(data)
    return h.hexdigest()
