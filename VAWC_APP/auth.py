import bcrypt
from db import get_connection
from datetime import datetime, timedelta

def verify_login(username, password):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        
        # Check if user is locked out
        cursor.execute("SELECT password_hash, role, login_attempts, lockout_until FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            connection.close()
            return None
            
        password_hash, role, attempts, lockout_until = user
        
        # Check lockout
        if lockout_until:
            lockout_time = datetime.fromisoformat(lockout_until)
            if datetime.now() < lockout_time:
                cursor.close()
                connection.close()
                raise Exception(f"Account locked. Try again after {lockout_time.strftime('%I:%M %p')}.")

        if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
            # Reset attempts on success
            cursor.execute("UPDATE users SET login_attempts = 0, lockout_until = NULL WHERE username = ?", (username,))
            connection.commit()
            cursor.close()
            connection.close()
            return role
        else:
            # Increment attempts on failure
            new_attempts = (attempts or 0) + 1
            new_lockout = None
            if new_attempts >= 5:
                new_lockout = (datetime.now() + timedelta(minutes=10)).isoformat()
            
            cursor.execute("UPDATE users SET login_attempts = ?, lockout_until = ? WHERE username = ?", 
                           (new_attempts, new_lockout, username))
            connection.commit()
            cursor.close()
            connection.close()
            return None
    except Exception as e:
        if "Account locked" in str(e):
            raise e
        raise Exception(f"Login verification failed: {str(e)}")