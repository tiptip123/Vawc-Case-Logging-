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
from .people import PeopleScreen

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
        
        # Modern 2025 Dimensions - Full Screen
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
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 1. SIDEBAR (200px, fixed)
        self.sidebar = ctk.CTkFrame(self, width=200, fg_color=self.colors["sidebar_bg"], corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1) # Push bottom items
        self.sidebar.pack_propagate(False)

        # Sidebar - User Info
        self.user_area = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.user_area.pack(fill="x", padx=12, pady=10)
        self.setup_sidebar_user_info()

        # Sidebar - Divider
        ctk.CTkFrame(self.sidebar, height=1, fg_color="#1e3a5f").pack(fill="x", padx=12, pady=(0, 8))

        # Sidebar - Navigation Items
        self.nav_buttons = []
        self.nav_items = []
        self.create_nav_item("🏠  Dashboard", self.show_dashboard)
        self.create_nav_item("📋  VAWC Logs", self.show_logs)
        self.create_nav_item("👤  People", self.show_people)
        self.create_nav_item("➕  Add Record", self.show_add_record)
        self.create_nav_item("📊  Reports", self.show_reports)

        # Sidebar - Bottom Divider
        ctk.CTkFrame(self.sidebar, height=1, fg_color="#1e3a5f").pack(side="bottom", fill="x", padx=12, pady=(8, 8))

        # Sidebar - Bottom Items
        self.bottom_nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.bottom_nav_frame.pack(side="bottom", fill="x", pady=(0, 12))
        self.create_nav_item("⚙️  Settings", self.show_settings, parent=self.bottom_nav_frame, pady=(0, 0))

        # 2. CONTENT AREA
        self.content = ctk.CTkFrame(self, fg_color=self.colors["bg_light"], corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")

        # 4. STATUS BAR
        self.status_bar = ctk.CTkFrame(self, height=30, fg_color=["#f1f5f9", "#0f172a"], corner_radius=0, border_width=1, border_color=self.colors["border_light"])
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.status_bar.grid_propagate(False)

        # Status Bar Left: User Info
        status_left = ctk.CTkFrame(self.status_bar, fg_color="transparent")
        status_left.pack(side="left", padx=20)
        self.status_user_label = ctk.CTkLabel(status_left, text=f"👤 {self.username}", font=("Arial", 11, "bold"), text_color=self.colors["text_primary"])
        self.status_user_label.pack(side="left")
        role_chip = ctk.CTkLabel(status_left, text=self.user_role, font=("Arial", 10), text_color="white", fg_color=self.colors["sidebar_active"], corner_radius=10, padx=10, pady=4)
        role_chip.pack(side="left", padx=(10, 0))

        # Status Bar Right: Clock & DB
        status_right = ctk.CTkFrame(self.status_bar, fg_color="transparent")
        status_right.pack(side="right", padx=20)
        self.db_status = ctk.CTkLabel(status_right, text="🟢 DB Connected", font=("Arial", 11), text_color="#16a34a")
        self.db_status.pack(side="right", padx=(0, 12))
        self.clock_label = ctk.CTkLabel(status_right, text="", font=("Arial", 11), text_color=self.colors["text_secondary"])
        self.clock_label.pack(side="right")
        # IDs for scheduled callbacks (for clean cancel on logout)
        self._clock_after_id = None
        self._session_after_id = None
        self.update_clock()
        self.update_fonts()
        self.setup_global_shortcuts()
        self.check_database_status()

        self.current_frame = None
        self.show_dashboard()
        
        # Set full-screen after layout is complete
        self.after_idle(lambda: self.state("zoomed"))

    def update_fonts(self):
        self.status_user_label.configure(font=get_scaled_font(11, "normal", self.font_scale))
        self.db_status.configure(font=get_scaled_font(11, "normal", self.font_scale))
        self.clock_label.configure(font=get_scaled_font(11, "normal", self.font_scale))
        for btn in self.nav_buttons:
            btn.configure(font=get_scaled_font(12, "normal", self.font_scale))

    def setup_global_shortcuts(self):
        self.last_activity = datetime.now()
        self.bind_all("<Control-n>", lambda e: self.show_add_record())
        self.bind_all("<Control-f>", lambda e: self.focus_search())
        self.bind_all("<Escape>", lambda e: self.show_dashboard())
        self.bind_all("<Any-KeyPress>", self.reset_session_timer)
        self.bind_all("<Any-ButtonPress>", self.reset_session_timer)
        self.check_session_timeout()

    def check_database_status(self):
        try:
            conn = get_connection()
            conn.close()
            self.db_status.configure(text="🟢 DB Connected", text_color="#16a34a")
        except Exception:
            self.db_status.configure(text="🔴 DB Offline", text_color="#dc2626")
        finally:
            self.after(60000, self.check_database_status)

    def toggle_theme(self):
        pass

    def adjust_font_scale(self, delta):
        self.font_scale = min(max(self.font_scale + delta, 0.85), 1.5)
        self.config["font_scale"] = round(self.font_scale, 2)
        save_config(self.config)
        self.update_fonts()
        self.refresh_all_frames()

    def setup_sidebar_user_info(self):
        for widget in self.user_area.winfo_children():
            widget.destroy()

        # Fetch current user data from DB
        connection = None
        user_full_name = self.username
        user_pic_data = None
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute(
                "SELECT full_name, profile_picture FROM users WHERE username = ?",
                (self.username,)
            )
            res = cursor.fetchone()
            if res:
                user_full_name = res[0] or self.username
                user_pic_data = res[1]
        except Exception:
            pass
        finally:
            if connection:
                connection.close()

        # Horizontal profile frame
        profile_frame = ctk.CTkFrame(self.user_area, fg_color="transparent")
        profile_frame.pack(fill="x")

        # Avatar (40x40 circle)
        avatar_size = 40
        self.avatar_img = make_circle_image(user_pic_data, size=avatar_size)

        if self.avatar_img:
            avatar_label = ctk.CTkLabel(
                profile_frame,
                text="",
                image=self.avatar_img,
                width=avatar_size,
                height=avatar_size
            )
            avatar_label.pack(side="left")
        else:
            initials = ""
            parts = user_full_name.strip().split()
            if len(parts) >= 2:
                initials = parts[0][0].upper() + parts[-1][0].upper()
            elif parts:
                initials = parts[0][0].upper()
            else:
                initials = "?"

            avatar_circle = ctk.CTkFrame(
                profile_frame,
                width=avatar_size,
                height=avatar_size,
                corner_radius=avatar_size // 2,
                fg_color="#1e3a5f"
            )
            avatar_circle.pack(side="left")
            avatar_circle.pack_propagate(False)
            ctk.CTkLabel(
                avatar_circle,
                text=initials,
                font=("Segoe UI", 16, "bold"),
                text_color="white"
            ).place(relx=0.5, rely=0.5, anchor="center")

        info_frame = ctk.CTkFrame(profile_frame, fg_color="transparent")
        info_frame.pack(side="left", padx=(10, 0), fill="both", expand=True)

        display_name = user_full_name
        if len(display_name) > 16:
            display_name = display_name[:14] + "..."

        ctk.CTkLabel(
            info_frame,
            text=display_name,
            font=("Segoe UI", 12, "bold"),
            text_color="white",
            anchor="w",
            wraplength=140
        ).pack(fill="x")

        role_color = "#8b0000" if self.user_role == "Admin" else "#1a2a4a"
        badge = ctk.CTkFrame(info_frame, fg_color=role_color, corner_radius=10)
        badge.pack(anchor="w", pady=(2, 0))
        ctk.CTkLabel(
            badge,
            text=self.user_role,
            font=("Segoe UI", 8),
            text_color="white",
            padx=10,
            pady=4
        ).pack()

    def reset_session_timer(self, event=None):
        self.last_activity = datetime.now()

    def check_session_timeout(self):
        if (datetime.now() - self.last_activity).total_seconds() > 900: # 15 minutes
            messagebox.showinfo("Session Timeout", "Your session has expired due to inactivity.")
            self.logout()
        else:
            try:
                if getattr(self, '_session_after_id', None):
                    self.after_cancel(self._session_after_id)
            except Exception:
                pass
            self._session_after_id = self.after(30000, self.check_session_timeout) # Check every 30 seconds

    def create_nav_item(self, text, command, parent=None, pack_side="top", pady=(0, 2)):
        parent = parent or self.sidebar
        container = ctk.CTkFrame(parent, fg_color="transparent", height=34)
        container.pack(side=pack_side, fill="x", padx=8, pady=pady)
        container.pack_propagate(False)

        accent = ctk.CTkFrame(container, width=3, fg_color="transparent", corner_radius=0)
        accent.pack(side="left", fill="y")

        btn = ctk.CTkButton(
            container,
            text=text,
            command=command,
            anchor="w",
            height=34,
            fg_color="transparent",
            text_color="#94a3b8",
            hover_color="#1e3a5f",
            font=("Segoe UI", 12),
            corner_radius=6,
            border_width=0
        )
        btn.pack(side="left", fill="both", expand=True, padx=(4, 4))

        self.nav_buttons.append(btn)
        self.nav_items.append((btn, accent, container))
        return btn

    def set_active_nav(self, active_btn):
        target_btn = active_btn[0] if isinstance(active_btn, tuple) else active_btn
        for btn, accent, container in self.nav_items:
            accent.configure(fg_color="transparent")
            container.configure(fg_color="transparent")
            btn.configure(
                fg_color="transparent",
                text_color="#94a3b8",
                font=("Segoe UI", 12)
            )

        for btn, accent, container in self.nav_items:
            if btn == target_btn:
                accent.configure(fg_color="#ff4444")
                container.configure(fg_color="#12203b")
                btn.configure(
                    fg_color="#12203b",
                    text_color="white",
                    font=("Segoe UI", 12, "bold")
                )
                break

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
            elif frame_class == PeopleScreen: self.show_people()
            elif frame_class == SettingsFrame: self.show_settings()
            elif frame_class == AuditLogFrame: self.show_audit_logs()
            elif frame_class == UserManagementFrame: self.show_user_management()
            elif frame_class == AnalyticsFrame: self.show_analytics()

    def update_clock(self):
        now = datetime.now().strftime("%I:%M %p • %b %d, %Y")
        self.clock_label.configure(text=now)
        try:
            if getattr(self, '_clock_after_id', None):
                self.after_cancel(self._clock_after_id)
        except Exception:
            pass
        self._clock_after_id = self.after(1000, self.update_clock)

    def show_dashboard(self):
        if not self.check_unsaved_changes(): return
        self.clear_content()
        self.current_frame = DashboardFrame(self.content)
        self.current_frame.pack(fill="both", expand=True)
        self.set_active_nav(self.nav_buttons[0])

    def show_logs(self):
        if not self.check_unsaved_changes(): return
        self.clear_content()
        self.current_frame = LogsTabFrame(self.content, self.username, self.user_role)
        self.current_frame.pack(fill="both", expand=True)
        self.set_active_nav(self.nav_buttons[1])

    def show_add_record(self):
        if not self.check_unsaved_changes(): return
        self.clear_content()
        # Do not redirect after save; keep user on Add Record page
        self.current_frame = AddRecordFrame(self.content, self.username, self.user_role, on_save=None)
        self.current_frame.pack(fill="both", expand=True)
        self.set_active_nav(self.nav_buttons[3])

    def show_reports(self):
        if not self.check_unsaved_changes(): return
        self.clear_content()
        self.current_frame = ReportsFrame(self.content)
        self.current_frame.pack(fill="both", expand=True)
        self.set_active_nav(self.nav_buttons[4])

    def show_settings(self):
        if not self.check_unsaved_changes(): return
        self.clear_content()
        self.current_frame = SettingsFrame(self.content, self.user_role, self)
        self.current_frame.pack(fill="both", expand=True)
        self.set_active_nav(self.nav_buttons[5])

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
        self.clear_content()
        self.current_frame = AnalyticsFrame(self.content)
        self.current_frame.pack(fill="both", expand=True)
        self.set_active_nav(self.nav_buttons[4]) # Keep reports active for analytics

    def show_people(self):
        if not self.check_unsaved_changes(): return
        self.clear_content()
        self.current_frame = PeopleScreen(self.content, self.username, self.user_role)
        self.current_frame.pack(fill="both", expand=True)
        self.set_active_nav(self.nav_buttons[2])

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

    def focus_search(self):
        self.show_logs()
        if hasattr(self.current_frame, 'search_entry'):
            self.current_frame.search_entry.focus_set()

    def logout(self):
        # Close the main window and return to login screen
        self.destroy()
        from .login import LoginScreen
        LoginScreen().mainloop()