from flask import Flask
from config import Config
import datetime
from flask_session import Session
from patient_eggs.shop.database import db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Configure Flask-Session
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = True
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_FILE_DIR'] = app.config.get('SESSION_FILE_DIR', './flask_session')
    app.config['SESSION_KEY_PREFIX'] = 'patient_eggs:'
    # Fix for bytes vs string issue
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    Session(app)
    
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    from patient_eggs.main import bp as main_bp
    from patient_eggs.shop import bp as shop_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(shop_bp, url_prefix='/shop')
    
    @app.context_processor
    def inject_now():
        return {'now': datetime.datetime.now()}
    
    return app
