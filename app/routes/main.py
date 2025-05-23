from flask import Blueprint, render_template
from app.models. import init_db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    init_db()  # создаст таблицу, если ещё нет
    return render_template('index.html')
