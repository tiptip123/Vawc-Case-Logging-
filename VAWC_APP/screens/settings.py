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
        super().__init__(parent, fg_color="#f5f5f5")
        self.user_role = user_role
        self.main_window = main_window
        self.version_file = os.path.join(os.getcwd(), "version.txt")
        self.current_version = self.load_version()

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(30, 20))
        ctk.CTkLabel(header, text="⚙ System Settings", font=("Arial", 24, "bold"), text_color="#1a2a4a").pack(side="left")

        # Scrollable area for cards
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Responsive Grid Layout
        self.grid_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        self.grid_frame.pack(fill="x", padx=20)
        self.grid_frame.grid_columnconfigure((0, 1), weight=1, pad=20)

        self.setup_cards()

    def load_version(self):
        try:
            if os.path.exists(self.version_file):
                with open(self.version_file, "r") as f:
                    return f.read().strip()
            return "1.0.0"
        except:
            return "1.0.0"

    def setup_cards(self):
        # Card 1: User Management (Only for Admin)
        if self.user_role == "Admin":
            self.create_card(
                0, 0,
                "👥", "User Management",
                "Manage system users, roles, and access permissions.",
                "Open User Management",
                self.main_window.show_user_management,
                "#1a2a4a"
            )

            # Card 5: Audit Logs (Only for Admin)
            self.create_card(
                0, 1,
                "📜", "Audit Logs",
                "View system-wide activity, login history, and record changes.",
                "View Audit Logs",
                self.show_audit_logs,
                "#1a2a4a"
            )

        # Card 2: System Update
        update_info = f"Current Version: {self.current_version}"
        row_idx = 1 if self.user_role == "Admin" else 0
        self.create_card(
            row_idx, 0,
            "🔄", "System Update",
            f"Install updates from a local folder on this computer.\n{update_info}",
            "Install Update",
            self.install_update,
            "#1a2a4a"
        )

        # Card 3: About System
        self.create_card(
            row_idx, 1,
            "📖", "About VAWC System",
            "Learn about the VAWC Case Logging System and the law that protects women and children.",
            "View Details",
            self.show_about,
            "#1a2a4a"
        )

        # Card 4: Logout
        self.create_card(
            row_idx + 1, 0,
            "🚪", "Logout",
            "Sign out of the system safely.",
            "Logout Now",
            self.confirm_logout,
            "#8b0000" # Dark Red/Maroon
        )

    def show_audit_logs(self):
        self.main_window.show_audit_logs()

    def create_card(self, row, col, icon, title, desc, btn_text, btn_cmd, btn_color):
        card = ctk.CTkFrame(self.grid_frame, fg_color="white", corner_radius=15, border_width=1, border_color="#e0e0e0")
        card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        # Icon
        ctk.CTkLabel(card, text=icon, font=("Arial", 48)).pack(pady=(24, 10))

        # Title
        ctk.CTkLabel(card, text=title, font=("Arial", 18, "bold"), text_color="#1a2a4a").pack(pady=5)

        # Description
        ctk.CTkLabel(card, text=desc, font=("Arial", 12), text_color="#666666", wraplength=250).pack(pady=(5, 20), padx=24)

        # Button
        btn = ctk.CTkButton(card, text=btn_text, command=btn_cmd, fg_color=btn_color, hover_color="#337ab7" if btn_color != "#8b0000" else "#a00000", height=40, font=("Arial", 13, "bold"))
        btn.pack(fill="x", side="bottom", padx=24, pady=24)

    def confirm_logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.main_window.logout()

    def show_about(self):
        about_win = ctk.CTkToplevel(self)
        about_win.title("About VAWC System")
        about_win.geometry("600x500")
        about_win.grab_set()

        scroll = ctk.CTkScrollableFrame(about_win, fg_color="white")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(scroll, text="VAWC Case Logging System", font=("Arial", 20, "bold"), text_color="#1a2a4a").pack(pady=(0, 5))
        ctk.CTkLabel(scroll, text=f"Version {self.current_version}", font=("Arial", 12), text_color="#666666").pack()
        ctk.CTkLabel(scroll, text="Built for: Barangay Tankulan, Manolo Fortich, Bukidnon", font=("Arial", 12, "italic")).pack(pady=10)

        # RA 9262 Section
        ra_frame = ctk.CTkFrame(scroll, fg_color="#f8f9fa", corner_radius=10)
        ra_frame.pack(fill="x", pady=20, padx=10)
        
        ctk.CTkLabel(ra_frame, text="Republic Act 9262", font=("Arial", 16, "bold"), text_color="#1a2a4a").pack(pady=(15, 10), padx=20, anchor="w")
        ra_text = "RA 9262, also known as the Anti-Violence Against Women and Their Children Act of 2004, defines and criminalizes acts of violence against women and their children committed by their intimate partners such as spouses, former spouses, or any person with whom the woman has or had a sexual or dating relationship."
        ctk.CTkLabel(ra_frame, text=ra_text, font=("Arial", 12), text_color="#333333", wraplength=500, justify="left").pack(pady=(0, 15), padx=20)

        # Rights Section
        rights_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        rights_frame.pack(fill="x", padx=10)
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

        ctk.CTkButton(scroll, text="Close", command=about_win.destroy, fg_color="#1a2a4a", width=100).pack(pady=30)

    def install_update(self):
        update_dir = filedialog.askdirectory(title="Select Update Folder")
        if not update_dir:
            return

        manifest_path = os.path.join(update_dir, "update_manifest.json")
        if not os.path.exists(manifest_path):
            messagebox.showerror("Error", "Invalid update folder. No update_manifest.json found. Please select a valid update package.")
            return

        try:
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
            
            new_version = manifest.get("version", "0.0.0")
            description = manifest.get("description", "No description provided.")
            files_to_update = manifest.get("files", [])

            if self.is_newer(new_version, self.current_version):
                if messagebox.askyesno("Update Found", f"Update v{new_version} found.\n\nDescription: {description}\n\nDo you want to install it now?"):
                    self.perform_update(update_dir, new_version, files_to_update)
            else:
                messagebox.showinfo("No Update Needed", f"No update needed. The selected folder contains version {new_version} but you are already running version {self.current_version} or newer.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process update: {str(e)}")

    def is_newer(self, v1, v2):
        try:
            return [int(x) for x in v1.split(".")] > [int(x) for x in v2.split(".")]
        except:
            return False

    def perform_update(self, update_dir, new_version, files):
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

            if messagebox.askyesno("Success", "Update installed successfully. Please restart the application to apply changes.\n\nRestart Now?"):
                self.restart_app()

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
            
            messagebox.showerror("Update Failed", f"Update failed: {str(e)}\n\nYour previous version has been restored as much as possible.")

    def restart_app(self):
        try:
            python = sys.executable
            os.execl(python, python, *sys.argv)
        except Exception as e:
            # Fallback for some environments
            subprocess.Popen([sys.executable, "main.py"])
            sys.exit()
