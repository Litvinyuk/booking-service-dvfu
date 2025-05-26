from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/register')
def register():
    return render_template('register.html')

@main_bp.route('/login')
def login():
    return render_template('login.html')

# Другие маршруты...
@main_bp.route('/catalog')
def catalog():
    return render_template('catalog.html')

@main_bp.route('/booking')
def booking():
    return render_template('booking.html')

@main_bp.route('/space')
def space():
    return render_template('space.html')