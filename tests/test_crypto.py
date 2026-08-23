import pytest
import os
import base64
from app.services.crypto_service import encrypt_file, decrypt_file, calculate_hash
from app.services.key_service import (
    generate_rsa_key_pair, encrypt_private_key, decrypt_private_key,
    encrypt_aes_key_for_recipient, decrypt_aes_key, derive_key_from_password
)
from app.services.signature_service import (
    sign_data, verify_signature, create_file_signature, verify_file_signature
)

def test_aes_encrypt_decrypt():
    data = b"Secret data"
    enc = encrypt_file(data)
    
    dec = decrypt_file(
        enc['ciphertext'],
        enc['key'],
        enc['nonce'],
        enc['tag']
    )
    assert dec == data

def test_aes_wrong_key():
    data = b"Secret data"
    enc = encrypt_file(data)
    
    wrong_key = os.urandom(32)
    with pytest.raises(Exception):
        decrypt_file(
            enc['ciphertext'],
            wrong_key,
            enc['nonce'],
            enc['tag']
        )

def test_aes_tampered_ciphertext():
    data = b"Secret data"
    enc = encrypt_file(data)
    
    # Tamper with ciphertext
    tampered_ct = bytearray(enc['ciphertext'])
    tampered_ct[0] ^= 1
    
    with pytest.raises(Exception):
        decrypt_file(
            bytes(tampered_ct),
            enc['key'],
            enc['nonce'],
            enc['tag']
        )

def test_aes_tampered_tag():
    data = b"Secret data"
    enc = encrypt_file(data)
    
    tampered_tag = bytearray(enc['tag'])
    tampered_tag[0] ^= 1
    
    with pytest.raises(Exception):
        decrypt_file(
            enc['ciphertext'],
            enc['key'],
            enc['nonce'],
            bytes(tampered_tag)
        )

def test_rsa_key_generation():
    priv, pub = generate_rsa_key_pair(2048)
    assert b"PRIVATE KEY" in priv
    assert b"PUBLIC KEY" in pub

def test_rsa_key_wrapping():
    priv, pub = generate_rsa_key_pair(2048)
    aes_key = os.urandom(32)
    
    enc_key = encrypt_aes_key_for_recipient(aes_key, pub)
    dec_key = decrypt_aes_key(enc_key, priv)
    
    assert aes_key == dec_key

def test_rsa_wrong_private_key():
    privA, pubA = generate_rsa_key_pair(2048)
    privB, pubB = generate_rsa_key_pair(2048)
    
    aes_key = os.urandom(32)
    enc_key = encrypt_aes_key_for_recipient(aes_key, pubA)
    
    with pytest.raises(Exception):
        decrypt_aes_key(enc_key, privB)

def test_private_key_encryption_decryption():
    priv, _ = generate_rsa_key_pair(2048)
    password = "StrongPassword123!"
    
    enc = encrypt_private_key(priv, password)
    
    dec_priv = decrypt_private_key(
        enc['encrypted_key'],
        password,
        enc['salt'],
        enc['nonce']
    )
    assert dec_priv == priv

def test_private_key_wrong_password():
    priv, _ = generate_rsa_key_pair(2048)
    password = "StrongPassword123!"
    
    enc = encrypt_private_key(priv, password)
    
    with pytest.raises(Exception):
        decrypt_private_key(
            enc['encrypted_key'],
            "WrongPassword!",
            enc['salt'],
            enc['nonce']
        )

def test_digital_signature_valid():
    priv, pub = generate_rsa_key_pair(2048)
    data = b"Data to sign"
    
    sig = sign_data(data, priv)
    is_valid = verify_signature(data, sig, pub)
    
    assert is_valid is True

def test_digital_signature_invalid():
    privA, _ = generate_rsa_key_pair(2048)
    _, pubB = generate_rsa_key_pair(2048)
    data = b"Data to sign"
    
    sig = sign_data(data, privA)
    is_valid = verify_signature(data, sig, pubB)
    
    assert is_valid is False

def test_digital_signature_tampered_data():
    priv, pub = generate_rsa_key_pair(2048)
    data = b"Data to sign"
    
    sig = sign_data(data, priv)
    
    is_valid = verify_signature(b"Tampered data", sig, pub)
    assert is_valid is False

def test_file_signature():
    priv, pub = generate_rsa_key_pair(2048)
    pt_hash = calculate_hash(b"plain")
    ct_hash = calculate_hash(b"cipher")
    nonce_hex = os.urandom(12).hex()
    
    sig = create_file_signature(pt_hash, ct_hash, nonce_hex, priv)
    is_valid = verify_file_signature(pt_hash, ct_hash, nonce_hex, sig, pub)
    
    assert is_valid is True

def test_hash_consistency():
    data = b"Data to hash"
    hash1 = calculate_hash(data)
    hash2 = calculate_hash(data)
    assert hash1 == hash2

def test_hash_different_data():
    hash1 = calculate_hash(b"Data 1")
    hash2 = calculate_hash(b"Data 2")
    assert hash1 != hash2
