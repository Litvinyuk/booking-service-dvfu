from app.models.database import get_connection
from datetime import datetime, timedelta
import hashlib


def can_cancel_booking(booking_id):
    booking = get_booking_by_id(booking_id)
    if not booking:
        return False
    booking_datetime_str = booking['booking_date'] + ' ' + booking['start_time']
    booking_datetime = datetime.strptime(booking_datetime_str, '%Y-%m-%d %H:%M')
    return datetime.now() + timedelta(hours=24) <= booking_datetime
def hash_password(password):
    salt = "fixed_salt"
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()

def verify_password(hashed_password, input_password):
    return hashed_password == hash_password(input_password)

# --- USERS ---
def get_all_users():
    conn = get_connection()
    cur = conn.cursor()
    rows = cur.execute("SELECT id, email, first_name, last_name, is_admin FROM users").fetchall()
    conn.close()
    return [
        {'id': r[0], 'email': r[1], 'first_name': r[2], 'last_name': r[3], 'is_admin': bool(r[4])}
        for r in rows
    ]

def get_user_by_id(user_id):
    conn = get_connection()
    cur = conn.cursor()
    row = cur.execute(
        "SELECT id, email, first_name, last_name, password, is_admin FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    conn.close()
    if row:
        return {
            'id': row[0],
            'email': row[1],
            'first_name': row[2],
            'last_name': row[3],
            'password': row[4],
            'is_admin': bool(row[5])
        }
    return None


def create_user(email, first_name, last_name, password, is_admin=False):
    hashed_pw = hash_password(password)
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO users (email, first_name, last_name, password, is_admin) VALUES (?, ?, ?, ?, ?)",
        (email, first_name, last_name, hashed_pw, int(is_admin))
    )

    conn.commit()
    conn.close()

def update_user_info(user_id, email, first_name, last_name, is_admin):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET email = ?, first_name = ?, last_name = ?, is_admin = ?
        WHERE id = ?
    """, (email, first_name, last_name, is_admin, user_id))
    conn.commit()
    conn.close()


def update_user_password(user_id, new_password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET password = ? WHERE id = ?",
        (new_password, user_id)
    )
    conn.commit()
    conn.close()

def get_user_by_email(email):
    conn = get_connection()
    cur = conn.cursor()
    row = cur.execute(
        "SELECT id, email, first_name, last_name, password, is_admin FROM users WHERE email = ?",
        (email,)
    ).fetchone()
    conn.close()
    if row:
        return {
            'id': row[0],
            'email': row[1],
            'first_name': row[2],
            'last_name': row[3],
            'password': row[4],
            'is_admin': bool(row[5])
        }
    return None

def delete_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

# --- BOOKINGS ---
def get_all_bookings():
    conn = get_connection()
    cur = conn.cursor()
    rows = cur.execute('''
        SELECT b.id, b.user_id, b.space_id, b.booking_date, b.start_time, b.end_time,
               u.first_name || ' ' || u.last_name AS user_name, s.space_title
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        JOIN spaces s ON b.space_id = s.id
    ''').fetchall()
    conn.close()
    return [
        {
            'id': r[0],
            'user_id': r[1],
            'space_id': r[2],
            'booking_date': r[3],
            'start_time': r[4],
            'end_time': r[5],
            'user_name': r[6],
            'space_title': r[7]
        }
        for r in rows
    ]

def get_booking_by_id(booking_id):
    conn = get_connection()
    cur = conn.cursor()
    row = cur.execute(
        "SELECT id, user_id, space_id, booking_date, start_time, end_time FROM bookings WHERE id = ?",
        (booking_id,)
    ).fetchone()
    conn.close()
    if row:
        return {
            'id': row[0], 'user_id': row[1], 'space_id': row[2],
            'booking_date': row[3], 'start_time': row[4], 'end_time': row[5]
        }
    return None

def update_booking(booking_id, user_id, space_id, booking_date, start_time, end_time):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        '''
        UPDATE bookings
        SET user_id = ?, space_id = ?, booking_date = ?, start_time = ?, end_time = ?
        WHERE id = ?
        ''',
        (user_id, space_id, booking_date, start_time, end_time, booking_id)
    )
    conn.commit()
    conn.close()

def delete_booking(booking_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    conn.commit()
    conn.close()

def create_booking(user_id, space_id, booking_date, start_time, end_time):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        '''
        INSERT INTO bookings (user_id, space_id, booking_date, start_time, end_time)
        VALUES (?, ?, ?, ?, ?)
        ''',
        (user_id, space_id, booking_date, start_time, end_time)
    )
    conn.commit()
    conn.close()

def has_booking_conflict(space_id, booking_date, start_time, end_time, exclude_booking_id=None):
    conn = get_connection()
    cur = conn.cursor()

    query = '''
    SELECT COUNT(*)
    FROM bookings
    WHERE space_id = ?
    AND booking_date = ?
    AND NOT (end_time <= ? OR start_time >= ?)
    '''
    params = [space_id, booking_date, start_time, end_time]

    if exclude_booking_id is not None:
        query += " AND id != ?"
        params.append(exclude_booking_id)

    cur.execute(query, params)
    (count,) = cur.fetchone()
    conn.close()

    return count > 0

# --- SPACES ---
def get_all_spaces():
    conn = get_connection()
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT id, space_title, space_location, space_capacity, space_image, space_type, space_description FROM spaces"
    ).fetchall()
    conn.close()
    return [
        {
            'id': r[0], 'title': r[1], 'location': r[2], 'capacity': r[3],
            'image': r[4], 'type': r[5], 'description': r[6]
        }
        for r in rows
    ]

def get_space_by_id(space_id):
    conn = get_connection()
    cur = conn.cursor()
    row = cur.execute(
        "SELECT id, space_title, space_location, space_capacity, space_image, space_type, space_description FROM spaces WHERE id = ?",
        (space_id,)
    ).fetchone()
    conn.close()
    if row:
        return {
            'id': row[0], 'title': row[1], 'location': row[2], 'capacity': row[3],
            'image': row[4], 'type': row[5], 'description': row[6]
        }
    return None

def update_space(space_id, title, location, capacity, image, type, description):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        '''
        UPDATE spaces
        SET space_title = ?, space_location = ?, space_capacity = ?, space_image = ?, space_type = ?, space_description = ?
        WHERE id = ?
        ''',
        (title, location, capacity, image, type, description, space_id)
    )
    conn.commit()
    conn.close()

def delete_space(space_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM spaces WHERE id = ?", (space_id,))
    conn.commit()
    conn.close()

def create_space(title, location, capacity, image, type, description):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        '''
        INSERT INTO spaces (space_title, space_location, space_capacity, space_image, space_type, space_description)
        VALUES (?, ?, ?, ?, ?, ?)
        ''',
        (title, location, capacity, image, type, description)
    )
    conn.commit()
    conn.close()

# --- USER BOOKINGS ---
def get_user_bookings(user_id):
    conn = get_connection()
    cur = conn.cursor()
    rows = cur.execute('''
        SELECT b.id, b.user_id, b.space_id, b.booking_date, b.start_time, b.end_time,
               u.first_name || ' ' || u.last_name AS user_name, s.space_title
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        JOIN spaces s ON b.space_id = s.id
        WHERE b.user_id = ?
    ''', (user_id,)).fetchall()
    conn.close()
    return [
        {
            'id': r[0],
            'user_id': r[1],
            'space_id': r[2],
            'booking_date': r[3],
            'start_time': r[4],
            'end_time': r[5],
            'user_name': r[6],
            'space_title': r[7]
        }
        for r in rows
    ]

def get_upcoming_bookings(space_id):
    conn = get_connection()
    cur = conn.cursor()
    today = datetime.today().strftime('%Y-%m-%d')
    res = cur.execute('''
        SELECT id, user_id, space_id, booking_date, start_time, end_time
        FROM bookings
        WHERE space_id = ? AND booking_date >= ?
        ORDER BY booking_date, start_time
    ''', (space_id, today)).fetchall()
    conn.close()
    return [
        {
            'id': b[0],
            'user_id': b[1],
            'space_id': b[2],
            'booking_date': b[3],
            'start_time': b[4],
            'end_time': b[5]
        } for b in res
    ]

def get_bookings_by_date(space_id, booking_date):
    """Получает бронирования для конкретной даты и пространства"""
    conn = get_connection()
    cur = conn.cursor()
    res = cur.execute('''
        SELECT start_time, end_time 
        FROM bookings 
        WHERE space_id = ? AND booking_date = ?
    ''', (space_id, booking_date)).fetchall()
    conn.close()
    return [{'start_time': r[0], 'end_time': r[1]} for r in res]

def update_user_password(user_id, new_password):
    # Хешируем пароль перед сохранением
    hashed_pw = hash_password(new_password)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET password = ? WHERE id = ?",
        (hashed_pw, user_id)
    )
    conn.commit()
    conn.close()


from datetime import datetime, timedelta, time


def get_time_slots(space_id, selected_date, all_bookings):
    """
    Формирует слоты времени с учетом всех бронирований
    """
    # Преобразуем дату
    selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()

    # Фильтрация бронирований по пространству и дате
    bookings = [
        b for b in all_bookings
        if b['space_id'] == space_id and b['booking_date'] == selected_date
    ]

    # Преобразуем времена начала/окончания бронирований в объекты time
    booked_intervals = [
        (
            datetime.strptime(b["start_time"], "%H:%M").time(),
            datetime.strptime(b["end_time"], "%H:%M").time()
        )
        for b in bookings
    ]

    # Строим список всех слотов по 1 часу (с 08:00 до 20:00)
    slots = []
    current = time(8, 0)
    end = time(20, 0)

    while current < end:
        next_time = (datetime.combine(datetime.today(), current) + timedelta(hours=1)).time()
        status = "free"

        now = datetime.now()
        slot_start_datetime = datetime.combine(selected_date_obj, current)

        if slot_start_datetime < now:
            status = "past"
        else:
            for start, finish in booked_intervals:
                if not (next_time <= start or current >= finish):
                    status = "booked"
                    break

        slots.append({
            "start": current.strftime("%H:%M"),
            "end": next_time.strftime("%H:%M"),
            "status": status
        })
        current = next_time

    return slots

def count_user_active_bookings(user_id, date_from):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT COUNT(*) FROM bookings
        WHERE user_id = ? AND booking_date >= ?
        """,
        (user_id, date_from)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0