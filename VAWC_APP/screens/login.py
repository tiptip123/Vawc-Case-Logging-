import customtkinter as ctk
from tkinter import messagebox
from auth import verify_login
from .main_window import MainWindow

class LoginScreen(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VAWC Case Logging System")
        self.geometry("420x340")
        self.resizable(False, False)
        self.configure(fg_color="#f5f5f5")

        header_frame = ctk.CTkFrame(self, fg_color="#1a2a4a")
        header_frame.pack(fill="x")
        ctk.CTkLabel(header_frame, text="VAWC Case Logging System", font=("Arial", 18, "bold"), text_color="white").pack(padx=20, pady=20)

        form_frame = ctk.CTkFrame(self, fg_color="#eef0f4")
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(form_frame, text="Username", anchor="w").pack(fill="x", padx=15, pady=(15, 2))
        self.entry_username = ctk.CTkEntry(form_frame, placeholder_text="Enter your username", border_width=2, corner_radius=8)
        self.entry_username.pack(padx=15, pady=(0, 10), fill="x")

        ctk.CTkLabel(form_frame, text="Password", anchor="w").pack(fill="x", padx=15, pady=(0, 2))
        self.entry_password = ctk.CTkEntry(form_frame, placeholder_text="Enter your password", show="*", border_width=2, corner_radius=8)
        self.entry_password.pack(padx=15, pady=(0, 15), fill="x")

        self.btn_login = ctk.CTkButton(form_frame, text="Login", fg_color="#8b0000", hover_color="#a50000", command=self.login)
        self.btn_login.pack(padx=15, pady=(0, 20), fill="x")

    def login(self):
        username = self.entry_username.get()
        password = self.entry_password.get()
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password.")
            return
        role = verify_login(username, password)
        if role:
            self.destroy()
            MainWindow(role).mainloop()
        else:
            messagebox.showerror("Error", "Invalid username or password.")