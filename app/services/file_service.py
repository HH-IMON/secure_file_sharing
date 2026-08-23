import os
from flask import current_app
from werkzeug.utils import secure_filename
from app.models.user import User
from app.models.file import File
from app.models.file_key import FileKey
from app.models.share import FileShare
from app.extensions import db
from app.utils.security import generate_uuid
from app.services.crypto_service import encrypt_file, decrypt_file, calculate_hash
from app.services.key_service import decrypt_private_key_with_derived_key, encrypt_aes_key_for_recipient, decrypt_aes_key
from app.services.signature_service import create_file_signature, verify_file_signature

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    allowed_exts = current_app.config.get('ALLOWED_EXTENSIONS', set())
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_exts

def validate_file(file) -> tuple[bool, str]:
    """Validate uploaded file for basic requirements."""
    if not file:
        return False, "No file provided."
    if not file.filename:
        return False, "Empty filename."
    if not allowed_file(file.filename):
        return False, "File extension not allowed."
    
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    max_size = current_app.config.get('MAX_FILE_SIZE', 10 * 1024 * 1024)
    if size > max_size:
        return False, "File size exceeds maximum limit."
        
    return True, ""

def sanitize_filename(filename: str) -> str:
    """Sanitize original filename."""
    return secure_filename(filename)

def save_encrypted_file(file, user: User, derived_key_hex: str) -> File:
    """Encrypt and save a file securely."""
    file_data = file.read()
    plaintext_hash = calculate_hash(file_data)
    
    enc_result = encrypt_file(file_data)
    ciphertext = enc_result['ciphertext']
    aes_key = enc_result['key']
    nonce = enc_result['nonce']
    tag = enc_result['tag']
    
    ciphertext_hash = calculate_hash(ciphertext)
    
    private_key_pem = decrypt_private_key_with_derived_key(
        user.encrypted_private_key,
        bytes.fromhex(derived_key_hex),
        user.private_key_nonce
    )
    
    signature = create_file_signature(plaintext_hash, ciphertext_hash, nonce.hex(), private_key_pem)
    
    file_uuid = generate_uuid()
    stored_filename = file_uuid
    
    storage_path = current_app.config.get('FILE_STORAGE_PATH', 'storage')
    os.makedirs(storage_path, exist_ok=True)
    with open(os.path.join(storage_path, stored_filename), 'wb') as f:
        f.write(ciphertext)
        
    enc_aes_key_b64 = encrypt_aes_key_for_recipient(aes_key, user.public_key.encode())
    
    new_file = File(
        uuid=file_uuid,
        owner_id=user.id,
        original_filename=sanitize_filename(file.filename),
        stored_filename=stored_filename,
        mime_type=file.mimetype,
        file_size=len(file_data),
        encrypted_size=len(ciphertext),
        nonce=nonce,
        auth_tag=tag,
        plaintext_hash=plaintext_hash,
        ciphertext_hash=ciphertext_hash,
        signature=signature,
        status='active'
    )
    db.session.add(new_file)
    db.session.flush()
    
    file_key = FileKey(
        file_id=new_file.id,
        recipient_id=user.id,
        encrypted_aes_key=enc_aes_key_b64
    )
    db.session.add(file_key)
    db.session.commit()
    
    return new_file

def get_file_for_download(file_uuid: str, user: User, derived_key_hex: str) -> tuple[bytes, str, dict]:
    """Retrieve and decrypt file for download."""
    file_record = File.query.filter_by(uuid=file_uuid, status='active').first()
    if not file_record:
        raise ValueError("File not found or inactive")
        
    is_authorized = False
    if file_record.owner_id == user.id:
        is_authorized = True
    else:
        share = FileShare.query.filter_by(file_id=file_record.id, recipient_id=user.id).first()
        if share and share.is_active:
            is_authorized = True
            
    if not is_authorized:
        raise ValueError("Unauthorized access")
        
    file_key = FileKey.query.filter_by(file_id=file_record.id, recipient_id=user.id).first()
    if not file_key:
        raise ValueError("Decryption key not found")
        
    private_key_pem = decrypt_private_key_with_derived_key(
        user.encrypted_private_key,
        bytes.fromhex(derived_key_hex),
        user.private_key_nonce
    )
    
    aes_key = decrypt_aes_key(file_key.encrypted_aes_key, private_key_pem)
    
    storage_path = current_app.config.get('FILE_STORAGE_PATH', 'storage')
    with open(os.path.join(storage_path, file_record.stored_filename), 'rb') as f:
        ciphertext = f.read()
        
    decrypted_data = decrypt_file(ciphertext, aes_key, file_record.nonce, file_record.auth_tag)
    
    calc_pt_hash = calculate_hash(decrypted_data)
    is_integrity_valid = (calc_pt_hash == file_record.plaintext_hash)
    
    owner = User.query.get(file_record.owner_id)
    is_auth_valid = verify_file_signature(
        file_record.plaintext_hash,
        file_record.ciphertext_hash,
        file_record.nonce.hex(),
        file_record.signature,
        owner.public_key.encode()
    )
    
    verification_dict = {
        'encryption': True,
        'key_protection': True,
        'integrity': is_integrity_valid,
        'authenticity': is_auth_valid
    }
    
    return decrypted_data, file_record.original_filename, verification_dict

def delete_file(file_uuid: str, user: User) -> bool:
    """Delete a file from storage and database."""
    file_record = File.query.filter_by(uuid=file_uuid, owner_id=user.id).first()
    if not file_record:
        return False
        
    storage_path = current_app.config.get('FILE_STORAGE_PATH', 'storage')
    file_path = os.path.join(storage_path, file_record.stored_filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        
    db.session.delete(file_record)
    db.session.commit()
    return True

def get_user_files(user: User) -> list:
    """Retrieve all active files for a user."""
    return File.query.filter_by(owner_id=user.id, status='active').all()
