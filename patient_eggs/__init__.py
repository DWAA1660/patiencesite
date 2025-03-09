from flask import Flask
from config import Config
import datetime

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    from patient_eggs.main import bp as main_bp
    from patient_eggs.shop import bp as shop_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(shop_bp, url_prefix='/shop')
    
    @app.context_processor
    def inject_now():
        return {'now': datetime.datetime.now()}
    
    return app
