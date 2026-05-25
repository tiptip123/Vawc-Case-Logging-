import sqlite3
import shutil
import os
import re
from datetime import datetime
from db import DB_FILE

def backup_database(output_path):
    """Backup SQLite database to SQL file"""
    try:
        # Connect to the database
        connection = sqlite3.connect(DB_FILE)
        cursor = connection.cursor()

        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        with open(output_path, 'w', encoding='utf-8') as f:
            # Write header
            f.write("-- SQLite Database Backup\n")
            f.write(f"-- Generated on: {sqlite3.datetime.datetime.now()}\n\n")

            # Backup each table
            for table_name in tables:
                table = table_name[0]
                if table.startswith('sqlite_'):
                    continue  # Skip SQLite internal tables

                f.write(f"-- Table: {table}\n")

                # Get table schema
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]

                # Get table data
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()

                # Write INSERT statements
                for row in rows:
                    # Escape single quotes in data
                    escaped_values = []
                    for value in row:
                        if value is None:
                            escaped_values.append('NULL')
                        elif isinstance(value, str):
                            escaped_values.append(f"'{value.replace(chr(39), chr(39)*2)}'")
                        else:
                            escaped_values.append(str(value))

                    values_str = ', '.join(escaped_values)
                    f.write(f"INSERT INTO {table} ({', '.join(column_names)}) VALUES ({values_str});\n")

                f.write("\n")

        cursor.close()
        connection.close()

    except Exception as e:
        raise Exception(f"Backup failed: {str(e)}")


def restore_database(input_path):
    """Restore SQLite database from SQL file"""
    try:
        # Connect to the database
        connection = sqlite3.connect(DB_FILE)
        cursor = connection.cursor()

        # Read and execute the SQL file
        with open(input_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # Split by semicolons and execute each statement
        statements = sql_content.split(';')
        for statement in statements:
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                cursor.execute(statement)

        connection.commit()
        cursor.close()
        connection.close()

    except Exception as e:
        raise Exception(f"Restore failed: {str(e)}")


def _is_sqlite_file_hashed(sqlite_path):
    try:
        temp_conn = sqlite3.connect(sqlite_path)
        temp_cursor = temp_conn.cursor()
        temp_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if temp_cursor.fetchone():
            temp_cursor.execute("PRAGMA table_info(users)")
            users_columns = [row[1] for row in temp_cursor.fetchall()]
            if 'password_hash' in users_columns or 'security_answer' in users_columns:
                temp_cursor.execute("SELECT password_hash, security_answer FROM users LIMIT 5")
                for row in temp_cursor.fetchall():
                    for value in row:
                        if value is None:
                            continue
                        if isinstance(value, str) and value.strip() and not re.match(r"\$2[aby]\$.{56}$", value.strip()):
                            return False
        temp_cursor.close()
        temp_conn.close()
        return True
    except Exception:
        return True


def _is_sql_dump_hashed(dump_path):
    try:
        with open(dump_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'password_hash' in content or 'security_answer' in content:
            if not re.search(r"\$2[aby]\$.{56}", content):
                return False
        return True
    except Exception:
        return True


def validate_import_file(input_path):
    lower = input_path.lower()
    if lower.endswith('.sqlite'):
        if not _is_sqlite_file_hashed(input_path):
            raise Exception('The selected SQLite backup appears to contain unhashed credentials. Import aborted.')
        return True
    if lower.endswith('.sql'):
        if not _is_sql_dump_hashed(input_path):
            raise Exception('The selected SQL dump appears to contain unhashed credentials. Import aborted.')
        return True
    raise Exception('Unsupported import format. Please select a .sqlite or .sql file.')


def restore_database(input_path):
    """Restore SQLite database from SQL file or SQLite backup"""
    validate_import_file(input_path)
    backup_dir = os.path.join(os.path.dirname(DB_FILE), 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(backup_dir, f'vawc_db_before_import_{timestamp}.sqlite')

    try:
        if os.path.exists(DB_FILE):
            shutil.copy2(DB_FILE, backup_path)

        if input_path.lower().endswith('.sqlite'):
            # Replace current DB with imported SQLite file
            shutil.copy2(input_path, DB_FILE)
            return

        # For SQL dumps, load into a temporary DB and then replace current DB file
        temp_db = os.path.join(os.path.dirname(DB_FILE), f'temp_import_{timestamp}.sqlite')
        temp_conn = sqlite3.connect(temp_db)
        temp_cursor = temp_conn.cursor()
        with open(input_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        temp_conn.executescript(sql_content)
        temp_conn.commit()
        temp_cursor.close()
        temp_conn.close()

        shutil.copy2(temp_db, DB_FILE)
        os.remove(temp_db)
    except Exception as e:
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, DB_FILE)
        raise Exception(f"Restore failed: {str(e)}")
