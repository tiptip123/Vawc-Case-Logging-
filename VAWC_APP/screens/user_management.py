import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from db import get_connection
from utils.helpers import make_circle_image
import base64
import io
from PIL import Image, ImageTk, ImageDraw
import bcrypt

class UserManagementFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.setup_ui()

    def setup_ui(self):
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()

        # Stats Cards
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=20, pady=(20, 10))
        self.stats_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.load_user_stats()
        self.create_stat_card(self.stats_frame, 0, 0, "Total Users", str(self.total_users), "#2563eb", "👥")
        self.create_stat_card(self.stats_frame, 0, 1, "Admins", str(self.admin_count), "#8b0000", "🛡️")
        self.create_stat_card(self.stats_frame, 0, 2, "Staff", str(self.staff_count), "#1e3a5f", "👤")

        # User Table Card
        table_card = ctk.CTkFrame(self, fg_color=["white", "#242424"], corner_radius=12, border_width=1, border_color=["#e2e8f0", "#333333"])
        table_card.pack(fill="both", expand=True, padx=20, pady=10)

        # Toolbar
        toolbar = ctk.CTkFrame(table_card, fg_color="transparent", height=60)
        toolbar.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(toolbar, text="➕ Add New User", fg_color="#1a2a4a", hover_color="#0f1e35", 
                      height=38, corner_radius=8, font=("Arial", 13, "bold"), command=self.add_user).pack(side="left")
        
        btn_actions = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_actions.pack(side="right")
        
        ctk.CTkButton(btn_actions, text="📝 Edit User", fg_color="transparent", text_color=["#2563eb", "#60a5fa"], 
                      border_width=1, border_color=["#e2e8f0", "#333333"], height=38, corner_radius=8, command=self.edit_user).pack(side="left", padx=5)
        
        ctk.CTkButton(btn_actions, text="🗑 Delete", fg_color="transparent", text_color="#dc2626", 
                      border_width=1, border_color=["#fecaca", "#991b1b"], height=38, corner_radius=8, command=self.delete_user).pack(side="left", padx=5)

        # Main Table Area
        self.container = ctk.CTkFrame(table_card, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        self.show_table_view()

    def show_table_view(self):
        for widget in self.container.winfo_children(): widget.destroy()

        # Treeview (Professional Style)
        table_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        is_dark = ctk.get_appearance_mode() == "Dark"

        style = ttk.Style()
        tree_bg = "#ffffff" if ctk.get_appearance_mode() == "Light" else "#2b2b2b"
        tree_fg = "#000000" if ctk.get_appearance_mode() == "Light" else "#ffffff"
        style.configure("User.Treeview", background=tree_bg, foreground=tree_fg, rowheight=40, fieldbackground=tree_bg, font=("Arial", 11), borderwidth=0)
        style.map("User.Treeview", background=[("selected", "#1a2a4a")], foreground=[("selected", "#ffffff")])

        # Heading configuration
        heading_bg = "#f1f5f9" if not is_dark else "#1a1a1a"
        style.configure("User.Treeview.Heading", background=heading_bg, foreground=tree_fg, font=("Arial", 11, "bold"), borderwidth=0)

        self.tree = ttk.Treeview(table_frame, columns=("Username", "Full Name", "Role", "Status"), show="headings", selectmode="browse", style="User.Treeview")

        self.tree.heading("Username", text="USERNAME")
        self.tree.heading("Full Name", text="FULL NAME")
        self.tree.heading("Role", text="ROLE")
        # Configure tags with single strings
        self.tree.tag_configure("evenrow", background="#242424" if is_dark else "#ffffff", foreground="#ffffff" if is_dark else "#000000")
        self.tree.tag_configure("oddrow", background="#1e1e1e" if is_dark else "#f8fafc", foreground="#ffffff" if is_dark else "#000000")

        for col in self.tree["columns"]:
            self.tree.column(col, anchor="w", width=200)

        # Custom Scrollbar
        scrollbar = ctk.CTkScrollbar(table_frame, orientation="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.load_users()

    def create_stat_card(self, parent, row, col, label, value, color, icon):
        card = ctk.CTkFrame(parent, fg_color=["white", "#242424"], corner_radius=12, border_width=1, border_color=["#e2e8f0", "#333333"])
        card.grid(row=row, column=col, padx=10, pady=5, sticky="nsew")
        
        accent = ctk.CTkFrame(card, width=4, fg_color=color, corner_radius=2)
        accent.place(relx=0, rely=0.2, relheight=0.6)
        
        ctk.CTkLabel(card, text=icon, font=("Arial", 20)).place(relx=0.9, rely=0.2, anchor="center")
        ctk.CTkLabel(card, text=label, font=("Arial", 12), text_color=["#64748b", "#94a3b8"]).pack(pady=(20, 0), padx=20, anchor="w")
        ctk.CTkLabel(card, text=value, font=("Arial", 24, "bold"), text_color=["#0f172a", "#f8fafc"]).pack(pady=(5, 20), padx=20, anchor="w")

    def refresh(self):
        """Refresh user management data and UI"""
        self.setup_ui()

    def load_user_stats(self):
        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()

            # Total users
            cursor.execute("SELECT COUNT(*) FROM users")
            self.total_users = cursor.fetchone()[0]

            # Admin count
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'Admin'")
            self.admin_count = cursor.fetchone()[0]

            # Staff count
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'Staff'")
            self.staff_count = cursor.fetchone()[0]
        except Exception:
            self.total_users = 0
            self.admin_count = 0
            self.staff_count = 0
        finally:
            if connection:
                connection.close()

    def load_users(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT username, full_name, role FROM users")
            rows = cursor.fetchall()

            # Alternating row colors
            for i, row in enumerate(rows):
                tag = "evenrow" if i % 2 == 0 else "oddrow"
                self.tree.insert("", "end", values=row + ("Active",), tags=(tag,))

            # Tag configuration moved to show_table_view to handle themes correctly
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            if connection:
                connection.close()

    def add_user(self):
        for widget in self.winfo_children(): widget.destroy()
        AddUserPanel(self, on_save=self.setup_ui, on_cancel=self.setup_ui)

    def delete_user(self):
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Warning", "Please select a user to delete.")
            return
        username = self.tree.item(item[0], "values")[0]
        
        # Security: Prevent deleting protected users or own account
        if username == "admin":
             messagebox.showerror("Restricted", "The default admin account cannot be deleted.")
             return

        # Use SettingsFrame for inline confirmation if available
        settings = self.winfo_toplevel().current_frame
        if hasattr(settings, 'show_confirmation_banner'):
            settings.show_confirmation_banner(f"Are you sure you want to delete user {username}?", 
                                               lambda: self.do_delete(username))
        else:
            if messagebox.askyesno("Confirm", f"Delete user {username}?"):
                self.do_delete(username)

    def do_delete(self, username):
        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))
            connection.commit()
            
            settings = self.winfo_toplevel().current_frame
            if hasattr(settings, 'show_banner'):
                settings.show_banner(f"User {username} deleted successfully.", "success", parent=self)
            else:
                messagebox.showinfo("Success", f"User {username} deleted.")
                
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            if connection:
                connection.close()

    def edit_user(self):
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Warning", "Please select a user to edit.")
            return
        username = self.tree.item(item[0], "values")[0]
        
        # Switch to inline edit panel
        for widget in self.winfo_children(): widget.destroy()
        EditUserPanel(self, username, on_cancel=self.setup_ui, on_save=self.setup_ui)

class EditUserPanel(ctk.CTkScrollableFrame):
    def __init__(self, parent, username, on_cancel, on_save):
        super().__init__(parent, fg_color="transparent")
        self.target_username = username
        self.on_cancel = on_cancel
        self.on_save = on_save
        self.profile_pic_base64 = None
        self.pack(fill="both", expand=True)
        
        # Add a local back button for User Management
        ctk.CTkButton(self, text="← Back to User List", command=self.on_cancel, 
                      fg_color="transparent", text_color=["#1a2a4a", "#cbd5e1"], hover_color=["#eeeeee", "#333333"],
                      font=("Arial", 12, "bold"), width=140).pack(anchor="w", padx=40, pady=(20, 0))

        self.user_data = self.load_user_data()
        if not self.user_data:
            self.on_cancel()
            return
            
        self.setup_ui()

    def load_user_data(self):
        import sqlite3
        connection = None
        try:
            connection = get_connection()
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (self.target_username,))
            return cursor.fetchone()
        finally:
            if connection: connection.close()

    def setup_ui(self):
        # Two-column layout in a more compact container
        container = ctk.CTkFrame(self, fg_color=["white", "#242424"], corner_radius=15, border_width=1, border_color=["#e2e8f0", "#333333"])
        container.pack(fill="x", padx=40, pady=20)
        
        container.grid_columnconfigure(0, weight=1) # Left: Profile
        container.grid_columnconfigure(1, weight=1) # Right: Security
        
        # Left Section: Profile
        left_sec = ctk.CTkFrame(container, fg_color="transparent")
        left_sec.grid(row=0, column=0, padx=40, pady=30, sticky="nsew")
        
        ctk.CTkLabel(left_sec, text="👤 Profile Settings", font=("Arial", 16, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(anchor="w", pady=(0, 20))
        
        # Avatar Preview (Circular 128x128)
        self.avatar_size = 128
        self.avatar_frame = ctk.CTkFrame(left_sec, width=self.avatar_size, height=self.avatar_size, corner_radius=self.avatar_size//2, fg_color=["#f1f5f9", "#1a1a1a"])
        self.avatar_frame.pack(pady=10)
        self.avatar_frame.pack_propagate(False)
        
        self.avatar_label = ctk.CTkLabel(self.avatar_frame, text="")
        self.avatar_label.place(relx=0.5, rely=0.5, anchor="center")

        # Load existing pic
        self.profile_pic_base64 = self.user_data['profile_picture'] # profile_picture column (base64 string)
        self.refresh_avatar_display()

        # Change Photo Button
        ctk.CTkButton(left_sec, text="📷 Change Photo", fg_color="#1a2a4a", hover_color="#0f1e35", height=32, width=140, corner_radius=8, command=self.upload_pic).pack(pady=10)

        # Fields
        ctk.CTkLabel(left_sec, text="Full Name *", font=("Arial", 11, "bold"), anchor="w").pack(fill="x", pady=(15, 2))
        self.entry_fullname = ctk.CTkEntry(left_sec, height=40, placeholder_text="Enter full name")
        self.entry_fullname.insert(0, self.user_data['full_name'] or "")
        self.entry_fullname.pack(fill="x")

        ctk.CTkLabel(left_sec, text="Username *", font=("Arial", 11, "bold"), anchor="w").pack(fill="x", pady=(15, 2))
        self.entry_username = ctk.CTkEntry(left_sec, height=40, placeholder_text="Enter username")
        self.entry_username.insert(0, self.user_data['username'])
        self.entry_username.pack(fill="x")

        # Right Section: Security
        right_sec = ctk.CTkFrame(container, fg_color="transparent")
        right_sec.grid(row=0, column=1, padx=40, pady=30, sticky="nsew")
        
        ctk.CTkLabel(right_sec, text="🔒 Security Settings", font=("Arial", 16, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(anchor="w", pady=(0, 20))

        # Password (Optional)
        ctk.CTkLabel(right_sec, text="New Password (Leave blank to keep current)", font=("Arial", 11, "bold"), anchor="w").pack(fill="x", pady=(0, 2))
        self.entry_pass = ctk.CTkEntry(right_sec, height=40, show="*", placeholder_text="Enter new password")
        self.entry_pass.pack(fill="x")

        self.entry_confirm = ctk.CTkEntry(right_sec, height=40, show="*", placeholder_text="Confirm new password")
        self.entry_confirm.pack(fill="x", pady=10)

        # Passcode
        ctk.CTkLabel(right_sec, text="6-Digit Recovery Passcode (Optional)", font=("Arial", 11, "bold"), anchor="w").pack(fill="x", pady=(15, 2))
        self.entry_passcode = ctk.CTkEntry(right_sec, height=40, placeholder_text="e.g. 123456")
        self.entry_passcode.pack(fill="x")

        # Security Question
        ctk.CTkLabel(right_sec, text="Security Question", font=("Arial", 11, "bold"), anchor="w").pack(fill="x", pady=(15, 2))
        self.questions = [
            "What is the name of your elementary school?",
            "What is your mother's maiden name?",
            "What was your first pet's name?",
            "In what city were you born?",
            "What is your favorite book?"
        ]
        self.sec_var = ctk.StringVar(value=self.user_data['security_question'] or self.questions[0])
        self.sec_combo = ctk.CTkComboBox(right_sec, values=self.questions, variable=self.sec_var, height=40)
        self.sec_combo.pack(fill="x")

        self.entry_answer = ctk.CTkEntry(right_sec, height=40, placeholder_text="Security Answer (Optional)")
        self.entry_answer.pack(fill="x", pady=10)

        # Footer Actions
        footer = ctk.CTkFrame(container, fg_color="transparent")
        footer.grid(row=1, column=0, columnspan=2, pady=20, sticky="ew")
        footer.grid_columnconfigure((0, 1), weight=1)
        
        ctk.CTkButton(footer, text="Save Changes", fg_color="#1a2a4a", hover_color="#0f1e35", height=42, corner_radius=8, font=("Arial", 13, "bold"), command=self.save).pack(side="left", fill="x", expand=True, padx=10)
        ctk.CTkButton(footer, text="Cancel", fg_color="transparent", text_color=["#64748b", "#94a3b8"], border_width=1, border_color=["#e2e8f0", "#333333"], height=42, corner_radius=8, command=self.on_cancel).pack(side="left", fill="x", expand=True, padx=10)

    def upload_pic(self):
        file_path = filedialog.askopenfilename(
            title="Choose Profile Picture",
            filetypes=[
                ("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("All Files", "*.*")
            ]
        )
        if not file_path:
            return
            
        try:
            # Open, resize, and convert to base64
            img = Image.open(file_path).convert("RGBA")
            # Create square crop first
            w, h = img.size
            min_dim = min(w, h)
            left = (w - min_dim)/2
            top = (h - min_dim)/2
            right = (w + min_dim)/2
            bottom = (h + min_dim)/2
            img = img.crop((left, top, right, bottom)).resize((256, 256), Image.Resampling.LANCZOS)
            
            # Save to base64 string
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            self.profile_pic_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            
            # Refresh preview
            self.refresh_avatar_display()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process image: {e}")

    def refresh_avatar_display(self):
        # Clear existing
        for w in self.avatar_frame.winfo_children(): w.destroy()
        
        self.avatar_img = make_circle_image(self.profile_pic_base64, size=self.avatar_size)
        
        if self.avatar_img:
            ctk.CTkLabel(self.avatar_frame, image=self.avatar_img, text="").place(relx=0.5, rely=0.5, anchor="center")
        else:
            # Initials placeholder
            fullname = self.entry_fullname.get().strip() or self.target_username
            initial = fullname[0].upper() if fullname else "?"
            ctk.CTkLabel(self.avatar_frame, text=initial, font=("Arial", 32, "bold"), text_color=["#1a2a4a", "#f8fafc"]).place(relx=0.5, rely=0.5, anchor="center")

    def save(self):
        fullname = self.entry_fullname.get().strip()
        username = self.entry_username.get().strip()
        new_pass = self.entry_pass.get().strip()
        confirm = self.entry_confirm.get().strip()
        passcode = self.entry_passcode.get().strip()
        sec_q = self.sec_var.get()
        sec_a = self.entry_answer.get().strip()

        if not fullname or not username:
            messagebox.showwarning("Error", "Full Name and Username are required.")
            return

        # Password validation if changed
        if new_pass:
            if new_pass != confirm:
                messagebox.showerror("Error", "Passwords do not match.")
                return
            if len(new_pass) < 8 or not any(c.isupper() for c in new_pass) or not any(c.isdigit() for c in new_pass):
                messagebox.showerror("Security", "Password must be 8+ chars with uppercase and number.")
                return

        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()
            
            # Check username uniqueness if changed
            if username != self.target_username:
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                if cursor.fetchone():
                    messagebox.showerror("Error", "Username already taken.")
                    return

            # Update basic info
            cursor.execute("""
                UPDATE users 
                SET full_name = ?, username = ?, profile_picture = ?, security_question = ?
                WHERE username = ?
            """, (fullname, username, self.profile_pic_base64, sec_q, self.target_username))

            # Update password if provided
            if new_pass:
                hashed = bcrypt.hashpw(new_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (hashed, username))

            # Update passcode if provided
            if passcode:
                hashed_pc = bcrypt.hashpw(passcode.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cursor.execute("UPDATE users SET passcode = ? WHERE username = ?", (hashed_pc, username))

            # Update security answer if provided
            if sec_a:
                hashed_sa = bcrypt.hashpw(sec_a.lower().encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cursor.execute("UPDATE users SET security_answer = ? WHERE username = ?", (hashed_sa, username))

            connection.commit()
            
            # Show inline success message instead of messagebox
            # We'll need to reach back to SettingsFrame for show_banner
            settings = self.winfo_toplevel().current_frame
            if hasattr(settings, 'show_banner'):
                settings.show_banner(f"User {username} updated successfully.", "success", parent=self)
            else:
                messagebox.showinfo("Success", f"User {username} updated successfully.")
            
            # Update sidebar if editing own profile
            main_window = self.winfo_toplevel()
            if hasattr(main_window, 'setup_sidebar_user_info') and self.target_username == main_window.username:
                main_window.username = username # Update current username reference
                main_window.setup_sidebar_user_info()

            self.on_save()
            self.on_cancel() # Return to list after save
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            if connection: connection.close()

class ResetPasswordDialog(ctk.CTkToplevel):
    def __init__(self, parent, target_username, on_save):
        super().__init__(parent)
        self.title("Reset User Password")
        self.geometry("450x450")
        self.target_username = target_username
        self.on_save = on_save
        self.user_data = self.load_user_data()
        self.grab_set()
        self.resizable(False, False)
        
        self.configure(fg_color=["#f8fafc", "#1a1a1a"])
        
        # Container
        self.container = ctk.CTkFrame(self, fg_color=["white", "#242424"], corner_radius=15, border_width=1, border_color=["#e2e8f0", "#333333"])
        self.container.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.show_verification_step()

    def load_user_data(self):
        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (self.target_username,))
            data = cursor.fetchone()
            return data
        except: return None
        finally:
            if connection:
                connection.close()

    def show_verification_step(self):
        for w in self.container.winfo_children(): w.destroy()
        
        ctk.CTkLabel(self.container, text=f"Verify to Reset: {self.target_username}", font=("Arial", 16, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(pady=20)
        
        ctk.CTkLabel(self.container, text="Enter the user's 6-digit passcode:", anchor="w", font=("Arial", 11)).pack(fill="x", padx=40, pady=(10, 2))
        self.entry_verify_pass = ctk.CTkEntry(self.container, height=40, show="*")
        self.entry_verify_pass.pack(fill="x", padx=40, pady=(0, 10))
        
        ctk.CTkButton(self.container, text="Verify Passcode", fg_color="#1a2a4a", command=self.verify_passcode).pack(fill="x", padx=40, pady=10)
        
        ctk.CTkButton(self.container, text="Use Security Question instead", fg_color="transparent", text_color="#1a73e8", font=("Arial", 11), command=self.show_security_step).pack(pady=5)

    def verify_passcode(self):
        entered = self.entry_verify_pass.get().strip()
        stored_hash = self.user_data['passcode']
        
        if stored_hash and bcrypt.checkpw(entered.encode('utf-8'), stored_hash.encode('utf-8')):
            self.show_reset_step()
        else:
            messagebox.showerror("Error", "Incorrect passcode.")

    def show_security_step(self):
        for w in self.container.winfo_children(): w.destroy()
        
        ctk.CTkLabel(self.container, text="Security Verification", font=("Arial", 16, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(pady=20)
        
        question = self.user_data['security_question'] or "No security question set."
        ctk.CTkLabel(self.container, text=question, font=("Arial", 12, "bold"), wraplength=350).pack(pady=10)
        
        self.entry_verify_sec = ctk.CTkEntry(self.container, height=40, placeholder_text="Answer")
        self.entry_verify_sec.pack(fill="x", padx=40, pady=10)
        
        ctk.CTkButton(self.container, text="Verify Answer", fg_color="#1a2a4a", command=self.verify_security).pack(fill="x", padx=40, pady=10)
        
        ctk.CTkButton(self.container, text="← Back", fg_color="transparent", text_color=["#666666", "#94a3b8"], command=self.show_verification_step).pack(pady=5)

    def verify_security(self):
        answer = self.entry_verify_sec.get().strip().lower()
        stored_hash = self.user_data['security_answer']
        if stored_hash and bcrypt.checkpw(answer.encode('utf-8'), stored_hash.encode('utf-8')):
            self.show_reset_step()
        else:
            messagebox.showerror("Error", "Incorrect answer.")

    def show_reset_step(self):
        for w in self.container.winfo_children(): w.destroy()
        
        ctk.CTkLabel(self.container, text="Set New Password", font=("Arial", 16, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(pady=20)
        
        self.entry_new_p1 = ctk.CTkEntry(self.container, height=40, placeholder_text="New Password", show="*")
        self.entry_new_p1.pack(fill="x", padx=40, pady=10)
        
        self.entry_new_p2 = ctk.CTkEntry(self.container, height=40, placeholder_text="Confirm Password", show="*")
        self.entry_new_p2.pack(fill="x", padx=40, pady=10)
        
        ctk.CTkButton(self.container, text="Reset Password", fg_color="#16a34a", command=self.do_reset).pack(fill="x", padx=40, pady=20)

    def do_reset(self):
        p1 = self.entry_new_p1.get()
        p2 = self.entry_new_p2.get()
        if p1 != p2:
            messagebox.showerror("Error", "Passwords do not match.")
            return
            
        try:
            hashed = bcrypt.hashpw(p1.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (hashed, self.target_username))
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Success", f"Password for {self.target_username} has been reset.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))

class AddUserPanel(ctk.CTkFrame):
    def __init__(self, parent, on_save, on_cancel):
        super().__init__(parent, fg_color="transparent")
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.pack(fill="both", expand=True)

        # Back Button
        ctk.CTkButton(self, text="← Back to User List", command=self.on_cancel, 
                      fg_color="transparent", text_color=["#1a2a4a", "#cbd5e1"], hover_color=["#eeeeee", "#333333"],
                      font=("Arial", 12, "bold"), width=140).pack(anchor="w", padx=40, pady=(15, 0))

        # Compact Container
        container = ctk.CTkFrame(self, fg_color=["white", "#242424"], corner_radius=15, border_width=1, border_color=["#e2e8f0", "#333333"])
        container.pack(fill="x", padx=40, pady=15)
        
        # Header
        ctk.CTkLabel(container, text="👤 Create User Account", font=("Arial", 18, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(pady=15)

        # Form Grid
        form_grid = ctk.CTkFrame(container, fg_color="transparent")
        form_grid.pack(fill="x", padx=30, pady=10)
        form_grid.grid_columnconfigure((0, 1), weight=1)
        
        self.entries = {}
        self.error_labels = {}

        self.create_field_grid(form_grid, "Username", "username", 0, 0)
        self.create_field_grid(form_grid, "Full Name", "full_name", 0, 1)
        self.create_field_grid(form_grid, "Password", "password", 1, 0, show="*")
        
        # Passcode
        pc_frame = ctk.CTkFrame(form_grid, fg_color="transparent")
        pc_frame.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(pc_frame, text="6-Digit Passcode *", anchor="w", font=("Arial", 11, "bold")).pack(fill="x")
        self.entry_passcode = ctk.CTkEntry(pc_frame, placeholder_text="e.g. 123456", height=38)
        self.entry_passcode.pack(fill="x", pady=(2, 0))
        self.entries["passcode"] = self.entry_passcode
        self.error_labels["passcode"] = ctk.CTkLabel(pc_frame, text="", text_color="#dc2626", font=("Arial", 10))
        self.error_labels["passcode"].pack(anchor="w")

        # Role
        role_frame = ctk.CTkFrame(form_grid, fg_color="transparent")
        role_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(role_frame, text="Role *", anchor="w", font=("Arial", 11, "bold")).pack(fill="x")
        self.role_var = ctk.StringVar(value="Staff")
        self.role_menu = ctk.CTkOptionMenu(role_frame, values=["Staff", "Admin"], variable=self.role_var, height=38, fg_color="#1a2a4a")
        self.role_menu.pack(fill="x", pady=(2, 0))

        # Security Answer
        self.create_field_grid(form_grid, "Security Answer", "answer", 2, 1)

        # Buttons
        btn_container = ctk.CTkFrame(container, fg_color="transparent")
        btn_container.pack(fill="x", padx=30, pady=25)
        
        ctk.CTkButton(btn_container, text="Create User", fg_color="#1a2a4a", hover_color="#0f1e35", 
                      height=42, corner_radius=8, font=("Arial", 13, "bold"), command=self.save_user).pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(btn_container, text="Cancel", fg_color="transparent", text_color=["#333333", "#cbd5e1"],
                      border_width=1, border_color=["#cccccc", "#555555"], height=42, corner_radius=8, command=self.on_cancel).pack(side="right", fill="x", expand=True)

    def create_field_grid(self, parent, label, attr_name, row, col, show=None):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(frame, text=f"{label} *", anchor="w", font=("Arial", 11, "bold")).pack(fill="x")
        entry = ctk.CTkEntry(frame, placeholder_text=f"Enter {label.lower()}", height=38, show=show)
        entry.pack(fill="x", pady=(2, 0))
        self.entries[attr_name] = entry
        err_label = ctk.CTkLabel(frame, text="", text_color="#dc2626", font=("Arial", 10))
        err_label.pack(anchor="w")
        self.error_labels[attr_name] = err_label

    def save_user(self):
        for key in self.entries:
            self.entries[key].configure(border_color=["#dce4ee", "#333333"])
            self.error_labels[key].configure(text="")

        data = {k: v.get().strip() for k, v in self.entries.items()}
        data['role'] = self.role_var.get()

        has_error = False
        for field in ["username", "full_name", "password", "passcode", "answer"]:
            if not data[field]:
                self.entries[field].configure(border_color="#dc2626")
                self.error_labels[field].configure(text="Required")
                has_error = True

        if has_error: return

        if not data['passcode'].isdigit() or len(data['passcode']) != 6:
            self.entries['passcode'].configure(border_color="#dc2626")
            self.error_labels['passcode'].configure(text="Must be 6 digits")
            return

        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (data['username'],))
            if cursor.fetchone():
                self.entries['username'].configure(border_color="#dc2626")
                self.error_labels['username'].configure(text="Already taken")
                connection.close()
                return

            hashed_pass = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            hashed_pc = bcrypt.hashpw(data['passcode'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            hashed_ans = bcrypt.hashpw(data['answer'].lower().encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role, passcode, security_answer)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (data['username'], hashed_pass, data['full_name'], data['role'], hashed_pc, hashed_ans))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            settings = self.winfo_toplevel().current_frame
            if hasattr(settings, 'show_banner'):
                settings.show_banner(f"User {data['username']} created.", "success", parent=self.master)
            
            self.on_save()
        except Exception as e:
            messagebox.showerror("Error", str(e))
