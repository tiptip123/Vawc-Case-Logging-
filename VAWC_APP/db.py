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

def log_action(username, action, target_record="", details=""):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO audit_logs (username, action, target_record, details)
            VALUES (?, ?, ?, ?)
        """, (username, action, target_record, details))
        connection.commit()
        cursor.close()
        connection.close()
    except:
        pass # Fail silently for logging

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
                referred_to TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Schema updates for vawc_logs
        try:
            cursor.execute("ALTER TABLE vawc_logs ADD COLUMN referred_to TEXT")
        except: pass

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
        except: pass
        try:
            cursor.execute("ALTER TABLE audit_logs ADD COLUMN details TEXT")
        except: pass

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
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Apply schema updates for existing databases
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN passcode TEXT")
        except: pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN security_question TEXT")
        except: pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN security_answer TEXT")
        except: pass

        # Seed default admin user if not exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", ('admin',))
        if cursor.fetchone()[0] == 0:
            hashed = bcrypt.hashpw("admin".encode('utf-8'), bcrypt.gensalt())
            # For the default admin, we'll set a default passcode '123456' and a dummy security answer
            passcode = "123456"
            sec_question = "What is the name of your elementary school?"
            sec_answer = bcrypt.hashpw("AdminSchool".lower().encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role, passcode, security_question, security_answer)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ('admin', hashed.decode('utf-8'), 'Administrator', 'Admin', passcode, sec_question, sec_answer))

        connection.commit()
        cursor.close()
        connection.close()
    except sqlite3.Error as e:
        raise Exception(f"Database initialization failed: {str(e)}")