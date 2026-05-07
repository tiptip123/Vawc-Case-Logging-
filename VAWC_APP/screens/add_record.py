import customtkinter as ctk
import os
import json
from tkinter import messagebox, filedialog
from tkcalendar import DateEntry
from datetime import datetime
from db import get_connection
from vawc_number import generate_vawc_number
from utils.helpers import calculate_age

class AddRecordFrame(ctk.CTkFrame):
    def __init__(self, parent, username, on_save=None):
        super().__init__(parent, fg_color="transparent")
        self.username = username
        self.on_save = on_save
        self.parent = parent
        self.attachments = []

        # Main scrollable container
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Form Card
        self.form_card = ctk.CTkFrame(self.scroll_container, fg_color=["white", "#242424"], corner_radius=12, border_width=1, border_color=["#e2e8f0", "#333333"])
        self.form_card.pack(fill="x", padx=40, pady=10)

        # Header Banner (Navy)
        self.header_banner = ctk.CTkFrame(self.form_card, fg_color=["#1a2a4a", "#0f172a"], corner_radius=12, height=100)
        self.header_banner.pack(fill="x", padx=0, pady=0)
        self.header_banner.pack_propagate(False)
        
        # Left side title
        title_frame = ctk.CTkFrame(self.header_banner, fg_color="transparent")
        title_frame.pack(side="left", padx=30, pady=20)
        ctk.CTkLabel(title_frame, text="Add New Record", font=("Arial", 22, "bold"), text_color="white").pack(anchor="w")
        ctk.CTkLabel(title_frame, text="All required fields are marked with *", font=("Arial", 12), text_color=["#94a3b8", "#cbd5e1"]).pack(anchor="w")

        # Right side VAWC No preview
        self.vawc_preview = ctk.CTkLabel(self.header_banner, text="Will be assigned: VAWC-2026-XXXX", 
                                        font=("Arial", 12, "bold"), text_color="#cbd5e1", 
                                        fg_color=["#1e3a5f", "#1a2a4a"], corner_radius=6, padx=12, pady=6)
        self.vawc_preview.pack(side="right", padx=30)

        # Content Container
        self.content_frame = ctk.CTkFrame(self.form_card, fg_color="transparent")
        self.content_frame.pack(fill="x", padx=30, pady=30)

        self.setup_form_fields()

        # Auto-save Draft Timer
        self.draft_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "draft_record.json")
        self.load_draft()
        self.start_autosave()

    def start_autosave(self):
        self.save_draft()
        self.after(30000, self.start_autosave) # Every 30 seconds

    def save_draft(self):
        try:
            draft_data = {
                "client_name": self.client_entry.get(),
                "birthdate": self.birthdate_entry.get(),
                "contact": self.contact_entry.get(),
                "address": self.address_text.get("1.0", "end"),
                "respondent": self.respondent_entry.get(),
                "remarks": self.remarks_text.get("1.0", "end"),
                "status": self.case_status_var.get(),
                "timestamp": datetime.now().isoformat()
            }
            with open(self.draft_file, "w") as f:
                json.dump(draft_data, f)
        except (IOError, json.JSONDecodeError):
            pass

    def load_draft(self):
        try:
            if os.path.exists(self.draft_file):
                with open(self.draft_file, "r") as f:
                    data = json.load(f)
                    if data.get("client_name") or data.get("respondent"):
                        if messagebox.askyesno("Restore Draft", "A previous unsaved record was found. Would you like to restore it?"):
                            self.client_entry.insert(0, data.get("client_name", ""))
                            self.birthdate_entry.insert(0, data.get("birthdate", ""))
                            self.contact_entry.insert(0, data.get("contact", ""))
                            self.address_text.insert("1.0", data.get("address", ""))
                            self.respondent_entry.insert(0, data.get("respondent", ""))
                            self.remarks_text.insert("1.0", data.get("remarks", ""))
                            self.case_status_var.set(data.get("status", "Settled"))
                            self.update_status_style(data.get("status", "Settled"))
        except (IOError, json.JSONDecodeError):
            pass

    def setup_form_fields(self):
        # Section Header Helper
        def create_section(text, icon):
            frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
            frame.pack(fill="x", pady=(20, 10))
            ctk.CTkLabel(frame, text=f"{icon}  {text}", font=("Arial", 16, "bold"), text_color=["#0f172a", "#f8fafc"]).pack(side="left")
            ctk.CTkFrame(frame, height=1, fg_color=["#e2e8f0", "#333333"]).pack(side="left", fill="x", expand=True, padx=(15, 0))

        # Field Helper
        def create_field(parent, label, placeholder="", is_required=True):
            container = ctk.CTkFrame(parent, fg_color="transparent")
            label_text = f"{label} *" if is_required else label
            ctk.CTkLabel(container, text=label_text, font=("Arial", 12, "bold"), text_color=["#0f172a", "#f8fafc"]).pack(anchor="w", pady=(0, 5))
            entry = ctk.CTkEntry(container, placeholder_text=placeholder, height=42, corner_radius=8, border_width=1, border_color=["#e2e8f0", "#333333"])
            entry.pack(fill="x")
            return container, entry

        # 👤 Client Information Section
        create_section("Client Information", "👤")
        
        row1 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row1.pack(fill="x", pady=5)
        row1.grid_columnconfigure((0, 1), weight=1)

        # Date of Report
        col1_1 = ctk.CTkFrame(row1, fg_color="transparent")
        col1_1.grid(row=0, column=0, padx=(0, 15), sticky="nsew")
        ctk.CTkLabel(col1_1, text="Date of Report *", font=("Arial", 12, "bold"), text_color=["#0f172a", "#f8fafc"]).pack(anchor="w", pady=(0, 5))
        self.date_entry = DateEntry(col1_1, date_pattern="mm/dd/yyyy", font=("Arial", 11))
        self.date_entry.pack(fill="x", ipady=5)

        # Client Name
        col1_2, self.client_entry = create_field(row1, "Client Name", "Full name of client")
        col1_2.grid(row=0, column=1, sticky="nsew")
        self.client_entry.bind("<KeyRelease>", self.check_repeat_victim)

        # Repeat Victim Warning Banner (Hidden by default)
        self.victim_warning = ctk.CTkFrame(self.content_frame, fg_color=["#fff3cd", "#332b00"], border_width=1, border_color=["#ffeeba", "#665500"], corner_radius=8, height=40)
        self.victim_warning_label = ctk.CTkLabel(self.victim_warning, text="", font=("Arial", 11, "bold"), text_color=["#856404", "#ffeeba"])
        self.victim_warning_label.pack(side="left", padx=15)
        
        row2 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row2.pack(fill="x", pady=5)
        row2.grid_columnconfigure((0, 1), weight=1)

        # Birthdate
        col2_1, self.birthdate_entry = create_field(row2, "Birthdate", "MM/DD/YYYY")
        col2_1.grid(row=0, column=0, padx=(0, 15), sticky="nsew")
        self.birthdate_entry.bind("<KeyRelease>", self.on_birthdate_key)
        self.birthdate_entry.bind("<FocusOut>", self.on_birthdate_focus_out)

        # Age
        col2_2, self.age_entry = create_field(row2, "Age", "Auto-calculated", is_required=False)
        col2_2.grid(row=0, column=1, sticky="nsew")

        # Contact
        row3_1 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row3_1.pack(fill="x", pady=5)
        col3_1, self.contact_entry = create_field(row3_1, "Contact Information", "Phone or email")
        col3_1.pack(fill="x")

        # 📍 Address Section
        create_section("Address", "📍")
        row3_2 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row3_2.pack(fill="x", pady=5)
        ctk.CTkLabel(row3_2, text="Complete Address *", font=("Arial", 12, "bold"), text_color=["#0f172a", "#f8fafc"]).pack(anchor="w", pady=(0, 5))
        self.address_text = ctk.CTkTextbox(row3_2, height=60, corner_radius=8, border_width=1, border_color=["#e2e8f0", "#333333"])
        self.address_text.pack(fill="x")

        # ⚖️ Case Information Section
        create_section("Case Information", "⚖️")
        
        # Respondent
        row4 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row4.pack(fill="x", pady=5)
        col4, self.respondent_entry = create_field(row4, "Name of Respondent", "Full name of respondent")
        col4.pack(fill="x")

        # Abuse Type (Pill style)
        row5 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row5.pack(fill="x", pady=(15, 10))
        ctk.CTkLabel(row5, text="Type of Abuse *", font=("Arial", 12, "bold"), text_color=["#0f172a", "#f8fafc"]).pack(anchor="w", pady=(0, 10))
        
        self.abuse_frame = ctk.CTkFrame(row5, fg_color="transparent")
        self.abuse_frame.pack(fill="x")
        
        self.abuse_vars = {}
        abuses = ["Domestic Abuse", "Financial Abuse", "Material Abuse", "Modern Slavery", "Criminal Exploitation", "Neglect", "Acts of Omission", "Organisational Abuse", "Self-Neglect", "Hoarding", "Sexual Abuse", "Sexual Exploitation", "Emotional Abuse", "Psychological Abuse"]
        
        for i, abuse in enumerate(abuses):
            var = ctk.BooleanVar()
            self.abuse_vars[abuse] = var
            pill = ctk.CTkFrame(self.abuse_frame, fg_color=["white", "#2b2b2b"], border_width=1, border_color=["#e2e8f0", "#333333"], corner_radius=20)
            pill.grid(row=i//4, column=i%4, padx=5, pady=5, sticky="ew")
            self.abuse_frame.grid_columnconfigure(i%4, weight=1)
            cb = ctk.CTkCheckBox(pill, text=abuse, variable=var, font=("Arial", 11), text_color=["black", "white"], checkbox_width=18, checkbox_height=18, command=lambda a=abuse, p=pill, v=var: self.update_pill_style(a, p, v))
            cb.pack(padx=15, pady=8, side="left")

        # Status & Referral
        row7 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row7.pack(fill="x", pady=10)
        row7.grid_columnconfigure((0, 1), weight=1)

        col7_1 = ctk.CTkFrame(row7, fg_color="transparent")
        col7_1.grid(row=0, column=0, padx=(0, 15), sticky="nsew")
        ctk.CTkLabel(col7_1, text="Case Status *", font=("Arial", 12, "bold"), text_color=["#0f172a", "#f8fafc"]).pack(anchor="w", pady=(0, 5))
        self.case_status_var = ctk.StringVar(value="Settled")
        self.case_status_menu = ctk.CTkOptionMenu(col7_1, values=["Ongoing", "Settled", "Issued BPO", "Referred"], variable=self.case_status_var, height=42, corner_radius=8, command=self.update_status_style)
        self.case_status_menu.pack(fill="x")
        self.update_status_style("Settled")

        col7_2 = ctk.CTkFrame(row7, fg_color="transparent")
        col7_2.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(col7_2, text="Referred To (Agency)", font=("Arial", 12, "bold"), text_color="#0f172a").pack(anchor="w", pady=(0, 5))
        self.referred_to_entry = ctk.CTkEntry(col7_2, placeholder_text="Enter agency name", height=42, corner_radius=8, border_width=1, border_color="#e2e8f0")
        self.referred_to_entry.pack(fill="x")
        self.referred_to_entry.configure(state="disabled", fg_color="#f1f5f9")
        
        # Add trace to handle referred_to field in add_record
        self.case_status_var.trace_add("write", self.on_status_change_add)

        # Remarks
        row6 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row6.pack(fill="x", pady=10)
        ctk.CTkLabel(row6, text="Case Remarks / Notes", font=("Arial", 12, "bold"), text_color="#0f172a").pack(anchor="w", pady=(0, 5))
        self.remarks_text = ctk.CTkTextbox(row6, height=80, corner_radius=8, border_width=1, border_color="#e2e8f0")
        self.remarks_text.pack(fill="x")

        # 📎 Attachments Section
        create_section("Attachments", "📎")
        row8 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row8.pack(fill="x", pady=5)
        self.upload_area = ctk.CTkFrame(row8, fg_color="#f8fafc", border_width=2, border_color="#e2e8f0", corner_radius=10, height=80)
        self.upload_area.pack(fill="x")
        self.upload_area.pack_propagate(False)
        self.upload_btn = ctk.CTkButton(self.upload_area, text="📎 Click to attach files", fg_color="transparent", text_color="#2563eb", font=("Arial", 13, "bold"), command=self.select_attachments)
        self.upload_btn.pack(expand=True)
        self.file_list_frame = ctk.CTkFrame(row8, fg_color="transparent")
        self.file_list_frame.pack(fill="x", pady=5)

        # Buttons
        row9 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row9.pack(fill="x", pady=(30, 0))
        self.btn_save = ctk.CTkButton(row9, text="Save Record", font=("Arial", 14, "bold"), fg_color="#1a2a4a", hover_color="#0f1e35", height=45, width=160, corner_radius=8, command=self.save)
        self.btn_save.pack(side="right", padx=(15, 0))
        self.btn_clear = ctk.CTkButton(row9, text="Clear Form", font=("Arial", 14), fg_color="transparent", text_color="#64748b", border_width=1, border_color="#e2e8f0", height=45, width=140, corner_radius=8, command=self.clear)
        self.btn_clear.pack(side="right")

    def check_repeat_victim(self, event=None):
        client_name = self.client_entry.get().strip()
        if len(client_name) < 3:
            self.victim_warning.pack_forget()
            return

        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()
            escaped_name = client_name.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
            cursor.execute("SELECT COUNT(*) FROM vawc_logs WHERE client_name LIKE ? ESCAPE '\\' AND is_deleted = 0", (f"%{escaped_name}%",))
            count = cursor.fetchone()[0]

            if count > 0:
                self.victim_warning_label.configure(text=f"⚠️ This client has {count} previous cases in the system.")
                self.victim_warning.pack(fill="x", pady=(5, 10), after=self.client_entry.master)
            else:
                self.victim_warning.pack_forget()
        except Exception:
            self.victim_warning.pack_forget()
        finally:
            if connection:
                connection.close()

    def on_status_change_add(self, *args):
        status = self.case_status_var.get()
        if status == "Referred":
            self.referred_to_entry.configure(state="normal", fg_color="white", border_color="#1a2a4a")
        else:
            self.referred_to_entry.delete(0, "end")
            self.referred_to_entry.configure(state="disabled", fg_color="#f1f5f9", border_color="#e2e8f0")

    def update_pill_style(self, abuse, pill, var):
        if var.get():
            pill.configure(fg_color="#1a2a4a", border_width=0)
            for widget in pill.winfo_children():
                if isinstance(widget, ctk.CTkCheckBox):
                    widget.configure(text_color="white")
        else:
            pill.configure(fg_color=["white", "#2b2b2b"], border_width=1, border_color=["#e2e8f0", "#333333"])
            for widget in pill.winfo_children():
                if isinstance(widget, ctk.CTkCheckBox):
                    widget.configure(text_color=["black", "white"])

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
            f_frame = ctk.CTkFrame(self.file_list_frame, fg_color=["#f0f2f5", "#1a1a1a"], corner_radius=5)
            f_frame.pack(fill="x", pady=2)
            
            ctk.CTkLabel(f_frame, text=os.path.basename(f), font=("Arial", 11), text_color=["#0f172a", "#f8fafc"]).pack(side="left", padx=10, pady=5)
            ctk.CTkButton(f_frame, text="✕", width=20, height=20, fg_color="transparent", text_color="#dc3545", 
                          hover_color=["#ffdddd", "#442222"], command=lambda path=f: self.remove_attachment(path)).pack(side="right", padx=5)

    def on_birthdate_key(self, event):
        if event.keysym == 'BackSpace' or event.keysym == 'Delete':
            return
            
        text = self.birthdate_entry.get().replace("/", "")
        if len(text) > 8: text = text[:8]
        
        new_text = ""
        for i, char in enumerate(text):
            if char.isdigit():
                if i == 2 or i == 4:
                    new_text += "/"
                new_text += char
        
        # To avoid infinite loop with bind
        if self.birthdate_entry.get() != new_text:
            self.birthdate_entry.delete(0, "end")
            self.birthdate_entry.insert(0, new_text)

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

    def has_unsaved_changes(self):
        """Check if any primary field has input that hasn't been saved"""
        try:
            if self.client_entry.get().strip(): return True
            if self.respondent_entry.get().strip(): return True
            if self.address_text.get("1.0", "end").strip(): return True
            if any(v.get() for v in self.abuse_vars.values()): return True
        except: pass
        return False

    def save(self):
        self.client_entry.configure(border_color="#e2e8f0")
        date = self.date_entry.get_date()
        client = self.client_entry.get().strip()
        age = self.age_entry.get().strip()
        contact = self.contact_entry.get().strip()
        birthdate_str = self.birthdate_entry.get().strip()
        address = self.address_text.get("1.0", "end").strip()
        respondent = self.respondent_entry.get().strip()
        remarks = self.remarks_text.get("1.0", "end").strip()
        status = self.case_status_var.get()
        referred_to = self.referred_to_entry.get().strip()

        # Validation
        errors = []
        if not client: errors.append("Client Name")
        if not address: errors.append("Address")
        if not respondent: errors.append("Respondent")
        
        abuses = [abuse for abuse, var in self.abuse_vars.items() if var.get()]
        if not abuses: errors.append("Type of Abuse (select at least one)")

        if errors:
            messagebox.showwarning("Required Fields", f"Please fill in the following:\n- " + "\n- ".join(errors))
            return

        # Duplicate Detection
        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT vawc_no FROM vawc_logs WHERE client_name = ? AND date = ? AND is_deleted = 0", (client, date.strftime("%Y-%m-%d")))
            dup = cursor.fetchone()
            if dup:
                if not messagebox.askyesno("Potential Duplicate", f"A record for '{client}' on this date already exists ({dup[0]}). Save anyway?"):
                    return
        except Exception:
            pass
        finally:
            if connection:
                connection.close()

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
                final_attachments.append(f) # Fallback to original path

        attachments_str = ";".join(final_attachments)
        abuses_str = ", ".join(abuses)
        vawc_no = generate_vawc_number(date)

        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO vawc_logs 
                (vawc_no, date, client_name, age, contact, birthdate, address, type_of_abuse, name_of_respondent, case_status, attachments, remarks, referred_to)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (vawc_no, date.strftime("%Y-%m-%d"), client, int(age) if age else None, contact, birthdate_str, address, abuses_str, respondent, status, attachments_str, remarks, referred_to))
            
            connection.commit()
            
            # Log action
            from db import log_action
            log_action(self.username, "Add Record", target_record=vawc_no, details=f"Client: {client}")
            
            messagebox.showinfo("Success", f"Record saved successfully!\nVAWC No: {vawc_no}")
            
            # Remove draft if exists
            if os.path.exists(self.draft_file):
                os.remove(self.draft_file)
                
            self.clear()
            if self.on_save:
                self.on_save()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            if connection:
                connection.close()