"""
Configuration settings for Event Ticketing Application
"""
import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Azure Storage (optional)
    AZURE_STORAGE_CONNECTION_STRING = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
    AZURE_STORAGE_CONTAINER = os.environ.get('AZURE_STORAGE_CONTAINER', 'uploads')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    
    # Support both PostgreSQL (Supabase) and SQLite for development
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgresql'):
        SQLALCHEMY_DATABASE_URI = database_url
        print("🐘 Using PostgreSQL (Supabase) for development")
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get('SQLITE_DATABASE_URL') or \
            'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance', 'app.db')
        print("📁 Using SQLite for development")

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    # Production prefers PostgreSQL (Supabase) but allows fallback during development
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgresql'):
        SQLALCHEMY_DATABASE_URI = database_url
        print("🐘 Using PostgreSQL (Supabase) for production")
    else:
        # Fallback for development/testing
        SQLALCHEMY_DATABASE_URI = os.environ.get('SQLITE_DATABASE_URL') or \
            'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance', 'app.db')
        print("⚠️  Production config using SQLite fallback - set PostgreSQL DATABASE_URL for production")
    
    # PostgreSQL connection optimization for Supabase
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'sslmode': 'require',
            'connect_timeout': 10
        }
    }
    
    # Security settings for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}