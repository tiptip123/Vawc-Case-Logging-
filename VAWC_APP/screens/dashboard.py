import customtkinter as ctk
from tkinter import ttk
from db import get_connection
from datetime import datetime
from .screen_header import ScreenHeader

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#f5f5f5")
        self.load_data()

        ScreenHeader(self, "Dashboard").pack(fill="x")

        # Welcome Section
        welcome_frame = ctk.CTkFrame(self, fg_color="#f5f5f5")
        welcome_frame.pack(fill="x", padx=20, pady=(10, 5))

        welcome_card = ctk.CTkFrame(welcome_frame, fg_color="white", corner_radius=10)
        welcome_card.pack(fill="x", pady=5)

        ctk.CTkLabel(
            welcome_card,
            text="🏠 VAWC Case Management Dashboard - Barangay Tankulan, Manolo Fortich, Bukidnon",
            font=("Arial", 18, "bold"),
            text_color="#1a2a4a",
            wraplength=900,
            justify="center"
        ).pack(pady=(15, 5))
        ctk.CTkLabel(welcome_card, text=f"Welcome back! Today is {datetime.now().strftime('%B %d, %Y')}", font=("Arial", 12), text_color="#666666").pack(pady=(0, 15))

        # Primary Statistics Cards
        stats_frame = ctk.CTkFrame(self, fg_color="#f5f5f5")
        stats_frame.pack(fill="x", padx=20, pady=(5, 5))
        stats_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Total Records Card
        self.card_total = ctk.CTkFrame(stats_frame, fg_color="white", corner_radius=10)
        self.card_total.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(self.card_total, text="📊 Total Cases", font=("Arial", 16, "bold"), text_color="#1a2a4a").pack(pady=(15, 5))
        ctk.CTkLabel(self.card_total, text=str(self.total_records), font=("Arial", 28, "bold"), text_color="#8b0000").pack(pady=(0, 5))
        ctk.CTkLabel(self.card_total, text="All time records", font=("Arial", 10), text_color="#666666").pack(pady=(0, 15))

        # This Month Card
        self.card_month = ctk.CTkFrame(stats_frame, fg_color="white", corner_radius=10)
        self.card_month.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(self.card_month, text="📅 This Month", font=("Arial", 16, "bold"), text_color="#1a2a4a").pack(pady=(15, 5))
        ctk.CTkLabel(self.card_month, text=str(self.month_cases), font=("Arial", 28, "bold"), text_color="#1a73e8").pack(pady=(0, 5))
        month_name = datetime.now().strftime("%B")
        ctk.CTkLabel(self.card_month, text=f"Cases in {month_name}", font=("Arial", 10), text_color="#666666").pack(pady=(0, 15))

        # This Year Card
        self.card_year = ctk.CTkFrame(stats_frame, fg_color="white", corner_radius=10)
        self.card_year.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(self.card_year, text="📈 This Year", font=("Arial", 16, "bold"), text_color="#1a2a4a").pack(pady=(15, 5))
        ctk.CTkLabel(self.card_year, text=str(self.year_cases), font=("Arial", 28, "bold"), text_color="#28a745").pack(pady=(0, 5))
        year = datetime.now().year
        ctk.CTkLabel(self.card_year, text=f"Cases in {year}", font=("Arial", 10), text_color="#666666").pack(pady=(0, 15))

        # Case Status Overview
        status_overview_frame = ctk.CTkFrame(self, fg_color="#f5f5f5")
        status_overview_frame.pack(fill="x", padx=20, pady=(5, 5))
        status_overview_frame.grid_columnconfigure(0, weight=1)

        # Case Status Summary Card (now full width)
        status_card = ctk.CTkFrame(status_overview_frame, fg_color="white", corner_radius=10)
        status_card.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        ctk.CTkLabel(status_card, text="📋 Case Status Overview", font=("Arial", 16, "bold"), text_color="#1a2a4a").pack(pady=(15, 10))

        status_container = ctk.CTkFrame(status_card, fg_color="white")
        status_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        if self.status_counts:
            for status, count in self.status_counts.items():
                status_frame = ctk.CTkFrame(status_container, fg_color="#f8f9fa", corner_radius=6)
                status_frame.pack(fill="x", pady=2)

                # Status indicator colors
                color_map = {
                    "Ongoing": "#ffc107",
                    "Resolved": "#28a745",
                    "Referred": "#1a73e8"
                }
                indicator_color = color_map.get(status, "#6c757d")

                # Status indicator
                indicator = ctk.CTkFrame(status_frame, fg_color=indicator_color, width=12, height=12, corner_radius=6)
                indicator.pack(side="left", padx=(10, 8), pady=8)
                indicator.pack_propagate(False)

                # Status text
                ctk.CTkLabel(status_frame, text=f"{status}: {count}", font=("Arial", 12, "bold"), text_color="#1a2a4a").pack(side="left", pady=8)
        else:
            ctk.CTkLabel(status_container, text="No case data available", font=("Arial", 12), text_color="#666666").pack(pady=20)

        # Recent Entries Section
        recent_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        recent_frame.pack(fill="both", expand=True, padx=20, pady=(5, 10))

        ctk.CTkLabel(recent_frame, text="🕒 Recent Case Entries", font=("Arial", 16, "bold"), text_color="#1a2a4a").pack(anchor="w", padx=20, pady=(20, 10))

        # Enhanced table styling
        table_container = ctk.CTkFrame(recent_frame, fg_color="#f8f9fa", corner_radius=8)
        table_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        style = ttk.Style()
        style.configure("Treeview.Heading", background="#1a2a4a", foreground="white", font=("Arial", 11, "bold"), padding=(10, 5))
        style.configure("Treeview", rowheight=30, font=("Arial", 10), background="#ffffff", foreground="#000000")
        style.map("Treeview", background=[("selected", "#8b0000")], foreground=[("selected", "#ffffff")])

        self.tree = ttk.Treeview(table_container, columns=("VAWC No", "Date", "Client Name", "Type of Abuse", "Status", "Respondent"),
                               show="headings", selectmode="browse")

        # Configure columns with better widths and alignment
        column_config = {
            "VAWC No": (120, "center"),
            "Date": (100, "center"),
            "Client Name": (150, "w"),
            "Type of Abuse": (120, "w"),
            "Status": (100, "center"),
            "Respondent": (150, "w")
        }

        for col, (width, anchor) in column_config.items():
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor=anchor)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 5), pady=10)
        scrollbar.pack(side="right", fill="y", padx=(5, 10), pady=10)

        # Populate table with enhanced data
        for index, row in enumerate(self.recent_entries):
            tag = "evenrow" if index % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=row, tags=(tag,))

        self.tree.tag_configure("evenrow", background="#ffffff")
        self.tree.tag_configure("oddrow", background="#f8f9fa")

        # Abuse Types Breakdown Section
        breakdown_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        breakdown_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(breakdown_frame, text="🎯 Abuse Types Distribution", font=("Arial", 16, "bold"), text_color="#1a2a4a").pack(anchor="w", padx=20, pady=(20, 10))

        breakdown_container = ctk.CTkFrame(breakdown_frame, fg_color="#f8f9fa", corner_radius=8)
        breakdown_container.pack(fill="x", padx=20, pady=(0, 20))

        if self.abuse_counts:
            # Sort by count descending
            sorted_abuse = sorted(self.abuse_counts.items(), key=lambda x: x[1], reverse=True)

            for abuse_type, count in sorted_abuse:
                abuse_frame = ctk.CTkFrame(breakdown_container, fg_color="white", corner_radius=6)
                abuse_frame.pack(fill="x", padx=10, pady=3)

                # Progress bar visualization
                progress_frame = ctk.CTkFrame(abuse_frame, fg_color="white")
                progress_frame.pack(fill="x", padx=15, pady=8)

                # Calculate percentage
                total = sum(self.abuse_counts.values())
                percentage = (count / total) * 100 if total > 0 else 0

                # Type label
                ctk.CTkLabel(progress_frame, text=f"{abuse_type}", font=("Arial", 12, "bold"), text_color="#1a2a4a").pack(side="left")

                # Count and percentage
                ctk.CTkLabel(progress_frame, text=f"{count} ({percentage:.1f}%)", font=("Arial", 11), text_color="#666666").pack(side="right")

                # Simple progress bar using colored frame
                progress_bar = ctk.CTkFrame(progress_frame, fg_color="#8b0000", height=6, corner_radius=3)
                progress_bar.pack(fill="x", pady=(5, 0))
                progress_bar.pack_propagate(False)

                # Set width based on percentage (max 200px for demo)
                bar_width = min(200, int(percentage * 2))
                progress_bar.configure(width=bar_width)
        else:
            ctk.CTkLabel(breakdown_container, text="No abuse type data available", font=("Arial", 12), text_color="#666666").pack(pady=20)

    def get_case_status(self, vawc_no):
        """Get case status for a specific VAWC number"""
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT case_status FROM vawc_logs WHERE vawc_no = ?", (vawc_no,))
            result = cursor.fetchone()
            cursor.close()
            connection.close()
            return result[0] if result else "Unknown"
        except Exception:
            return "Unknown"

    def load_data(self):
        try:
            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute("SELECT COUNT(*) FROM vawc_logs")
            self.total_records = cursor.fetchone()[0]

            now = datetime.now()
            cursor.execute("SELECT COUNT(*) FROM vawc_logs WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?", (str(now.year), f"{now.month:02d}"))
            self.month_cases = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM vawc_logs WHERE strftime('%Y', date) = ?", (str(now.year),))
            self.year_cases = cursor.fetchone()[0]

            cursor.execute("SELECT vawc_no, date, client_name, type_of_abuse, case_status, name_of_respondent FROM vawc_logs ORDER BY created_at DESC LIMIT 10")
            self.recent_entries = cursor.fetchall()

            cursor.execute("SELECT type_of_abuse, COUNT(*) FROM vawc_logs GROUP BY type_of_abuse")
            self.abuse_counts = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("SELECT case_status, COUNT(*) FROM vawc_logs GROUP BY case_status")
            self.status_counts = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.close()
            connection.close()
        except Exception:
            self.total_records = 0
            self.month_cases = 0
            self.year_cases = 0
            self.recent_entries = []
            self.abuse_counts = {}