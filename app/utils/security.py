import secrets
import uuid
from flask import request
from urllib.parse import urlparse, urljoin

def generate_secure_token(length: int = 32) -> str:
    """Use secrets.token_urlsafe."""
    return secrets.token_urlsafe(length)

def generate_uuid() -> str:
    """Return str(uuid4())."""
    return str(uuid.uuid4())

def get_client_ip() -> str:
    """Get IP from request, handle X-Forwarded-For."""
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0].split(',')[0].strip()
    return request.remote_addr

def is_safe_url(target: str) -> bool:
    """Validate safe redirect URL."""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def safe_redirect(target: str, default: str = 'dashboard.index') -> str:
    """Validate redirect target is safe (same host)."""
    if target and is_safe_url(target):
        return target
    return default
