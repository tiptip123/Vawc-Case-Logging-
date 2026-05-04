import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
from utils.pdf_export import export_full_pdf, export_filtered_pdf
from utils.excel_export import export_to_excel
from utils.db_backup import backup_database, restore_database
from .analytics import AnalyticsFrame
from .screen_header import ScreenHeader

class ReportsFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#f5f5f5")

        ScreenHeader(self, "Reports").pack(fill="x")

        # Main container for cards
        cards_frame = ctk.CTkFrame(self, fg_color="#f5f5f5")
        cards_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Configure grid layout for cards (2 columns)
        cards_frame.grid_columnconfigure(0, weight=1)
        cards_frame.grid_columnconfigure(1, weight=1)
        cards_frame.grid_rowconfigure((0, 1, 2), weight=1)

        # Export Reports Card
        export_card = ctk.CTkFrame(cards_frame, fg_color="white", corner_radius=10)
        export_card.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")

        ctk.CTkLabel(export_card, text="📄 Export Reports", font=("Arial", 16, "bold"), text_color="#1a2a4a").pack(pady=(15, 10))

        self.btn_full_pdf = ctk.CTkButton(export_card, text="Full List PDF", fg_color="#8b0000", hover_color="#a50000", command=self.export_full_pdf)
        self.btn_full_pdf.pack(pady=(0, 5), padx=15, fill="x")

        self.btn_filtered_pdf = ctk.CTkButton(export_card, text="Filtered PDF", fg_color="#8b0000", hover_color="#a50000", command=self.export_filtered_pdf)
        self.btn_filtered_pdf.pack(pady=(0, 5), padx=15, fill="x")

        self.btn_excel = ctk.CTkButton(export_card, text="Export to Excel", fg_color="#8b0000", hover_color="#a50000", command=self.export_excel)
        self.btn_excel.pack(pady=(0, 15), padx=15, fill="x")

        # Database Management Card
        db_card = ctk.CTkFrame(cards_frame, fg_color="white", corner_radius=10)
        db_card.grid(row=0, column=1, padx=6, pady=6, sticky="nsew")

        ctk.CTkLabel(db_card, text="💾 Database Management", font=("Arial", 16, "bold"), text_color="#1a2a4a").pack(pady=(15, 10))

        self.btn_backup = ctk.CTkButton(db_card, text="Backup Database", fg_color="#1a73e8", hover_color="#1967d2", command=self.backup_db)
        self.btn_backup.pack(pady=(0, 5), padx=15, fill="x")

        self.btn_restore = ctk.CTkButton(db_card, text="Restore Database", fg_color="#1a73e8", hover_color="#1967d2", command=self.restore_db)
        self.btn_restore.pack(pady=(0, 15), padx=15, fill="x")

        # Analytics Card (spans full width)
        analytics_card = ctk.CTkFrame(cards_frame, fg_color="white", corner_radius=10)
        analytics_card.grid(row=1, column=0, columnspan=2, padx=6, pady=6, sticky="nsew")

        ctk.CTkLabel(analytics_card, text="📊 Analytics & Charts", font=("Arial", 16, "bold"), text_color="#1a2a4a").pack(pady=(15, 10))

        self.btn_analytics = ctk.CTkButton(analytics_card, text="View Analytics Dashboard", fg_color="#8b0000", hover_color="#a50000", command=self.show_analytics)
        self.btn_analytics.pack(pady=(0, 15), padx=15, fill="x")

    def export_full_pdf(self):
        try:
            export_full_pdf()
            messagebox.showinfo("Success", "PDF exported to Desktop.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def export_filtered_pdf(self):
        # For simplicity, export full; in real app, pass filters
        try:
            export_filtered_pdf()
            messagebox.showinfo("Success", "Filtered PDF exported to Desktop.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def export_excel(self):
        try:
            export_to_excel()
            messagebox.showinfo("Success", "Excel exported to Desktop.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def backup_db(self):
        try:
            output_path = filedialog.asksaveasfilename(defaultextension=".sql", filetypes=[("SQL files", "*.sql")])
            if output_path:
                backup_database(output_path)
                messagebox.showinfo("Success", f"Database backed up to {output_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def restore_db(self):
        try:
            input_path = filedialog.askopenfilename(filetypes=[("SQL files", "*.sql")])
            if input_path:
                restore_database(input_path)
                messagebox.showinfo("Success", "Database restored successfully")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_analytics(self):
        # Clear current content and show analytics
        parent_container = self.master
        self.destroy()
        AnalyticsFrame(parent_container).pack(fill="both", expand=True)