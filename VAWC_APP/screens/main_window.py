import customtkinter as ctk
from tkinter import ttk, messagebox
import os
from PIL import Image
from .dashboard import DashboardFrame
from .logs_tab import LogsTabFrame
from .add_record import AddRecordFrame
from .reports import ReportsFrame
from .analytics import AnalyticsFrame
from .user_management import UserManagementFrame
from .settings import SettingsFrame
from .audit_logs import AuditLogFrame

class MainWindow(ctk.CTk):
    def __init__(self, username, user_role):
        super().__init__()
        self.username = username
        self.user_role = user_role
        self.title("VAWC Case Logging System")
        self.normal_geometry = "1100x680+100+100"
        self.geometry(self.normal_geometry)
        self.minsize(1100, 680)
        self.fullscreen = True
        self.attributes("-fullscreen", True)
        self.bind("<F8>", lambda e: self.toggle_fullscreen())

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.title_bar = ctk.CTkFrame(self, height=80, fg_color="#1a2a4a")
        self.title_bar.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.title_bar.grid_columnconfigure(0, weight=1)
        self.title_bar.grid_rowconfigure(0, weight=1)

        # Logo and Title Container
        title_container = ctk.CTkFrame(self.title_bar, fg_color="#1a2a4a")
        title_container.grid(row=0, column=0, padx=20, pady=10, sticky="w")

        # Add Logo
        logo_path = os.path.join(os.getcwd(), "logo", "tankulan.jpg")
        if os.path.exists(logo_path):
            try:
                logo_image = ctk.CTkImage(
                    light_image=Image.open(logo_path),
                    dark_image=Image.open(logo_path),
                    size=(50, 50)
                )
                self.logo_label = ctk.CTkLabel(title_container, image=logo_image, text="")
                self.logo_label.pack(side="left", padx=(0, 15))
            except Exception as e:
                print(f"Error loading logo: {e}")

        ctk.CTkLabel(
            title_container,
            text="VAWC Case Logging System - Barangay Tankulan, Manolo Fortich, Bukidnon",
            font=("Arial", 16, "bold"),
            text_color="white",
            wraplength=800,
            justify="left"
        ).pack(side="left")

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color="#1a2a4a")
        self.sidebar.grid(row=1, column=0, sticky="ns")
        self.sidebar.grid_rowconfigure(5, weight=1) # Push settings to bottom

        self.btn_dashboard = ctk.CTkButton(self.sidebar, text="Dashboard", fg_color="#1a2a4a", hover_color="#337ab7", command=self.show_dashboard)
        self.btn_dashboard.grid(row=0, column=0, pady=8, padx=10, sticky="ew")

        self.btn_logs = ctk.CTkButton(self.sidebar, text="VAWC Logs", fg_color="#1a2a4a", hover_color="#337ab7", command=self.show_logs)
        self.btn_logs.grid(row=1, column=0, pady=8, padx=10, sticky="ew")

        self.btn_add = ctk.CTkButton(self.sidebar, text="Add Record", fg_color="#1a2a4a", hover_color="#337ab7", command=self.show_add_record)
        self.btn_add.grid(row=2, column=0, pady=8, padx=10, sticky="ew")

        self.btn_reports = ctk.CTkButton(self.sidebar, text="Reports", fg_color="#1a2a4a", hover_color="#337ab7", command=self.show_reports)
        self.btn_reports.grid(row=3, column=0, pady=8, padx=10, sticky="ew")

        # Settings button at the bottom
        self.btn_settings = ctk.CTkButton(self.sidebar, text="⚙ Settings", fg_color="#1a2a4a", hover_color="#337ab7", command=self.show_settings)
        self.btn_settings.grid(row=6, column=0, pady=20, padx=10, sticky="ew")

        self.sidebar_buttons = [self.btn_dashboard, self.btn_logs, self.btn_add, self.btn_reports, self.btn_settings]

        # Content area
        self.content = ctk.CTkFrame(self, fg_color="#f5f5f5")
        self.content.grid(row=1, column=1, sticky="nsew")

        self.current_frame = None
        self.show_dashboard()

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()
        self.current_frame = None

    def set_active_button(self, active_button):
        for button in self.sidebar_buttons:
            button.configure(fg_color="#1a2a4a")
        active_button.configure(fg_color="#25597a")

    def show_dashboard(self):
        self.clear_content()
        self.current_frame = DashboardFrame(self.content)
        self.current_frame.pack(fill="both", expand=True)
        self.set_active_button(self.btn_dashboard)

    def show_logs(self):
        try:
            self.clear_content()
            self.current_frame = LogsTabFrame(self.content, self.username)
            self.current_frame.pack(fill="both", expand=True)
            self.set_active_button(self.btn_logs)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load Logs: {str(e)}")

    def show_add_record(self):
        try:
            self.clear_content()
            self.current_frame = AddRecordFrame(self.content, self.username, on_save=self.refresh_current_view)
            self.current_frame.pack(fill="both", expand=True)
            self.set_active_button(self.btn_add)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load Add Record: {str(e)}")

    def refresh_current_view(self):
        if self.current_frame and hasattr(self.current_frame, 'refresh'):
            self.current_frame.refresh()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.attributes("-fullscreen", self.fullscreen)
        if not self.fullscreen:
            self.geometry(self.normal_geometry)

    def close_app(self):
        self.destroy()

    def show_reports(self):
        self.clear_content()
        self.current_frame = ReportsFrame(self.content)
        self.current_frame.pack(fill="both", expand=True)
        self.set_active_button(self.btn_reports)

    def show_analytics(self):
        self.clear_content()
        self.current_frame = AnalyticsFrame(self.content)
        self.current_frame.pack(fill="both", expand=True)
        self.set_active_button(self.btn_reports)

    def show_user_management(self):
        self.clear_content()
        self.current_frame = UserManagementFrame(self.content)
        self.current_frame.pack(fill="both", expand=True)
        # Add back button to return to settings
        back_btn = ctk.CTkButton(self.current_frame, text="← Back to Settings", command=self.show_settings, fg_color="transparent", text_color="#1a2a4a", hover_color="#eeeeee", width=120)
        back_btn.place(x=20, y=10)

    def show_audit_logs(self):
        self.clear_content()
        self.current_frame = AuditLogFrame(self.content)
        self.current_frame.pack(fill="both", expand=True)
        # Add back button
        back_btn = ctk.CTkButton(self.current_frame, text="← Back to Settings", command=self.show_settings, fg_color="transparent", text_color="#1a2a4a", hover_color="#eeeeee", width=120)
        back_btn.place(x=20, y=10)

    def show_settings(self):
        self.clear_content()
        self.current_frame = SettingsFrame(self.content, self.user_role, self)
        self.current_frame.pack(fill="both", expand=True)
        self.set_active_button(self.btn_settings)

    def logout(self):
        self.destroy()
        from .login import LoginScreen
        LoginScreen().mainloop()