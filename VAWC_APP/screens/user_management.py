import customtkinter as ctk
from tkinter import ttk, messagebox
from db import get_connection
import bcrypt
from .screen_header import ScreenHeader

class UserManagementFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#f5f5f5")

        ScreenHeader(self, "User Management").pack(fill="x")

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
        # Simple popup for add user
        dialog = ctk.CTkInputDialog(text="Enter username:", title="Add User")
        username = dialog.get_input()
        if not username:
            return
        dialog = ctk.CTkInputDialog(text="Enter full name:", title="Add User")
        full_name = dialog.get_input()
        dialog = ctk.CTkInputDialog(text="Enter password:", title="Add User")
        password = dialog.get_input()
        dialog = ctk.CTkInputDialog(text="Enter role (Admin/Staff):", title="Add User")
        role = dialog.get_input()
        if role not in ["Admin", "Staff"]:
            role = "Staff"
        try:
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)", (username, hashed.decode('utf-8'), full_name, role))
            connection.commit()
            cursor.close()
            connection.close()
            self.load_users()
        except Exception as e:
            messagebox.showerror("Error", str(e))

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
                self.load_users()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def change_password(self):
        item = self.tree.selection()
        if not item:
            return
        username = self.tree.item(item[0], "values")[0]
        dialog = ctk.CTkInputDialog(text="Enter new password:", title="Change Password")
        password = dialog.get_input()
        try:
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (hashed.decode('utf-8'), username))
            connection.commit()
            cursor.close()
            connection.close()
            messagebox.showinfo("Success", "Password changed.")
        except Exception as e:
            messagebox.showerror("Error", str(e))