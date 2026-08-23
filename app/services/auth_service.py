import re
from datetime import datetime, timezone
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from app.models.user import User
from app.extensions import db
from app.services.key_service import generate_rsa_key_pair, encrypt_private_key, derive_key_from_password
from app.utils.security import generate_uuid

def hash_password(password: str) -> str:
    """Hash password using Argon2id."""
    ph = PasswordHasher()
    return ph.hash(password)

def verify_password(password_hash: str, password: str) -> bool:
    """Verify Argon2id password hash."""
    ph = PasswordHasher()
    try:
        ph.verify(password_hash, password)
        return True
    except VerifyMismatchError:
        return False

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Check password strength requirements."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, ""

def register_user(name: str, email: str, password: str) -> User:
    """Register a new user, create keys, and store securely."""
    is_valid, error_msg = validate_password_strength(password)
    if not is_valid:
        raise ValueError(error_msg)
        
    pwd_hash = hash_password(password)
    private_key_pem, public_key_pem = generate_rsa_key_pair()
    
    enc_data = encrypt_private_key(private_key_pem, password)
    
    user = User(
        uuid=generate_uuid(),
        name=name,
        email=email,
        password_hash=pwd_hash,
        public_key=public_key_pem.decode(),
        encrypted_private_key=enc_data['encrypted_key'],
        private_key_salt=enc_data['salt'],
        private_key_nonce=enc_data['nonce'],
        role='user',
        is_active=True
    )
    db.session.add(user)
    db.session.commit()
    return user

def authenticate_user(email: str, password: str) -> tuple[User | None, str | None]:
    """Authenticate user and return (User, derived_key_hex)."""
    user = User.query.filter_by(email=email).first()
    if not user:
        return None, None
        
    if not verify_password(user.password_hash, password):
        return None, None
        
    if not user.is_active:
        return None, None
        
    user.last_login_at = datetime.now(timezone.utc)
    db.session.commit()
    
    derived_key_hex = None
    if user.private_key_salt:
        salt_bytes = bytes.fromhex(user.private_key_salt)
        derived_key = derive_key_from_password(password, salt_bytes)
        derived_key_hex = derived_key.hex()
        
    return user, derived_key_hex
