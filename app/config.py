import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # Get database URL from environment variable and ensure it uses postgresql://
    database_url = os.environ.get('DATABASE_URL', '')
    
    # Handle both postgres:// and postgresql:// formats
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = database_url or 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
