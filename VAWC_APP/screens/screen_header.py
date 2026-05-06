import customtkinter as ctk
import os
from PIL import Image

class ScreenHeader(ctk.CTkFrame):
    def __init__(self, parent, title, actions=None):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)

        header_container = ctk.CTkFrame(self, fg_color="transparent")
        header_container.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        # Add Logo
        logo_path = os.path.join(os.getcwd(), "logo", "tankulan.jpg")
        if os.path.exists(logo_path):
            try:
                logo_image = ctk.CTkImage(
                    light_image=Image.open(logo_path),
                    dark_image=Image.open(logo_path),
                    size=(40, 40)
                )
                self.logo_label = ctk.CTkLabel(header_container, image=logo_image, text="")
                self.logo_label.pack(side="left", padx=(0, 10))
            except Exception:
                pass

        ctk.CTkLabel(header_container, text=title, font=("Arial", 22, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(side="left")

        if actions:
            action_frame = ctk.CTkFrame(self, fg_color="transparent")
            action_frame.grid(row=0, column=1, sticky="e", padx=(0, 20))
            for action in actions:
                button = ctk.CTkButton(
                    action_frame,
                    text=action.get("text", ""),
                    command=action.get("command"),
                    fg_color=action.get("fg_color", "#8b0000"),
                    hover_color=action.get("hover_color", "#a50000"),
                    text_color=action.get("text_color", "white"),
                    width=action.get("width", 160),
                    height=action.get("height", 38),
                    corner_radius=action.get("corner_radius", 10),
                    font=("Arial", 12, "bold")
                )
                button.pack(side="left", padx=5)
