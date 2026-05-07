import bcrypt
from db import get_connection
from datetime import datetime, timedelta

def authenticate_user(username, password):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        
        # Check if account is locked
        cursor.execute("SELECT login_attempts, lockout_until FROM users WHERE username = ?", (username,))
        user_row = cursor.fetchone()
        
        if user_row:
            login_attempts, lockout_until = user_row
            if lockout_until:
                try:
                    # SQLite stores datetime objects as strings
                    if isinstance(lockout_until, str):
                        lockout_dt = datetime.fromisoformat(lockout_until)
                    else:
                        lockout_dt = lockout_until
                        
                    if datetime.now() < lockout_dt:
                        remaining = int((lockout_dt - datetime.now()).total_seconds() / 60)
                        return False, f"Account locked. Try again in {remaining} minutes."
                except (ValueError, TypeError):
                    pass # Fall through if parsing fails
        
        # Verify password
        cursor.execute("SELECT password_hash, role, login_attempts FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        
        if row and bcrypt.checkpw(password.encode('utf-8'), row[0].encode('utf-8')):
            # Reset failed attempts on success
            cursor.execute("UPDATE users SET login_attempts = 0, lockout_until = NULL WHERE username = ?", (username,))
            connection.commit()
            return True, row[1]  # role
        
        # Increment failed attempts
        if user_row:
            new_attempts = login_attempts + 1
            lockout = None
            if new_attempts >= 5:
                lockout = datetime.now() + timedelta(minutes=15)
            cursor.execute("UPDATE users SET login_attempts = ?, lockout_until = ? WHERE username = ?", 
                          (new_attempts, lockout, username))
            connection.commit()
        
        return False, "Invalid credentials"
    finally:
        if connection:
            connection.close()