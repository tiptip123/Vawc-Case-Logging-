import customtkinter as ctk
from db import init_db
from screens.login import LoginScreen

# Initialize database on startup
init_db()

if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    app = LoginScreen()
    app.mainloop()