from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    # Import and register blueprints
    from patient_eggs.main.routes import main
    from patient_eggs.auth.routes import auth
    from patient_eggs.shop.routes import shop
    from patient_eggs.admin.routes import admin

    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(shop, url_prefix='/shop')
    app.register_blueprint(admin, url_prefix='/admin')

    return app
