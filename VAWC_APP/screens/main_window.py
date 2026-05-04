import customtkinter as ctk
from tkinter import ttk
from .dashboard import DashboardFrame
from .logs_tab import LogsTabFrame
from .add_record import AddRecordWindow
from .reports import ReportsFrame
from .user_management import UserManagementFrame

class MainWindow(ctk.CTk):
    def __init__(self, user_role):
        super().__init__()
        self.user_role = user_role
        self.title("VAWC Case Logging System")
        self.normal_geometry = "1100x680+100+100"
        self.geometry(self.normal_geometry)
        self.minsize(1100, 680)
        self.fullscreen = True
        self.attributes("-fullscreen", True)

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.title_bar = ctk.CTkFrame(self, height=80, fg_color="#1a2a4a")
        self.title_bar.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.title_bar.grid_columnconfigure(0, weight=1)
        self.title_bar.grid_rowconfigure(0, weight=1)

        ctk.CTkLabel(
            self.title_bar,
            text="VAWC Case Logging System - Barangay Tankulan, Manolo Fortich, Bukidnon",
            font=("Arial", 16, "bold"),
            text_color="white",
            wraplength=900,
            justify="left"
        ).grid(row=0, column=0, padx=20, pady=10, sticky="w")

        button_frame = ctk.CTkFrame(self.title_bar, fg_color="#1a2a4a")
        button_frame.grid(row=0, column=1, padx=10, pady=10, sticky="e")

        btn_config = {"width":40, "height":30, "corner_radius":10, "text_color":"white", "font":("Arial", 12, "bold")}
        self.btn_minimize = ctk.CTkButton(button_frame, text="—", command=self.iconify, fg_color="#3b5d7a", hover_color="#25597a", **btn_config)
        self.btn_minimize.pack(side="left", padx=3)
        self.btn_toggle = ctk.CTkButton(button_frame, text="🗖", command=self.toggle_fullscreen, fg_color="#3b5d7a", hover_color="#25597a", **btn_config)
        self.btn_toggle.pack(side="left", padx=3)
        self.btn_close = ctk.CTkButton(button_frame, text="✕", command=self.close_app, fg_color="#b30000", hover_color="#8b0000", **btn_config)
        self.btn_close.pack(side="left", padx=3)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color="#1a2a4a")
        self.sidebar.grid(row=1, column=0, sticky="ns")
        self.sidebar.grid_rowconfigure(8, weight=1)

        self.btn_dashboard = ctk.CTkButton(self.sidebar, text="Dashboard", fg_color="#1a2a4a", hover_color="#337ab7", command=self.show_dashboard)
        self.btn_dashboard.grid(row=0, column=0, pady=8, padx=10, sticky="ew")

        self.btn_logs = ctk.CTkButton(self.sidebar, text="VAWC Logs", fg_color="#1a2a4a", hover_color="#337ab7", command=self.show_logs)
        self.btn_logs.grid(row=2, column=0, pady=8, padx=10, sticky="ew")

        self.btn_add = ctk.CTkButton(self.sidebar, text="Add Record", fg_color="#1a2a4a", hover_color="#337ab7", command=self.show_add_record)
        self.btn_add.grid(row=3, column=0, pady=8, padx=10, sticky="ew")

        self.btn_reports = ctk.CTkButton(self.sidebar, text="Reports", fg_color="#1a2a4a", hover_color="#337ab7", command=self.show_reports)
        self.btn_reports.grid(row=4, column=0, pady=8, padx=10, sticky="ew")

        if user_role == "Admin":
            self.btn_users = ctk.CTkButton(self.sidebar, text="User Management", fg_color="#1a2a4a", hover_color="#337ab7", command=self.show_user_management)
            self.btn_users.grid(row=5, column=0, pady=8, padx=10, sticky="ew")

        self.btn_logout = ctk.CTkButton(self.sidebar, text="Logout", fg_color="#1a2a4a", hover_color="#337ab7", command=self.logout)
        self.btn_logout.grid(row=7, column=0, pady=8, padx=10, sticky="ew")

        self.sidebar_buttons = [self.btn_dashboard, self.btn_logs, self.btn_add, self.btn_reports, self.btn_logout]
        if user_role == "Admin":
            self.sidebar_buttons.insert(4, self.btn_users)

        # Content area
        self.content = ctk.CTkFrame(self, fg_color="#f5f5f5")
        self.content.grid(row=1, column=1, sticky="nsew")

        self.show_dashboard()

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def set_active_button(self, active_button):
        for button in self.sidebar_buttons:
            button.configure(fg_color="#1a2a4a")
        active_button.configure(fg_color="#25597a")

    def show_dashboard(self):
        self.clear_content()
        DashboardFrame(self.content).pack(fill="both", expand=True)
        self.set_active_button(self.btn_dashboard)

    def show_logs(self):
        self.clear_content()
        LogsTabFrame(self.content, self.user_role).pack(fill="both", expand=True)
        self.set_active_button(self.btn_logs)

    def show_add_record(self):
        AddRecordWindow(self)
        self.set_active_button(self.btn_add)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.attributes("-fullscreen", self.fullscreen)
        self.btn_toggle.configure(text="🗗" if self.fullscreen else "🗖")
        if not self.fullscreen:
            self.geometry(self.normal_geometry)

    def close_app(self):
        self.destroy()

    def show_reports(self):
        self.clear_content()
        ReportsFrame(self.content).pack(fill="both", expand=True)
        self.set_active_button(self.btn_reports)

    def show_user_management(self):
        self.clear_content()
        UserManagementFrame(self.content).pack(fill="both", expand=True)
        self.set_active_button(self.btn_users)

    def logout(self):
        self.destroy()
        from .login import LoginScreen
        LoginScreen().mainloop()