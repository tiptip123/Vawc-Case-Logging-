import customtkinter as ctk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from db import get_connection
from datetime import datetime, timedelta
from .screen_header import ScreenHeader

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.setup_ui()

    def setup_ui(self):
        # Clear existing widgets and close matplotlib figures
        plt.close('all')
        for widget in self.winfo_children():
            widget.destroy()

        self.load_data()

        # Responsive scrollable container
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True)

        # 1. PRIMARY STATS (4 cards)
        stats_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=(20, 10))
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        total_cases = sum(self.status_counts.values())
        self.create_stat_card(stats_frame, 0, 0, "Total Records", str(total_cases), "#1a2a4a", "📋")
        
        month_cases = self.monthly_counts.get(datetime.now().strftime('%Y-%m'), 0)
        self.create_stat_card(stats_frame, 0, 1, "This Month", str(month_cases), "#2563eb", "📅")
        
        year_prefix = datetime.now().strftime('%Y-')
        year_cases = sum(count for month, count in self.monthly_counts.items() if month.startswith(year_prefix))
        self.create_stat_card(stats_frame, 0, 2, "This Year", str(year_cases), "#16a34a", "📈")
        
        sorted_abuse = sorted(self.abuse_counts.items(), key=lambda x: x[1], reverse=True)
        top_abuse = sorted_abuse[0][0] if sorted_abuse else "None"
        self.create_stat_card(stats_frame, 0, 3, "Common Abuse", top_abuse, "#8b0000", "⚖️", is_small_text=True)

        # 2. ADVANCED ANALYTICS (3 cards)
        analytics_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        analytics_frame.pack(fill="x", padx=20, pady=10)
        analytics_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Abuse Card
        abuse_card = self.create_list_card(analytics_frame, 0, 0, "🏆 Top 3 Abuse Types", ["#1a2a4a", "#f8fafc"])
        for i, (abuse, count) in enumerate(sorted_abuse[:3]):
            self.create_list_row(abuse_card, f"#{i+1} {abuse}", str(count), "#8b0000")

        # Hotspots Card
        hotspot_card = self.create_list_card(analytics_frame, 0, 1, "📍 Barangay Hotspots", ["#1a2a4a", "#f8fafc"])
        sorted_locations = sorted(self.location_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        if sorted_locations:
            for i, (loc, count) in enumerate(sorted_locations):
                short_loc = (loc[:25] + '...') if len(loc) > 25 else loc
                self.create_list_row(hotspot_card, f"#{i+1} {short_loc}", str(count), "#2563eb")
        else:
            ctk.CTkLabel(hotspot_card, text="No location data", font=("Arial", 11, "italic")).pack(pady=10)

        # Risk Card
        risk_card = self.create_list_card(analytics_frame, 0, 2, "🚩 High Risk Respondents", "#dc2626")
        if self.high_risk_respondents:
            for i, (name, count) in enumerate(self.high_risk_respondents[:3]):
                short_name = (name[:20] + '...') if len(name) > 20 else name
                self.create_list_row(risk_card, f"⚠️ {short_name}", f"{count} cases", "#dc3545")
        else:
            ctk.CTkLabel(risk_card, text="No high risk found", font=("Arial", 11, "italic")).pack(pady=10)

        # 3. CHARTS (2 main charts)
        charts_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        charts_frame.pack(fill="x", padx=20, pady=10)
        charts_frame.grid_columnconfigure((0, 1), weight=1)

        # Monthly Trend
        trend_card = ctk.CTkFrame(charts_frame, fg_color=["white", "#242424"], corner_radius=12, border_width=1, border_color=["#e2e8f0", "#333333"])
        trend_card.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        ctk.CTkLabel(trend_card, text="Monthly Case Trends", font=("Arial", 14, "bold"), text_color=["#0f172a", "#f8fafc"]).pack(pady=15, padx=20, anchor="w")
        self.plot_trend(trend_card)

        # Status Distribution
        dist_card = ctk.CTkFrame(charts_frame, fg_color=["white", "#242424"], corner_radius=12, border_width=1, border_color=["#e2e8f0", "#333333"])
        dist_card.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        ctk.CTkLabel(dist_card, text="Case Status Distribution", font=("Arial", 14, "bold"), text_color=["#0f172a", "#f8fafc"]).pack(pady=15, padx=20, anchor="w")
        self.plot_status_bar(dist_card)

        # 4. REMINDERS (If any)
        if self.reminders:
            reminder_card = ctk.CTkFrame(self.scroll_container, fg_color=["#fff3cd", "#451a03"], border_width=1, border_color=["#ffeeba", "#713f12"], corner_radius=10)
            reminder_card.pack(fill="x", padx=20, pady=10)
            ctk.CTkLabel(reminder_card, text="⚠️ Follow-up Reminders (Untouched for 30+ Days)", font=("Arial", 13, "bold"), text_color=["#856404", "#fef9c3"]).pack(pady=(10, 5), padx=20, anchor="w")
            
            for vawc_no, client, updated in self.reminders[:5]:
                row = ctk.CTkFrame(reminder_card, fg_color="transparent")
                row.pack(fill="x", padx=20, pady=2)
                ctk.CTkLabel(row, text=f"{vawc_no} - {client}", font=("Arial", 11), text_color=["#856404", "#fef9c3"]).pack(side="left")
                ctk.CTkLabel(row, text=f"Last update: {updated}", font=("Arial", 10, "italic"), text_color=["#856404", "#fef9c3"]).pack(side="right")

    def create_stat_card(self, parent, row, col, label, value, color, icon, is_small_text=False):
        card = ctk.CTkFrame(parent, fg_color=["#ffffff", "#1f2937"], corner_radius=16, border_width=1, border_color=["#e2e8f0", "#334155"])
        card.grid(row=row, column=col, padx=10, pady=5, sticky="nsew")
        
        accent = ctk.CTkFrame(card, width=6, fg_color=color, corner_radius=3)
        accent.place(relx=0, rely=0.16, relheight=0.68)
        
        ctk.CTkLabel(card, text=icon, font=("Arial", 22), text_color=["#0f172a", "#f8fafc"]).place(relx=0.9, rely=0.18, anchor="center")
        ctk.CTkLabel(card, text=label, font=("Arial", 12), text_color=["#64748b", "#cbd5e1"]).pack(pady=(24, 0), padx=20, anchor="w")
        
        val_font = ("Arial", 18, "bold") if is_small_text else ("Arial", 28, "bold")
        ctk.CTkLabel(card, text=value, font=val_font, text_color=["#0f172a", "#f8fafc"]).pack(pady=(8, 20), padx=20, anchor="w")

    def create_list_card(self, parent, row, col, title, title_color):
        card = ctk.CTkFrame(parent, fg_color=["#ffffff", "#1f2937"], corner_radius=16, border_width=1, border_color=["#e2e8f0", "#334155"])
        card.grid(row=row, column=col, padx=10, pady=5, sticky="nsew")
        ctk.CTkLabel(card, text=title, font=("Arial", 14, "bold"), text_color=title_color).pack(pady=(18, 10), padx=20, anchor="w")
        return card

    def create_list_row(self, parent, text, val, val_color):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=4)
        ctk.CTkLabel(row, text=text, font=("Arial", 11), text_color=["#333333", "#cbd5e1"]).pack(side="left")
        ctk.CTkLabel(row, text=val, font=("Arial", 11, "bold"), text_color=val_color).pack(side="right")

    def plot_trend(self, parent):
        if not self.monthly_counts: return
        
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_color = "#242424" if is_dark else "white"
        text_color = "#f8fafc" if is_dark else "#0f172a"
        grid_color = "#333333" if is_dark else "#e2e8f0"

        fig, ax = plt.subplots(figsize=(5, 3), dpi=100, facecolor=bg_color)
        months = sorted(self.monthly_counts.keys())[-6:] # Last 6 months
        counts = [self.monthly_counts[m] for m in months]
        
        ax.plot(months, counts, marker='o', color='#2563eb', linewidth=2)
        ax.fill_between(months, counts, alpha=0.1, color='#2563eb')
        
        ax.set_facecolor(bg_color)
        for spine in ax.spines.values(): spine.set_visible(False)
        ax.tick_params(axis='both', colors=text_color, labelsize=8)
        ax.grid(True, axis='y', linestyle='--', alpha=0.3, color=grid_color)
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def plot_status_bar(self, parent):
        if not self.status_counts: return
        
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_color = "#242424" if is_dark else "white"
        text_color = "#f8fafc" if is_dark else "#0f172a"

        fig, ax = plt.subplots(figsize=(5, 3), dpi=100, facecolor=bg_color)
        labels = list(self.status_counts.keys())
        values = list(self.status_counts.values())
        colors = ['#d97706', '#16a34a', '#2563eb', '#7c3aed'] # Yellow, Green, Blue, Purple
        
        ax.bar(labels, values, color=colors[:len(labels)], width=0.6)
        ax.set_facecolor(bg_color)
        for spine in ax.spines.values(): spine.set_visible(False)
        ax.tick_params(axis='both', colors=text_color, labelsize=8)
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def plot_monthly_bar(self, parent):
        year_prefix = datetime.now().strftime('%Y-')
        data = {f"{i:02d}": 0 for i in range(1, 13)}
        for month, count in self.monthly_counts.items():
            if month.startswith(year_prefix):
                data[month.split('-')[1]] = count
        
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        values = [data[f"{i+1:02d}"] for i in range(12)]

        if sum(values) == 0:
            ctk.CTkLabel(parent, text="No case data available for the current year", font=("Arial", 12, "italic"), text_color=["#64748b", "#94a3b8"]).pack(pady=40)
            return

        fig, ax = plt.subplots(figsize=(5, 3), dpi=100)
        ax.bar(months, values, color="#2563eb", width=0.6)
        ax.set_facecolor('white')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#e2e8f0')
        ax.spines['bottom'].set_color('#e2e8f0')
        ax.tick_params(axis='both', colors='#64748b', labelsize=8)
        ax.yaxis.grid(True, linestyle='--', alpha=0.3, color='#e2e8f0')
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def plot_abuse_donut(self, parent):
        if not self.abuse_counts:
            ctk.CTkLabel(parent, text="No data available", text_color="#64748b").pack(pady=40)
            return

        labels = list(self.abuse_counts.keys())[:5]
        values = list(self.abuse_counts.values())[:5]
        colors = ["#1a2a4a", "#8b0000", "#2563eb", "#16a34a", "#d97706"]

        fig, ax = plt.subplots(figsize=(5, 3), dpi=100)
        ax.pie(values, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90, 
               textprops={'fontsize': 8, 'color': '#64748b'}, pctdistance=0.85)
        
        # Donut hole
        centre_circle = plt.Circle((0,0), 0.70, fc='white')
        fig.gca().add_artist(centre_circle)
        
        ax.axis('equal')
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def setup_recent_table(self, parent):
        table_frame = ctk.CTkFrame(parent, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Headers
        headers = ["VAWC No", "Client Name", "Type", "Date", "Status"]
        header_row = ctk.CTkFrame(table_frame, fg_color="#f1f5f9", height=32, corner_radius=4)
        header_row.pack(fill="x", pady=(0, 4))
        header_row.pack_propagate(False)
        
        for i, h in enumerate(headers):
            ctk.CTkLabel(header_row, text=h, font=("Arial", 11, "bold"), text_color="#0f172a").place(relx=i/5 + 0.02, rely=0.5, anchor="w")

        # Fetch recent 10 records
        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT vawc_no, client_name, type_of_abuse, date, case_status FROM vawc_logs WHERE is_deleted = 0 ORDER BY created_at DESC LIMIT 10")
            recent = cursor.fetchall()

            for i, row in enumerate(recent):
                bg = "white" if i % 2 == 0 else "#f8fafc"
                row_frame = ctk.CTkFrame(table_frame, fg_color=bg, height=36, corner_radius=0)
                row_frame.pack(fill="x")
                row_frame.pack_propagate(False)
                
                for j, val in enumerate(row):
                    # Shorten type if needed
                    display_val = (str(val)[:15] + '...') if j == 2 and val and len(str(val)) > 15 else str(val) if val else ""
                    ctk.CTkLabel(row_frame, text=display_val, font=("Arial", 11), text_color="#334155").place(relx=j/5 + 0.02, rely=0.5, anchor="w")
        except Exception:
            pass
        finally:
            if connection:
                connection.close()

    def setup_status_pills(self, parent):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        status_colors = {
            "Settled": "#16a34a",
            "Issued BPO": "#2563eb",
            "Ongoing": "#d97706",
            "Archived": "#64748b",
            "Referred": "#7c3aed"
        }

        for status, count in self.status_counts.items():
            pill = ctk.CTkFrame(container, fg_color="white", border_width=1, border_color="#e2e8f0", height=40, corner_radius=20)
            pill.pack(fill="x", pady=5)
            pill.pack_propagate(False)
            
            dot = ctk.CTkFrame(pill, width=10, height=10, corner_radius=5, fg_color=status_colors.get(status, "#64748b"))
            dot.pack(side="left", padx=(15, 10))
            
            ctk.CTkLabel(pill, text=status, font=("Arial", 12), text_color="#0f172a").pack(side="left")
            ctk.CTkLabel(pill, text=str(count), font=("Arial", 12, "bold"), text_color="#0f172a").pack(side="right", padx=15)

        # Top 3 Abuse Types & Hotspots & High Risk Respondents (Advanced Analytics)
        analytics_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        analytics_frame.pack(fill="x", padx=20, pady=(10, 5))
        analytics_frame.grid_columnconfigure((0, 1, 2), weight=1)

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
        hotspot_card.grid(row=0, column=1, padx=5, sticky="nsew")
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

        # High Risk Respondents Card
        risk_card = ctk.CTkFrame(analytics_frame, fg_color="white", corner_radius=10)
        risk_card.grid(row=0, column=2, padx=(10, 0), sticky="nsew")
        ctk.CTkLabel(risk_card, text="🚩 High Risk Respondents", font=("Arial", 14, "bold"), text_color="#8b0000").pack(pady=(15, 10))

        if self.high_risk_respondents:
            for i, (name, count) in enumerate(self.high_risk_respondents[:3]):
                row = ctk.CTkFrame(risk_card, fg_color="transparent")
                row.pack(fill="x", padx=20, pady=2)
                short_name = (name[:20] + '...') if len(name) > 20 else name
                ctk.CTkLabel(row, text=f"⚠️ {short_name}", font=("Arial", 11), text_color="#333333").pack(side="left")
                ctk.CTkLabel(row, text=f"{count} cases", font=("Arial", 11, "bold"), text_color="#dc3545").pack(side="right")
        else:
            ctk.CTkLabel(risk_card, text="No high risk respondents found", font=("Arial", 10, "italic"), text_color="#64748b").pack(pady=10)

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
        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()

            # Handle multi-abuse counting separately
            cursor.execute("SELECT type_of_abuse FROM vawc_logs WHERE is_deleted = 0")
            self.abuse_counts = {}
            for row in cursor.fetchall():
                if row[0]:
                    abuses = [a.strip() for a in row[0].split(',')]
                    for abuse in abuses:
                        if abuse:
                            self.abuse_counts[abuse] = self.abuse_counts.get(abuse, 0) + 1

            cursor.execute("SELECT case_status, COUNT(*) FROM vawc_logs WHERE is_deleted = 0 GROUP BY case_status")
            self.status_counts = {row[0]: row[1] for row in cursor.fetchall() if row[0]}

            cursor.execute("SELECT strftime('%Y-%m', date), COUNT(*) FROM vawc_logs WHERE is_deleted = 0 GROUP BY strftime('%Y-%m', date)")
            self.monthly_counts = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("SELECT address, COUNT(*) FROM vawc_logs WHERE is_deleted = 0 GROUP BY address")
            self.location_counts = {row[0]: row[1] for row in cursor.fetchall() if row[0]}

            # Age Demographics
            cursor.execute("SELECT age FROM vawc_logs WHERE is_deleted = 0")
            self.age_groups = {'Children': 0, 'Adults': 0, 'Seniors': 0}
            for row in cursor.fetchall():
                if row[0]:
                    try:
                        age = int(row[0])
                        if age < 18: self.age_groups['Children'] += 1
                        elif age < 60: self.age_groups['Adults'] += 1
                        else: self.age_groups['Seniors'] += 1
                    except (ValueError, TypeError):
                        pass

            # Follow-up Reminders (Ongoing cases not touched for 30 days)
            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            cursor.execute("""
                SELECT vawc_no, client_name, updated_at 
                FROM vawc_logs 
                WHERE case_status = 'Ongoing' AND updated_at < ? AND is_deleted = 0
            """, (thirty_days_ago,))
            self.reminders = cursor.fetchall()

            # High Risk Respondents (3 or more cases)
            cursor.execute("""
                SELECT name_of_respondent, COUNT(*) as case_count 
                FROM vawc_logs 
                WHERE is_deleted = 0 AND name_of_respondent IS NOT NULL AND name_of_respondent != ''
                GROUP BY name_of_respondent 
                HAVING case_count >= 3
                ORDER BY case_count DESC
            """)
            self.high_risk_respondents = cursor.fetchall()

        except Exception:
            self.abuse_counts = {}
            self.status_counts = {}
            self.monthly_counts = {}
            self.location_counts = {}
            self.age_groups = {}
            self.reminders = []
            self.high_risk_respondents = []
        finally:
            if connection:
                connection.close()