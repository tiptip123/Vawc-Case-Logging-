import sqlite3
import bcrypt
import secrets
import string
from datetime import datetime
import os

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vawc_db.sqlite')

def get_connection(retry_count=0, max_retries=2):
    try:
        conn = sqlite3.connect(DB_FILE, timeout=30.0)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 30000")
        conn.execute("PRAGMA journal_mode = WAL")
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
                assigned_to TEXT,
                follow_up_date TEXT,
                attachments TEXT,
                remarks TEXT,
                referred_to TEXT,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TEXT,
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
            cursor.execute("ALTER TABLE vawc_logs ADD COLUMN assigned_to TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE vawc_logs ADD COLUMN follow_up_date TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE vawc_logs ADD COLUMN is_deleted INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE vawc_logs ADD COLUMN deleted_at TEXT")
        except sqlite3.OperationalError:
            pass

        # Clean expired trash records older than 15 days
        try:
            cursor.execute("""
                DELETE FROM vawc_logs
                WHERE is_deleted = 1
                AND (
                    (deleted_at IS NOT NULL AND julianday('now') - julianday(deleted_at) > 15)
                    OR (deleted_at IS NULL AND julianday('now') - julianday(updated_at) > 15)
                )
            """)
        except sqlite3.Error:
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
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN failed_attempts INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
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

        # Create abuse_types table and seed defaults if empty
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS abuse_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)

        try:
            cursor.execute("SELECT COUNT(*) FROM abuse_types")
            count = cursor.fetchone()[0]
        except Exception:
            count = 0

        if count == 0:
            default_types = [
                "Domestic Abuse", "Financial Abuse", "Material Abuse", "Modern Slavery",
                "Criminal Exploitation", "Neglect", "Acts of Omission", "Organisational Abuse",
                "Self-Neglect", "Hoarding", "Sexual Abuse", "Sexual Exploitation",
                "Emotional Abuse", "Psychological Abuse"
            ]
            for t in default_types:
                try:
                    cursor.execute("INSERT INTO abuse_types (name) VALUES (?)", (t,))
                except sqlite3.IntegrityError:
                    pass

        connection.commit()
    except sqlite3.Error as e:
        raise Exception(f"Database initialization failed: {str(e)}")
    finally:
        if connection:
            connection.close()

def get_abuse_types():
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM abuse_types ORDER BY name")
        rows = cursor.fetchall()
        return [r[0] for r in rows]
    except Exception:
        # Fallback to common list if DB read fails
        return [
            "Domestic Abuse", "Financial Abuse", "Material Abuse", "Modern Slavery",
            "Criminal Exploitation", "Neglect", "Acts of Omission", "Organisational Abuse",
            "Self-Neglect", "Hoarding", "Sexual Abuse", "Sexual Exploitation",
            "Emotional Abuse", "Psychological Abuse"
        ]
    finally:
        if connection:
            connection.close()

def add_abuse_type(name):
    if not name or not name.strip():
        raise ValueError("Name cannot be empty")
    name = name.strip()
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM abuse_types WHERE LOWER(name)=LOWER(?)", (name,))
        if cursor.fetchone():
            raise ValueError("Abuse type already exists")
        cursor.execute("INSERT INTO abuse_types (name) VALUES (?)", (name,))
        connection.commit()
        return True
    finally:
        if connection:
            connection.close()


def ensure_abuse_type(name):
    if not name or not name.strip():
        return False
    name = name.strip()
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM abuse_types WHERE LOWER(name)=LOWER(?)", (name,))
        if cursor.fetchone():
            return False
        cursor.execute("INSERT INTO abuse_types (name) VALUES (?)", (name,))
        connection.commit()
        return True
    finally:
        if connection:
            connection.close()


def is_abuse_type_in_use(name):
    if not name or not name.strip():
        return False
    name = name.strip()
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM vawc_logs WHERE is_deleted = 0 AND (type_of_abuse = ? OR type_of_abuse LIKE ? OR type_of_abuse LIKE ? OR type_of_abuse LIKE ?)",
            (name, f"{name}, %", f"%, {name}", f"%, {name}, %")
        )
        return cursor.fetchone()[0] > 0
    finally:
        if connection:
            connection.close()


def update_abuse_type(old_name, new_name):
    if not old_name or not old_name.strip():
        raise ValueError("Original name cannot be empty")
    if not new_name or not new_name.strip():
        raise ValueError("New name cannot be empty")
    old_name = old_name.strip()
    new_name = new_name.strip()
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM abuse_types WHERE LOWER(name)=LOWER(?)", (old_name,))
        row = cursor.fetchone()
        if not row:
            raise ValueError("Abuse type not found")
        type_id = row[0]
        cursor.execute("SELECT 1 FROM abuse_types WHERE LOWER(name)=LOWER(?) AND id != ?", (new_name, type_id))
        if cursor.fetchone():
            raise ValueError("Abuse type already exists")
        cursor.execute("UPDATE abuse_types SET name = ? WHERE id = ?", (new_name, type_id))

        cursor.execute(
            "SELECT id, type_of_abuse FROM vawc_logs WHERE is_deleted = 0 AND (type_of_abuse = ? OR type_of_abuse LIKE ? OR type_of_abuse LIKE ? OR type_of_abuse LIKE ?)",
            (old_name, f"{old_name}, %", f"%, {old_name}", f"%, {old_name}, %")
        )
        rows = cursor.fetchall()
        for record_id, type_of_abuse in rows:
            parts = [p.strip() for p in type_of_abuse.split(",") if p.strip()]
            updated_parts = [new_name if p.lower() == old_name.lower() else p for p in parts]
            cursor.execute("UPDATE vawc_logs SET type_of_abuse = ? WHERE id = ?", (", ".join(updated_parts), record_id))

        connection.commit()
        return True
    finally:
        if connection:
            connection.close()


def delete_abuse_type(name):
    if not name or not name.strip():
        raise ValueError("Name cannot be empty")
    name = name.strip()
    if is_abuse_type_in_use(name):
        raise ValueError("This type is in use and cannot be deleted")
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM abuse_types WHERE LOWER(name)=LOWER(?)", (name,))
        if cursor.rowcount == 0:
            raise ValueError("Abuse type not found")
        connection.commit()
        return True
    finally:
        if connection:
            connection.close()