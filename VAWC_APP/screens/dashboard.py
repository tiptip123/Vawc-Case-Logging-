import customtkinter as ctk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from db import get_connection
from datetime import datetime, timedelta
from .screen_header import ScreenHeader

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#f5f5f5")
        self.setup_ui()

    def setup_ui(self):
        # Clear existing widgets and close matplotlib figures to prevent memory leaks
        plt.close('all')
        for widget in self.winfo_children():
            widget.destroy()

        self.load_data()

        # Use a scrollable frame for the dashboard to be responsive
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="#f5f5f5")
        self.scroll_container.pack(fill="both", expand=True)

        # Welcome Section
        welcome_card = ctk.CTkFrame(self.scroll_container, fg_color="white", corner_radius=10)
        welcome_card.pack(fill="x", padx=20, pady=(15, 10))

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
        stats_frame = ctk.CTkFrame(self.scroll_container, fg_color="#f5f5f5")
        stats_frame.pack(fill="x", padx=15, pady=5)
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Total Records Card
        total_cases = sum(self.status_counts.values())
        total_card = ctk.CTkFrame(stats_frame, fg_color="white", corner_radius=10)
        total_card.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(total_card, text="📊 Total Cases", font=("Arial", 14, "bold"), text_color="#1a2a4a").pack(pady=(15, 5))
        ctk.CTkLabel(total_card, text=str(total_cases), font=("Arial", 26, "bold"), text_color="#8b0000").pack(pady=(0, 5))
        ctk.CTkLabel(total_card, text="All time records", font=("Arial", 10), text_color="#666666").pack(pady=(0, 15))

        # This Month Card
        month_cases = self.monthly_counts.get(datetime.now().strftime('%Y-%m'), 0)
        month_card = ctk.CTkFrame(stats_frame, fg_color="white", corner_radius=10)
        month_card.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(month_card, text="📅 This Month", font=("Arial", 14, "bold"), text_color="#1a2a4a").pack(pady=(15, 5))
        ctk.CTkLabel(month_card, text=str(month_cases), font=("Arial", 26, "bold"), text_color="#1a73e8").pack(pady=(0, 5))
        ctk.CTkLabel(month_card, text=f"Cases in {datetime.now().strftime('%B')}", font=("Arial", 10), text_color="#666666").pack(pady=(0, 15))

        # This Year Card
        year_prefix = datetime.now().strftime('%Y-')
        year_cases = sum(count for month, count in self.monthly_counts.items() if month.startswith(year_prefix))
        year_card = ctk.CTkFrame(stats_frame, fg_color="white", corner_radius=10)
        year_card.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(year_card, text="📈 This Year", font=("Arial", 14, "bold"), text_color="#1a2a4a").pack(pady=(15, 5))
        ctk.CTkLabel(year_card, text=str(year_cases), font=("Arial", 26, "bold"), text_color="#28a745").pack(pady=(0, 5))
        ctk.CTkLabel(year_card, text=f"Cases in {datetime.now().year}", font=("Arial", 10), text_color="#666666").pack(pady=(0, 15))

        # Ongoing Cases Card
        ongoing = self.status_counts.get('Ongoing', 0)
        ongoing_card = ctk.CTkFrame(stats_frame, fg_color="white", corner_radius=10)
        ongoing_card.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(ongoing_card, text="⏳ Ongoing", font=("Arial", 14, "bold"), text_color="#1a2a4a").pack(pady=(15, 5))
        ctk.CTkLabel(ongoing_card, text=str(ongoing), font=("Arial", 26, "bold"), text_color="#ffc107").pack(pady=(0, 5))
        ctk.CTkLabel(ongoing_card, text="Pending action", font=("Arial", 10), text_color="#666666").pack(pady=(0, 15))

        # Top 3 Abuse Types & Hotspots (Advanced Analytics)
        analytics_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        analytics_frame.pack(fill="x", padx=20, pady=(10, 5))
        analytics_frame.grid_columnconfigure((0, 1), weight=1)

        # Abuse Card
        abuse_card = ctk.CTkFrame(analytics_frame, fg_color="white", corner_radius=10)
        abuse_card.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        ctk.CTkLabel(abuse_card, text="🏆 Top 3 Abuse Types", font=("Arial", 14, "bold"), text_color="#1a2a4a").pack(pady=(15, 10))
        
        sorted_abuse = sorted(self.abuse_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        for i, (abuse, count) in enumerate(sorted_abuse):
            row = ctk.CTkFrame(abuse_card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=2)
            ctk.CTkLabel(row, text=f"#{i+1} {abuse}", font=("Arial", 11), text_color="#333333").pack(side="left")
            ctk.CTkLabel(row, text=str(count), font=("Arial", 11, "bold"), text_color="#8b0000").pack(side="right")

        # Hotspots Card (Top 3 Locations)
        hotspot_card = ctk.CTkFrame(analytics_frame, fg_color="white", corner_radius=10)
        hotspot_card.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        ctk.CTkLabel(hotspot_card, text="📍 Barangay Hotspots", font=("Arial", 14, "bold"), text_color="#1a2a4a").pack(pady=(15, 10))
        
        sorted_locations = sorted(self.location_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        if sorted_locations:
            for i, (loc, count) in enumerate(sorted_locations):
                row = ctk.CTkFrame(hotspot_card, fg_color="transparent")
                row.pack(fill="x", padx=20, pady=2)
                # Shorten address if too long
                short_loc = (loc[:25] + '...') if len(loc) > 25 else loc
                ctk.CTkLabel(row, text=f"#{i+1} {short_loc}", font=("Arial", 11), text_color="#333333").pack(side="left")
                ctk.CTkLabel(row, text=str(count), font=("Arial", 11, "bold"), text_color="#1a73e8").pack(side="right")
        else:
            ctk.CTkLabel(hotspot_card, text="No address data available", font=("Arial", 10, "italic")).pack(pady=10)

        # Charts Section
        charts_frame = ctk.CTkFrame(self.scroll_container, fg_color="#f5f5f5")
        charts_frame.pack(fill="both", expand=True, padx=15, pady=5)
        charts_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Abuse Types Pie Chart
        pie_card = ctk.CTkFrame(charts_frame, fg_color="white", corner_radius=10)
        pie_card.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
        ctk.CTkLabel(pie_card, text="Type of Abuse Distribution", font=("Arial", 15, "bold"), text_color="#1a2a4a").pack(pady=(12, 8))

        if self.abuse_counts:
            fig1, ax1 = plt.subplots(figsize=(4.5, 4), facecolor='white')
            colors = ['#8b0000', '#1a73e8', '#28a745', '#ffc107', '#dc3545', '#6f42c1', '#20c997']
            ax1.pie(self.abuse_counts.values(), labels=self.abuse_counts.keys(), autopct='%1.1f%%', startangle=90, colors=colors[:len(self.abuse_counts)])
            ax1.axis('equal')
            canvas1 = FigureCanvasTkAgg(fig1, master=pie_card)
            canvas1.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 15))
        else:
            ctk.CTkLabel(pie_card, text="No data available", font=("Arial", 12), text_color="#666666").pack(pady=20)

        # Case Status Bar Chart
        bar_card = ctk.CTkFrame(charts_frame, fg_color="white", corner_radius=10)
        bar_card.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")
        ctk.CTkLabel(bar_card, text="Case Status Summary", font=("Arial", 15, "bold"), text_color="#1a2a4a").pack(pady=(12, 8))

        if self.status_counts:
            fig2, ax2 = plt.subplots(figsize=(4.5, 4), facecolor='white')
            ax2.bar(self.status_counts.keys(), self.status_counts.values(), color=['#ffc107', '#28a745', '#1a73e8', '#dc3545'])
            ax2.set_ylabel('Number of Cases')
            canvas2 = FigureCanvasTkAgg(fig2, master=bar_card)
            canvas2.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 15))
        else:
            ctk.CTkLabel(bar_card, text="No data available", font=("Arial", 12), text_color="#666666").pack(pady=20)

        # Age Demographics Chart
        age_card = ctk.CTkFrame(charts_frame, fg_color="white", corner_radius=10)
        age_card.grid(row=0, column=2, padx=8, pady=8, sticky="nsew")
        ctk.CTkLabel(age_card, text="Victim Age Demographics", font=("Arial", 15, "bold"), text_color="#1a2a4a").pack(pady=(12, 8))

        if self.age_groups:
            fig4, ax4 = plt.subplots(figsize=(4.5, 4), facecolor='white')
            labels = ['Children\n(0-17)', 'Adults\n(18-59)', 'Seniors\n(60+)']
            counts = [self.age_groups.get('Children', 0), self.age_groups.get('Adults', 0), self.age_groups.get('Seniors', 0)]
            colors = ['#dc3545', '#1a73e8', '#28a745']
            ax4.bar(labels, counts, color=colors)
            ax4.set_ylabel('Cases')
            canvas4 = FigureCanvasTkAgg(fig4, master=age_card)
            canvas4.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 15))
        else:
            ctk.CTkLabel(age_card, text="No age data available", font=("Arial", 12), text_color="#666666").pack(pady=20)

        # Trend Chart
        trend_card = ctk.CTkFrame(self.scroll_container, fg_color="white", corner_radius=10)
        trend_card.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(trend_card, text="Monthly Case Trends", font=("Arial", 15, "bold"), text_color="#1a2a4a").pack(pady=(12, 8))

        # Follow-up Reminders (Bottom)
        if self.reminders:
            reminder_card = ctk.CTkFrame(self.scroll_container, fg_color="#fff3cd", border_width=1, border_color="#ffeeba", corner_radius=10)
            reminder_card.pack(fill="x", padx=20, pady=10)
            ctk.CTkLabel(reminder_card, text="⚠️ Follow-up Reminders (Untouched for 30+ Days)", font=("Arial", 14, "bold"), text_color="#856404").pack(pady=(10, 5))
            
            for vawc_no, client, updated in self.reminders:
                row = ctk.CTkFrame(reminder_card, fg_color="transparent")
                row.pack(fill="x", padx=20, pady=2)
                ctk.CTkLabel(row, text=f"{vawc_no} - {client}", font=("Arial", 11), text_color="#856404").pack(side="left")
                ctk.CTkLabel(row, text=f"Last update: {updated}", font=("Arial", 10, "italic"), text_color="#856404").pack(side="right")

        if self.monthly_counts:
            fig3, ax3 = plt.subplots(figsize=(9, 3.5), facecolor='white')
            months = sorted(self.monthly_counts.keys())
            counts = [self.monthly_counts[m] for m in months]
            ax3.plot(months, counts, marker='o', linewidth=2, color='#8b0000')
            ax3.fill_between(months, counts, alpha=0.3, color='#8b0000')
            ax3.set_ylabel('Cases')
            ax3.tick_params(axis='x', rotation=45)
            canvas3 = FigureCanvasTkAgg(fig3, master=trend_card)
            canvas3.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 15))
        else:
            ctk.CTkLabel(trend_card, text="No trend data available", font=("Arial", 12), text_color="#666666").pack(pady=20)

    def refresh(self):
        self.setup_ui()

    def load_data(self):
        try:
            connection = get_connection()
            cursor = connection.cursor()

            # ... (Existing counts remain the same) ...

            # Handle multi-abuse counting separately
            cursor.execute("SELECT type_of_abuse FROM vawc_logs")
            self.abuse_counts = {}
            for row in cursor.fetchall():
                if row[0]:
                    abuses = [a.strip() for a in row[0].split(',')]
                    for abuse in abuses:
                        if abuse:
                            self.abuse_counts[abuse] = self.abuse_counts.get(abuse, 0) + 1

            cursor.execute("SELECT case_status, COUNT(*) FROM vawc_logs GROUP BY case_status")
            self.status_counts = {row[0]: row[1] for row in cursor.fetchall() if row[0]}

            cursor.execute("SELECT strftime('%Y-%m', date), COUNT(*) FROM vawc_logs GROUP BY strftime('%Y-%m', date)")
            self.monthly_counts = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("SELECT address, COUNT(*) FROM vawc_logs GROUP BY address")
            self.location_counts = {row[0]: row[1] for row in cursor.fetchall() if row[0]}

            # Age Demographics
            cursor.execute("SELECT age FROM vawc_logs")
            self.age_groups = {'Children': 0, 'Adults': 0, 'Seniors': 0}
            for row in cursor.fetchall():
                if row[0]:
                    try:
                        age = int(row[0])
                        if age < 18: self.age_groups['Children'] += 1
                        elif age < 60: self.age_groups['Adults'] += 1
                        else: self.age_groups['Seniors'] += 1
                    except: pass

            # Follow-up Reminders (Ongoing cases not touched for 30 days)
            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            cursor.execute("""
                SELECT vawc_no, client_name, updated_at 
                FROM vawc_logs 
                WHERE case_status = 'Ongoing' AND updated_at < ?
            """, (thirty_days_ago,))
            self.reminders = cursor.fetchall()

            cursor.close()
            connection.close()
        except Exception:
            # ... (Error handling) ...
            self.abuse_counts = {}
            self.status_counts = {}
            self.monthly_counts = {}
            self.location_counts = {}
            self.age_groups = {}
            self.reminders = []