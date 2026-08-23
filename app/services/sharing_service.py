from datetime import datetime, timezone
from app.models.user import User
from app.models.file import File
from app.models.file_key import FileKey
from app.models.share import FileShare
from app.extensions import db
from app.utils.security import generate_uuid
from app.services.key_service import decrypt_private_key_with_derived_key, encrypt_aes_key_for_recipient, decrypt_aes_key

def share_file(file_uuid: str, sender: User, recipient_id: int, permission: str, expires_at, message: str, one_time: bool, derived_key_hex: str) -> FileShare:
    """Share a file with another user securely."""
    file_record = File.query.filter_by(uuid=file_uuid, owner_id=sender.id).first()
    if not file_record:
        raise ValueError("File not found or not owned by user.")
        
    recipient = User.query.get(recipient_id)
    if not recipient or not recipient.public_key:
        raise ValueError("Recipient not found or lacks public key.")
        
    sender_file_key = FileKey.query.filter_by(file_id=file_record.id, recipient_id=sender.id).first()
    if not sender_file_key:
        raise ValueError("Sender decryption key not found.")
        
    private_key_pem = decrypt_private_key_with_derived_key(
        sender.encrypted_private_key,
        bytes.fromhex(derived_key_hex),
        sender.private_key_nonce
    )
    aes_key = decrypt_aes_key(sender_file_key.encrypted_aes_key, private_key_pem)
    
    enc_aes_key_b64 = encrypt_aes_key_for_recipient(aes_key, recipient.public_key.encode())
    
    recipient_file_key = FileKey.query.filter_by(file_id=file_record.id, recipient_id=recipient.id).first()
    if not recipient_file_key:
        recipient_file_key = FileKey(
            file_id=file_record.id,
            recipient_id=recipient.id,
            encrypted_aes_key=enc_aes_key_b64
        )
        db.session.add(recipient_file_key)
        
    share = FileShare(
        uuid=generate_uuid(),
        file_id=file_record.id,
        sender_id=sender.id,
        recipient_id=recipient.id,
        permission=permission,
        message=message,
        one_time_download=one_time,
        expires_at=expires_at
    )
    db.session.add(share)
    db.session.commit()
    return share

def get_shares_for_recipient(user: User) -> list[dict]:
    """Retrieve all files shared with user."""
    shares = db.session.query(FileShare, File, User).join(File, FileShare.file_id == File.id).join(User, FileShare.sender_id == User.id).filter(FileShare.recipient_id == user.id).all()
    result = []
    for share, file_rec, sender in shares:
        result.append({
            'share': share,
            'file': file_rec,
            'sender': sender
        })
    return result

def revoke_share(share_uuid: str, user: User) -> bool:
    """Revoke an existing share."""
    share = FileShare.query.filter_by(uuid=share_uuid, sender_id=user.id).first()
    if not share:
        return False
    share.revoked_at = datetime.now(timezone.utc)
    db.session.commit()
    return True

def get_file_shares(file_uuid: str, user: User) -> list[FileShare]:
    """Retrieve all shares for a file."""
    file_record = File.query.filter_by(uuid=file_uuid, owner_id=user.id).first()
    if not file_record:
        return []
    return FileShare.query.filter_by(file_id=file_record.id).all()
