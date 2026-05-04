import sqlite3
import shutil
import os
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
