import bcrypt
from db import get_connection

def verify_login(username, password):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT password_hash, role FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        if user and bcrypt.checkpw(password.encode('utf-8'), user[0].encode('utf-8')):
            return user[1]
        return None
    except Exception as e:
        raise Exception(f"Login verification failed: {str(e)}")