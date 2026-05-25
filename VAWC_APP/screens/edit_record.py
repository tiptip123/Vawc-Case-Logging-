import os
import sqlite3
import customtkinter as ctk
from tkinter import messagebox, filedialog
from tkcalendar import DateEntry
from datetime import datetime
from db import get_connection
from db import get_abuse_types, add_abuse_type, update_abuse_type, delete_abuse_type
from utils.helpers import calculate_age

class EditRecordWindow(ctk.CTkToplevel):
    def __init__(self, parent, vawc_no, user_role="Staff", on_save=None):
        super().__init__(parent)
        self.on_save = on_save
        self.user_role = user_role
        self.title("Edit Record")
        self.attributes("-fullscreen", True)  # Always full screen
        self.configure(fg_color=["#f5f5f5", "#1a1a1a"])
        self.vawc_no = vawc_no

        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM vawc_logs WHERE vawc_no = ?", (vawc_no,))
            self.record = cursor.fetchone()
            cursor.close()
            connection.close()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.destroy()
            return

        ctk.CTkLabel(self, text="Edit VAWC Case Record", font=("Arial", 18, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(pady=(15, 10))

        form_frame = ctk.CTkFrame(self, fg_color=["#eef0f4", "#242424"])
        form_frame.pack(fill="both", expand=True, padx=15, pady=10)

        ctk.CTkLabel(form_frame, text="Record ID", anchor="w", text_color=["#0f172a", "#f8fafc"]).pack(fill="x", padx=10, pady=(10, 2))
        self.id_entry = ctk.CTkEntry(form_frame, placeholder_text="Record ID", border_width=2, corner_radius=8, text_color=["black", "white"], state="disabled")
        self.id_entry.insert(0, str(self.record[0]) if self.record[0] is not None else "")
        self.id_entry.pack(padx=10, pady=(0, 10), fill="x")

        ctk.CTkLabel(form_frame, text="VAWC Number", anchor="w", text_color=["#0f172a", "#f8fafc"]).pack(fill="x", padx=10, pady=(0, 2))
        self.vawc_no_entry = ctk.CTkEntry(form_frame, placeholder_text="VAWC Number", border_width=2, corner_radius=8, text_color=["black", "white"])
        self.vawc_no_entry.insert(0, self.record[1] or "")
        self.vawc_no_entry.pack(padx=10, pady=(0, 10), fill="x")

        ctk.CTkLabel(form_frame, text="Date of Report", anchor="w", text_color=["#0f172a", "#f8fafc"]).pack(fill="x", padx=10, pady=(10, 2))
        self.date_entry = DateEntry(form_frame, date_pattern="mm/dd/yyyy")
        date_value = None
        if self.record[2]:
            try:
                date_value = datetime.strptime(self.record[2], "%Y-%m-%d")
            except ValueError:
                date_value = None
        if date_value:
            self.date_entry.set_date(date_value)
        self.date_entry.pack(padx=10, pady=(0, 10), fill="x")

        ctk.CTkLabel(form_frame, text="Client Name", anchor="w", text_color=["#0f172a", "#f8fafc"]).pack(fill="x", padx=10, pady=(0, 2))
        self.client_entry = ctk.CTkEntry(form_frame, placeholder_text="Client Name", border_width=2, corner_radius=8, text_color=["black", "white"])
        self.client_entry.insert(0, self.record[3] or "")
        self.client_entry.pack(padx=10, pady=(0, 10), fill="x")

        ctk.CTkLabel(form_frame, text="Age", anchor="w", text_color=["#0f172a", "#f8fafc"]).pack(fill="x", padx=10, pady=(0, 2))
        self.age_entry = ctk.CTkEntry(form_frame, placeholder_text="Auto-calculated from birthdate", border_width=2, corner_radius=8, text_color=["black", "white"])
        if self.record[4] is not None:
            self.age_entry.insert(0, str(self.record[4]))
        self.age_entry.pack(padx=10, pady=(0, 10), fill="x")

        ctk.CTkLabel(form_frame, text="Contact", anchor="w", text_color=["#0f172a", "#f8fafc"]).pack(fill="x", padx=10, pady=(0, 2))
        self.contact_entry = ctk.CTkEntry(form_frame, placeholder_text="Contact", border_width=2, corner_radius=8, text_color=["black", "white"])
        if self.record[5]:
            self.contact_entry.insert(0, self.record[5])
        self.contact_entry.pack(padx=10, pady=(0, 10), fill="x")

        ctk.CTkLabel(form_frame, text="Birthdate", anchor="w", text_color=["#0f172a", "#f8fafc"]).pack(fill="x", padx=10, pady=(0, 2))
        self.birthdate_entry = DateEntry(form_frame, date_pattern="mm/dd/yyyy")
        if self.record[6]:
            try:
                self.birthdate_entry.set_date(datetime.strptime(self.record[6], "%Y-%m-%d"))
            except ValueError:
                pass
        self.birthdate_entry.pack(padx=10, pady=(0, 10), fill="x")
        self.birthdate_entry.bind("<<DateEntrySelected>>", self.on_birthdate_change)

        ctk.CTkLabel(form_frame, text="Address", anchor="w", text_color=["#0f172a", "#f8fafc"]).pack(fill="x", padx=10, pady=(0, 2))
        self.address_text = ctk.CTkTextbox(form_frame, height=80, corner_radius=8, text_color=["black", "white"])
        self.address_text.insert("1.0", self.record[7] or "")
        self.address_text.pack(padx=10, pady=(0, 10), fill="x")

        ctk.CTkLabel(form_frame, text="Type of Abuse", anchor="w", text_color=["#0f172a", "#f8fafc"]).pack(fill="x", padx=10, pady=(0, 2))
        self.abuse_vars = {}
        self.abuse_order = get_abuse_types()
        existing_abuses = set(self.record[8].split(", ")) if self.record[8] else set()
        self.abuse_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        self.abuse_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.render_abuse_grid(existing_abuses)

        ctk.CTkLabel(form_frame, text="Name of Respondent", anchor="w", text_color=["#0f172a", "#f8fafc"]).pack(fill="x", padx=10, pady=(0, 2))
        self.respondent_entry = ctk.CTkEntry(form_frame, placeholder_text="Name of Respondent", border_width=2, corner_radius=8, text_color=["black", "white"])
        if self.record[9]:
            self.respondent_entry.insert(0, self.record[9])
        self.respondent_entry.pack(padx=10, pady=(0, 10), fill="x")

        ctk.CTkLabel(form_frame, text="Case Status", anchor="w", text_color=["#0f172a", "#f8fafc"]).pack(fill="x", padx=10, pady=(0, 2))
        self.case_status_var = ctk.StringVar(value=self.record[10] or "Ongoing")
        self.case_status_menu = ctk.CTkOptionMenu(form_frame, values=["Ongoing", "Settled", "Issued BPO", "Referred"], variable=self.case_status_var, command=self.on_status_change)
        self.case_status_menu.pack(padx=10, pady=(0, 10), fill="x")

        ctk.CTkLabel(form_frame, text="Referred To (Agency)", anchor="w", text_color=["#0f172a", "#f8fafc"]).pack(fill="x", padx=10, pady=(0, 2))
        self.referred_entry = ctk.CTkEntry(form_frame, placeholder_text="Enter agency name", border_width=2, corner_radius=8, text_color=["black", "white"])
        self.referred_entry.insert(0, self.record[13] or "")
        self.referred_entry.pack(padx=10, pady=(0, 2), fill="x")
        
        self.referred_hint = ctk.CTkLabel(form_frame, text="Set Case Status to 'Referred' to enable this field", font=("Arial", 10), text_color=["#64748b", "#94a3b8"])
        self.referred_hint.pack(anchor="w", padx=10)
        
        # Initial state
        if self.case_status_var.get() != "Referred":
            self.referred_entry.configure(state="disabled", fg_color=["#f1f5f9", "#1a1a1a"], border_color=["#e2e8f0", "#333333"])
        else:
            self.referred_hint.pack_forget()

        ctk.CTkLabel(form_frame, text="Attachments", anchor="w", text_color=["#0f172a", "#f8fafc"]).pack(fill="x", padx=10, pady=(0, 2))
        attach_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        attach_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.attachment_button = ctk.CTkButton(attach_frame, text="Choose Files", command=self.select_attachments, width=120)
        self.attachment_button.pack(side="left")
        self.attachment_label = ctk.CTkLabel(attach_frame, text="No files selected", anchor="w", text_color=["#0f172a", "#f8fafc"])
        self.attachment_label.pack(side="left", padx=(10, 0), fill="x")
        self.attachments = self.record[11].split(";") if self.record[11] else []
        if self.attachments:
            self.attachment_label.configure(text="; ".join([os.path.basename(f) for f in self.attachments]))

        ctk.CTkLabel(form_frame, text="Remarks", anchor="w", text_color=["#0f172a", "#f8fafc"]).pack(fill="x", padx=10, pady=(0, 2))
        self.remarks_text = ctk.CTkTextbox(form_frame, height=100, corner_radius=8, text_color=["black", "white"])
        self.remarks_text.insert("1.0", self.record[12] or "")
        self.remarks_text.pack(padx=10, pady=(0, 10), fill="x")

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.btn_save = ctk.CTkButton(button_frame, text="Save Changes", fg_color="#8b0000", hover_color="#a50000", command=self.save)
        self.btn_save.pack(side="left", padx=(0, 10), pady=5, ipadx=10)

        self.btn_cancel = ctk.CTkButton(button_frame, text="Cancel", fg_color="#6c757d", hover_color="#5a6268", command=self.destroy)
        self.btn_cancel.pack(side="right", padx=(10, 0), pady=5, ipadx=10)

    def render_abuse_grid(self, existing_abuses=None):
        existing_abuses = existing_abuses or set()
        self.abuse_order = get_abuse_types()
        for widget in self.abuse_frame.winfo_children():
            widget.destroy()

        for i, abuse in enumerate(self.abuse_order):
            selected = abuse in existing_abuses
            var = self.abuse_vars.get(abuse) or ctk.BooleanVar(value=selected)
            self.abuse_vars[abuse] = var
            pill = ctk.CTkFrame(self.abuse_frame, fg_color=["white", "#2b2b2b"], border_width=1, border_color=["#dce4ee", "#333333"], corner_radius=20)
            pill.grid(row=i//4, column=i%4, padx=5, pady=5, sticky="ew")
            self.abuse_frame.grid_columnconfigure(i%4, weight=1)
            cb = ctk.CTkCheckBox(pill, text=abuse, variable=var, text_color=["black", "white"], checkbox_width=18, checkbox_height=18, command=lambda a=abuse, p=pill, v=var: self.update_pill_style(a, p, v))
            cb.pack(padx=15, pady=8, side="left")
            var._pill_widget = pill

            if self.user_role == 'Admin':
                controls_frame = ctk.CTkFrame(pill, fg_color="transparent")
                edit_btn = ctk.CTkButton(controls_frame, text="Edit", width=52, height=28, fg_color="transparent", hover_color="#e2e8f0", text_color="#475569", command=lambda a=abuse: self.open_edit_type_modal(a))
                delete_btn = ctk.CTkButton(controls_frame, text="Delete", width=58, height=28, fg_color="transparent", hover_color="#fee2e2", text_color="#b91c1c", command=lambda a=abuse: self.confirm_delete_type(a))
                edit_btn.pack(side="left", padx=(0, 4))
                delete_btn.pack(side="left", padx=(0, 4))
                controls_frame.pack(side="right", padx=(0, 10), pady=8)

        if self.user_role == 'Admin':
            i = len(self.abuse_order)
            add_pill = ctk.CTkFrame(self.abuse_frame, fg_color=["white", "#2b2b2b"], border_width=1, border_color=["#dce4ee", "#333333"], corner_radius=20)
            add_pill.grid(row=i//4, column=i%4, padx=5, pady=5, sticky="ew")
            self.abuse_frame.grid_columnconfigure(i%4, weight=1)
            add_btn = ctk.CTkButton(add_pill, text="+ Add New Type", fg_color="transparent", text_color=["#1a2a4a", "#f8fafc"], border_width=1, border_color=["#94a3b8", "#6b7280"], command=self.open_add_type_modal)
            add_btn.pack(padx=15, pady=8, fill="x")

    def open_add_type_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Add New Type of Abuse")
        modal.geometry("420x140")
        modal.grab_set()

        ctk.CTkLabel(modal, text="New Type of Abuse", font=("Arial", 12, "bold")).pack(pady=(12, 6), anchor="w", padx=16)
        entry = ctk.CTkEntry(modal, placeholder_text="Enter new abuse type name", height=36)
        entry.pack(fill="x", padx=16)

        err_label = ctk.CTkLabel(modal, text="", text_color="#dc2626")
        err_label.pack(pady=(6, 0))

        btn_frame = ctk.CTkFrame(modal, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=12)

        def do_cancel():
            modal.destroy()

        def do_save():
            name = entry.get().strip()
            if not name:
                err_label.configure(text="Name cannot be empty")
                return
            existing = [x.lower() for x in self.abuse_order]
            if name.lower() in existing:
                err_label.configure(text="Type already exists")
                return
            try:
                add_abuse_type(name)
                self.abuse_order = get_abuse_types()
                self.render_abuse_grid(set(self.record[8].split(", ")) if self.record[8] else set())
                modal.destroy()
            except ValueError as ve:
                err_label.configure(text=str(ve))
            except Exception:
                err_label.configure(text="Failed to save new type")

        ctk.CTkButton(btn_frame, text="Save", fg_color="#1a2a4a", command=do_save).pack(side="right", padx=(8,0))
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="transparent", command=do_cancel).pack(side="right")

    def open_edit_type_modal(self, current_name):
        modal = ctk.CTkToplevel(self)
        modal.title("Edit Abuse Type")
        modal.geometry("420x150")
        modal.grab_set()

        ctk.CTkLabel(modal, text="Edit Type of Abuse", font=("Arial", 12, "bold")).pack(pady=(12, 6), anchor="w", padx=16)
        entry = ctk.CTkEntry(modal, placeholder_text="Enter updated type name", height=36)
        entry.insert(0, current_name)
        entry.pack(fill="x", padx=16)

        err_label = ctk.CTkLabel(modal, text="", text_color="#dc2626")
        err_label.pack(pady=(6, 0))

        btn_frame = ctk.CTkFrame(modal, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=12)

        def do_cancel():
            modal.destroy()

        def do_save():
            new_name = entry.get().strip()
            if not new_name:
                err_label.configure(text="Name cannot be empty")
                return
            try:
                update_abuse_type(current_name, new_name)
                var = self.abuse_vars.pop(current_name, None)
                if var is not None:
                    self.abuse_vars[new_name] = var
                self.abuse_order = get_abuse_types()
                self.render_abuse_grid(set(self.record[8].split(", ")) if self.record[8] else set())
                messagebox.showinfo("Success", f"'{current_name}' updated to '{new_name}'")
                modal.destroy()
            except ValueError as ve:
                err_label.configure(text=str(ve))
            except Exception:
                err_label.configure(text="Failed to update type")

        ctk.CTkButton(btn_frame, text="Save", fg_color="#1a2a4a", command=do_save).pack(side="right", padx=(8,0))
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="transparent", command=do_cancel).pack(side="right")

    def confirm_delete_type(self, abuse_name):
        if not messagebox.askyesno("Delete Abuse Type", f"Are you sure you want to delete '{abuse_name}'? This cannot be undone."):
            return
        try:
            delete_abuse_type(abuse_name)
            self.abuse_order = [a for a in self.abuse_order if a.lower() != abuse_name.lower()]
            self.abuse_vars.pop(abuse_name, None)
            self.render_abuse_grid(set(self.record[8].split(", ")) if self.record[8] else set())
            messagebox.showinfo("Deleted", f"'{abuse_name}' has been deleted")
        except ValueError as ve:
            messagebox.showwarning("Cannot Delete", str(ve))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_status_change(self, choice):
        if choice == "Referred":
            self.referred_entry.configure(state="normal", fg_color=["white", "#2b2b2b"], border_color="#1a2a4a")
            self.referred_hint.pack_forget()
        else:
            self.referred_entry.delete(0, "end")
            self.referred_entry.configure(state="disabled", fg_color=["#f1f5f9", "#1a1a1a"], border_color=["#e2e8f0", "#333333"])
            self.referred_hint.pack(anchor="w", padx=10)

    def on_birthdate_change(self, event):
        try:
            birthdate = datetime.strptime(self.birthdate_entry.get(), "%m/%d/%Y")
            age = calculate_age(birthdate)
            self.age_entry.delete(0, "end")
            self.age_entry.insert(0, str(age))
        except Exception:
            pass

    def select_attachments(self):
        files = filedialog.askopenfilenames(title="Select attachments")
        if files:
            self.attachments = list(files)
            display_text = "; ".join([os.path.basename(f) for f in files])
            self.attachment_label.configure(text=display_text)

    def save(self):
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
        referred_to = self.referred_entry.get().strip()

        vawc_no = self.vawc_no_entry.get().strip()
        if not vawc_no:
            messagebox.showerror("Error", "VAWC Number is required.")
            return

        if not client:
            self.client_entry.configure(border_color="red")
            messagebox.showerror("Error", "Client Name is required.")
            return

        attachments = ";".join(self.attachments) if self.attachments else None
        case_status = self.case_status_var.get()

        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE vawc_logs SET vawc_no=?, date=?, client_name=?, age=?, contact=?, birthdate=?, address=?, type_of_abuse=?, name_of_respondent=?, case_status=?, attachments=?, remarks=?, referred_to=?
                WHERE id=?
            """, (vawc_no, date, client, int(age) if age else None, contact, birthdate, address, type_of_abuse, respondent, case_status, attachments, remarks, referred_to, self.record[0]))
            connection.commit()
            self.vawc_no = vawc_no
            cursor.close()
            connection.close()
            messagebox.showinfo("Success", "Record updated.")
            if self.on_save:
                self.on_save()
            self.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "VAWC Number already exists. Please enter a different VAWC number.")
        except Exception as e:
            messagebox.showerror("Error", str(e))