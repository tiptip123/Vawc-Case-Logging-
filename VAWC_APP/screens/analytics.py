import customtkinter as ctk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from db import get_connection
from datetime import datetime
from .screen_header import ScreenHeader

class AnalyticsFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        # Clear existing widgets if any
        for widget in self.winfo_children():
            widget.destroy()

        self.load_data()

        ScreenHeader(self, "Analytics & Charts", actions=[
            {"text": "Back to Reports", "command": self.back_to_reports, "fg_color": "#6c757d", "hover_color": "#5a6268", "width": 140}
        ]).pack(fill="x")

        # Statistics Summary Cards
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=15, pady=(8, 4))
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Total Cases Card
        total_cases = sum(self.status_counts.values())
        total_card = ctk.CTkFrame(stats_frame, fg_color=["white", "#242424"], corner_radius=10, border_width=1, border_color=["#e2e8f0", "#333333"])
        total_card.grid(row=0, column=0, padx=4, pady=4, sticky="nsew")
        ctk.CTkLabel(total_card, text="📊 Total Cases", font=("Arial", 13, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(pady=(12, 4))
        ctk.CTkLabel(total_card, text=str(total_cases), font=("Arial", 24, "bold"), text_color="#8b0000").pack(pady=(0, 15))

        # Ongoing Cases Card
        ongoing = self.status_counts.get('Ongoing', 0)
        ongoing_card = ctk.CTkFrame(stats_frame, fg_color=["white", "#242424"], corner_radius=10, border_width=1, border_color=["#e2e8f0", "#333333"])
        ongoing_card.grid(row=0, column=1, padx=4, pady=4, sticky="nsew")
        ctk.CTkLabel(ongoing_card, text="⏳ Ongoing Cases", font=("Arial", 13, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(pady=(12, 4))
        ctk.CTkLabel(ongoing_card, text=str(ongoing), font=("Arial", 24, "bold"), text_color="#ffc107").pack(pady=(0, 15))

        # Resolved Cases Card
        resolved = self.status_counts.get('Resolved', 0)
        resolved_card = ctk.CTkFrame(stats_frame, fg_color=["white", "#242424"], corner_radius=10, border_width=1, border_color=["#e2e8f0", "#333333"])
        resolved_card.grid(row=0, column=2, padx=4, pady=4, sticky="nsew")
        ctk.CTkLabel(resolved_card, text="✅ Resolved Cases", font=("Arial", 13, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(pady=(12, 4))
        ctk.CTkLabel(resolved_card, text=str(resolved), font=("Arial", 24, "bold"), text_color="#28a745").pack(pady=(0, 15))

        # Referred Cases Card
        referred = self.status_counts.get('Referred', 0)
        referred_card = ctk.CTkFrame(stats_frame, fg_color=["white", "#242424"], corner_radius=10, border_width=1, border_color=["#e2e8f0", "#333333"])
        referred_card.grid(row=0, column=3, padx=4, pady=4, sticky="nsew")
        ctk.CTkLabel(referred_card, text="🔄 Referred Cases", font=("Arial", 13, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(pady=(12, 4))
        ctk.CTkLabel(referred_card, text=str(referred), font=("Arial", 24, "bold"), text_color="#1a73e8").pack(pady=(0, 15))

        # Charts Section
        charts_frame = ctk.CTkFrame(self, fg_color="transparent")
        charts_frame.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        # Configure grid for charts (2x2 layout)
        charts_frame.grid_columnconfigure((0, 1), weight=1)
        charts_frame.grid_rowconfigure((0, 1), weight=1)

        # Theme-aware matplotlib background
        is_dark = ctk.get_appearance_mode() == "Dark"
        plt_bg = "#242424" if is_dark else "white"
        plt_text = "#f8fafc" if is_dark else "#0f172a"

        # Abuse Types Pie Chart Card
        pie_card = ctk.CTkFrame(charts_frame, fg_color=["white", "#242424"], corner_radius=10, border_width=1, border_color=["#e2e8f0", "#333333"])
        pie_card.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

        ctk.CTkLabel(pie_card, text="📈 Type of Abuse Distribution", font=("Arial", 15, "bold"), text_color=["#1a2a4a", "#f8fafc"], wraplength=320, justify="center").pack(pady=(12, 8))

        if self.abuse_counts:
            fig1, ax1 = plt.subplots(figsize=(4.5, 4), facecolor=plt_bg)
            colors = ['#8b0000', '#1a73e8', '#28a745', '#ffc107', '#dc3545', '#6f42c1', '#20c997']
            wedges, texts, autotexts = ax1.pie(
                self.abuse_counts.values(),
                labels=self.abuse_counts.keys(),
                autopct='%1.1f%%',
                startangle=90,
                colors=colors[:len(self.abuse_counts)],
                textprops={'color': plt_text}
            )
            ax1.axis('equal')
            ax1.set_title('Abuse Types Breakdown', fontsize=12, fontweight='bold', pad=20, color=plt_text)

            # Style the text
            for text in texts:
                text.set_fontsize(10)
            for autotext in autotexts:
                autotext.set_fontsize(9)
                autotext.set_fontweight('bold')

            canvas1 = FigureCanvasTkAgg(fig1, master=pie_card)
            canvas1.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 15))
        else:
            ctk.CTkLabel(pie_card, text="No data available", font=("Arial", 12), text_color=["#666666", "#999999"]).pack(pady=20)

        # Case Status Bar Chart Card
        bar_card = ctk.CTkFrame(charts_frame, fg_color=["white", "#242424"], corner_radius=10, border_width=1, border_color=["#e2e8f0", "#333333"])
        bar_card.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")

        ctk.CTkLabel(bar_card, text="📊 Case Status Summary", font=("Arial", 15, "bold"), text_color=["#1a2a4a", "#f8fafc"], wraplength=320, justify="center").pack(pady=(12, 8))

        if self.status_counts:
            fig2, ax2 = plt.subplots(figsize=(4.5, 4), facecolor=plt_bg)
            ax2.set_facecolor(plt_bg)
            bars = ax2.bar(
                self.status_counts.keys(),
                self.status_counts.values(),
                color=['#ffc107', '#28a745', '#1a73e8', '#dc3545']
            )
            ax2.set_title('Case Status Distribution', fontsize=12, fontweight='bold', pad=20, color=plt_text)
            ax2.set_ylabel('Number of Cases', fontsize=10, color=plt_text)
            ax2.tick_params(axis='x', rotation=0, labelsize=10, colors=plt_text)
            ax2.tick_params(axis='y', labelsize=10, colors=plt_text)
            for spine in ax2.spines.values(): spine.set_color(plt_text)

            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{int(height)}', ha='center', va='bottom', fontsize=9, fontweight='bold', color=plt_text)

            canvas2 = FigureCanvasTkAgg(fig2, master=bar_card)
            canvas2.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 15))
        else:
            ctk.CTkLabel(bar_card, text="No data available", font=("Arial", 12), text_color=["#666666", "#999999"]).pack(pady=20)

        # Cases Over Time Line Chart (spans full width)
        line_card = ctk.CTkFrame(charts_frame, fg_color=["white", "#242424"], corner_radius=10, border_width=1, border_color=["#e2e8f0", "#333333"])
        line_card.grid(row=1, column=0, columnspan=2, padx=8, pady=8, sticky="nsew")

        ctk.CTkLabel(line_card, text="📉 Cases Over Time Trend", font=("Arial", 15, "bold"), text_color=["#1a2a4a", "#f8fafc"], wraplength=720, justify="center").pack(pady=(12, 8))

        if self.monthly_counts:
            fig3, ax3 = plt.subplots(figsize=(8, 3.5), facecolor=plt_bg)
            ax3.set_facecolor(plt_bg)
            months = sorted(self.monthly_counts.keys())
            counts = [self.monthly_counts[m] for m in months]

            ax3.plot(months, counts, marker='o', linewidth=2, markersize=6, color='#8b0000')
            ax3.fill_between(months, counts, alpha=0.3, color='#8b0000')

            ax3.set_title('Monthly Case Trends (2020-2026)', fontsize=12, fontweight='bold', pad=20, color=plt_text)
            ax3.set_ylabel('Number of Cases', fontsize=10, color=plt_text)
            ax3.tick_params(axis='x', rotation=45, labelsize=9, colors=plt_text)
            ax3.tick_params(axis='y', labelsize=10, colors=plt_text)
            for spine in ax3.spines.values(): spine.set_color(plt_text)
            ax3.grid(True, alpha=0.3, color=plt_text)

            # Add data points
            for i, (month, count) in enumerate(zip(months, counts)):
                ax3.annotate(f'{count}', (month, count), xytext=(0, 5),
                           textcoords='offset points', ha='center', fontsize=8, fontweight='bold', color=plt_text)

            canvas3 = FigureCanvasTkAgg(fig3, master=line_card)
            canvas3.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 15))
        else:
            ctk.CTkLabel(line_card, text="No historical data available", font=("Arial", 12), text_color=["#666666", "#999999"]).pack(pady=20)

    def back_to_reports(self):
        # Use main window to show reports so it's tracked as current_frame
        if hasattr(self.master.master, 'show_reports'):
            self.master.master.show_reports()
        else:
            # Fallback
            from .reports import ReportsFrame
            self.destroy()
            ReportsFrame(self.parent).pack(fill="both", expand=True)

    def refresh(self):
        """Refresh analytics data and charts"""
        self.setup_ui()

    def load_data(self):
        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute("SELECT type_of_abuse, COUNT(*) FROM vawc_logs WHERE is_deleted = 0 GROUP BY type_of_abuse")
            self.abuse_counts = {row[0]: row[1] for row in cursor.fetchall() if row[0]}

            cursor.execute("SELECT case_status, COUNT(*) FROM vawc_logs WHERE is_deleted = 0 GROUP BY case_status")
            self.status_counts = {row[0]: row[1] for row in cursor.fetchall() if row[0]}

            cursor.execute("SELECT strftime('%Y', date), strftime('%m', date), COUNT(*) FROM vawc_logs WHERE is_deleted = 0 GROUP BY strftime('%Y', date), strftime('%m', date)")
            self.monthly_counts = {f"{row[0]}-{int(row[1]):02d}": row[2] for row in cursor.fetchall()}

        except Exception:
            self.abuse_counts = {}
            self.status_counts = {}
            self.monthly_counts = {}
        finally:
            if connection:
                connection.close()