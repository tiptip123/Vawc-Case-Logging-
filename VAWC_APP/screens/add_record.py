import customtkinter as ctk
import os
from tkinter import messagebox, filedialog
from tkcalendar import DateEntry
from datetime import datetime
from db import get_connection
from vawc_number import generate_vawc_number
from utils.helpers import calculate_age

class AddRecordFrame(ctk.CTkFrame):
    def __init__(self, parent, username, on_save=None):
        super().__init__(parent, fg_color="#f5f5f5")
        self.username = username
        self.on_save = on_save
        self.parent = parent
        self.attachments = []

        # Main scrollable container
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="#f5f5f5")
        self.scroll_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Form Card
        self.form_card = ctk.CTkFrame(self.scroll_container, fg_color="white", corner_radius=15)
        self.form_card.pack(fill="x", padx=40, pady=10)

        # Header Banner
        self.header_banner = ctk.CTkFrame(self.form_card, fg_color="#1a2a4a", corner_radius=15, height=80)
        self.header_banner.pack(fill="x", padx=0, pady=0)
        self.header_banner.pack_propagate(False)
        
        ctk.CTkLabel(self.header_banner, text="Add New Record", font=("Arial", 20, "bold"), text_color="white").pack(pady=(15, 2))
        ctk.CTkLabel(self.header_banner, text="Fill in all required fields below", font=("Arial", 12), text_color="#cccccc").pack()

        # Content Container
        self.content_frame = ctk.CTkFrame(self.form_card, fg_color="transparent")
        self.content_frame.pack(fill="x", padx=30, pady=25)

        self.setup_form_fields()

    def setup_form_fields(self):
        # Helper to create labeled fields
        def create_label(parent, text):
            return ctk.CTkLabel(parent, text=text, font=("Arial", 11, "bold"), text_color="#1a2a4a", anchor="w")

        # Row 1: Date of Report | Client Name
        row1 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row1.pack(fill="x", pady=10)
        row1.grid_columnconfigure((0, 1), weight=1)

        col1_1 = ctk.CTkFrame(row1, fg_color="transparent")
        col1_1.grid(row=0, column=0, padx=(0, 15), sticky="nsew")
        create_label(col1_1, "Date of Report").pack(fill="x")
        self.date_entry = DateEntry(col1_1, date_pattern="mm/dd/yyyy", font=("Arial", 11))
        self.date_entry.pack(fill="x", pady=(5, 0), ipady=3)

        col1_2 = ctk.CTkFrame(row1, fg_color="transparent")
        col1_2.grid(row=0, column=1, sticky="nsew")
        create_label(col1_2, "Client Name").pack(fill="x")
        self.client_entry = ctk.CTkEntry(col1_2, placeholder_text="Full name of client", border_width=2, height=38, border_color="#dce4ee")
        self.client_entry.pack(fill="x", pady=(5, 0))

        # Row 2: Birthdate | Age
        row2 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row2.pack(fill="x", pady=10)
        row2.grid_columnconfigure((0, 1), weight=1)

        col2_1 = ctk.CTkFrame(row2, fg_color="transparent")
        col2_1.grid(row=0, column=0, padx=(0, 15), sticky="nsew")
        create_label(col2_1, "Birthdate (MM/DD/YYYY)").pack(fill="x")
        self.birthdate_entry = ctk.CTkEntry(col2_1, placeholder_text="MM/DD/YYYY", border_width=2, height=38, border_color="#dce4ee")
        self.birthdate_entry.pack(fill="x", pady=(5, 0))
        self.birthdate_entry.bind("<KeyRelease>", self.on_birthdate_key)
        self.birthdate_entry.bind("<FocusOut>", self.on_birthdate_focus_out)

        col2_2 = ctk.CTkFrame(row2, fg_color="transparent")
        col2_2.grid(row=0, column=1, sticky="nsew")
        create_label(col2_2, "Age (auto-calculated)").pack(fill="x")
        self.age_entry = ctk.CTkEntry(col2_2, placeholder_text="Age", border_width=2, height=38, border_color="#dce4ee")
        self.age_entry.pack(fill="x", pady=(5, 0))

        # Row 3: Contact Information | Complete Address
        row3 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row3.pack(fill="x", pady=10)
        row3.grid_columnconfigure((0, 1), weight=1)

        col3_1 = ctk.CTkFrame(row3, fg_color="transparent")
        col3_1.grid(row=0, column=0, padx=(0, 15), sticky="nsew")
        create_label(col3_1, "Contact Information").pack(fill="x")
        self.contact_entry = ctk.CTkEntry(col3_1, placeholder_text="Phone or email", border_width=2, height=38, border_color="#dce4ee")
        self.contact_entry.pack(fill="x", pady=(5, 0))

        col3_2 = ctk.CTkFrame(row3, fg_color="transparent")
        col3_2.grid(row=0, column=1, sticky="nsew")
        create_label(col3_2, "Complete Address").pack(fill="x")
        self.address_text = ctk.CTkTextbox(col3_2, height=38, border_width=2, border_color="#dce4ee")
        self.address_text.pack(fill="x", pady=(5, 0))

        # Row 4: Name of Respondent
        row4 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row4.pack(fill="x", pady=10)
        create_label(row4, "Name of Respondent").pack(fill="x")
        self.respondent_entry = ctk.CTkEntry(row4, placeholder_text="Full name of respondent", border_width=2, height=38, border_color="#dce4ee")
        self.respondent_entry.pack(fill="x", pady=(5, 0))

        # Row 5: Type of Abuse (Horizontal Grid)
        row5 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row5.pack(fill="x", pady=(15, 10))
        create_label(row5, "Type of Abuse").pack(fill="x", pady=(0, 10))
        
        self.abuse_frame = ctk.CTkFrame(row5, fg_color="transparent")
        self.abuse_frame.pack(fill="x")
        
        self.abuse_vars = {}
        abuses = [
            "Domestic Abuse", "Financial Abuse", "Material Abuse", "Modern Slavery",
            "Criminal Exploitation", "Neglect", "Acts of Omission", "Organisational Abuse",
            "Self-Neglect", "Hoarding", "Sexual Abuse", "Sexual Exploitation",
            "Emotional Abuse", "Psychological Abuse"
        ]
        
        # Grid layout for abuse pills
        for i, abuse in enumerate(abuses):
            var = ctk.BooleanVar()
            self.abuse_vars[abuse] = var
            
            pill = ctk.CTkFrame(self.abuse_frame, fg_color="white", border_width=1, border_color="#cccccc", corner_radius=20)
            pill.grid(row=i//4, column=i%4, padx=5, pady=5, sticky="ew")
            self.abuse_frame.grid_columnconfigure(i%4, weight=1)
            
            cb = ctk.CTkCheckBox(pill, text=abuse, variable=var, font=("Arial", 11), 
                                 checkbox_width=18, checkbox_height=18,
                                 command=lambda a=abuse, p=pill, v=var: self.update_pill_style(a, p, v))
            cb.pack(padx=15, pady=8, side="left")

        # Row 6: Case Remarks
        row6 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row6.pack(fill="x", pady=10)
        create_label(row6, "Case Remarks / Notes").pack(fill="x")
        self.remarks_text = ctk.CTkTextbox(row6, height=100, border_width=2, border_color="#dce4ee")
        self.remarks_text.pack(fill="x", pady=(5, 0))

        # Row 7: Case Status | Referred To
        row7 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row7.pack(fill="x", pady=10)
        row7.grid_columnconfigure((0, 1), weight=1)

        col7_1 = ctk.CTkFrame(row7, fg_color="transparent")
        col7_1.grid(row=0, column=0, padx=(0, 15), sticky="nsew")
        create_label(col7_1, "Case Status").pack(fill="x")
        self.case_status_var = ctk.StringVar(value="Settled")
        self.case_status_menu = ctk.CTkOptionMenu(col7_1, values=["Settled", "Issued BPO", "Ongoing", "Referred", "Archived"], 
                                                 variable=self.case_status_var, height=38,
                                                 command=self.update_status_style)
        self.case_status_menu.pack(fill="x", pady=(5, 0))
        self.update_status_style("Settled")

        col7_2 = ctk.CTkFrame(row7, fg_color="transparent")
        col7_2.grid(row=0, column=1, sticky="nsew")
        create_label(col7_2, "Referred To (Agency)").pack(fill="x")
        self.referred_to_var = ctk.StringVar()
        self.referred_menu = ctk.CTkOptionMenu(col7_2, values=["None", "PNP (Police)", "MSWDO", "Hospital", "Court", "Other"], 
                                              variable=self.referred_to_var, height=38)
        self.referred_menu.pack(fill="x", pady=(5, 0))

        # Row 8: Attachments
        row8 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row8.pack(fill="x", pady=15)
        create_label(row8, "Attachments").pack(fill="x", pady=(0, 5))
        
        self.upload_area = ctk.CTkFrame(row8, fg_color="#f8f9fa", border_width=2, border_color="#dce4ee", corner_radius=10, height=80)
        self.upload_area.pack(fill="x")
        self.upload_area.pack_propagate(False)
        
        self.upload_btn = ctk.CTkButton(self.upload_area, text="📎 Click to attach files", fg_color="transparent", 
                                        text_color="#1a2a4a", font=("Arial", 13), hover=False, command=self.select_attachments)
        self.upload_btn.pack(expand=True)
        
        self.file_list_frame = ctk.CTkFrame(row8, fg_color="transparent")
        self.file_list_frame.pack(fill="x", pady=5)

        # Row 9: Buttons
        row9 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row9.pack(fill="x", pady=(5, 0)) # Snug fit
        
        self.btn_save = ctk.CTkButton(row9, text="Save Record", font=("Arial", 13, "bold"), fg_color="#1a2a4a", hover_color="#101a2e", height=40, width=120, command=self.save)
        self.btn_save.pack(side="right", padx=(10, 0))
        
        self.btn_clear = ctk.CTkButton(row9, text="Clear Form", font=("Arial", 13), fg_color="transparent", text_color="#333333", 
                                       border_width=1, border_color="#cccccc", hover_color="#f0f0f0", height=40, width=120, command=self.clear)
        self.btn_clear.pack(side="right")

    def update_pill_style(self, abuse, pill, var):
        if var.get():
            pill.configure(fg_color="#1a2a4a", border_width=0)
            for widget in pill.winfo_children():
                if isinstance(widget, ctk.CTkCheckBox):
                    widget.configure(text_color="white")
        else:
            pill.configure(fg_color="white", border_width=1, border_color="#cccccc")
            for widget in pill.winfo_children():
                if isinstance(widget, ctk.CTkCheckBox):
                    widget.configure(text_color="black")

    def update_status_style(self, choice):
        if choice == "Settled":
            self.case_status_menu.configure(fg_color="#28a745", button_color="#218838", button_hover_color="#1e7e34")
        elif choice == "Issued BPO":
            self.case_status_menu.configure(fg_color="#1a73e8", button_color="#1967d2", button_hover_color="#185abc")
        else:
            self.case_status_menu.configure(fg_color="#1a2a4a", button_color="#101a2e", button_hover_color="#0d1526")

    def select_attachments(self):
        files = filedialog.askopenfilenames(
            title="Select attachments",
            filetypes=[("Documents & Images", "*.pdf *.png *.jpg *.jpeg *.png")]
        )
        if files:
            for f in files:
                if f not in self.attachments:
                    self.attachments.append(f)
            self.refresh_file_list()

    def remove_attachment(self, file_path):
        if file_path in self.attachments:
            self.attachments.remove(file_path)
            self.refresh_file_list()

    def refresh_file_list(self):
        for widget in self.file_list_frame.winfo_children():
            widget.destroy()
            
        for f in self.attachments:
            f_frame = ctk.CTkFrame(self.file_list_frame, fg_color="#f0f2f5", corner_radius=5)
            f_frame.pack(fill="x", pady=2)
            
            ctk.CTkLabel(f_frame, text=os.path.basename(f), font=("Arial", 11)).pack(side="left", padx=10, pady=5)
            ctk.CTkButton(f_frame, text="✕", width=20, height=20, fg_color="transparent", text_color="#dc3545", 
                          hover_color="#ffdddd", command=lambda path=f: self.remove_attachment(path)).pack(side="right", padx=5)

    def on_birthdate_key(self, event):
        if event.keysym == 'BackSpace':
            return
            
        text = self.birthdate_entry.get().replace("/", "")
        new_text = ""
        
        for i, char in enumerate(text):
            if char.isdigit():
                if i == 2 or i == 4:
                    new_text += "/"
                new_text += char
        
        self.birthdate_entry.delete(0, "end")
        self.birthdate_entry.insert(0, new_text[:10])

    def on_birthdate_focus_out(self, event):
        try:
            date_str = self.birthdate_entry.get().strip()
            # Reset border
            self.birthdate_entry.configure(border_color="#dce4ee")
            
            if not date_str:
                return

            # Try common separators
            for fmt in ("%m/%d/%Y", "%m-%d-%Y", "%m.%d.%Y", "%Y-%m-%d"):
                try:
                    birthdate = datetime.strptime(date_str, fmt)
                    # Standardize format to MM/DD/YYYY
                    self.birthdate_entry.delete(0, "end")
                    self.birthdate_entry.insert(0, birthdate.strftime("%m/%d/%Y"))
                    
                    age = calculate_age(birthdate)
                    self.age_entry.delete(0, "end")
                    self.age_entry.insert(0, str(age))
                    return
                except ValueError:
                    continue
            
            # If we reach here, parsing failed
            self.birthdate_entry.configure(border_color="red")
        except Exception:
            self.birthdate_entry.configure(border_color="red")

    def clear(self):
        self.date_entry.set_date(datetime.now())
        self.client_entry.delete(0, "end")
        self.age_entry.delete(0, "end")
        self.contact_entry.delete(0, "end")
        self.birthdate_entry.delete(0, "end")
        self.birthdate_entry.configure(border_color="#dce4ee")
        self.address_text.delete("1.0", "end")
        
        # Reset abuse pills
        for abuse, var in self.abuse_vars.items():
            var.set(False)
            # Find the pill frame (it's the master of the checkbox)
            for widget in self.abuse_frame.winfo_children():
                for sub in widget.winfo_children():
                    if isinstance(sub, ctk.CTkCheckBox) and sub.cget("text") == abuse:
                        self.update_pill_style(abuse, widget, var)
        
        self.respondent_entry.delete(0, "end")
        self.case_status_var.set("Settled")
        self.update_status_style("Settled")
        self.attachments = []
        self.refresh_file_list()
        self.remarks_text.delete("1.0", "end")

    def save(self):
        self.client_entry.configure(border_color="#dce4ee")
        date = self.date_entry.get_date()
        client = self.client_entry.get().strip()
        age = self.age_entry.get().strip()
        contact = self.contact_entry.get().strip()
        birthdate_str = self.birthdate_entry.get().strip()
        address = self.address_text.get("1.0", "end").strip()
        respondent = self.respondent_entry.get().strip()
        remarks = self.remarks_text.get("1.0", "end").strip()
        status = self.case_status_var.get()
        referred_to = self.referred_to_var.get()

        if not client:
            self.client_entry.configure(border_color="red")
            messagebox.showwarning("Required", "Client name is required.")
            return

        # Prepare Attachments (Vault)
        vault_dir = os.path.join(os.getcwd(), "attachments")
        os.makedirs(vault_dir, exist_ok=True)
        
        final_attachments = []
        for f in self.attachments:
            if f.startswith(vault_dir):
                final_attachments.append(f)
                continue
            
            try:
                # Create unique filename to avoid overwrites
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(f)}"
                dest = os.path.join(vault_dir, filename)
                import shutil
                shutil.copy2(f, dest)
                final_attachments.append(dest)
            except Exception as e:
                print(f"Failed to vault file {f}: {e}")
                final_attachments.append(f) # Fallback to original path

        attachments_str = ";".join(final_attachments)
        abuses = ", ".join([abuse for abuse, var in self.abuse_vars.items() if var.get()])
        vawc_no = generate_vawc_number(date)

        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO vawc_logs 
                (vawc_no, date, client_name, age, contact, birthdate, address, type_of_abuse, name_of_respondent, case_status, attachments, remarks, referred_to)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (vawc_no, date.strftime("%Y-%m-%d"), client, age, contact, birthdate_str, address, abuses, respondent, status, attachments_str, remarks, referred_to))
            
            connection.commit()
            
            # Log action
            from db import log_action
            log_action(self.username, "Add Record", target_record=vawc_no, details=f"Client: {client}")
            cursor.close()
            connection.close()
            
            messagebox.showinfo("Success", f"Record saved successfully!\nVAWC No: {vawc_no}")
            self.clear()
            if self.on_save:
                self.on_save()
        except Exception as e:
            messagebox.showerror("Error", str(e))