import customtkinter as ctk

class ScreenHeader(ctk.CTkFrame):
    def __init__(self, parent, title, actions=None):
        super().__init__(parent, fg_color="#f5f5f5")
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text=title, font=("Arial", 22, "bold"), text_color="#1a2a4a").grid(
            row=0, column=0, sticky="w", padx=20, pady=(20, 10)
        )

        if actions:
            action_frame = ctk.CTkFrame(self, fg_color="#f5f5f5")
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
