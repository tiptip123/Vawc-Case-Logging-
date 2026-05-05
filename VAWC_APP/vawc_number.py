from db import get_connection
from datetime import datetime

def generate_vawc_number(report_date=None):
    if report_date is None:
        report_date = datetime.now()
    
    year = report_date.year
    prefix = f"VAWC-{year}-"
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT MAX(vawc_no) FROM vawc_logs WHERE vawc_no LIKE ?", (prefix + '%',))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        if result[0]:
            last_num = int(result[0].split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1
        return f"{prefix}{next_num:04d}"
    except Exception as e:
        raise Exception(f"VAWC number generation failed: {str(e)}")