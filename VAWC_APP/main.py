import customtkinter as ctk
from db import init_db, log_action
from screens.login import LoginScreen

def login_with_logging(login_screen, username, role):
    log_action(username, "Login", details=f"Role: {role}")
    login_screen.session_user = username
    login_screen.session_role = role
    login_screen.show_main_window()

# Initialize database on startup
init_db()

if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    app = LoginScreen()
    app.mainloop()