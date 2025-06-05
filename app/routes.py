from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import sqlite3
from app.models.database import get_connection

main_bp = Blueprint('main', __name__)

def login_required(f):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# Функция для получения всех пространств из БД
def get_all_spaces():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM spaces')
    spaces = cursor.fetchall()
    conn.close()

    # Преобразуем в список словарей для удобства
    spaces_list = []
    for space in spaces:
        spaces_list.append({
            'id': space[0],
            'title': space[1],
            'location': space[2],
            'capacity': space[3],
            'image': space[4],
            'type': space[5],
            'description': space[6]
        })
    return spaces_list


@main_bp.route('/')
def index():
    return render_template('index.html')


@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        first_name = request.form['firstname']
        last_name = request.form['surname']
        password = request.form['password']
        user_role = request.form['user_role']

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO users (email, first_name, last_name, password, user_role)
                VALUES (?, ?, ?, ?, ?)
            ''', (email, first_name, last_name, password, user_role))
            conn.commit()
            flash('Регистрация успешна! Теперь войдите.', 'success')
            return redirect(url_for('main.login'))
        except sqlite3.IntegrityError:
            flash('Email уже занят', 'error')
        finally:
            conn.close()

    return render_template('register.html')


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT id, password FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()

            if not user:
                flash('Пользователь не найден', 'error')
                return redirect(url_for('main.login'))

            if user[1] == password:
                session['user_id'] = user[0]
                return redirect(url_for('main.profile'))
            else:
                flash('Неверный пароль', 'error')
                return redirect(url_for('main.login'))

        finally:
            conn.close()

    return render_template('login.html')

@main_bp.route('/logout')
def logout():
    session.pop('user_id', None)  # Удаляем сессию
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('main.index'))


@main_bp.route('/profile')
@login_required
def profile():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, email, first_name, last_name, user_role FROM users WHERE id = ?', (session['user_id'],))
    user_data = cursor.fetchone()
    conn.close()

    if user_data:
        user = {
            'id': user_data[0],
            'email': user_data[1],
            'first_name': user_data[2],
            'last_name': user_data[3],
            'role': user_data[4]
        }
        return render_template('profile.html', user=user)

    return redirect(url_for('main.login'))



@main_bp.route('/catalog')
def catalog():
    spaces = get_all_spaces()
    return render_template('catalog.html', spaces=spaces)

@main_bp.route('/booking')
def booking():
    return render_template('booking.html')

@main_bp.route('/space')
def space():
    return render_template('space.html')