import sqlite3
import bcrypt
import secrets
import string
from datetime import datetime
import os

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vawc_db.sqlite')

def get_connection(retry_count=0, max_retries=2):
    try:
        conn = sqlite3.connect(DB_FILE, timeout=5.0)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.OperationalError as e:
        if ("locked" in str(e) or "unable to open" in str(e)) and retry_count < max_retries:
            from tkinter import messagebox
            messagebox.showerror("Database Error",
                                 "The database file is currently locked or missing.\n\n"
                                 "Please ensure no other instances of the app are running and "
                                 "you have write permissions in the folder.\n\n"
                                 "Click OK to retry.")
            return get_connection(retry_count + 1, max_retries)
        raise e

def log_action(username, action, target_record="", details=""):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO audit_logs (username, action, target_record, details)
            VALUES (?, ?, ?, ?)
        """, (username, action, target_record, details))
        connection.commit()
    except sqlite3.Error as e:
        print(f"Database logging error: {e}")
    finally:
        if connection:
            connection.close()

def init_db():
    connection = None
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
                referred_to TEXT,
                is_deleted INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Schema updates for vawc_logs
        try:
            cursor.execute("ALTER TABLE vawc_logs ADD COLUMN referred_to TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE vawc_logs ADD COLUMN is_deleted INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        # Create audit_logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                action TEXT,
                target_record TEXT,
                details TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Schema updates for audit_logs
        try:
            cursor.execute("ALTER TABLE audit_logs ADD COLUMN target_record TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE audit_logs ADD COLUMN details TEXT")
        except sqlite3.OperationalError:
            pass

        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'Staff',
                passcode TEXT,
                security_question TEXT,
                security_answer TEXT,
                profile_picture TEXT,
                login_attempts INTEGER DEFAULT 0,
                lockout_until TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Apply schema updates for existing databases
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN passcode TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN security_question TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN security_answer TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN profile_picture TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN login_attempts INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN lockout_until TEXT")
        except sqlite3.OperationalError:
            pass

        # Seed default admin user if not exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", ('admin',))
        if cursor.fetchone()[0] == 0:
            default_password = secrets.choice(string.ascii_uppercase) + ''.join(
                secrets.choice(string.ascii_letters + string.digits) for _ in range(11)
            )
            hashed_pass = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            default_passcode = ''.join(secrets.choice(string.digits) for _ in range(6))
            hashed_passcode = bcrypt.hashpw(default_passcode.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            sec_question = "What is the name of your elementary school?"
            hashed_sec_answer = bcrypt.hashpw("AdminSchool".lower().encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role, passcode, security_question, security_answer)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ('admin', hashed_pass, 'Administrator', 'Admin', hashed_passcode, sec_question, hashed_sec_answer))

            from tkinter import messagebox
            messagebox.showinfo("First Run Setup",
                               f"Admin account created.\n\n"
                               f"Username: admin\n"
                               f"Password: {default_password}\n"
                               f"Passcode: {default_passcode}\n\n"
                               f"Please save these credentials securely and change them after your first login.")

        connection.commit()
    except sqlite3.Error as e:
        raise Exception(f"Database initialization failed: {str(e)}")
    finally:
        if connection:
            connection.close()