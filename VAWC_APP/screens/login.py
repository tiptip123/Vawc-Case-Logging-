import customtkinter as ctk
from tkinter import messagebox
import os
from PIL import Image
from auth import verify_login
from .main_window import MainWindow

from utils.helpers import load_config

class LoginScreen(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.title(f"VAWC Case Logging System - {self.config['lgu_name']}")
        self.geometry("1000x600")
        self.resizable(False, False)
        
        # Apply theme
        mode = self.config.get("appearance_mode", "light")
        ctk.set_appearance_mode(mode)
        
        self.configure(fg_color=["white", "#1a1a1a"])
        
        # Center the window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (1000 // 2)
        y = (screen_height // 2) - (600 // 2)
        self.geometry(f"1000x600+{x}+{y}")

        # Main container (Split layout)
        self.main_container = ctk.CTkFrame(self, fg_color=["white", "#1a1a1a"], corner_radius=0)
        self.main_container.pack(fill="both", expand=True)

        self.show_login_view()

    def show_login_view(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

        # Left Panel (40%) - Dark Navy
        left_panel = ctk.CTkFrame(self.main_container, width=400, fg_color=["#0f1e35", "#0a1424"], corner_radius=0)
        left_panel.pack(side="left", fill="both")
        left_panel.pack_propagate(False)

        # Center content in left panel
        left_content = ctk.CTkFrame(left_panel, fg_color="transparent")
        left_content.place(relx=0.5, rely=0.5, anchor="center")

        # Shield Logo
        ctk.CTkLabel(left_content, text="🛡️", font=("Arial", 80)).pack(pady=(0, 20))
        
        ctk.CTkLabel(left_content, text="VAWC", font=("Arial", 32, "bold"), text_color="white").pack()
        ctk.CTkLabel(left_content, text="Case Logging System", font=("Arial", 16), text_color="#94a3b8").pack(pady=(0, 40))
        
        ctk.CTkLabel(left_content, text=self.config['lgu_name'], font=("Arial", 14, "bold"), text_color="white").pack()
        ctk.CTkLabel(left_content, text=f"{self.config['municipality']}, {self.config['province']}", font=("Arial", 12), text_color="#94a3b8").pack()

        # Bottom text in left panel
        ctk.CTkFrame(left_panel, height=1, fg_color="#1e3a5f", width=300).place(relx=0.5, rely=0.9, anchor="center")
        ctk.CTkLabel(left_panel, text="Republic of the Philippines", font=("Arial", 10), text_color="#64748b").place(relx=0.5, rely=0.93, anchor="center")

        # Right Panel (60%)
        right_panel = ctk.CTkFrame(self.main_container, fg_color=["#f8fafc", "#1a1a1a"], corner_radius=0)
        right_panel.pack(side="right", fill="both", expand=True)

        # Login Card
        login_card = ctk.CTkFrame(right_panel, fg_color=["white", "#242424"], width=400, height=450, corner_radius=15, border_width=1, border_color=["#e2e8f0", "#333333"])
        login_card.place(relx=0.5, rely=0.5, anchor="center")
        login_card.pack_propagate(False)

        ctk.CTkLabel(login_card, text="Welcome back", font=("Arial", 24, "bold"), text_color=["#0f172a", "#f8fafc"]).pack(pady=(40, 5))
        ctk.CTkLabel(login_card, text="Please enter your details", font=("Arial", 14), text_color=["#64748b", "#94a3b8"]).pack(pady=(0, 30))

        # Form
        form_inner = ctk.CTkFrame(login_card, fg_color="transparent")
        form_inner.pack(fill="both", expand=True, padx=40)

        ctk.CTkLabel(form_inner, text="Username", font=("Arial", 12, "bold"), text_color=["#0f172a", "#f8fafc"], anchor="w").pack(fill="x", pady=(0, 5))
        self.entry_username = ctk.CTkEntry(form_inner, placeholder_text="Enter your username", height=45, corner_radius=8, border_width=1, border_color=["#e2e8f0", "#333333"], fg_color=["white", "#1a1a1a"], text_color=["#0f172a", "#f8fafc"])
        self.entry_username.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(form_inner, text="Password", font=("Arial", 12, "bold"), text_color=["#0f172a", "#f8fafc"], anchor="w").pack(fill="x", pady=(0, 5))
        self.entry_password = ctk.CTkEntry(form_inner, placeholder_text="Enter your password", show="*", height=45, corner_radius=8, border_width=1, border_color=["#e2e8f0", "#333333"], fg_color=["white", "#1a1a1a"], text_color=["#0f172a", "#f8fafc"])
        self.entry_password.pack(fill="x", pady=(0, 25))

        self.btn_login = ctk.CTkButton(form_inner, text="Login", height=45, corner_radius=8, fg_color="#1a2a4a", hover_color="#0f1e35", font=("Arial", 14, "bold"), command=self.login)
        self.btn_login.pack(fill="x", pady=(0, 15))

        self.btn_forgot = ctk.CTkButton(form_inner, text="Forgot Password?", fg_color="transparent", text_color="#2563eb", hover_color=["#eff6ff", "#1e3a5f"], font=("Arial", 12), command=self.open_forgot_password)
        self.btn_forgot.pack()

    def open_forgot_password(self):
        self.show_forgot_password_view()

    def show_forgot_password_view(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()
        
        wizard = ForgotPasswordWizard(self.main_container, on_cancel=self.show_login_view)
        wizard.pack(fill="both", expand=True)

    def login(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password.")
            return
            
        try:
            role = verify_login(username, password)
            if role:
                from db import log_action
                log_action(username, "Login", details=f"Role: {role}")
                self.destroy()
                MainWindow(username, role).mainloop()
            else:
                messagebox.showerror("Error", "Invalid username or password.")
        except Exception as e:
            messagebox.showerror("Login Error", str(e))

class ForgotPasswordWizard(ctk.CTkFrame):
    def __init__(self, parent, on_cancel):
        super().__init__(parent, fg_color="#f5f5f5")
        self.on_cancel_callback = on_cancel

        self.user_data = None
        self.passcode_attempts = 0
        self.security_attempts = 0
        self.current_step = 1

        # Progress Indicator
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.pack(fill="x", pady=20)
        self.setup_progress_indicator()

        # Main Card
        self.card = ctk.CTkFrame(self, fg_color="white", corner_radius=15)
        self.card.pack(fill="both", expand=True, padx=30, pady=(0, 30))

        self.show_step_1()

    def setup_progress_indicator(self):
        for widget in self.progress_frame.winfo_children():
            widget.destroy()
        
        steps_frame = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
        steps_frame.pack()

        for i in range(1, 4):
            color = "#1a2a4a" if i == self.current_step else "#d1d5db"
            dot = ctk.CTkLabel(steps_frame, text="●", font=("Arial", 20), text_color=color)
            dot.pack(side="left", padx=10)
        
        self.step_label = ctk.CTkLabel(self.progress_frame, text=f"Step {self.current_step} of 3", font=("Arial", 11, "bold"), text_color="#666666")
        self.step_label.pack()

    def clear_card(self):
        for widget in self.card.winfo_children():
            widget.destroy()

    def show_step_1(self):
        self.current_step = 1
        self.setup_progress_indicator()
        self.clear_card()

        ctk.CTkLabel(self.card, text="🔍 Find Your Account", font=("Arial", 18, "bold"), text_color="#1a2a4a").pack(pady=(30, 10))
        ctk.CTkLabel(self.card, text="Enter your username to continue", font=("Arial", 12), text_color="#666666").pack(pady=(0, 20))

        self.entry_recovery_user = ctk.CTkEntry(self.card, placeholder_text="Username", height=45, border_width=2)
        self.entry_recovery_user.pack(fill="x", padx=40, pady=10)

        self.btn_continue = ctk.CTkButton(self.card, text="Continue", height=45, fg_color="#1a2a4a", command=self.verify_user)
        self.btn_continue.pack(fill="x", padx=40, pady=20)

        ctk.CTkButton(self.card, text="Cancel", fg_color="transparent", text_color="#666666", command=self.on_cancel_callback).pack(pady=10)

    def verify_user(self):
        username = self.entry_recovery_user.get().strip()
        if not username: return

        from db import get_connection
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            self.user_data = cursor.fetchone()
            cursor.close()
            conn.close()

            if self.user_data:
                self.show_step_2()
            else:
                messagebox.showerror("Error", "Username not found.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_step_2(self):
        self.current_step = 2
        self.setup_progress_indicator()
        self.clear_card()

        ctk.CTkLabel(self.card, text="🔐 Passcode Verification", font=("Arial", 18, "bold"), text_color="#1a2a4a").pack(pady=(30, 10))
        ctk.CTkLabel(self.card, text="Enter the 6-digit passcode given to you\nduring registration", font=("Arial", 12), text_color="#666666").pack(pady=(0, 20))

        self.entry_passcode = ctk.CTkEntry(self.card, placeholder_text="Passcode", height=45, border_width=2, show="*")
        self.entry_passcode.pack(fill="x", padx=40, pady=10)

        self.btn_verify_pass = ctk.CTkButton(self.card, text="Verify Passcode", height=45, fg_color="#1a2a4a", command=self.verify_passcode)
        self.btn_verify_pass.pack(fill="x", padx=40, pady=10)

        self.link_security = ctk.CTkButton(self.card, text="Forgot passcode? Use security question", fg_color="transparent", text_color="#1a73e8", font=("Arial", 11), command=self.show_step_2b)
        self.link_security.pack(pady=5)

        back_cancel_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        back_cancel_frame.pack(fill="x", side="bottom", pady=20)
        ctk.CTkButton(back_cancel_frame, text="Back", width=100, fg_color="#6c757d", command=self.show_step_1).pack(side="left", padx=40)
        ctk.CTkButton(back_cancel_frame, text="Cancel", width=100, fg_color="transparent", text_color="#666666", command=self.on_cancel_callback).pack(side="right", padx=40)

    def verify_passcode(self):
        import bcrypt
        entered = self.entry_passcode.get().strip()
        stored_hash = self.user_data[5] # passcode column

        if stored_hash and bcrypt.checkpw(entered.encode('utf-8'), stored_hash.encode('utf-8')):
            self.show_step_3()
        else:
            self.passcode_attempts += 1
            if self.passcode_attempts >= 3:
                messagebox.showwarning("Locked", "Passcode attempts exhausted. Switching to security question.")
                self.show_step_2b()
            else:
                messagebox.showerror("Error", f"Incorrect passcode. {3 - self.passcode_attempts} attempts remaining.")

    def show_step_2b(self):
        self.current_step = 2
        self.setup_progress_indicator()
        self.clear_card()

        ctk.CTkLabel(self.card, text="🛡 Security Question", font=("Arial", 18, "bold"), text_color="#1a2a4a").pack(pady=(30, 10))
        
        question = self.user_data[6] or "Security question not set."
        ctk.CTkLabel(self.card, text=question, font=("Arial", 13, "bold"), text_color="#333333", wraplength=350).pack(pady=10)

        self.entry_sec_answer = ctk.CTkEntry(self.card, placeholder_text="Your answer", height=45, border_width=2)
        self.entry_sec_answer.pack(fill="x", padx=40, pady=10)

        self.btn_verify_sec = ctk.CTkButton(self.card, text="Verify Answer", height=45, fg_color="#1a2a4a", command=self.verify_security_answer)
        self.btn_verify_sec.pack(fill="x", padx=40, pady=20)

        back_cancel_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        back_cancel_frame.pack(fill="x", side="bottom", pady=20)
        ctk.CTkButton(back_cancel_frame, text="Back", width=100, fg_color="#6c757d", command=self.show_step_2).pack(side="left", padx=40)
        ctk.CTkButton(back_cancel_frame, text="Cancel", width=100, fg_color="transparent", text_color="#666666", command=self.on_cancel_callback).pack(side="right", padx=40)

    def verify_security_answer(self):
        import bcrypt
        entered = self.entry_sec_answer.get().strip().lower()
        stored_hash = self.user_data[7]

        if stored_hash and bcrypt.checkpw(entered.encode('utf-8'), stored_hash.encode('utf-8')):
            self.show_step_3()
        else:
            self.security_attempts += 1
            if self.security_attempts >= 3:
                messagebox.showerror("Locked", "Account recovery locked. Please contact your administrator.")
                self.on_cancel_callback()
            else:
                messagebox.showerror("Error", f"Incorrect answer. {3 - self.security_attempts} attempts remaining.")

    def show_step_3(self):
        self.current_step = 3
        self.setup_progress_indicator()
        self.clear_card()

        ctk.CTkLabel(self.card, text="🆕 Reset Password", font=("Arial", 18, "bold"), text_color="#1a2a4a").pack(pady=(30, 5))
        
        hints = "• At least 8 characters\n• One uppercase, one number, one special character"
        ctk.CTkLabel(self.card, text=hints, font=("Arial", 10), text_color="#666666", justify="left").pack(pady=(0, 15))

        self.entry_new_pass = ctk.CTkEntry(self.card, placeholder_text="New Password", height=45, border_width=2, show="*")
        self.entry_new_pass.pack(fill="x", padx=40, pady=5)

        self.entry_confirm_pass = ctk.CTkEntry(self.card, placeholder_text="Confirm New Password", height=45, border_width=2, show="*")
        self.entry_confirm_pass.pack(fill="x", padx=40, pady=5)

        self.btn_reset = ctk.CTkButton(self.card, text="Reset Password", height=45, fg_color="#28a745", command=self.reset_password)
        self.btn_reset.pack(fill="x", padx=40, pady=20)

        ctk.CTkButton(self.card, text="Cancel", fg_color="transparent", text_color="#666666", command=self.on_cancel_callback).pack(side="bottom", pady=20)

    def reset_password(self):
        p1 = self.entry_new_pass.get()
        p2 = self.entry_confirm_pass.get()

        if p1 != p2:
            messagebox.showerror("Error", "Passwords do not match.")
            return

        import re
        if len(p1) < 8 or not re.search(r"[A-Z]", p1) or not re.search(r"\d", p1) or not re.search(r"[!@#$%^&*(),.?\":{}|<>]", p1):
            messagebox.showerror("Weak Password", "Password does not meet requirements.")
            return

        import bcrypt
        from db import get_connection
        try:
            hashed = bcrypt.hashpw(p1.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (hashed, self.user_data[1]))
            conn.commit()
            cursor.close()
            conn.close()

            messagebox.showinfo("Success", "Password has been reset successfully. Please login with your new password.")
            self.on_cancel_callback()
        except Exception as e:
            messagebox.showerror("Error", str(e))