import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
from datetime import datetime
from utils.pdf_export import export_full_pdf, export_filtered_pdf
from utils.excel_export import export_to_excel
from db import get_abuse_types

class ReportsFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.setup_ui()

    def setup_ui(self):
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()

        # Main container
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Filter Section for Export
        filter_card = ctk.CTkFrame(self.scroll_container, fg_color=["white", "#242424"], corner_radius=12, border_width=1, border_color=["#e2e8f0", "#333333"])
        filter_card.pack(fill="x", padx=10, pady=(0, 20))
        
        ctk.CTkLabel(filter_card, text="🔍 Export Filters", font=("Arial", 16, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(anchor="w", padx=20, pady=(15, 5))
        ctk.CTkLabel(filter_card, text="Apply filters below before clicking 'Export Filtered' or 'Export to Excel'.", font=("Arial", 12), text_color=["#64748b", "#94a3b8"]).pack(anchor="w", padx=20, pady=(0, 15))
        
        filter_grid = ctk.CTkFrame(filter_card, fg_color="transparent")
        filter_grid.pack(fill="x", padx=20, pady=(0, 20))
        
        # Search
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(filter_grid, placeholder_text="Search name/VAWC No...", textvariable=self.search_var, height=38, width=250)
        self.search_entry.pack(side="left", padx=(0, 10))
        
        # Status
        self.status_var = ctk.StringVar(value="Status")
        self.status_combo = ctk.CTkComboBox(filter_grid, values=["Status", "Ongoing", "Settled", "Referred", "Archived", "Issued BPO"], variable=self.status_var, height=38)
        self.status_combo.pack(side="left", padx=5)
        
        # Abuse Type
        self.abuse_var = ctk.StringVar(value="Type of Abuse")
        try:
            abuse_values = ["Type of Abuse"] + get_abuse_types()
        except Exception:
            abuse_values = ["Type of Abuse"]
        self.abuse_combo = ctk.CTkComboBox(filter_grid, values=abuse_values, variable=self.abuse_var, height=38)
        self.abuse_combo.pack(side="left", padx=5)
        
        # Year
        self.year_var = ctk.StringVar(value="Year")
        years = ["Year"] + [str(y) for y in range(datetime.now().year, 2019, -1)]
        self.year_combo = ctk.CTkComboBox(filter_grid, values=years, variable=self.year_var, height=38, width=100)
        self.year_combo.pack(side="left", padx=5)

        # Export Grid (3 cards)
        export_grid = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        export_grid.pack(fill="x", pady=10)
        export_grid.grid_columnconfigure((0, 1, 2), weight=1)

        # 1. PDF Full List
        self.create_export_card(
            export_grid, 0, 0,
            "📄", "Export Full List", "PDF",
            "Generate a complete PDF report of all case records in the system.",
            self.export_full_pdf
        )

        # 2. PDF Filtered List
        self.create_export_card(
            export_grid, 0, 1,
            "📄", "Export Filtered", "PDF",
            "Generate a PDF report based on your current search and filters.",
            self.export_filtered_pdf
        )

        # 3. Excel Export
        self.create_export_card(
            export_grid, 0, 2,
            "📊", "Export to Excel", "XLSX",
            "Export raw data to a spreadsheet based on filters.",
            self.export_excel
        )

    def create_export_card(self, parent, row, col, icon, title, format_tag, desc, command):
        card = ctk.CTkFrame(parent, fg_color=["white", "#242424"], corner_radius=12, border_width=1, border_color=["#e2e8f0", "#333333"])
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(card, text=icon, font=("Arial", 40)).pack(pady=(25, 10))
        
        title_frame = ctk.CTkFrame(card, fg_color="transparent")
        title_frame.pack()
        ctk.CTkLabel(title_frame, text=title, font=("Arial", 14, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(side="left")
        
        tag_color = "#2563eb" if format_tag == "PDF" else "#16a34a"
        tag_bg = ["#eff6ff", "#1e3a5f"] if format_tag == "PDF" else ["#f0fdf4", "#064e3b"]
        tag = ctk.CTkLabel(card, text=format_tag, font=("Arial", 10, "bold"), text_color=tag_color, fg_color=tag_bg, corner_radius=4, padx=8)
        tag.pack(pady=5)
        
        ctk.CTkLabel(card, text=desc, font=("Arial", 11), text_color=["#64748b", "#94a3b8"], wraplength=200).pack(pady=(10, 20), padx=20)
        
        ctk.CTkButton(card, text="Generate Export", fg_color="#1a2a4a", hover_color="#0f1e35", height=38, corner_radius=8, command=command).pack(fill="x", padx=20, pady=(0, 20))
        
        # Last Export Info
        ctk.CTkLabel(card, text="Last exported: Never", font=("Arial", 10), text_color=["#94a3b8", "#64748b"]).pack(pady=(0, 15))

    def create_report_card(self, parent, title, subtitle, buttons, row=0, col=0, is_full_width=False):
        card = ctk.CTkFrame(parent, fg_color=["white", "#242424"], corner_radius=15)
        if is_full_width:
            card.pack(fill="x", pady=10)
        else:
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(card, text=title, font=("Arial", 16, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(card, text=subtitle, font=("Arial", 11), text_color=["#666666", "#999999"]).pack(anchor="w", padx=20, pady=(0, 15))

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
            export_filtered_pdf(
                search_term=self.search_var.get(),
                filter_status=self.status_var.get(),
                filter_abuse=self.abuse_var.get(),
                filter_year=self.year_var.get()
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def export_excel(self):
        try:
            export_to_excel(
                search_term=self.search_var.get(),
                filter_status=self.status_var.get(),
                filter_abuse=self.abuse_var.get(),
                filter_year=self.year_var.get()
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def refresh(self):
        self.setup_ui()