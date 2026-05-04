import customtkinter as ctk
import os
from tkinter import messagebox, filedialog
from tkcalendar import DateEntry
from datetime import datetime
from db import get_connection
from vawc_number import generate_vawc_number
from utils.helpers import calculate_age

class AddRecordWindow(ctk.CTkToplevel):
    def __init__(self, parent, on_save=None):
        super().__init__(parent)
        self.on_save = on_save
        self.title("Add Record")
        self.attributes("-fullscreen", True)  # Always full screen
        self.configure(fg_color="#f5f5f5")
        self.transient(parent)
        self.grab_set()
        self.focus_force()
        self.lift()
        self.attributes("-topmost", True)
        self.parent = parent

        ctk.CTkLabel(self, text="Add VAWC Case Record", font=("Arial", 18, "bold"), text_color="#1a2a4a").pack(pady=(15, 10))

        form_frame = ctk.CTkFrame(self, fg_color="#eef0f4")
        form_frame.pack(fill="both", expand=True, padx=15, pady=10)

        ctk.CTkLabel(form_frame, text="Date of Report", anchor="w", text_color="#1a2a4a").pack(fill="x", padx=10, pady=(10, 2))
        self.date_entry = DateEntry(form_frame, date_pattern="mm/dd/yyyy")
        self.date_entry.set_date(datetime.now())
        self.date_entry.pack(padx=10, pady=(0, 10), fill="x")

        ctk.CTkLabel(form_frame, text="Client Name", anchor="w", text_color="#1a2a4a").pack(fill="x", padx=10, pady=(0, 2))
        self.client_entry = ctk.CTkEntry(form_frame, placeholder_text="Enter client full name", border_width=2, corner_radius=8)
        self.client_entry.pack(padx=10, pady=(0, 10), fill="x")

        ctk.CTkLabel(form_frame, text="Age", anchor="w", text_color="#1a2a4a").pack(fill="x", padx=10, pady=(0, 2))
        self.age_entry = ctk.CTkEntry(form_frame, placeholder_text="Auto-calculated from birthdate", border_width=2, corner_radius=8)
        self.age_entry.pack(padx=10, pady=(0, 10), fill="x")

        ctk.CTkLabel(form_frame, text="Contact", anchor="w", text_color="#1a2a4a").pack(fill="x", padx=10, pady=(0, 2))
        self.contact_entry = ctk.CTkEntry(form_frame, placeholder_text="Contact number or email", border_width=2, corner_radius=8)
        self.contact_entry.pack(padx=10, pady=(0, 10), fill="x")

        ctk.CTkLabel(form_frame, text="Birthdate", anchor="w", text_color="#1a2a4a").pack(fill="x", padx=10, pady=(0, 2))
        self.birthdate_entry = DateEntry(form_frame, date_pattern="mm/dd/yyyy")
        self.birthdate_entry.pack(padx=10, pady=(0, 10), fill="x")
        self.birthdate_entry.bind("<<DateEntrySelected>>", self.on_birthdate_change)

        ctk.CTkLabel(form_frame, text="Address", anchor="w", text_color="#1a2a4a").pack(fill="x", padx=10, pady=(0, 2))
        self.address_text = ctk.CTkTextbox(form_frame, height=80, corner_radius=8)
        self.address_text.pack(padx=10, pady=(0, 10), fill="x")

        ctk.CTkLabel(form_frame, text="Type of Abuse", anchor="w", text_color="#1a2a4a").pack(fill="x", padx=10, pady=(0, 2))
        self.abuse_vars = {}
        abuses = ["Physical", "Sexual", "Psychological", "Economic"]
        abuse_frame = ctk.CTkFrame(form_frame, fg_color="#eef0f4")
        abuse_frame.pack(fill="x", padx=10, pady=(0, 10))
        for abuse in abuses:
            var = ctk.BooleanVar()
            self.abuse_vars[abuse] = var
            ctk.CTkCheckBox(abuse_frame, text=abuse, variable=var).pack(anchor="w", pady=2)

        ctk.CTkLabel(form_frame, text="Name of Respondent", anchor="w", text_color="#1a2a4a").pack(fill="x", padx=10, pady=(0, 2))
        self.respondent_entry = ctk.CTkEntry(form_frame, placeholder_text="Enter respondent name", border_width=2, corner_radius=8)
        self.respondent_entry.pack(padx=10, pady=(0, 10), fill="x")

        ctk.CTkLabel(form_frame, text="Case Status", anchor="w", text_color="#1a2a4a").pack(fill="x", padx=10, pady=(0, 2))
        self.case_status_var = ctk.StringVar(value="Ongoing")
        self.case_status_menu = ctk.CTkOptionMenu(form_frame, values=["Ongoing", "Resolved", "Referred", "Archived"], variable=self.case_status_var)
        self.case_status_menu.pack(padx=10, pady=(0, 10), fill="x")

        ctk.CTkLabel(form_frame, text="Attachments", anchor="w", text_color="#1a2a4a").pack(fill="x", padx=10, pady=(0, 2))
        attach_frame = ctk.CTkFrame(form_frame, fg_color="#eef0f4")
        attach_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.attachment_button = ctk.CTkButton(attach_frame, text="Choose Files", command=self.select_attachments, width=120)
        self.attachment_button.pack(side="left")
        self.attachment_label = ctk.CTkLabel(attach_frame, text="No files selected", anchor="w", text_color="#1a2a4a")
        self.attachment_label.pack(side="left", padx=(10, 0), fill="x")
        self.attachments = []

        ctk.CTkLabel(form_frame, text="Remarks", anchor="w", text_color="#1a2a4a").pack(fill="x", padx=10, pady=(0, 2))
        self.remarks_text = ctk.CTkTextbox(form_frame, height=100, corner_radius=8)
        self.remarks_text.pack(padx=10, pady=(0, 10), fill="x")

        button_frame = ctk.CTkFrame(self, fg_color="#f5f5f5")
        button_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.btn_save = ctk.CTkButton(button_frame, text="Save", fg_color="#8b0000", hover_color="#a50000", command=self.save)
        self.btn_save.pack(side="left", padx=(0, 10), pady=5, ipadx=10)

        self.btn_cancel = ctk.CTkButton(button_frame, text="Cancel", fg_color="#6c757d", hover_color="#5a6268", command=self.destroy)
        self.btn_cancel.pack(side="left", padx=(0, 10), pady=5, ipadx=10)

        self.btn_clear = ctk.CTkButton(button_frame, text="Clear", fg_color="#1a73e8", hover_color="#1967d2", command=self.clear)
        self.btn_clear.pack(side="right", padx=(10, 0), pady=5, ipadx=10)

    def on_birthdate_change(self, event):
        try:
            birthdate = datetime.strptime(self.birthdate_entry.get(), "%m/%d/%Y")
            age = calculate_age(birthdate)
            self.age_entry.delete(0, "end")
            self.age_entry.insert(0, str(age))
        except Exception:
            pass

    def select_attachments(self):
        # Bring window to front before showing dialog
        self.lift()
        self.attributes("-topmost", True)
        self.after(100, lambda: self.attributes("-topmost", False))

        files = filedialog.askopenfilenames(title="Select attachments", parent=self)
        if files:
            self.attachments = list(files)
            display_text = "; ".join([os.path.basename(f) for f in files])
            self.attachment_label.configure(text=display_text)

    def save(self):
        self.client_entry.configure(border_color="#8b0000")
        date = self.date_entry.get_date()
        client = self.client_entry.get().strip()
        age = self.age_entry.get().strip()
        contact = self.contact_entry.get().strip()
        birthdate = self.birthdate_entry.get_date() if self.birthdate_entry.get() else None
        address = self.address_text.get("1.0", "end").strip()
        abuses = [k for k, v in self.abuse_vars.items() if v.get()]
        type_of_abuse = ", ".join(abuses)
        respondent = self.respondent_entry.get().strip()
        remarks = self.remarks_text.get("1.0", "end").strip()

        if not client:
            self.client_entry.configure(border_color="red")
            messagebox.showerror("Error", "Client Name is required.")
            return

        vawc_no = generate_vawc_number()
        attachments = ";".join(self.attachments) if self.attachments else None
        case_status = self.case_status_var.get()
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO vawc_logs (vawc_no, date, client_name, age, contact, birthdate, address, type_of_abuse, name_of_respondent, case_status, attachments, remarks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (vawc_no, date, client, int(age) if age else None, contact, birthdate, address, type_of_abuse, respondent, case_status, attachments, remarks))
            connection.commit()
            cursor.close()
            connection.close()
            messagebox.showinfo("Success", f"Record saved with VAWC No: {vawc_no}")
            if self.on_save:
                self.on_save()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def clear(self):
        self.date_entry.set_date(datetime.now())
        self.client_entry.delete(0, "end")
        self.age_entry.delete(0, "end")
        self.contact_entry.delete(0, "end")
        self.birthdate_entry.set_date(datetime.now())
        self.address_text.delete("1.0", "end")
        for var in self.abuse_vars.values():
            var.set(False)
        self.respondent_entry.delete(0, "end")
        self.case_status_var.set("Ongoing")
        self.attachments = []
        self.attachment_label.configure(text="No files selected")
        self.remarks_text.delete("1.0", "end")