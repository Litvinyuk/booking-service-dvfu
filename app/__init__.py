from flask import Flask
import os


def create_app():
    app = Flask(__name__)
    app.secret_key = 'key_228'

    # Регистрируем Blueprint
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app