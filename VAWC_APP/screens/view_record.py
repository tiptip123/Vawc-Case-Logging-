import customtkinter as ctk
from tkinter import messagebox
import os
import subprocess
import platform
from PIL import Image, ImageTk
import tkinter as tk
from datetime import datetime
from db import get_connection
from utils.pdf_export import export_single_pdf
from .edit_record import EditRecordWindow
from .screen_header import ScreenHeader

def open_file_cross_platform(file_path):
    try:
        if platform.system() == "Windows":
            os.startfile(file_path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", file_path])
        else:
            subprocess.Popen(["xdg-open", file_path])
    except Exception as e:
        messagebox.showerror("Error", f"Could not open file: {str(e)}")

class ViewRecordWindow(ctk.CTkToplevel):
    def __init__(self, parent, vawc_no, user_role="Staff", on_edit_saved=None):
        super().__init__(parent)
        self.user_role = user_role
        self.on_edit_saved = on_edit_saved
        self.title("View Record")
        self.attributes("-fullscreen", True)  # Always full screen
        self.configure(fg_color=["#f8fafc", "#1a1a1a"])

        # Always bring to front
        self.lift()
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))

        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM vawc_logs WHERE vawc_no = ?", (vawc_no,))
            record = cursor.fetchone()
            cursor.close()
            connection.close()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.destroy()
            return

        ScreenHeader(self, f"Record Details - {record[1]}").pack(fill="x")

        # Parse dates
        date_obj = datetime.strptime(record[2], "%Y-%m-%d") if record[2] else None
        birthdate_obj = datetime.strptime(record[6], "%Y-%m-%d") if record[6] else None

        fields = [
            ("Date", date_obj.strftime("%m/%d/%Y") if date_obj else ""),
            ("Client Name", record[3] or ""),
            ("Age", str(record[4]) if record[4] else ""),
            ("Contact", record[5] or ""),
            ("Birthdate", birthdate_obj.strftime("%m/%d/%Y") if birthdate_obj else ""),
            ("Address", record[7] or ""),
            ("Type of Abuse", record[8] or ""),
            ("Case Status", record[10] or "Ongoing"),
            ("Referred To", record[13] or ""),
            ("Attachments", record[11] or ""),
            ("Name of Respondent", record[9] or ""),
            ("Remarks", record[12] or "")
        ]

        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(10, 10))

        for label, value in fields:
            item_frame = ctk.CTkFrame(
                content_frame,
                fg_color=["white", "#242424"],
                corner_radius=6,
                border_width=1,
                border_color=["#e2e8f0", "#333333"]
            )
            item_frame.pack(fill="x", pady=5)

            # Label (Title)
            ctk.CTkLabel(
                item_frame,
                text=f"{label}:",
                font=("Arial", 12, "bold"),
                text_color=["#1a2a4a", "#f8fafc"]
            ).pack(side="left", padx=10, pady=10)

            # Value (Content)
            ctk.CTkLabel(
                item_frame,
                text=value,
                font=("Arial", 12),
                text_color=["#333333", "#cbd5e1"],  # Readable in both modes
                wraplength=350,
                justify="left"
            ).pack(side="left", padx=10, pady=10)

        # Print Button and Close Button
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.btn_print = ctk.CTkButton(
            button_frame,
            text="Print to PDF",
            fg_color="#8b0000",
            hover_color="#a30000",
            text_color="white",
            command=lambda: export_single_pdf(record)
        )
        self.btn_print.pack(side="left", padx=(0, 10), pady=5)

        self.btn_edit = ctk.CTkButton(
            button_frame,
            text="Edit Record",
            fg_color="#1a73e8",
            hover_color="#1967d2",
            text_color="white",
            command=lambda: self.open_edit_record(record[1])
        )
        self.btn_edit.pack(side="left", padx=(0, 10), pady=5)

        self.btn_close = ctk.CTkButton(
            button_frame,
            text="Close",
            fg_color="#6c757d",
            hover_color="#5a6268",
            text_color="white",
            command=self.destroy
        )
        self.btn_close.pack(side="right", padx=(10, 0), pady=5)

        # Attachments Section
        attachments = record[11] or ""
        if attachments:
            attachments_frame = ctk.CTkFrame(self, fg_color="transparent")
            attachments_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

            ctk.CTkLabel(attachments_frame, text="📎 Attached Files", font=("Arial", 14, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(anchor="w", pady=(10, 15))

            attachment_files = attachments.split(';')
            for file_path in attachment_files:
                if file_path.strip():
                    self.display_attachment(attachments_frame, file_path.strip())

    def open_edit_record(self, vawc_no):
        self.destroy()
        EditRecordWindow(self.master, vawc_no, user_role=self.user_role, on_save=self.on_edit_saved)

    def display_attachment(self, parent_frame, file_path):
        import os
        from PIL import Image, ImageTk
        import tkinter as tk

        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()

        # Create attachment item frame
        item_frame = ctk.CTkFrame(parent_frame, fg_color=["white", "#242424"], corner_radius=8)
        item_frame.pack(fill="x", pady=5, padx=10)

        # Check if it's an image file
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        if file_ext in image_extensions and os.path.exists(file_path):
            try:
                # Load and resize image for thumbnail
                image = Image.open(file_path)
                image.thumbnail((100, 100))  # Thumbnail size
                photo = ImageTk.PhotoImage(image)

                # Image label
                is_dark = ctk.get_appearance_mode() == "Dark"
                img_label = tk.Label(item_frame, image=photo, bg="#242424" if is_dark else "white")
                img_label.image = photo  # Keep reference
                img_label.pack(side="left", padx=10, pady=10)

                # File info
                info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
                info_frame.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=10)

                ctk.CTkLabel(info_frame, text=file_name, font=("Arial", 12, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(anchor="w")
                ctk.CTkLabel(info_frame, text=f"Size: {os.path.getsize(file_path)} bytes", font=("Arial", 10), text_color=["#666666", "#999999"]).pack(anchor="w")

                # Open button
                ctk.CTkButton(info_frame, text="Open Image", fg_color="#8b0000", command=lambda: open_file_cross_platform(file_path)).pack(anchor="w", pady=(5, 0))

            except Exception as e:
                # Fallback if image can't be loaded
                self.display_file_item(item_frame, file_name, file_path)
        else:
            # Regular file display
            self.display_file_item(item_frame, file_name, file_path)

    def display_file_item(self, parent_frame, file_name, file_path):
        import os

        # File icon (using emoji)
        icon_label = ctk.CTkLabel(parent_frame, text="📄", font=("Arial", 24))
        icon_label.pack(side="left", padx=10, pady=10)

        # File info
        info_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=10)

        ctk.CTkLabel(info_frame, text=file_name, font=("Arial", 12, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(anchor="w")

        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            ctk.CTkLabel(info_frame, text=f"Size: {file_size} bytes", font=("Arial", 10), text_color=["#666666", "#999999"]).pack(anchor="w")

            # Open button
            ctk.CTkButton(info_frame, text="Open File", fg_color="#1a73e8", command=lambda: open_file_cross_platform(file_path)).pack(anchor="w", pady=(5, 0))
        else:
            ctk.CTkLabel(info_frame, text="File not found", font=("Arial", 10), text_color="#ff0000").pack(anchor="w")