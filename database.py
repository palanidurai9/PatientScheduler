import sqlite3

DATABASE = 'database.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Add this new table creation for users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user' -- e.g., 'admin', 'user'
        )
    ''')

    # Your existing appointments table creation
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            patient_phone TEXT NOT NULL,
            patient_email TEXT NOT NULL,
            appointment_time TEXT NOT NULL UNIQUE, -- Store as YYYY-MM-DD HH:MM
            status TEXT DEFAULT 'booked' -- booked, confirmed, cancelled, no-show
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == '__main__':
    init_db()