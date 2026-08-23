import email_validator
import uuid
from markupsafe import escape

def validate_email(email: str) -> bool:
    """Basic email validation using email_validator library."""
    try:
        email_validator.validate_email(email)
        return True
    except email_validator.EmailNotValidError:
        return False

def validate_file_extension(filename: str, allowed: set) -> bool:
    """Check file extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed

def validate_file_size(file_size: int, max_size: int) -> bool:
    """Check size limit."""
    return file_size <= max_size

def validate_uuid(uuid_str: str) -> bool:
    """Validate UUID format."""
    try:
        uuid_obj = uuid.UUID(uuid_str)
        return str(uuid_obj) == uuid_str
    except ValueError:
        return False

def sanitize_input(text: str) -> str:
    """Strip HTML tags, escape special chars using markupsafe."""
    import re
    clean_text = re.sub(r'<[^>]+>', '', text)
    return escape(clean_text)
