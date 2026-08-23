import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

def sign_data(data: bytes, private_key_pem: bytes) -> str:
    """Sign data using RSA-PSS."""
    private_key = serialization.load_pem_private_key(private_key_pem, password=None)
    signature = private_key.sign(
        data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode()

def verify_signature(data: bytes, signature_b64: str, public_key_pem: bytes) -> bool:
    """Verify RSA-PSS signature."""
    public_key = serialization.load_pem_public_key(public_key_pem)
    signature = base64.b64decode(signature_b64)
    try:
        public_key.verify(
            signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except InvalidSignature:
        return False

def create_file_signature(plaintext_hash: str, ciphertext_hash: str, nonce_hex: str, private_key_pem: bytes) -> str:
    """Create signature over file hashes and nonce."""
    canonical_data = f'{plaintext_hash}:{ciphertext_hash}:{nonce_hex}'.encode()
    return sign_data(canonical_data, private_key_pem)

def verify_file_signature(plaintext_hash: str, ciphertext_hash: str, nonce_hex: str, signature_b64: str, public_key_pem: bytes) -> bool:
    """Verify file signature."""
    canonical_data = f'{plaintext_hash}:{ciphertext_hash}:{nonce_hex}'.encode()
    return verify_signature(canonical_data, signature_b64, public_key_pem)
