import openpyxl
from openpyxl.styles import Font
import os
from db import get_connection

def export_to_excel():
    filename = "VAWC_Records.xlsx"
    path = os.path.join(os.path.expanduser("~/Desktop"), filename)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "VAWC Logs"

    # Add title
    ws.cell(row=1, column=1).value = "VAWC Case Logging System - Barangay Tankulan, Manolo Fortich, Bukidnon"
    ws.cell(row=1, column=1).font = Font(bold=True, size=14)

    headers = ["VAWC No", "Date", "Client Name", "Age", "Contact", "Birthdate", "Address", "Type of Abuse", "Case Status", "Attachments", "Respondent", "Remarks"]
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=2, column=col_num)
        cell.value = header
        cell.font = Font(bold=True)

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT vawc_no, date, client_name, age, contact, birthdate, address, type_of_abuse, case_status, attachments, name_of_respondent, remarks FROM vawc_logs")
    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    for row_num, row in enumerate(rows, 3):
        for col_num, cell_value in enumerate(row, 1):
            ws.cell(row=row_num, column=col_num).value = str(cell_value) if cell_value else ""

    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column_letter].width = adjusted_width

    wb.save(path)