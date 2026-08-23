import os
import sys

# Add parent directory to path to allow importing app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db

def init_database():
    """Initialize the database and create tables."""
    app = create_app()
    with app.app_context():
        # Create all database tables
        db.create_all()
        print("Database tables created successfully.")
        
        # Ensure storage directory exists
        storage_path = app.config.get('FILE_STORAGE_PATH', 'storage/encrypted')
        os.makedirs(storage_path, exist_ok=True)
        print(f"Storage directory '{storage_path}' created or verified.")

if __name__ == '__main__':
    init_database()
