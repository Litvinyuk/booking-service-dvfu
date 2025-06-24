from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db_api
from functools import wraps
from datetime import datetime, time, timedelta

main_bp = Blueprint('main', __name__)

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Доступ запрещен. Требуются права администратора', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return wrapper

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return wrapper

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/admin')
@admin_required
def admin_index():
    return render_template('admin.html')

# --- Пользователи ---
@main_bp.route('/admin/users')
@admin_required
def manage_users():
    users = db_api.get_all_users()
    return render_template('manage_users.html', users=users)


@main_bp.route('/admin/users/add', methods=['GET', 'POST'])
@admin_required
def add_user():
    if request.method == 'POST':
        data = request.form
        is_admin = 'is_admin' in data and data['is_admin'] == 'on'

        # Пароль будет автоматически захэширован в create_user
        db_api.create_user(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            password=data['password'],
            is_admin=is_admin
        )
        flash('Пользователь добавлен', 'success')
        return redirect(url_for('main.manage_users'))
    return render_template('edit_user.html', user=None)


@main_bp.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    # Получаем данные пользователя из базы данных
    user = db_api.get_user_by_id(user_id)

    # Если пользователь не найден - показываем ошибку
    if not user:
        flash('Пользователь не найден', 'error')
        return redirect(url_for('main.manage_users'))

    # Обработка отправки формы
    if request.method == 'POST':
        # Получаем данные из формы
        data = request.form
        email = data['email']
        first_name = data['first_name']
        last_name = data['last_name']

        # Определяем, является ли пользователь администратором
        is_admin = 'is_admin' in data and data['is_admin'] == 'on'

        try:
            # Обновляем основную информацию о пользователе
            db_api.update_user_info(
                user_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_admin=is_admin
            )

            # Если указан новый пароль - обновляем его
            if data['password']:
                db_api.update_user_password(user_id, data['password'])
                flash('Пароль успешно обновлён', 'success')

            flash('Данные пользователя обновлены', 'success')
            return redirect(url_for('main.manage_users'))

        except Exception as e:
            flash(f'Ошибка при обновлении пользователя: {str(e)}', 'error')

    # Для GET-запроса просто показываем форму редактирования
    return render_template('edit_user.html', user=user)


# --- Пространства ---
@main_bp.route('/admin/spaces')
@admin_required
def manage_spaces():
    spaces = db_api.get_all_spaces()
    return render_template('manage_spaces.html', spaces=spaces)

@main_bp.route('/admin/spaces/add', methods=['GET', 'POST'])
@admin_required
def add_space():
    if request.method == 'POST':
        data = request.form
        db_api.create_space(
            title=data['title'],
            location=data['location'],
            capacity=int(data['capacity']),
            image=data['image'],
            type=data['type'],
            description=data['description']
        )
        flash('Пространство добавлено', 'success')
        return redirect(url_for('main.manage_spaces'))
    return render_template('edit_space.html', space=None)

@main_bp.route('/admin/spaces/<int:space_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_space(space_id):
    space = db_api.get_space_by_id(space_id)
    if not space:
        flash('Пространство не найдено', 'error')
        return redirect(url_for('main.manage_spaces'))

    if request.method == 'POST':
        data = request.form
        if 'delete' in data:
            db_api.delete_space(space_id)
            flash('Пространство удалено', 'success')
            return redirect(url_for('main.manage_spaces'))

        db_api.update_space(
            space_id,
            title=data['title'],
            location=data['location'],
            capacity=int(data['capacity']),
            image=data['image'],
            type=data['type'],
            description=data['description']
        )
        flash('Данные пространства обновлены', 'success')
        return redirect(url_for('main.manage_spaces'))

    return render_template('edit_space.html', space=space)

# --- Бронирования ---
@main_bp.route('/admin/bookings')
@admin_required
def manage_bookings():
    bookings = db_api.get_all_bookings()
    return render_template('manage_bookings.html', bookings=bookings)

@main_bp.route('/admin/bookings/<int:booking_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_booking(booking_id):
    booking = db_api.get_booking_by_id(booking_id)
    if not booking:
        flash('Бронирование не найдено', 'error')
        return redirect(url_for('main.manage_bookings'))

    if request.method == 'POST':
        data = request.form
        if 'delete' in data:
            db_api.delete_booking(booking_id)
            flash('Бронирование удалено', 'success')
            return redirect(url_for('main.manage_bookings'))

        # Иначе — обновление
        db_api.update_booking(
            booking_id,
            user_id=data['user_id'],
            space_id=data['space_id'],
            booking_date=data['booking_date'],
            start_time=data['start_time'],
            end_time=data['end_time']
        )
        flash('Бронирование обновлено', 'success')
        return redirect(url_for('main.manage_bookings'))

    users = db_api.get_all_users()
    spaces = db_api.get_all_spaces()
    return render_template('edit_booking.html', booking=booking, users=users, spaces=spaces)

@main_bp.route('/admin/bookings/add', methods=['GET', 'POST'])
@admin_required
def add_booking():
    if request.method == 'POST':
        data = request.form
        user_id = data['user_id']
        space_id = data['space_id']
        booking_date = data['booking_date']
        start_time = data['start_time']
        end_time = data['end_time']

        # Можно добавить проверку конфликтов, если есть функция в db_api
        if hasattr(db_api, 'has_booking_conflict'):
            if db_api.has_booking_conflict(space_id, booking_date, start_time, end_time):
                flash('В это время уже есть бронирование. Выберите другое время.', 'error')
                users = db_api.get_all_users()
                spaces = db_api.get_all_spaces()
                return render_template('edit_booking.html', booking=None, users=users, spaces=spaces)

        db_api.create_booking(user_id, space_id, booking_date, start_time, end_time)
        flash('Бронирование добавлено', 'success')
        return redirect(url_for('main.manage_bookings'))

    # GET запрос — просто отдаем форму с пользователями и пространствами
    users = db_api.get_all_users()
    spaces = db_api.get_all_spaces()
    return render_template('edit_booking.html', booking=None, users=users, spaces=spaces)


# --- Регистрация, вход, профиль ---
@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        first_name = request.form['firstname']
        last_name = request.form['surname']
        password = request.form['password']

        # По умолчанию все новые пользователи - не администраторы
        is_admin = False

        try:
            db_api.create_user(email, first_name, last_name, password, is_admin)
            flash('Регистрация успешна! Теперь войдите.', 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            flash('Ошибка при регистрации: ' + str(e), 'error')

    return render_template('register.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = db_api.get_user_by_email(email)

        if not user:
            flash('Пользователь не найден', 'error')
            return redirect(url_for('main.login'))

        # Проверяем пароль
        if db_api.verify_password(user['password'], password):
            session['user_id'] = user['id']
            session['is_admin'] = user['is_admin']
            session['username'] = user.get('first_name')
            return redirect(url_for('main.profile'))
        else:
            flash('Неверный пароль', 'error')

    return render_template('login.html')

@main_bp.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('main.index'))


@login_required
@main_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    user_id = session['user_id']
    user = db_api.get_user_by_id(user_id)

    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')

        if new_password:
            # Проверяем текущий пароль
            if db_api.verify_password(user['password'], current_password):
                # Обновляем пароль (автоматически хешируется)
                db_api.update_user_password(user_id, new_password)
                flash('Пароль успешно изменён', 'success')
            else:
                flash('Текущий пароль неверен', 'error')

        # Обновляем данные пользователя
        user = db_api.get_user_by_id(user_id)

    bookings = db_api.get_user_bookings(user_id)
    return render_template('profile.html', user=user, bookings=bookings)

# --- Каталог и бронирование ---
@main_bp.route('/catalog')
def catalog():
    spaces = db_api.get_all_spaces()
    return render_template('catalog.html', spaces=spaces)

@main_bp.route('/booking/<int:space_id>', methods=['GET', 'POST'])
def booking(space_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('Пожалуйста, авторизуйтесь для бронирования', 'error')
        return redirect(url_for('main.login'))

    # Обработка выбора даты
    selected_date = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))
    
    # Получение пространства
    space = db_api.get_space_by_id(space_id)
    if not space:
        flash('Пространство не найдено', 'error')
        return redirect(url_for('main.catalog'))
    
    # Получение бронирований для выбранной даты
    bookings = db_api.get_bookings_by_date(space_id, selected_date)
    booked_slots = [f"{b['start_time']}-{b['end_time']}" for b in bookings]
    
    # Генерация временных слотов (8:00 - 22:00 с шагом 30 минут)
    time_slots = []
    start_time_val = time(8, 0)
    end_time_val = time(22, 0)
    slot_duration = timedelta(minutes=30)
    
    current_datetime = datetime.combine(datetime.today(), start_time_val)
    end_datetime = datetime.combine(datetime.today(), end_time_val)
    
    while current_datetime < end_datetime:
        slot_start = current_datetime.time().strftime('%H:%M')
        slot_end = (current_datetime + slot_duration).time().strftime('%H:%M')
        
        # Определение статуса слота
        slot_key = f"{slot_start}-{slot_end}"
        selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
        today = datetime.today().date()
        
        if selected_date_obj < today:
            status = 'past'
        elif selected_date_obj == today:
            if datetime.now().time() > current_datetime.time():
                status = 'past'
            else:
                status = 'booked' if slot_key in booked_slots else 'free'
        else:
            status = 'booked' if slot_key in booked_slots else 'free'
        
        time_slots.append({
            'start': slot_start,
            'end': slot_end,
            'status': status
        })
        
        current_datetime += slot_duration

    # Обработка формы бронирования
    if request.method == 'POST':
        date = request.form['date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        
        # Проверка конфликтов
        if db_api.has_booking_conflict(space_id, date, start_time, end_time):
            flash('В это время уже есть бронирование', 'error')
        else:
            db_api.create_booking(user_id, space_id, date, start_time, end_time)
            flash('Бронирование успешно создано', 'success')
            # Остаемся на той же дате после бронирования
            return redirect(url_for('main.booking', space_id=space_id, date=date))
    
    return render_template('booking.html', 
                          space=space,
                          selected_date=selected_date,
                          time_slots=time_slots)

