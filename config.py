import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'patience-eggs-secure-key-2025-03-18'
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
    
    # Session configuration
    SESSION_PERMANENT = True
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = './flask_session'
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds
    
    # SQLAlchemy configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
