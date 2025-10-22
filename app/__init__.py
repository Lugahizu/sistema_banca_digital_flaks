from flask import Flask
from flask_login import LoginManager
from .db import database

login_manager = LoginManager()
login_manager.login_view = "main.login"

def create_app(test_config=None):
    app = Flask(__name__)
    if test_config is None:    
        app.config["SECRET_KEY"] = '123'
    else:
        app.config.update(test_config)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):        
        return database.get_user(user_id)   

    from .app import main as main_blueprint
    app.register_blueprint(main_blueprint)
    return app