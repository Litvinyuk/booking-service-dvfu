from flask import Flask
from .routes import main_bp  # Импортируем Blueprint из routes.py

def create_app():
    app = Flask(__name__)
    app.register_blueprint(main_bp)  # Подключаем маршруты

    return app
