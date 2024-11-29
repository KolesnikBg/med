import sqlite3

# Функция для получения подключения к базе данных
def get_db_connection():
    conn = sqlite3.connect("medical.db")
    conn.row_factory = sqlite3.Row  # Позволяет работать с данными как с аттрибутами строк
    return conn

# Модели базы данных для пользователей, врачей и записей на прием
def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES users(id),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        )
        """)

        conn.commit()
        print("Database initialized and tables created.")
