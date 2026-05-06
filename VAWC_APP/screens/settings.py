import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
import json
import shutil
import sys
import subprocess
from datetime import datetime

class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent, user_role, main_window):
        super().__init__(parent, fg_color="transparent")
        self.user_role = user_role
        self.main_window = main_window
        self.version_file = os.path.join(os.getcwd(), "version.txt")
        self.current_version = self.load_version()
        
        # Panel tracking
        self.current_panel = None
        self.setup_main_view()

    def setup_main_view(self):
        # Clear main content
        for widget in self.winfo_children():
            widget.destroy()

        # Scrollable area
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Responsive Grid Layout
        self.grid_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        self.grid_frame.pack(fill="x", padx=20, pady=20)
        self.grid_frame.grid_columnconfigure((0, 1), weight=1)

        self.setup_cards()

    def show_panel(self, panel_class, **kwargs):
        """Replaces the entire settings view with a specific panel inline"""
        for widget in self.winfo_children():
            widget.destroy()
        
        # Add back button at the top
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(20, 0))
        
        ctk.CTkButton(header, text="← Back to Settings", 
                      command=self.setup_main_view, 
                      fg_color="transparent", 
                      text_color=["#1a2a4a", "#cbd5e1"], 
                      hover_color=["#eeeeee", "#333333"], 
                      font=("Arial", 13, "bold"),
                      width=140).pack(side="left")

        self.current_panel = panel_class(self, **kwargs)
        self.current_panel.pack(fill="both", expand=True, padx=40, pady=20)

    def show_banner(self, message, type="success", parent=None, duration=3000):
        """Shows an inline success or error banner"""
        bg_color = ["#dcfce7", "#064e3b"] if type == "success" else ["#fee2e2", "#7f1d1d"]
        text_color = ["#166534", "#d1fae5"] if type == "success" else ["#991b1b", "#fef2f2"]
        icon = "✅" if type == "success" else "❌"
        
        banner = ctk.CTkFrame(parent or self, fg_color=bg_color, corner_radius=8, height=45)
        banner.pack(fill="x", padx=40, pady=10, before=parent.winfo_children()[1] if parent and len(parent.winfo_children()) > 1 else None)
        banner.pack_propagate(False)
        
        ctk.CTkLabel(banner, text=f"{icon}  {message}", font=("Arial", 12, "bold"), text_color=text_color).pack(side="left", padx=15)
        
        if type == "error":
            ctk.CTkButton(banner, text="✕", width=25, height=25, fg_color="transparent", text_color=text_color, 
                          hover_color=["#fecaca", "#991b1b"], command=banner.destroy).pack(side="right", padx=10)
        elif duration:
            self.after(duration, banner.destroy)
        
        return banner

    def show_confirmation_banner(self, message, confirm_cmd, type="warning", parent=None):
        """Shows an inline confirmation banner with Yes/Cancel buttons"""
        bg_color = ["#fef9c3", "#713f12"] if type == "warning" else ["#fee2e2", "#7f1d1d"]
        text_color = ["#854d0e", "#fef9c3"] if type == "warning" else ["#991b1b", "#fef2f2"]
        icon = "⚠️" if type == "warning" else "🚪"
        
        banner = ctk.CTkFrame(parent or self, fg_color=bg_color, corner_radius=8)
        banner.pack(fill="x", padx=40, pady=10, before=parent.winfo_children()[1] if parent and len(parent.winfo_children()) > 1 else None)
        
        content = ctk.CTkFrame(banner, fg_color="transparent")
        content.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(content, text=f"{icon}  {message}", font=("Arial", 13, "bold"), text_color=text_color).pack(side="left")
        
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(side="right")
        
        confirm_text = "Yes, Logout" if type == "logout" else "Yes, Proceed"
        ctk.CTkButton(btn_frame, text=confirm_text, height=32, width=120, 
                      fg_color="#8b0000" if type != "warning" else "#1a2a4a", 
                      command=lambda: [banner.destroy(), confirm_cmd()]).pack(side="left", padx=5)
                      
        ctk.CTkButton(btn_frame, text="Cancel", height=32, width=80, 
                      fg_color="transparent", text_color=text_color, border_width=1, border_color=text_color,
                      command=banner.destroy).pack(side="left", padx=5)
        
        return banner

    def load_version(self):
        try:
            if os.path.exists(self.version_file):
                with open(self.version_file, "r") as f:
                    return f.read().strip()
            return "1.0.0"
        except:
            return "1.0.0"

    def get_db_size(self):
        try:
            path = os.path.join(os.getcwd(), "vawc_db.sqlite")
            if os.path.exists(path):
                size = os.path.getsize(path) / (1024 * 1024)
                return f"{size:.2f} MB"
            return "0 MB"
        except: return "Unknown"

    def create_card(self, row, col, icon, title, desc, btn_text, btn_cmd, is_danger=False):
        card = ctk.CTkFrame(self.grid_frame, fg_color=["white", "#242424"], corner_radius=12, border_width=1, border_color=["#e2e8f0", "#333333"])
        card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
        
        ctk.CTkLabel(card, text=icon, font=("Arial", 40)).pack(pady=(25, 10))
        ctk.CTkLabel(card, text=title, font=("Arial", 16, "bold"), text_color=["#0f172a", "#f8fafc"]).pack(pady=5)
        ctk.CTkLabel(card, text=desc, font=("Arial", 12), text_color=["#64748b", "#94a3b8"], wraplength=280).pack(pady=(5, 25), padx=25)
        
        btn_color = "#dc2626" if is_danger else "#1a2a4a"
        btn_hover = "#b91c1c" if is_danger else "#0f1e35"
        
        ctk.CTkButton(card, text=btn_text, command=btn_cmd, fg_color=btn_color, hover_color=btn_hover, 
                      height=40, corner_radius=8, font=("Arial", 13, "bold")).pack(fill="x", side="bottom", padx=25, pady=25)

    def show_audit_logs(self):
        self.main_window.show_audit_logs()

    def setup_cards(self):
        # Clear main content
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        # Row 0: Appearance & User Management
        self.create_card(
            0, 0,
            "🌓", "Appearance Settings",
            "Change application theme between Light and Dark mode.",
            "Change Theme",
            self.show_appearance_settings
        )

        if self.user_role == "Admin":
            self.create_card(
                0, 1,
                "👥", "User Management",
                "Manage system users, reset passwords, and assign roles.",
                "Manage Users",
                self.main_window.show_user_management
            )

            # Row 1: Audit Logs & LGU Config
            self.create_card(
                1, 0,
                "📜", "Audit Logs",
                "View system-wide activity logs and record modifications.",
                "View Audit Logs",
                self.show_audit_logs
            )

            self.create_card(
                1, 1,
                "🏛️", "LGU Configuration",
                f"Barangay: {self.main_window.config['lgu_name']}",
                "Edit Config",
                self.edit_lgu_config
            )

            row_offset = 2
        else:
            # Staff view
            self.create_card(
                0, 1,
                "🏛️", "LGU Configuration",
                f"Barangay: {self.main_window.config['lgu_name']}",
                "Edit Config",
                self.edit_lgu_config
            )
            row_offset = 1

        # Database & Trash
        self.create_card(
            row_offset, 0,
            "🗄️", "Database & Backup",
            f"SQLite DB: vawc_db.sqlite",
            "Backup Settings",
            self.show_db_settings
        )

        self.create_card(
            row_offset, 1,
            "🗑️", "Trash / Deleted Records",
            "View and restore soft-deleted records.",
            "View Trash",
            self.show_deleted_records
        )

        # Update & About
        self.create_card(
            row_offset + 1, 0,
            "🔄", "System Update",
            f"Version: {self.current_version}",
            "Install Update",
            self.install_update
        )

        self.create_card(
            row_offset + 1, 1,
            "📖", "About & RA 9262",
            "Key provisions of RA 9262.",
            "View Details",
            self.show_about
        )

        # Logout
        self.create_card(
            row_offset + 2, 1,
            "🚪", "Logout",
            "Safely end your session.",
            "Logout",
            self.confirm_logout,
            is_danger=True
        )

    def show_appearance_settings(self):
        self.show_panel(AppearancePanel, main_window=self.main_window)

    def edit_lgu_config(self):
        self.show_panel(LGUConfigPanel, main_window=self.main_window)

    def show_db_settings(self):
        self.show_panel(DatabaseSettingsPanel)

    def show_deleted_records(self):
        self.show_panel(DeletedRecordsPanel)

    def show_about(self):
        self.show_panel(AboutPanel, main_window=self.main_window, current_version=self.current_version)

    def install_update(self):
        self.show_panel(UpdatePanel, current_version=self.current_version, settings_frame=self)

    def confirm_logout(self):
        self.show_confirmation_banner("Are you sure you want to logout?", 
                                      self.main_window.logout, 
                                      type="logout", 
                                      parent=self.grid_frame.master.master) # Show at the top of scroll container

class LGUConfigPanel(ctk.CTkFrame):
    def __init__(self, parent, main_window):
        super().__init__(parent, fg_color=["white", "#242424"], corner_radius=15)
        self.main_window = main_window
        self.settings = parent.master # SettingsFrame
        
        ctk.CTkLabel(self, text="LGU Details", font=("Arial", 18, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(pady=(20, 10))
        
        self.fields = {}
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=40)
        
        for key, label in [
            ("lgu_name", "Barangay Name"),
            ("municipality", "Municipality"),
            ("province", "Province"),
            ("region", "Region"),
            ("office_name", "Office Name"),
            ("contact_number", "Contact Number"),
            ("email", "Email Address")
        ]:
            ctk.CTkLabel(form, text=label, font=("Arial", 12), anchor="w").pack(fill="x", pady=(10, 2))
            entry = ctk.CTkEntry(form, height=35)
            entry.insert(0, self.main_window.config.get(key, ""))
            entry.pack(fill="x")
            self.fields[key] = entry
            
        def save():
            from utils.helpers import save_config
            new_config = {k: v.get().strip() for k, v in self.fields.items()}
            if save_config(new_config):
                self.main_window.config = new_config
                self.settings.show_banner("Configuration saved. Please restart the app for all changes to take effect.", parent=self)
            else:
                self.settings.show_banner("Failed to save configuration.", type="error", parent=self)
                
        ctk.CTkButton(self, text="Save Configuration", fg_color="#1a2a4a", command=save, height=45, corner_radius=8).pack(fill="x", padx=40, pady=30)

class DatabaseSettingsPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=["white", "#242424"], corner_radius=15)
        self.settings = parent.master
        
        ctk.CTkLabel(self, text="Database & Backup", font=("Arial", 18, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(pady=(20, 10))
        
        ctk.CTkButton(self, text="📂 Backup Database (.sqlite)", fg_color="#1a2a4a", height=45, corner_radius=8,
                      command=self.backup_db).pack(fill="x", padx=40, pady=10)
        
        ctk.CTkButton(self, text="📜 Export SQL Dump (.sql)", fg_color="#2c3e50", height=45, corner_radius=8,
                      command=self.export_sql).pack(fill="x", padx=40, pady=10)

    def backup_db(self):
        src = os.path.join(os.getcwd(), "vawc_db.sqlite")
        dst = filedialog.asksaveasfilename(defaultextension=".sqlite", initialfile=f"vawc_backup_{datetime.now().strftime('%Y%m%d')}.sqlite")
        if dst:
            try:
                shutil.copy2(src, dst)
                self.settings.show_banner(f"Backup saved to:\n{os.path.basename(dst)}", parent=self)
            except Exception as e:
                self.settings.show_banner(str(e), type="error", parent=self)

    def export_sql(self):
        dst = filedialog.asksaveasfilename(defaultextension=".sql", initialfile=f"vawc_dump_{datetime.now().strftime('%Y%m%d')}.sql")
        if dst:
            try:
                import sqlite3
                conn = sqlite3.connect("vawc_db.sqlite")
                with open(dst, 'w') as f:
                    for line in conn.iterdump():
                        f.write('%s\n' % line)
                conn.close()
                self.settings.show_banner(f"SQL Dump saved to:\n{os.path.basename(dst)}", parent=self)
            except Exception as e:
                self.settings.show_banner(str(e), type="error", parent=self)

class DeletedRecordsPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=["white", "#242424"], corner_radius=15)
        self.settings = parent.master
        
        ctk.CTkLabel(self, text="Soft-Deleted Records", font=("Arial", 18, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(pady=(20, 10))
        
        self.table_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        from tkinter import ttk
        style = ttk.Style()
        # Theme-aware treeview
        tree_bg = "#ffffff" if ctk.get_appearance_mode() == "Light" else "#2b2b2b"
        tree_fg = "#000000" if ctk.get_appearance_mode() == "Light" else "#ffffff"
        style.configure("Trash.Treeview", rowheight=35, background=tree_bg, foreground=tree_fg, fieldbackground=tree_bg)
        
        self.tree = ttk.Treeview(self.table_frame, columns=("VAWC No", "Client Name", "Date Deleted"), show="headings", style="Trash.Treeview")
        self.tree.heading("VAWC No", text="VAWC NO")
        self.tree.heading("Client Name", text="CLIENT NAME")
        self.tree.heading("Date Deleted", text="DATE DELETED")
        self.tree.pack(side="left", fill="both", expand=True)
        
        scrollbar = ctk.CTkScrollbar(self.table_frame, orientation="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
                    
        self.load_trash()
        
        ctk.CTkButton(self, text="♻️ Restore Selected Record", fg_color="#16a34a", height=45, corner_radius=8,
                      command=self.confirm_restore).pack(pady=20, padx=40, fill="x")

    def load_trash(self):
        from db import get_connection
        for item in self.tree.get_children(): self.tree.delete(item)
        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT vawc_no, client_name, updated_at FROM vawc_logs WHERE is_deleted = 1")
            for row in cursor.fetchall():
                self.tree.insert("", "end", values=row)
        finally:
            if connection: connection.close()

    def confirm_restore(self):
        item = self.tree.selection()
        if not item: return
        vawc_no = self.tree.item(item[0], "values")[0]
        self.settings.show_confirmation_banner(f"Are you sure you want to restore record {vawc_no}?", 
                                               lambda: self.restore(vawc_no), parent=self)

    def restore(self, vawc_no):
        from db import get_connection
        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("UPDATE vawc_logs SET is_deleted = 0 WHERE vawc_no = ?", (vawc_no,))
            connection.commit()
            self.load_trash()
            self.settings.show_banner(f"Record {vawc_no} restored successfully.", parent=self)
        except Exception as e:
            self.settings.show_banner(str(e), type="error", parent=self)
        finally:
            if connection: connection.close()

class AboutPanel(ctk.CTkScrollableFrame):
    def __init__(self, parent, main_window, current_version):
        super().__init__(parent, fg_color=["white", "#242424"], corner_radius=15)
        self.main_window = main_window

        ctk.CTkLabel(self, text="VAWC Case Logging System", font=("Arial", 20, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(pady=(0, 5))
        ctk.CTkLabel(self, text=f"Version {current_version}", font=("Arial", 12), text_color=["#666666", "#94a3b8"]).pack()
        
        lgu_text = f"Built for: {self.main_window.config['lgu_name']}\n{self.main_window.config['office_name']}\n{self.main_window.config['municipality']}, {self.main_window.config['province']}"
        ctk.CTkLabel(self, text=lgu_text, font=("Arial", 12, "italic"), justify="center", text_color=["#333333", "#cbd5e1"]).pack(pady=10)

        # RA 9262 Section
        ra_frame = ctk.CTkFrame(self, fg_color=["#f8f9fa", "#1a1a1a"], corner_radius=10)
        ra_frame.pack(fill="x", pady=20, padx=40)
        
        ctk.CTkLabel(ra_frame, text="Republic Act 9262", font=("Arial", 16, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(pady=(15, 10), padx=20, anchor="w")
        ra_text = "RA 9262, also known as the Anti-Violence Against Women and Their Children Act of 2004, defines and criminalizes acts of violence against women and their children committed by their intimate partners such as spouses, former spouses, or any person with whom the woman has or had a sexual or dating relationship."
        ctk.CTkLabel(ra_frame, text=ra_text, font=("Arial", 12), text_color=["#333333", "#cbd5e1"], wraplength=500, justify="left").pack(pady=(0, 15), padx=20)

        # Rights Section
        rights_frame = ctk.CTkFrame(self, fg_color="transparent")
        rights_frame.pack(fill="x", padx=40)
        ctk.CTkLabel(rights_frame, text="Your Rights", font=("Arial", 16, "bold"), text_color="#1a2a4a").pack(pady=10, anchor="w")
        
        rights = [
            "• Right to a Barangay Protection Order (BPO)",
            "• Right to medical assistance and counseling",
            "• Right to legal assistance from the PAO",
            "• Right to be treated with dignity and respect",
            "• Right to confidentiality and privacy"
        ]
        for right in rights:
            ctk.CTkLabel(rights_frame, text=right, font=("Arial", 12), text_color="#333333", anchor="w").pack(padx=10, pady=2, fill="x")

class UpdatePanel(ctk.CTkFrame):
    def __init__(self, parent, current_version, settings_frame):
        super().__init__(parent, fg_color=["white", "#242424"], corner_radius=15)
        self.current_version = current_version
        self.settings = settings_frame
        
        ctk.CTkLabel(self, text="System Update", font=("Arial", 18, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(pady=(20, 10))
        
        info_frame = ctk.CTkFrame(self, fg_color=["#f8f9fa", "#1a1a1a"], corner_radius=10)
        info_frame.pack(fill="x", padx=40, pady=20)
        
        ctk.CTkLabel(info_frame, text=f"Current Version: {self.current_version}", font=("Arial", 14, "bold"), text_color=["#0f172a", "#f8fafc"]).pack(pady=20)
        
        self.status_label = ctk.CTkLabel(self, text="Select an update folder to begin", font=("Arial", 12), text_color=["#64748b", "#94a3b8"])
        self.status_label.pack(pady=10)
        
        ctk.CTkButton(self, text="📂 Select Update Folder", fg_color="#1a2a4a", height=45, corner_radius=8,
                      command=self.select_update).pack(fill="x", padx=40, pady=10)

    def select_update(self):
        update_dir = filedialog.askdirectory(title="Select Update Folder")
        if not update_dir: return

        manifest_path = os.path.join(update_dir, "update_manifest.json")
        if not os.path.exists(manifest_path):
            self.settings.show_banner("Invalid update folder. No update_manifest.json found.", type="error", parent=self)
            return

        try:
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
            
            new_version = manifest.get("version", "0.0.0")
            description = manifest.get("description", "No description provided.")
            files = manifest.get("files", [])

            if self.is_newer(new_version, self.current_version):
                self.status_label.configure(text=f"New Version Available: v{new_version}", text_color="#16a34a")
                self.settings.show_confirmation_banner(f"Update v{new_version} found. Description: {description}. Install now?", 
                                                       lambda: self.perform_update(update_dir, new_version, files), parent=self)
            else:
                self.settings.show_banner(f"No update needed. You are running v{self.current_version}.", parent=self)
        except Exception as e:
            self.settings.show_banner(f"Failed to process update: {str(e)}", type="error", parent=self)

    def is_newer(self, v1, v2):
        try:
            return [int(x) for x in v1.split(".")] > [int(x) for x in v2.split(".")]
        except:
            return False

    def perform_update(self, update_dir, new_version, files, parent=None):
        backup_dir = os.path.join(os.getcwd(), "backup", datetime.now().strftime("%Y_%m_%d_%H%M%S"))
        os.makedirs(backup_dir, exist_ok=True)
        
        copied_files = []
        try:
            # Check if all files are writable before starting
            for rel_path in files:
                dst_path = os.path.join(os.getcwd(), rel_path)
                if os.path.exists(dst_path):
                    if not os.access(dst_path, os.W_OK):
                        raise Exception(f"File is locked or not writable: {rel_path}. Please close any other programs using it.")

            # Backup
            for rel_path in files:
                src_path = os.path.join(os.getcwd(), rel_path)
                if os.path.exists(src_path):
                    dst_path = os.path.join(backup_dir, rel_path)
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    shutil.copy2(src_path, dst_path)

            # Copy New Files with a small delay for stability
            for rel_path in files:
                src_path = os.path.join(update_dir, rel_path)
                dst_path = os.path.join(os.getcwd(), rel_path)
                
                if not os.path.exists(src_path):
                    raise Exception(f"Update file missing in source: {rel_path}")
                
                # If file exists, try to rename it first (safer than direct overwrite)
                temp_path = None
                if os.path.exists(dst_path):
                    temp_path = dst_path + ".old"
                    try:
                        if os.path.exists(temp_path): os.remove(temp_path)
                        os.rename(dst_path, temp_path)
                    except:
                        pass # If rename fails, we'll try direct copy
                
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                shutil.copy2(src_path, dst_path)
                
                # Cleanup temp file
                if temp_path and os.path.exists(temp_path):
                    try: os.remove(temp_path)
                    except: pass
                    
                copied_files.append(rel_path)

            # Update version file
            with open(self.version_file, "w") as f:
                f.write(new_version)

            # Show inline success with restart option
            self.show_confirmation_banner("Update installed successfully. Restart the application to apply changes?", 
                                           self.restart_app, type="warning", parent=parent)

        except Exception as e:
            # Restore from backup
            for rel_path in copied_files:
                backup_file = os.path.join(backup_dir, rel_path)
                original_file = os.path.join(os.getcwd(), rel_path)
                if os.path.exists(backup_file):
                    try:
                        os.makedirs(os.path.dirname(original_file), exist_ok=True)
                        shutil.copy2(backup_file, original_file)
                    except:
                        pass
            
            self.settings.show_banner(f"Update failed: {str(e)}. Previous version restored.", type="error", parent=parent)

    def confirm_logout(self):
        self.settings.show_confirmation_banner("Are you sure you want to logout?", 
                                              self.main_window.logout, 
                                              type="logout", 
                                              parent=self)

    def restart_app(self):
        try:
            python = sys.executable
            os.execl(python, python, *sys.argv)
        except Exception as e:
            # Fallback for some environments
            subprocess.Popen([sys.executable, "main.py"])
            sys.exit()

class AppearancePanel(ctk.CTkFrame):
    def __init__(self, parent, main_window):
        super().__init__(parent, fg_color=["white", "#242424"], corner_radius=15)
        self.main_window = main_window
        self.settings = parent.master
        
        ctk.CTkLabel(self, text="Appearance Settings", font=("Arial", 18, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(pady=(20, 10))
        
        container = ctk.CTkFrame(self, fg_color=["#f8fafc", "#1a1a1a"], corner_radius=10)
        container.pack(fill="x", padx=40, pady=20)
        
        ctk.CTkLabel(container, text="Theme Mode", font=("Arial", 14, "bold"), text_color=["#0f172a", "#f8fafc"]).pack(side="left", padx=20, pady=20)
        
        self.appearance_var = ctk.StringVar(value=self.main_window.config.get("appearance_mode", "light").capitalize())
        self.mode_switch = ctk.CTkOptionMenu(container, values=["Light", "Dark", "System"], variable=self.appearance_var, command=self.change_appearance)
        self.mode_switch.pack(side="right", padx=20)

    def change_appearance(self, new_mode):
        mode = new_mode.lower()
        ctk.set_appearance_mode(mode)
        
        # Save to config
        from utils.helpers import save_config
        self.main_window.config["appearance_mode"] = mode
        save_config(self.main_window.config)
        
        # Use parent reference correctly to find show_banner
        settings_frame = self.master
        while settings_frame and not hasattr(settings_frame, 'show_banner'):
            settings_frame = settings_frame.master
            
        if settings_frame:
            settings_frame.show_banner(f"Theme changed to {new_mode}.", parent=self)
        
        # Refresh all frames to apply theme changes immediately
        self.main_window.refresh_all_frames()
