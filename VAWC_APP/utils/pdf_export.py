from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from tkinter import filedialog
import os
from datetime import datetime
from db import get_connection


def parse_date(date_str):
    if not date_str:
        return None
    # Try common formats
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

def normalize_record(record):
    if record is None:
        return {}
    if isinstance(record, dict):
        # Already a dict, but might need date parsing if coming from UI
        data = record.copy()
        if isinstance(data.get('date'), str):
            data['date'] = parse_date(data['date'])
        if isinstance(data.get('birthdate'), str):
            data['birthdate'] = parse_date(data['birthdate'])
        return data
        
    return {
        'vawc_no': record[1],
        'date': parse_date(record[2]),
        'client_name': record[3],
        'age': record[4],
        'contact': record[5],
        'birthdate': parse_date(record[6]),
        'address': record[7],
        'type_of_abuse': record[8],
        'case_status': record[10] if record[10] else 'Ongoing',
        'attachments': record[11],
        'name_of_respondent': record[9],
        'remarks': record[12]
    }

def export_single_pdf(record):
    record = normalize_record(record)
    filename = f"VAWC_{record['vawc_no']}.pdf"
    path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=filename, filetypes=[("PDF files", "*.pdf")])
    if not path:
        return None
    doc = SimpleDocTemplate(path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("VAWC Case Logging System - Barangay Tankulan, Manolo Fortich, Bukidnon", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%m/%d/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 12))

    data = [
        ["VAWC No", record['vawc_no']],
        ["Date", record['date'].strftime("%m/%d/%Y")],
        ["Client Name", record['client_name']],
        ["Age", str(record['age']) if record['age'] else ""],
        ["Contact", record['contact'] or ""],
        ["Birthdate", record['birthdate'].strftime("%m/%d/%Y") if record['birthdate'] else ""],
        ["Address", record['address'] or ""],
        ["Type of Abuse", record['type_of_abuse'] or ""],
        ["Case Status", record['case_status'] or "Ongoing"],
        ["Attachments", record['attachments'] or ""],
        ["Name of Respondent", record['name_of_respondent'] or ""],
        ["Remarks", record['remarks'] or ""]
    ]

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    doc.build(elements)
    return path

def export_full_pdf():
    filename = "VAWC_Full_List.pdf"
    path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=filename, filetypes=[("PDF files", "*.pdf")])
    if not path:
        return
    doc = SimpleDocTemplate(path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("VAWC Case Logging System - Full List - Barangay Tankulan, Manolo Fortich, Bukidnon", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%m/%d/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 12))

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT vawc_no, date, client_name, age, contact, birthdate, address, type_of_abuse, case_status, attachments, name_of_respondent, remarks FROM vawc_logs")
    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    data = [["VAWC No", "Date", "Client Name", "Age", "Contact", "Birthdate", "Address", "Type of Abuse", "Case Status", "Attachments", "Respondent", "Remarks"]]
    for row in rows:
        data.append([str(cell) if cell else "" for cell in row])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    doc.build(elements)

def export_filtered_pdf():
    # Placeholder: same as full for now
    export_full_pdf()