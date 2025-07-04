import os
import sqlite3

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # корень проекта
DB_PATH = os.path.join(BASE_DIR,'app', 'data', 'data.db')


def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    print(f"[DEBUG] DB path: {DB_PATH}")
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            password TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0
        )
    ''')

    # Остальные таблицы остаются без изменений
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS spaces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            space_title TEXT NOT NULL,
            space_location TEXT,
            space_capacity INTEGER,
            space_image TEXT,
            space_type TEXT,
            space_description TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            space_id INTEGER,
            booking_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(space_id) REFERENCES spaces(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("[INFO] Таблицы успешно инициализированы.")