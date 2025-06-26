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
        # Все новые пользователи создаются как обычные (не админы)
        db_api.create_user(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            password=data['password'],
            is_admin=False  # Всегда false
        )
        flash('Пользователь добавлен', 'success')
        return redirect(url_for('main.manage_users'))
    return render_template('edit_user.html', user=None)


@main_bp.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = db_api.get_user_by_id(user_id)

    if not user:
        flash('Пользователь не найден', 'error')
        return redirect(url_for('main.manage_users'))

    if request.method == 'POST':
        data = request.form

        # Удаление
        if 'delete' in data:
            if user_id == session['user_id']:
                flash('Вы не можете удалить самого себя', 'error')
                return redirect(url_for('main.manage_users'))

            try:
                db_api.delete_user(user_id)
                flash('Пользователь удалён', 'success')
                return redirect(url_for('main.manage_users'))
            except Exception as e:
                flash(f'Ошибка при удалении пользователя: {str(e)}', 'error')
                return redirect(url_for('main.manage_users'))

        # Обновление
        email = data.get('email')
        first_name = data.get('first_name')
        last_name = data.get('last_name')

        try:
            # Не даём менять is_admin через форму
            db_api.update_user_info(
                user_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_admin=user['is_admin']  # оставляем как было
            )

            password = data.get('password')
            if password:
                hashed_password = db_api.hash_password(password)
                db_api.update_user_password(user_id, hashed_password)
                flash('Пароль успешно обновлён', 'success')

            flash('Данные пользователя обновлены', 'success')
            return redirect(url_for('main.manage_users'))

        except Exception as e:
            flash(f'Ошибка при обновлении пользователя: {str(e)}', 'error')

    return render_template('edit_user.html', user=user)



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

        # Проверка конфликтов с исключением текущего бронирования
        if db_api.has_booking_conflict(
                data['space_id'],
                data['booking_date'],
                data['start_time'],
                data['end_time'],
                exclude_booking_id=booking_id  # исключаем текущее бронирование
        ):
            flash('Конфликт бронирований! Выберите другое время или пространство.', 'error')
        else:
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
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        booking_id = request.form.get('cancel_booking_id')
        if booking_id:
            booking = db_api.get_booking_by_id(int(booking_id))
            if booking and booking['user_id'] == user_id:
                booking_datetime_str = booking['booking_date'] + ' ' + booking['start_time']
                booking_datetime = datetime.strptime(booking_datetime_str, '%Y-%m-%d %H:%M')
                if datetime.now() + timedelta(hours=24) <= booking_datetime:
                    db_api.delete_booking(int(booking_id))
                    flash('Бронирование успешно отменено', 'success')
                else:
                    flash('Отмена бронирования возможна не менее чем за 24 часа до начала', 'error')
            else:
                flash('Бронирование не найдено или доступ запрещён', 'error')
        return redirect(url_for('main.profile'))

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
    from datetime import datetime, timedelta, time

    user_id = session.get('user_id')
    if not user_id:
        flash('Пожалуйста, авторизуйтесь для бронирования', 'error')
        return redirect(url_for('main.login'))

    # Получаем дату из GET параметра, по умолчанию — сегодня
    selected_date = request.args.get('date')
    if not selected_date:
        selected_date = datetime.today().strftime('%Y-%m-%d')

    # Проверяем формат даты
    try:
        selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except ValueError:
        flash('Неверный формат даты', 'error')
        return redirect(url_for('main.booking', space_id=space_id))

    today = datetime.today().date()
    max_date = today + timedelta(days=15)

    # Получаем пространство
    space = db_api.get_space_by_id(space_id)
    if not space:
        flash('Пространство не найдено', 'error')
        return redirect(url_for('main.catalog'))

    # Получаем все бронирования пространства на выбранную дату
    bookings = db_api.get_bookings_by_date(space_id, selected_date)

    # Генерируем слоты времени с шагом 30 минут с 8:00 до 22:00
    time_slots = []
    start_dt = datetime.combine(selected_date_obj, time(8, 0))
    end_dt = datetime.combine(selected_date_obj, time(22, 0))
    slot_duration = timedelta(minutes=30)

    now = datetime.now()

    current_slot_start = start_dt
    while current_slot_start < end_dt:
        slot_start_time = current_slot_start.time()
        slot_end_time = (current_slot_start + slot_duration).time()

        # Определяем статус слота: past, booked или free
        if selected_date_obj < today or selected_date_obj > max_date:
            status = 'past'
        elif selected_date_obj == today and now.time() > slot_end_time:
            status = 'past'
        else:
            # Проверяем пересечения с бронированиями
            status = 'free'
            for b in bookings:
                b_start = datetime.strptime(b['start_time'], '%H:%M').time()
                b_end = datetime.strptime(b['end_time'], '%H:%M').time()
                # Если слоты пересекаются — помечаем booked
                if (slot_start_time < b_end) and (slot_end_time > b_start):
                    status = 'booked'
                    break

        time_slots.append({
            'start': slot_start_time.strftime('%H:%M'),
            'end': slot_end_time.strftime('%H:%M'),
            'status': status
        })

        current_slot_start += slot_duration

    # Обработка POST-запроса (создание бронирования)
    if request.method == 'POST':
        date_str = request.form.get('date')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')

        # Валидация входных данных
        try:
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time_obj = datetime.strptime(start_time_str, '%H:%M').time()
            end_time_obj = datetime.strptime(end_time_str, '%H:%M').time()
        except (ValueError, TypeError):
            flash('Неверный формат даты или времени', 'error')
            return redirect(url_for('main.booking', space_id=space_id, date=date_str))

        if booking_date < today:
            flash('Нельзя бронировать на прошедшую дату.', 'error')
            return redirect(url_for('main.booking', space_id=space_id, date=date_str))

        if booking_date > max_date:
            flash('Нельзя бронировать более чем на 15 дней вперёд.', 'error')
            return redirect(url_for('main.booking', space_id=space_id, date=date_str))

        if start_time_obj >= end_time_obj:
            flash('Время окончания должно быть позже времени начала.', 'error')
            return redirect(url_for('main.booking', space_id=space_id, date=date_str))

        # Проверяем количество активных бронирований пользователя (текущая дата включительно)
        active_bookings_count = db_api.count_user_active_bookings(user_id, today.strftime('%Y-%m-%d'))
        if active_bookings_count >= 3:
            flash('Нельзя иметь более 3 активных бронирований одновременно.', 'error')
            return redirect(url_for('main.booking', space_id=space_id, date=date_str))

        # Проверка конфликтов бронирования через API
        if db_api.has_booking_conflict(space_id, date_str, start_time_str, end_time_str):
            flash('В это время уже есть бронирование', 'error')
            return redirect(url_for('main.booking', space_id=space_id, date=date_str))

        # Создаём бронирование
        db_api.create_booking(user_id, space_id, date_str, start_time_str, end_time_str)
        flash('Бронирование успешно создано', 'success')
        return redirect(url_for('main.booking', space_id=space_id, date=date_str))

    return render_template(
        'booking.html',
        space=space,
        selected_date=selected_date,
        time_slots=time_slots
    )
