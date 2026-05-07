from db import get_connection
from datetime import datetime

def generate_vawc_number(report_date=None):
    if report_date is None:
        report_date = datetime.now()

    year = report_date.year
    prefix = f"VAWC-{year}-"
    connection = None
    try:
        connection = get_connection()
        connection.isolation_level = None
        cursor = connection.cursor()

        cursor.execute("BEGIN EXCLUSIVE")

        cursor.execute("SELECT MAX(vawc_no) FROM vawc_logs WHERE vawc_no LIKE ?", (prefix + '%',))
        result = cursor.fetchone()

        if result and result[0]:
            last_num = int(result[0].split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        vawc_number = f"{prefix}{next_num:04d}"
        cursor.execute("COMMIT")
        return vawc_number

    except Exception as e:
        if connection:
            try:
                cursor.execute("ROLLBACK")
            except:
                pass
        raise RuntimeError(f"Failed to generate VAWC number: {str(e)}")
    finally:
        if connection:
            connection.close()