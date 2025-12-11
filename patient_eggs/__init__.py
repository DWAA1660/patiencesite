from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
import markdown
from markupsafe import Markup

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    
    @app.template_filter('markdown')
    def render_markdown(text):
        return Markup(markdown.markdown(text))

    # Import and register blueprints
    from patient_eggs.main.routes import main
    from patient_eggs.auth.routes import auth
    from patient_eggs.shop.routes import shop
    from patient_eggs.admin.routes import admin

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(shop)
    app.register_blueprint(admin, url_prefix='/admin')

    # Context Processor for Site Settings
    from patient_eggs.models import SiteSetting
    @app.context_processor
    def inject_site_settings():
        settings = {s.key: s.value for s in SiteSetting.query.all()}
        return dict(site_settings=settings)

    return app
