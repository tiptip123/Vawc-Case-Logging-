import customtkinter as ctk
from tkinter import ttk, messagebox
import os
from PIL import Image
from datetime import datetime
from .dashboard import DashboardFrame
from .logs_tab import LogsTabFrame
from .add_record import AddRecordFrame
from .reports import ReportsFrame
from .analytics import AnalyticsFrame
from .user_management import UserManagementFrame
from .settings import SettingsFrame
from .audit_logs import AuditLogFrame

from utils.helpers import load_config, make_circle_image, save_config, get_scaled_font

from db import get_connection

class MainWindow(ctk.CTk):
    def __init__(self, username, user_role):
        super().__init__()
        self.username = username
        self.user_role = user_role
        self.config = load_config()
        self.title(f"VAWC Case Logging System - {self.config['lgu_name']}")
        
        # Apply Appearance Mode from Config
        mode = self.config.get("appearance_mode", "light")
        ctk.set_appearance_mode(mode)
        self.font_scale = self.config.get("font_scale", 1.0)
        
        # Modern 2025 Dimensions
        self.geometry("1280x800")
        self.minsize(1200, 750)
        
        # Color Palette
        self.colors = {
            "primary_navy": "#1a2a4a",
            "sidebar_bg": "#0f1e35",
            "sidebar_hover": "#1e3a5f",
            "sidebar_active": "#8b0000",
            "bg_light": ["#f8fafc", "#1a1a1a"],
            "text_primary": ["#0f172a", "#f8fafc"],
            "text_secondary": ["#64748b", "#94a3b8"],
            "border_light": ["#e2e8f0", "#333333"]
        }

        # Layout Configuration
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 1. SIDEBAR (220px, fixed)
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color=self.colors["sidebar_bg"], corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1) # Push bottom items
        self.sidebar.pack_propagate(False)

        # Sidebar - User Info
        self.user_area = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.user_area.pack(fill="x", padx=12, pady=12)
        self.setup_sidebar_user_info()

        # Sidebar - Divider
        ctk.CTkFrame(self.sidebar, height=1, fg_color="#1e3a5f").pack(fill="x", padx=20, pady=(0, 20))

        # Sidebar - Navigation Items
        self.nav_buttons = []
        self.create_nav_item("🏠  Dashboard", self.show_dashboard)
        self.create_nav_item("📋  VAWC Logs", self.show_logs)
        self.create_nav_item("➕  Add Record", self.show_add_record)
        self.create_nav_item("📊  Reports", self.show_reports)
        
        # Sidebar - Bottom Items
        self.create_nav_item("⚙️  Settings", self.show_settings, pack_side="bottom", pady=(0, 20))

        # 2. TOP HEADER BAR
        self.header = ctk.CTkFrame(self, height=60, fg_color=["white", "#242424"], corner_radius=0, border_width=1, border_color=self.colors["border_light"])
        self.header.grid(row=0, column=1, sticky="ew")
        self.header.grid_propagate(False)

        self.page_title = ctk.CTkLabel(self.header, text="Dashboard", font=get_scaled_font(18, "bold", self.font_scale), text_color=self.colors["text_primary"])
        self.page_title.pack(side="left", padx=30)

        # Header controls for quick appearance and size adjustments
        self.header_actions = ctk.CTkFrame(self.header, fg_color="transparent")
        self.header_actions.pack(side="right", padx=20)

        self.zoom_out_button = ctk.CTkButton(
            self.header_actions,
            text="A-",
            width=42,
            height=34,
            corner_radius=8,
            command=lambda: self.adjust_font_scale(-0.1),
            font=get_scaled_font(11, "bold", self.font_scale)
        )
        self.zoom_out_button.pack(side="right", padx=(0, 8))

        self.zoom_in_button = ctk.CTkButton(
            self.header_actions,
            text="A+",
            width=42,
            height=34,
            corner_radius=8,
            command=lambda: self.adjust_font_scale(0.1),
            font=get_scaled_font(11, "bold", self.font_scale)
        )
        self.zoom_in_button.pack(side="right", padx=(0, 8))

        current_mode = ctk.get_appearance_mode().capitalize()
        self.theme_button = ctk.CTkButton(
            self.header_actions,
            text="🌙" if current_mode == "Light" else "☀️",
            width=82,
            height=34,
            corner_radius=8,
            command=self.toggle_theme,
            font=get_scaled_font(11, "bold", self.font_scale)
        )
        self.theme_button.pack(side="right")

        # 3. CONTENT AREA
        self.content = ctk.CTkFrame(self, fg_color=self.colors["bg_light"], corner_radius=0)
        self.content.grid(row=1, column=1, sticky="nsew")

        # 4. STATUS BAR
        self.status_bar = ctk.CTkFrame(self, height=30, fg_color=["#f1f5f9", "#0f172a"], corner_radius=0, border_width=1, border_color=self.colors["border_light"])
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.status_bar.grid_propagate(False)

        # Status Bar Left: User Info
        self.status_user_label = ctk.CTkLabel(self.status_bar, text=f"👤 {self.username} ({self.user_role})", font=("Arial", 11), text_color=self.colors["text_secondary"])
        self.status_user_label.pack(side="left", padx=20)

        # Status Bar Right: Clock & DB
        self.db_status = ctk.CTkLabel(self.status_bar, text="🟢 DB Connected", font=("Arial", 11), text_color="#16a34a")
        self.db_status.pack(side="right", padx=20)
        
        self.clock_label = ctk.CTkLabel(self.status_bar, text="", font=("Arial", 11), text_color=self.colors["text_secondary"])
        self.clock_label.pack(side="right", padx=10)
        self.update_clock()
        self.update_fonts()

        self.current_frame = None
        self.show_dashboard()

    def update_fonts(self):
        self.page_title.configure(font=get_scaled_font(18, "bold", self.font_scale))
        self.status_user_label.configure(font=get_scaled_font(11, "normal", self.font_scale))
        self.db_status.configure(font=get_scaled_font(11, "normal", self.font_scale))
        self.clock_label.configure(font=get_scaled_font(11, "normal", self.font_scale))
        for btn in self.nav_buttons:
            btn.configure(font=get_scaled_font(13, "normal", self.font_scale))
        if hasattr(self, "theme_button"):
            self.theme_button.configure(font=get_scaled_font(11, "bold", self.font_scale))
            self.zoom_out_button.configure(font=get_scaled_font(11, "bold", self.font_scale))
            self.zoom_in_button.configure(font=get_scaled_font(11, "bold", self.font_scale))

    def toggle_theme(self):
        current = ctk.get_appearance_mode().lower()
        new_mode = "dark" if current == "light" else "light"
        ctk.set_appearance_mode(new_mode)
        self.config["appearance_mode"] = new_mode
        save_config(self.config)
        self.theme_button.configure(text="🌙" if new_mode == "light" else "☀️")
        self.refresh_all_frames()

    def adjust_font_scale(self, delta):
        self.font_scale = min(max(self.font_scale + delta, 0.85), 1.5)
        self.config["font_scale"] = round(self.font_scale, 2)
        save_config(self.config)
        self.update_fonts()
        self.refresh_all_frames()

        # Keyboard Shortcuts
        self.bind_all("<Control-n>", lambda e: self.show_add_record())
        self.bind_all("<Control-f>", lambda e: self.focus_search())
        self.bind_all("<Escape>", lambda e: self.show_dashboard())

        # Session Timeout (15 minutes)
        self.last_activity = datetime.now()
        self.bind_all("<Any-KeyPress>", self.reset_session_timer)
        self.bind_all("<Any-ButtonPress>", self.reset_session_timer)
        self.check_session_timeout()

    def setup_sidebar_user_info(self):
        for widget in self.user_area.winfo_children():
            widget.destroy()

        # Fetch current user data from DB for real-time updates
        connection = None
        user_full_name = self.username
        user_pic_data = None
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT full_name, profile_picture FROM users WHERE username = ?", (self.username,))
            res = cursor.fetchone()
            if res:
                user_full_name = res[0] or self.username
                user_pic_data = res[1]
        except Exception:
            pass
        finally:
            if connection: connection.close()

        # Profile Frame (Horizontal Layout)
        profile_frame = ctk.CTkFrame(self.user_area, fg_color="transparent")
        profile_frame.pack(fill="x")

        # Avatar Size 48x48
        avatar_size = 48
        self.avatar_img = make_circle_image(user_pic_data, size=avatar_size)
        
        avatar_label = ctk.CTkLabel(profile_frame, text="", width=avatar_size, height=avatar_size)
        avatar_label.pack(side="left")
        
        if self.avatar_img:
            avatar_label.configure(image=self.avatar_img)
        else:
            # Fallback to initials
            initial = user_full_name[0].upper() if user_full_name else "?"
            avatar_fallback = ctk.CTkFrame(profile_frame, width=avatar_size, height=avatar_size, corner_radius=avatar_size//2, fg_color="#1e3a5f")
            avatar_fallback.pack(side="left")
            avatar_fallback.pack_propagate(False)
            ctk.CTkLabel(avatar_fallback, text=initial, font=("Arial", 16, "bold"), text_color="white").place(relx=0.5, rely=0.5, anchor="center")
            avatar_label.pack_forget() # Don't show the empty label

        # Info Frame (Name + Role)
        info_frame = ctk.CTkFrame(profile_frame, fg_color="transparent")
        info_frame.pack(side="left", padx=(8, 0), fill="both", expand=True)

        # Full Name (White, Bold, 13px, Truncated)
        name_label = ctk.CTkLabel(info_frame, text=user_full_name, font=("Arial", 13, "bold"), text_color="white", anchor="w")
        name_label.pack(fill="x")
        
        # Role Badge (Pill, maroon/navy)
        role_color = self.colors["sidebar_active"] if self.user_role == "Admin" else self.colors["primary_navy"]
        badge_frame = ctk.CTkFrame(info_frame, fg_color=role_color, corner_radius=10)
        badge_frame.pack(anchor="w", pady=(2, 0))
        ctk.CTkLabel(badge_frame, text=self.user_role, font=("Arial", 10), text_color="white", padx=10, pady=1).pack()

    def reset_session_timer(self, event=None):
        self.last_activity = datetime.now()

    def check_session_timeout(self):
        if (datetime.now() - self.last_activity).total_seconds() > 900: # 15 minutes
            messagebox.showinfo("Session Timeout", "Your session has expired due to inactivity.")
            self.logout()
        else:
            self.after(30000, self.check_session_timeout) # Check every 30 seconds

    def create_nav_item(self, text, command, pack_side="top", pady=(0, 5)):
        btn = ctk.CTkButton(
            self.sidebar,
            text=text,
            command=command,
            anchor="w",
            height=42,
            fg_color="transparent",
            text_color="#cbd5e1",
            hover_color=self.colors["sidebar_hover"],
            font=("Arial", 13),
            corner_radius=0
        )
        btn.pack(side=pack_side, fill="x", padx=0, pady=pady)
        self.nav_buttons.append(btn)
        return btn

    def set_active_nav(self, active_btn):
        for btn in self.nav_buttons:
            btn.configure(fg_color="transparent", text_color="#cbd5e1", border_width=0)
        
        active_btn.configure(
            fg_color=self.colors["sidebar_active"],
            text_color="white"
        )
        # Add a left accent line (since we can't easily do it with CTKButton properties, 
        # we'll just use the background color for now as per overhaul specs)

    def refresh_all_frames(self):
        """Refresh the current frame to apply theme changes"""
        if hasattr(self, 'current_frame') and self.current_frame:
            # Get the current frame class
            frame_class = self.current_frame.__class__
            
            # Re-show the current frame using the appropriate method
            if frame_class == DashboardFrame: self.show_dashboard()
            elif frame_class == LogsTabFrame: self.show_logs()
            elif frame_class == AddRecordFrame: self.show_add_record()
            elif frame_class == ReportsFrame: self.show_reports()
            elif frame_class == SettingsFrame: self.show_settings()
            elif frame_class == AuditLogFrame: self.show_audit_logs()
            elif frame_class == UserManagementFrame: self.show_user_management()
            elif frame_class == AnalyticsFrame: self.show_analytics()

    def update_clock(self):
        now = datetime.now().strftime("%I:%M %p • %b %d, %Y")
        self.clock_label.configure(text=now)
        self.after(1000, self.update_clock)

    def show_dashboard(self):
        if not self.check_unsaved_changes(): return
        self.page_title.configure(text="Dashboard")
        self.clear_content()
        self.current_frame = DashboardFrame(self.content)
        self.current_frame.pack(fill="both", expand=True)
        self.set_active_nav(self.nav_buttons[0])

    def show_logs(self):
        if not self.check_unsaved_changes(): return
        self.page_title.configure(text="VAWC Logs")
        self.clear_content()
        self.current_frame = LogsTabFrame(self.content, self.username, self.user_role)
        self.current_frame.pack(fill="both", expand=True)
        self.set_active_nav(self.nav_buttons[1])

    def show_add_record(self):
        if not self.check_unsaved_changes(): return
        self.page_title.configure(text="Add New Record")
        self.clear_content()
        # Do not redirect after save; keep user on Add Record page
        self.current_frame = AddRecordFrame(self.content, self.username, self.user_role, on_save=None)
        self.current_frame.pack(fill="both", expand=True)
        self.set_active_nav(self.nav_buttons[2])

    def show_reports(self):
        if not self.check_unsaved_changes(): return
        self.page_title.configure(text="Reports")
        self.clear_content()
        self.current_frame = ReportsFrame(self.content)
        self.current_frame.pack(fill="both", expand=True)
        self.set_active_nav(self.nav_buttons[3])

    def show_settings(self):
        if not self.check_unsaved_changes(): return
        self.page_title.configure(text="Settings")
        self.clear_content()
        self.current_frame = SettingsFrame(self.content, self.user_role, self)
        self.current_frame.pack(fill="both", expand=True)
        self.set_active_nav(self.nav_buttons[4])

    def check_unsaved_changes(self):
        """Warn user if they are leaving a form with unsaved changes"""
        if isinstance(self.current_frame, AddRecordFrame):
            if hasattr(self.current_frame, 'has_unsaved_changes') and self.current_frame.has_unsaved_changes():
                if not messagebox.askyesno("Unsaved Changes", "You have unsaved data in the form. Are you sure you want to leave?"):
                    return False
        return True

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()
        self.current_frame = None

    def show_analytics(self):
        self.page_title.configure(text="Analytics")
        self.clear_content()
        self.current_frame = AnalyticsFrame(self.content)
        self.current_frame.pack(fill="both", expand=True)
        self.set_active_nav(self.nav_buttons[3]) # Keep reports active for analytics

    def show_user_management(self):
        self.page_title.configure(text="User Management")
        self.clear_content()
        self.current_frame = UserManagementFrame(self.content)
        self.current_frame.pack(fill="both", expand=True)
        # Add back button to return to settings
        back_btn = ctk.CTkButton(self.current_frame, text="← Back to Settings", command=self.show_settings, fg_color="transparent", text_color="#1a2a4a", hover_color="#eeeeee", width=120)
        back_btn.place(x=20, y=10)

    def show_audit_logs(self):
        self.page_title.configure(text="Audit Logs")
        self.clear_content()
        self.current_frame = AuditLogFrame(self.content)
        self.current_frame.pack(fill="both", expand=True)
        # Add back button
        back_btn = ctk.CTkButton(self.current_frame, text="← Back to Settings", command=self.show_settings, fg_color="transparent", text_color="#1a2a4a", hover_color="#eeeeee", width=120)
        back_btn.place(x=20, y=10)

    def focus_search(self):
        self.show_logs()
        if hasattr(self.current_frame, 'search_entry'):
            self.current_frame.search_entry.focus_set()

    def logout(self):
        self.destroy()
        self.quit()
        from .login import LoginScreen
        LoginScreen().mainloop()