from flask import Blueprint, render_template, request, redirect, url_for
from app.models.database import get_connection

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        first_name = request.form['firstname']     # соответствие полям формы
        last_name = request.form['surname']
        password = request.form['password']
        user_role = 'student'  # По умолчанию. Или добавь выбор в форме.

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO users (email, first_name, last_name, password, user_role)
                VALUES (?, ?, ?, ?, ?)
            ''', (email, first_name, last_name, password, user_role))
            conn.commit()
            return redirect(url_for('main.login'))  # редирект после успешной регистрации
        except Exception as e:
            conn.rollback()
            return f"<h3>Ошибка при регистрации: {str(e)}</h3>"
        finally:
            conn.close()

    return render_template('register.html')

@main_bp.route('/register-success')
def register_success():
    return "<h1>Регистрация прошла успешно!</h1><a href='/register'>Назад</a>"

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