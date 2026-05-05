import customtkinter as ctk
from tkinter import ttk, messagebox
from db import get_connection
import bcrypt

class UserManagementFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#f5f5f5")
        self.setup_ui()

    def setup_ui(self):
        # Clear existing widgets if any
        for widget in self.winfo_children():
            widget.destroy()

        # Load user statistics
        self.load_user_stats()

        # Statistics Cards
        stats_frame = ctk.CTkFrame(self, fg_color="#f5f5f5")
        stats_frame.pack(fill="x", padx=20, pady=(10, 5))
        stats_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Total Users Card
        total_card = ctk.CTkFrame(stats_frame, fg_color="white", corner_radius=10)
        total_card.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(total_card, text="👥 Total Users", font=("Arial", 14, "bold"), text_color="#1a2a4a").pack(pady=(15, 5))
        ctk.CTkLabel(total_card, text=str(self.total_users), font=("Arial", 24, "bold"), text_color="#8b0000").pack(pady=(0, 15))

        # Admin Users Card
        admin_card = ctk.CTkFrame(stats_frame, fg_color="white", corner_radius=10)
        admin_card.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(admin_card, text="👑 Admin Users", font=("Arial", 14, "bold"), text_color="#1a2a4a").pack(pady=(15, 5))
        ctk.CTkLabel(admin_card, text=str(self.admin_count), font=("Arial", 24, "bold"), text_color="#1a73e8").pack(pady=(0, 15))

        # Staff Users Card
        staff_card = ctk.CTkFrame(stats_frame, fg_color="white", corner_radius=10)
        staff_card.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(staff_card, text="👤 Staff Users", font=("Arial", 14, "bold"), text_color="#1a2a4a").pack(pady=(15, 5))
        ctk.CTkLabel(staff_card, text=str(self.staff_count), font=("Arial", 24, "bold"), text_color="#28a745").pack(pady=(0, 15))

        # Users Table Section
        table_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(5, 10))

        ctk.CTkLabel(table_frame, text="📋 User Accounts", font=("Arial", 16, "bold"), text_color="#1a2a4a").pack(anchor="w", padx=20, pady=(20, 10))

        # STYLE FIX (IMPORTANT)
        style = ttk.Style()
        style.theme_use("default")

        style.configure(
            "Treeview",
            background="#ffffff",
            foreground="#000000",  # FIX: readable text
            rowheight=32,
            fieldbackground="#ffffff",
            font=("Arial", 10)
        )

        style.map(
            "Treeview",
            background=[("selected", "#8b0000")],
            foreground=[("selected", "#ffffff")]
        )

        style.configure(
            "Treeview.Heading",
            background="#1a2a4a",
            foreground="#ffffff",
            font=("Arial", 12, "bold"),
            padding=(10, 5)
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=("Username", "Full Name", "Role"),
            show="headings",
            selectmode="browse"
        )

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=180, anchor="center")

        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(20, 5), pady=(0, 20))
        scrollbar.pack(side="right", fill="y", padx=(5, 20), pady=(0, 20))

        self.load_users()

        # Action Buttons Section
        actions_frame = ctk.CTkFrame(self, fg_color="#f5f5f5")
        actions_frame.pack(fill="x", padx=20, pady=(0, 20))

        # Left side buttons
        left_buttons = ctk.CTkFrame(actions_frame, fg_color="#f5f5f5")
        left_buttons.pack(side="left")

        self.btn_add = ctk.CTkButton(
            left_buttons,
            text="➕ Add User",
            fg_color="#28a745",
            hover_color="#218838",
            command=self.add_user,
            height=40,
            font=("Arial", 11, "bold")
        )
        self.btn_add.pack(side="left", padx=(0, 10), pady=5)

        # Right side buttons
        right_buttons = ctk.CTkFrame(actions_frame, fg_color="#f5f5f5")
        right_buttons.pack(side="right")

        self.btn_change_pass = ctk.CTkButton(
            right_buttons,
            text="🔑 Change Password",
            fg_color="#1a73e8",
            hover_color="#1967d2",
            command=self.change_password,
            height=40,
            font=("Arial", 11, "bold")
        )
        self.btn_change_pass.pack(side="right", padx=(10, 0), pady=5)

        self.btn_delete = ctk.CTkButton(
            right_buttons,
            text="🗑️ Delete User",
            fg_color="#dc3545",
            hover_color="#c82333",
            command=self.delete_user,
            height=40,
            font=("Arial", 11, "bold")
        )
        self.btn_delete.pack(side="right", padx=(10, 0), pady=5)

    def refresh(self):
        """Refresh user management data and UI"""
        self.setup_ui()

    def load_user_stats(self):
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

            cursor.close()
            connection.close()
        except Exception:
            self.total_users = 0
            self.admin_count = 0
            self.staff_count = 0

    def load_users(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT username, full_name, role FROM users")
            rows = cursor.fetchall()

            # Alternating row colors
            for i, row in enumerate(rows):
                tag = "evenrow" if i % 2 == 0 else "oddrow"
                self.tree.insert("", "end", values=row, tags=(tag,))

            self.tree.tag_configure("evenrow", background="#ffffff")
            self.tree.tag_configure("oddrow", background="#eef0f4")

            cursor.close()
            connection.close()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def add_user(self):
        AddUserDialog(self, on_save=self.refresh)

    def delete_user(self):
        item = self.tree.selection()
        if not item:
            return
        username = self.tree.item(item[0], "values")[0]
        if messagebox.askyesno("Confirm", f"Delete user {username}?"):
            try:
                connection = get_connection()
                cursor = connection.cursor()
                cursor.execute("DELETE FROM users WHERE username = ?", (username,))
                connection.commit()
                cursor.close()
                connection.close()
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def change_password(self):
        item = self.tree.selection()
        if not item:
            return
        username = self.tree.item(item[0], "values")[0]
        AdminResetDialog(self, username, on_save=self.refresh)

class AdminResetDialog(ctk.CTkToplevel):
    def __init__(self, parent, target_username, on_save):
        super().__init__(parent)
        self.title("Reset User Password")
        self.geometry("450x400")
        self.target_username = target_username
        self.on_save = on_save
        self.user_data = self.load_user_data()
        self.grab_set()
        self.resizable(False, False)
        
        self.configure(fg_color="#f5f5f5")
        
        # Container
        self.container = ctk.CTkFrame(self, fg_color="white", corner_radius=15)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.show_verification_step()

    def load_user_data(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (self.target_username,))
            data = cursor.fetchone()
            cursor.close()
            conn.close()
            return data
        except: return None

    def show_verification_step(self):
        for w in self.container.winfo_children(): w.destroy()
        
        ctk.CTkLabel(self.container, text=f"Verify to Reset: {self.target_username}", font=("Arial", 16, "bold"), text_color="#1a2a4a").pack(pady=20)
        
        ctk.CTkLabel(self.container, text="Enter the user's 6-digit passcode:", anchor="w", font=("Arial", 11)).pack(fill="x", padx=40, pady=(10, 2))
        self.entry_verify_pass = ctk.CTkEntry(self.container, height=40, show="*")
        self.entry_verify_pass.pack(fill="x", padx=40, pady=(0, 10))
        
        ctk.CTkButton(self.container, text="Verify Passcode", fg_color="#1a2a4a", command=self.verify_passcode).pack(fill="x", padx=40, pady=10)
        
        ctk.CTkButton(self.container, text="Use Security Question instead", fg_color="transparent", text_color="#1a73e8", font=("Arial", 11), command=self.show_security_step).pack(pady=5)

    def verify_passcode(self):
        if self.entry_verify_pass.get() == self.user_data[5]:
            self.show_reset_step()
        else:
            messagebox.showerror("Error", "Incorrect passcode.")

    def show_security_step(self):
        for w in self.container.winfo_children(): w.destroy()
        
        ctk.CTkLabel(self.container, text="Security Verification", font=("Arial", 16, "bold"), text_color="#1a2a4a").pack(pady=20)
        
        question = self.user_data[6] or "No security question set."
        ctk.CTkLabel(self.container, text=question, font=("Arial", 12, "bold"), wraplength=350).pack(pady=10)
        
        self.entry_verify_sec = ctk.CTkEntry(self.container, height=40, placeholder_text="Answer")
        self.entry_verify_sec.pack(fill="x", padx=40, pady=10)
        
        ctk.CTkButton(self.container, text="Verify Answer", fg_color="#1a2a4a", command=self.verify_security).pack(fill="x", padx=40, pady=10)
        
        ctk.CTkButton(self.container, text="← Back", fg_color="transparent", text_color="#666666", command=self.show_verification_step).pack(pady=5)

    def verify_security(self):
        answer = self.entry_verify_sec.get().strip().lower()
        stored_hash = self.user_data[7]
        if stored_hash and bcrypt.checkpw(answer.encode('utf-8'), stored_hash.encode('utf-8')):
            self.show_reset_step()
        else:
            messagebox.showerror("Error", "Incorrect answer.")

    def show_reset_step(self):
        for w in self.container.winfo_children(): w.destroy()
        
        ctk.CTkLabel(self.container, text="Set New Password", font=("Arial", 16, "bold"), text_color="#1a2a4a").pack(pady=20)
        
        self.entry_new_p1 = ctk.CTkEntry(self.container, height=40, placeholder_text="New Password", show="*")
        self.entry_new_p1.pack(fill="x", padx=40, pady=10)
        
        self.entry_new_p2 = ctk.CTkEntry(self.container, height=40, placeholder_text="Confirm Password", show="*")
        self.entry_new_p2.pack(fill="x", padx=40, pady=10)
        
        ctk.CTkButton(self.container, text="Reset Password", fg_color="#28a745", command=self.do_reset).pack(fill="x", padx=40, pady=20)

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

class AddUserDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.title("Add New User")
        self.geometry("500x750")
        self.on_save = on_save
        self.resizable(False, False)
        self.grab_set()

        self.configure(fg_color="#f5f5f5")

        # Container
        container = ctk.CTkFrame(self, fg_color="white", corner_radius=15)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text="👤 Create User Account", font=("Arial", 18, "bold"), text_color="#1a2a4a").pack(pady=20)

        # Fields
        self.create_field(container, "Username", "entry_username")
        self.create_field(container, "Full Name", "entry_full_name")
        self.create_field(container, "Password", "entry_password", show="*")
        
        # Passcode
        ctk.CTkLabel(container, text="Passcode (6-digit numeric)", anchor="w", font=("Arial", 11, "bold")).pack(fill="x", padx=30, pady=(10, 2))
        self.entry_passcode = ctk.CTkEntry(container, placeholder_text="e.g. 123456", height=40)
        self.entry_passcode.pack(fill="x", padx=30, pady=(0, 10))

        # Role
        ctk.CTkLabel(container, text="Role", anchor="w", font=("Arial", 11, "bold")).pack(fill="x", padx=30, pady=(10, 2))
        self.role_var = ctk.StringVar(value="Staff")
        self.role_menu = ctk.CTkOptionMenu(container, values=["Staff", "Admin"], variable=self.role_var, height=40, fg_color="#1a2a4a")
        self.role_menu.pack(fill="x", padx=30, pady=(0, 10))

        # Security Question
        ctk.CTkLabel(container, text="Security Question", anchor="w", font=("Arial", 11, "bold")).pack(fill="x", padx=30, pady=(10, 2))
        self.questions = [
            "What is your favorite food?",
            "What is your mother's maiden name?",
            "What is your pet's name?",
            "What is your best friend's name?",
            "What is the name of your elementary school?"
        ]
        self.question_var = ctk.StringVar(value=self.questions[0])
        self.question_menu = ctk.CTkOptionMenu(container, values=self.questions, variable=self.question_var, height=40, fg_color="#1a2a4a")
        self.question_menu.pack(fill="x", padx=30, pady=(0, 10))

        # Security Answer
        ctk.CTkLabel(container, text="Security Answer", anchor="w", font=("Arial", 11, "bold")).pack(fill="x", padx=30, pady=(10, 2))
        self.entry_answer = ctk.CTkEntry(container, placeholder_text="Your answer here", height=40)
        self.entry_answer.pack(fill="x", padx=30, pady=(0, 20))

        # Buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom", pady=20)

        ctk.CTkButton(btn_frame, text="Cancel", fg_color="#6c757d", hover_color="#5a6268", command=self.destroy, width=120).pack(side="left", padx=(30, 0))
        ctk.CTkButton(btn_frame, text="Create User", fg_color="#28a745", hover_color="#218838", command=self.save_user, width=150).pack(side="right", padx=(0, 30))

    def create_field(self, parent, label, attr_name, show=None):
        ctk.CTkLabel(parent, text=label, anchor="w", font=("Arial", 11, "bold")).pack(fill="x", padx=30, pady=(10, 2))
        entry = ctk.CTkEntry(parent, placeholder_text=f"Enter {label.lower()}", height=40, show=show)
        entry.pack(fill="x", padx=30, pady=(0, 10))
        setattr(self, attr_name, entry)

    def save_user(self):
        username = self.entry_username.get().strip()
        full_name = self.entry_full_name.get().strip()
        password = self.entry_password.get().strip()
        passcode = self.entry_passcode.get().strip()
        role = self.role_var.get()
        question = self.question_var.get()
        answer = self.entry_answer.get().strip().lower()

        if not all([username, full_name, password, passcode, answer]):
            messagebox.showerror("Error", "All fields are required.")
            return

        if not passcode.isdigit() or len(passcode) > 6:
            messagebox.showerror("Error", "Passcode must be numeric and max 6 digits.")
            return

        try:
            hashed_pass = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            hashed_answer = bcrypt.hashpw(answer.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role, passcode, security_question, security_answer)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (username, hashed_pass, full_name, role, passcode, question, hashed_answer))
            connection.commit()
            cursor.close()
            connection.close()
            
            messagebox.showinfo("Success", "User account created successfully.")
            self.on_save()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))