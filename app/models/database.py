import os
import sqlite3

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # корень проекта
DB_PATH = os.path.join(BASE_DIR,'app', 'data', 'spaces.db')


def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    print(f"[DEBUG] DB path: {DB_PATH}")
    conn = get_connection()
    cursor = conn.cursor()

    # Таблица пространств
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS spaces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT,
            capacity INTEGER
        )
    ''')

    # Таблица бронирований
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            space_id INTEGER,
            date TEXT NOT NULL,
            time_from TEXT NOT NULL,
            time_to TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(space_id) REFERENCES spaces(id)
        )
    ''')

    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            password TEXT NOT NULL,
            user_role TEXT NOT NULL CHECK (user_role IN ('student', 'teacher', 'admin'))
        )
    ''')

    conn.commit()
    conn.close()
    print("[INFO] Таблицы успешно инициализированы.")
