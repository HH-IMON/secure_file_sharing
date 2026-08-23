import os
import sys
from getpass import getpass
from argon2 import PasswordHasher

# Add parent directory to path to allow importing app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.user import User

def create_admin():
    """Create an admin user."""
    app = create_app()
    with app.app_context():
        # Check if admin already exists
        admin_email = os.environ.get('ADMIN_EMAIL')
        if not admin_email:
            admin_email = input("Enter admin email: ")
            
        existing_admin = User.query.filter_by(email=admin_email).first()
        if existing_admin:
            print(f"User with email {admin_email} already exists.")
            return

        admin_password = os.environ.get('ADMIN_PASSWORD')
        if not admin_password:
            admin_password = getpass("Enter admin password: ")

        # Hash password using Argon2
        ph = PasswordHasher()
        password_hash = ph.hash(admin_password)

        # Generate RSA Keys for Admin
        from app.services.key_service import generate_rsa_key_pair, encrypt_private_key
        private_key_pem, public_key_pem = generate_rsa_key_pair()
        enc_data = encrypt_private_key(private_key_pem, admin_password)

        # Create admin user
        admin = User(
            name='Administrator',
            email=admin_email,
            password_hash=password_hash,
            public_key=public_key_pem.decode(),
            encrypted_private_key=enc_data['encrypted_key'],
            private_key_salt=enc_data['salt'],
            private_key_nonce=enc_data['nonce'],
            role='admin'
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"Admin user '{admin_email}' created successfully.")

if __name__ == '__main__':
    create_admin()
