from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import sqlite3
from app.models.database import get_connection
from datetime import datetime

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

from datetime import datetime

@main_bp.route('/booking/<int:space_id>', methods=['GET', 'POST'])
@login_required
def booking(space_id):
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        date = request.form['date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        user_id = session['user_id']

        # Проверка конфликта по времени
        cursor.execute('''
            SELECT * FROM bookings
            WHERE space_id = ? AND date = ?
            AND (
                (start_time < ? AND end_time > ?) OR
                (start_time >= ? AND start_time < ?)
            )
        ''', (space_id, date, end_time, start_time, start_time, end_time))

        conflict = cursor.fetchone()
        if conflict:
            flash('Это время уже занято. Пожалуйста, выберите другое.', 'error')
        else:
            cursor.execute('''
                INSERT INTO bookings (space_id, user_id, date, start_time, end_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (space_id, user_id, date, start_time, end_time))
            conn.commit()
            flash('Бронирование успешно оформлено!', 'success')
            return redirect(url_for('main.booking', space_id=space_id))

    # Получение информации о пространстве
    cursor.execute('SELECT * FROM spaces WHERE id = ?', (space_id,))
    space_data = cursor.fetchone()

    if not space_data:
        flash('Пространство не найдено', 'error')
        return redirect(url_for('main.catalog'))

    space = {
        'id': space_data[0],
        'title': space_data[1],
        'location': space_data[2],
        'capacity': space_data[3],
        'image': space_data[4],
        'type': space_data[5],
        'description': space_data[6],
    }

    # Получение всех броней на ближайшие 7 дней
    cursor.execute('''
        SELECT date, start_time, end_time FROM bookings
        WHERE space_id = ? AND date >= date('now')
        ORDER BY date, start_time
    ''', (space_id,))
    bookings = cursor.fetchall()
    conn.close()

    return render_template('booking.html', space=space, bookings=bookings)


@main_bp.route('/space')
def space():
    return render_template('space.html')