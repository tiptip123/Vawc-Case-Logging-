import sqlite3
import bcrypt
from datetime import datetime

DB_FILE = 'vawc.db'

def get_connection():
    try:
        connection = sqlite3.connect(DB_FILE)
        return connection
    except sqlite3.Error as e:
        raise Exception(f"Database connection failed: {str(e)}")

def init_db():
    try:
        connection = get_connection()
        cursor = connection.cursor()

        # Create vawc_logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vawc_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vawc_no TEXT UNIQUE NOT NULL,
                date TEXT NOT NULL,
                client_name TEXT NOT NULL,
                age INTEGER,
                contact TEXT,
                birthdate TEXT,
                address TEXT,
                type_of_abuse TEXT,
                name_of_respondent TEXT,
                case_status TEXT DEFAULT 'Ongoing',
                attachments TEXT,
                remarks TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'Staff',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Seed default admin user if not exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", ('admin',))
        if cursor.fetchone()[0] == 0:
            hashed = bcrypt.hashpw("admin".encode('utf-8'), bcrypt.gensalt())
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role)
                VALUES (?, ?, ?, ?)
            """, ('admin', hashed.decode('utf-8'), 'Administrator', 'Admin'))

        connection.commit()
        cursor.close()
        connection.close()
    except sqlite3.Error as e:
        raise Exception(f"Database initialization failed: {str(e)}")