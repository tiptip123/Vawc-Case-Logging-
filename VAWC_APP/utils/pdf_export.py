from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib import colors
from tkinter import filedialog
import os
from datetime import datetime
from db import get_connection

PAGE_WIDTH, PAGE_HEIGHT = letter
PAGE_MARGIN = 36
AVAILABLE_PAGE_WIDTH = PAGE_WIDTH - (PAGE_MARGIN * 2)


def parse_date(date_str):
    if not date_str:
        return None
    # Try common formats
    for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def _escape_text(value):
    if value is None:
        return ""
    text = str(value)
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>')


def _get_table_col_widths(data, font_name='Helvetica', font_size=8, min_width=40):
    col_count = len(data[0]) if data else 0
    widths = [0] * col_count
    for row in data:
        for idx, cell in enumerate(row):
            cell_text = _escape_text(cell)
            width = stringWidth(cell_text, font_name, font_size) + 12
            if width > widths[idx]:
                widths[idx] = width

    total = sum(widths)
    if total <= AVAILABLE_PAGE_WIDTH:
        return widths

    scale = AVAILABLE_PAGE_WIDTH / total
    return [max(min_width, w * scale) for w in widths]


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
        'assigned_to': record[11] or "",
        'follow_up_date': parse_date(record[12]),
        'attachments': record[13] if len(record) > 13 else None,
        'name_of_respondent': record[9],
        'remarks': record[14] if len(record) > 14 else None
    }

def export_single_pdf(record):
    from utils.helpers import load_config
    config = load_config()
    
    record = normalize_record(record)
    filename = f"VAWC_{record['vawc_no']}.pdf"
    path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=filename, filetypes=[("PDF files", "*.pdf")])
    if not path:
        return None
    doc = SimpleDocTemplate(path, pagesize=letter, leftMargin=PAGE_MARGIN, rightMargin=PAGE_MARGIN, topMargin=PAGE_MARGIN, bottomMargin=PAGE_MARGIN)
    styles = getSampleStyleSheet()
    header_style = styles['Title']
    header_style.fontSize = 14
    header_style.textColor = colors.HexColor("#1a2a4a")
    table_header_style = ParagraphStyle('TableHeader', parent=styles['Heading6'], fontName='Helvetica-Bold', fontSize=8, leading=10)
    table_body_style = ParagraphStyle('TableBody', parent=styles['BodyText'], fontName='Helvetica', fontSize=8, leading=10)
    elements = []

    elements.append(Paragraph("REPUBLIC OF THE PHILIPPINES", styles['Normal']))
    elements.append(Paragraph(f"PROVINCE OF {config['province'].upper()}", styles['Normal']))
    elements.append(Paragraph(f"MUNICIPALITY OF {config['municipality'].upper()}", styles['Normal']))
    elements.append(Paragraph(config['lgu_name'].upper(), styles['Normal']))
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph(f"VAWC Case Report: {record['vawc_no']}", header_style))
    elements.append(Spacer(1, 15))

    raw_data = [
        ["Field", "Details"],
        ["VAWC Number", record['vawc_no']],
        ["Date Reported", record['date'].strftime("%B %d, %Y") if record['date'] else ""],
        ["Client Name", record['client_name']],
        ["Age", str(record['age']) if record['age'] else ""],
        ["Contact", record['contact'] or "N/A"],
        ["Birthdate", record['birthdate'].strftime("%B %d, %Y") if record['birthdate'] else ""],
        ["Complete Address", record['address'] or "N/A"],
        ["Types of Abuse", record['type_of_abuse'] or "N/A"],
        ["Name of Respondent", record['name_of_respondent'] or "N/A"],
        ["Current Status", record['case_status'] or "Ongoing"],
        ["Assigned To", record.get('assigned_to') or ""],
        # Settled/Follow-up Date: if case was Settled, show updated_at; otherwise show follow_up_date
        ["Settled/Follow-up Date", ""],
        ["Remarks/Notes", record['remarks'] or "None"]
    ]

    # Determine Settled/Follow-up Date: prefer updated_at when status is Settled
    settled_or_follow = ""
    try:
        if record.get('case_status') and str(record.get('case_status')).strip().lower() == 'settled':
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT updated_at FROM vawc_logs WHERE vawc_no = ?", (record['vawc_no'],))
            r = cur.fetchone()
            if r and r[0]:
                dt = parse_date(r[0])
                if dt:
                    settled_or_follow = dt.strftime("%B %d, %Y")
            cur.close()
            conn.close()
        else:
            if record.get('follow_up_date'):
                settled_or_follow = record['follow_up_date'].strftime("%B %d, %Y")
    except Exception:
        settled_or_follow = ""

    # Insert the computed date into the raw_data table (replace placeholder)
    for idx, row in enumerate(raw_data):
        if row[0] == "Settled/Follow-up Date":
            raw_data[idx][1] = settled_or_follow
            break

    table_data = [[Paragraph(_escape_text(cell), table_header_style) for cell in raw_data[0]]]
    for row in raw_data[1:]:
        table_data.append([Paragraph(_escape_text(cell), table_body_style) for cell in row])

    col_widths = _get_table_col_widths(raw_data, font_name='Helvetica', font_size=8)
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1a2a4a")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 1), (-1, -1), 8),
        ('RIGHTPADDING', (0, 1), (-1, -1), 8),
        ('WORDWRAP', (0, 0), (-1, -1), 'CJK')
    ]))
    elements.append(table)
    
    elements.append(Spacer(1, 40))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
    
    doc.build(elements)
    return path

def export_full_pdf():
    from utils.helpers import load_config
    config = load_config()
    
    filename = "VAWC_Full_List.pdf"
    path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=filename, filetypes=[("PDF files", "*.pdf")])
    if not path:
        return
    
    connection = None
    try:
        doc = SimpleDocTemplate(path, pagesize=letter, leftMargin=PAGE_MARGIN, rightMargin=PAGE_MARGIN, topMargin=PAGE_MARGIN, bottomMargin=PAGE_MARGIN)
        styles = getSampleStyleSheet()
        table_header_style = ParagraphStyle('TableHeader', parent=styles['Heading6'], fontName='Helvetica-Bold', fontSize=8, leading=10)
        table_body_style = ParagraphStyle('TableBody', parent=styles['BodyText'], fontName='Helvetica', fontSize=8, leading=10)
        elements = []

        elements.append(Paragraph("REPUBLIC OF THE PHILIPPINES", styles['Normal']))
        elements.append(Paragraph(f"PROVINCE OF {config['province'].upper()}", styles['Normal']))
        elements.append(Paragraph(f"MUNICIPALITY OF {config['municipality'].upper()}", styles['Normal']))
        elements.append(Paragraph(config['lgu_name'].upper(), styles['Normal']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("VAWC Case Logging System - Full List", styles['Title']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%m/%d/%Y %I:%M %p')}", styles['Normal']))
        elements.append(Spacer(1, 12))

        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT vawc_no, date, client_name, age, contact, birthdate, address, type_of_abuse, case_status, name_of_respondent, assigned_to, follow_up_date, updated_at, remarks FROM vawc_logs WHERE is_deleted = 0 ORDER BY date DESC")
        rows = cursor.fetchall()
        raw_data = [["VAWC No", "Date", "Client Name", "Age", "Type of Abuse", "Case Status", "Respondent", "Assigned To", "Follow-up Date"]]
        for row in rows:
            # Determine Settled/Follow-up date per row: if case_status == 'Settled' use updated_at, else follow_up_date
            try:
                follow = ""
                if str(row[8]).strip().lower() == 'settled':
                    follow = parse_date(row[12])
                else:
                    follow = parse_date(row[11])
                follow_str = follow.strftime("%m/%d/%Y") if follow else ""
            except Exception:
                follow_str = ""

            raw_data.append([
                row[0],
                row[1],
                row[2],
                row[3],
                row[7],
                row[8],
                row[9],
                row[10] if len(row) > 10 else "",
                follow_str
            ])

        table_data = [[Paragraph(_escape_text(cell), table_header_style) for cell in raw_data[0]]]
        for row in raw_data[1:]:
            table_data.append([Paragraph(_escape_text(cell), table_body_style) for cell in row])

        col_widths = _get_table_col_widths(raw_data, font_name='Helvetica', font_size=8)
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1a2a4a")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('WORDWRAP', (0, 0), (-1, -1), 'CJK')
        ]))
        elements.append(table)
        doc.build(elements)
    except Exception as e:
        from tkinter import messagebox
        messagebox.showerror("Export Error", f"Failed to generate PDF: {str(e)}")
    finally:
        if connection:
            connection.close()

def export_filtered_pdf(search_term="", filter_abuse="", filter_status="", filter_year="", filter_month=""):
    from utils.helpers import load_config
    config = load_config()
    
    filename = "VAWC_Filtered_List.pdf"
    path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=filename, filetypes=[("PDF files", "*.pdf")])
    if not path:
        return
    
    connection = None
    try:
        doc = SimpleDocTemplate(path, pagesize=letter, leftMargin=PAGE_MARGIN, rightMargin=PAGE_MARGIN, topMargin=PAGE_MARGIN, bottomMargin=PAGE_MARGIN)
        styles = getSampleStyleSheet()
        table_header_style = ParagraphStyle('TableHeader', parent=styles['Heading6'], fontName='Helvetica-Bold', fontSize=8, leading=10)
        table_body_style = ParagraphStyle('TableBody', parent=styles['BodyText'], fontName='Helvetica', fontSize=8, leading=10)
        elements = []

        elements.append(Paragraph("REPUBLIC OF THE PHILIPPINES", styles['Normal']))
        elements.append(Paragraph(f"PROVINCE OF {config['province'].upper()}", styles['Normal']))
        elements.append(Paragraph(f"MUNICIPALITY OF {config['municipality'].upper()}", styles['Normal']))
        elements.append(Paragraph(config['lgu_name'].upper(), styles['Normal']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("VAWC Case Logging System - Filtered List", styles['Title']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%m/%d/%Y %I:%M %p')}", styles['Normal']))
        elements.append(Spacer(1, 12))

        connection = get_connection()
        cursor = connection.cursor()
        
        query = "SELECT vawc_no, date, client_name, age, contact, birthdate, address, type_of_abuse, case_status, name_of_respondent, assigned_to, follow_up_date, updated_at, remarks FROM vawc_logs WHERE is_deleted = 0"
        params = []
        
        if search_term:
            query += " AND (client_name LIKE ? OR vawc_no LIKE ? OR name_of_respondent LIKE ?)"
            term = f"%{search_term}%"
            params.extend([term, term, term])
        if filter_abuse and filter_abuse != "Type of Abuse":
            query += " AND type_of_abuse LIKE ?"
            params.append(f"%{filter_abuse}%")
        if filter_status and filter_status != "Status":
            query += " AND case_status = ?"
            params.append(filter_status)
        if filter_year and filter_year != "Year":
            query += " AND strftime('%Y', date) = ?"
            params.append(filter_year)
        if filter_month and filter_month != "Month":
            query += " AND strftime('%m', date) = ?"
            params.append(filter_month)

        query += " ORDER BY date DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()

        raw_data = [["VAWC No", "Date", "Client Name", "Age", "Type of Abuse", "Case Status", "Respondent", "Assigned To", "Follow-up Date"]]
        for row in rows:
            try:
                follow = ""
                if str(row[8]).strip().lower() == 'settled':
                    follow = parse_date(row[12])
                else:
                    follow = parse_date(row[11])
                follow_str = follow.strftime("%m/%d/%Y") if follow else ""
            except Exception:
                follow_str = ""

            raw_data.append([
                row[0],
                row[1],
                row[2],
                row[3],
                row[7],
                row[8],
                row[9],
                row[10] if len(row) > 10 else "",
                follow_str
            ])

        table_data = [[Paragraph(_escape_text(cell), table_header_style) for cell in raw_data[0]]]
        for row in raw_data[1:]:
            table_data.append([Paragraph(_escape_text(cell), table_body_style) for cell in row])

        col_widths = _get_table_col_widths(raw_data, font_name='Helvetica', font_size=8)
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1a2a4a")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('WORDWRAP', (0, 0), (-1, -1), 'CJK')
        ]))
        elements.append(table)
        doc.build(elements)
    except Exception as e:
        from tkinter import messagebox
        messagebox.showerror("Export Error", f"Failed to generate PDF: {str(e)}")
    finally:
        if connection:
            connection.close()

def export_followup_schedule_pdf(search_term="", filter_abuse="", filter_status="", filter_year="", filter_month=""):
    from utils.helpers import load_config
    config = load_config()

    filename = "VAWC_Follow-up_Schedule.pdf"
    path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=filename, filetypes=[("PDF files", "*.pdf")])
    if not path:
        return

    connection = None
    try:
        doc = SimpleDocTemplate(path, pagesize=letter, leftMargin=PAGE_MARGIN, rightMargin=PAGE_MARGIN, topMargin=PAGE_MARGIN, bottomMargin=PAGE_MARGIN)
        styles = getSampleStyleSheet()
        table_header_style = ParagraphStyle('TableHeader', parent=styles['Heading6'], fontName='Helvetica-Bold', fontSize=8, leading=10)
        table_body_style = ParagraphStyle('TableBody', parent=styles['BodyText'], fontName='Helvetica', fontSize=8, leading=10)

        elements = []
        elements.append(Paragraph("REPUBLIC OF THE PHILIPPINES", styles['Normal']))
        elements.append(Paragraph(f"PROVINCE OF {config['province'].upper()}", styles['Normal']))
        elements.append(Paragraph(f"MUNICIPALITY OF {config['municipality'].upper()}", styles['Normal']))
        elements.append(Paragraph(config['lgu_name'].upper(), styles['Normal']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("VAWC Case Logging System - Follow-up Schedule", styles['Title']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%m/%d/%Y %I:%M %p')}", styles['Normal']))
        elements.append(Spacer(1, 12))

        connection = get_connection()
        cursor = connection.cursor()
        query = "SELECT vawc_no, client_name, assigned_to, follow_up_date, case_status, referred_to, remarks FROM vawc_logs WHERE is_deleted = 0 AND follow_up_date IS NOT NULL AND follow_up_date != ''"
        params = []

        if search_term:
            query += " AND (client_name LIKE ? OR vawc_no LIKE ? OR name_of_respondent LIKE ?)"
            term = f"%{search_term}%"
            params.extend([term, term, term])
        if filter_abuse and filter_abuse != "Type of Abuse":
            query += " AND type_of_abuse LIKE ?"
            params.append(f"%{filter_abuse}%")
        if filter_status and filter_status != "Status":
            query += " AND case_status = ?"
            params.append(filter_status)
        if filter_year and filter_year != "Year":
            query += " AND strftime('%Y', date) = ?"
            params.append(filter_year)
        if filter_month and filter_month != "Month":
            query += " AND strftime('%m', date) = ?"
            params.append(filter_month)

        query += " ORDER BY follow_up_date ASC"
        cursor.execute(query, params)
        rows = cursor.fetchall()

        raw_data = [["VAWC No", "Client Name", "Assigned To", "Follow-up Date", "Case Status", "Referred To", "Notes"]]
        for row in rows:
            follow_date_str = ""
            try:
                if row[3]:
                    follow_date = parse_date(row[3])
                    if follow_date:
                        follow_date_str = follow_date.strftime("%m/%d/%Y")
            except Exception:
                follow_date_str = row[3] or ""

            raw_data.append([
                row[0],
                row[1],
                row[2] or "",
                follow_date_str,
                row[4] or "",
                row[5] or "",
                row[6] or ""
            ])

        table_data = [[Paragraph(_escape_text(cell), table_header_style) for cell in raw_data[0]]]
        for row in raw_data[1:]:
            table_data.append([Paragraph(_escape_text(cell), table_body_style) for cell in row])

        col_widths = _get_table_col_widths(raw_data, font_name='Helvetica', font_size=8)
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1a2a4a")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('WORDWRAP', (0, 0), (-1, -1), 'CJK')
        ]))
        elements.append(table)
        doc.build(elements)
    except Exception as e:
        from tkinter import messagebox
        messagebox.showerror("Export Error", f"Failed to export follow-up schedule: {str(e)}")
    finally:
        if connection:
            connection.close()