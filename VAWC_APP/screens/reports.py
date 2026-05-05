import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
from datetime import datetime
from utils.pdf_export import export_full_pdf, export_filtered_pdf
from utils.excel_export import export_to_excel
from utils.db_backup import backup_database, restore_database

class ReportsFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#f5f5f5")
        self.setup_ui()

    def setup_ui(self):
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()

        # Main container with scrolling for responsiveness
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="#f5f5f5")
        self.scroll_container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(self.scroll_container, text="📂 Reports & Data Export", font=("Arial", 22, "bold"), text_color="#1a2a4a").pack(pady=(10, 20))

        # Grid for Export Cards
        export_grid = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        export_grid.pack(fill="x", pady=10)
        export_grid.grid_columnconfigure((0, 1), weight=1)

        # 1. PDF Export Card
        pdf_card = self.create_report_card(
            export_grid, "📄 PDF Reports", 
            "Generate professional PDF documents of case logs.",
            [
                {"text": "Export Full List to PDF", "desc": "Exports every record in the system to a PDF file.", "command": self.export_full_pdf},
                {"text": "Export Filtered List to PDF", "desc": "Exports records matching current filters (PDF).", "command": self.export_filtered_pdf}
            ],
            row=0, col=0
        )

        # 2. Excel Export Card
        excel_card = self.create_report_card(
            export_grid, "📊 Excel Reports",
            "Export raw data to spreadsheet for advanced analysis.",
            [
                {"text": "Export to Excel (.xlsx)", "desc": "Saves all records into an Excel spreadsheet format.", "command": self.export_excel}
            ],
            row=0, col=1
        )

        # 3. Database Management Card
        db_card = self.create_report_card(
            self.scroll_container, "💾 Database Management",
            "Securely backup or restore the application database.",
            [
                {"text": "Backup Database", "desc": "Create a security copy of all your case data.", "command": self.backup_db, "color": "#1a73e8"},
                {"text": "Restore Database", "desc": "Restore data from a previous backup file.", "command": self.restore_db, "color": "#1a73e8"}
            ],
            is_full_width=True
        )

    def create_report_card(self, parent, title, subtitle, buttons, row=0, col=0, is_full_width=False):
        card = ctk.CTkFrame(parent, fg_color="white", corner_radius=15)
        if is_full_width:
            card.pack(fill="x", pady=10)
        else:
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(card, text=title, font=("Arial", 16, "bold"), text_color="#1a2a4a").pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(card, text=subtitle, font=("Arial", 11), text_color="#666666").pack(anchor="w", padx=20, pady=(0, 15))

        for btn in buttons:
            btn_color = btn.get("color", "#8b0000")
            btn_hover = "#1967d2" if btn_color == "#1a73e8" else "#a50000"
            
            b = ctk.CTkButton(card, text=btn["text"], fg_color=btn_color, hover_color=btn_hover, 
                             font=("Arial", 12, "bold"), height=40, command=btn["command"])
            b.pack(fill="x", padx=20, pady=(10, 2))
            
            ctk.CTkLabel(card, text=btn["desc"], font=("Arial", 10), text_color="#777777").pack(anchor="w", padx=25, pady=(0, 10))

        return card

    def export_full_pdf(self):
        try:
            export_full_pdf()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def export_filtered_pdf(self):
        try:
            export_filtered_pdf()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def export_excel(self):
        try:
            export_to_excel()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def backup_db(self):
        try:
            output_path = filedialog.asksaveasfilename(defaultextension=".sql", filetypes=[("SQL files", "*.sql")])
            if output_path:
                backup_database(output_path)
                messagebox.showinfo("Success", "Database backup completed successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def restore_db(self):
        try:
            input_path = filedialog.askopenfilename(filetypes=[("SQL files", "*.sql")])
            if input_path:
                restore_database(input_path)
                messagebox.showinfo("Success", "Database restored successfully.")
                self.setup_ui()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def refresh(self):
        self.setup_ui()