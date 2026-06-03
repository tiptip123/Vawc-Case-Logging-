import customtkinter as ctk
import os
import re
import json
from tkinter import messagebox, filedialog, Toplevel, Listbox
from tkcalendar import DateEntry
from datetime import datetime
from db import get_connection, get_abuse_types, add_abuse_type, update_abuse_type, delete_abuse_type, is_abuse_type_in_use, ensure_abuse_type
from vawc_number import generate_vawc_number
from utils.helpers import calculate_age

class AddRecordFrame(ctk.CTkFrame):
    def __init__(self, parent, username, user_role, on_save=None):
        super().__init__(parent, fg_color="transparent")
        self.username = username
        self.user_role = user_role
        self.on_save = on_save
        self.parent = parent
        self.attachments = []
        self.client_suggestion_popup = None
        self.client_suggestion_listbox = None
        self.respondent_suggestion_popup = None
        self.respondent_suggestion_listbox = None

        # Main scrollable container
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Form Card
        self.form_card = ctk.CTkFrame(self.scroll_container, fg_color=["white", "#242424"], corner_radius=12, border_width=1, border_color=["#e2e8f0", "#333333"])
        self.form_card.pack(fill="x", padx=40, pady=5)

        # Content Container
        self.content_frame = ctk.CTkFrame(self.form_card, fg_color="transparent")
        self.content_frame.pack(fill="x", padx=30, pady=(0, 12))

        self.setup_form_fields()
        self.update_vawc_format()
        self.update_vawc_preview()

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
                "vawc_seq": self.vawc_seq_entry.get().strip(),
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
                            self.vawc_seq_entry.insert(0, data.get("vawc_seq", ""))
                            self.birthdate_entry.insert(0, data.get("birthdate", ""))
                            self.contact_entry.insert(0, data.get("contact", ""))
                            self.address_text.insert("1.0", data.get("address", ""))
                            self.respondent_entry.insert(0, data.get("respondent", ""))
                            self.remarks_text.insert("1.0", data.get("remarks", ""))
                            self.case_status_var.set(data.get("status", "Settled"))
                            self.update_status_style(data.get("status", "Settled"))
                            self.update_vawc_preview()
        except (IOError, json.JSONDecodeError):
            pass

    def setup_form_fields(self):
        # Field Helper
        def create_field(parent, label, placeholder="", is_required=True):
            container = ctk.CTkFrame(parent, fg_color="transparent")
            label_text = f"{label} *" if is_required else label
            ctk.CTkLabel(container, text=label_text, font=("Arial", 12, "bold"), text_color=["#0f172a", "#f8fafc"]).pack(anchor="w", pady=(0, 5))
            entry = ctk.CTkEntry(container, placeholder_text=placeholder, height=42, corner_radius=8, border_width=1, border_color=["#e2e8f0", "#333333"])
            entry.pack(fill="x")
            return container, entry

        # 👤 Client Information Section
        self.create_section("Client Information", "👤")

        row1 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row1.pack(fill="x", pady=5)
        row1.grid_columnconfigure((0, 1), weight=1)

        # Date of Report
        col1_1 = ctk.CTkFrame(row1, fg_color="transparent")
        col1_1.grid(row=0, column=0, padx=(0, 15), sticky="nsew")
        ctk.CTkLabel(col1_1, text="Date of Report *", font=("Arial", 12, "bold"), text_color=["#0f172a", "#f8fafc"]).pack(anchor="w", pady=(0, 5))
        self.date_entry = DateEntry(col1_1, date_pattern="mm/dd/yyyy", font=("Arial", 11))
        self.date_entry.pack(fill="x", ipady=5)
        self.date_entry.bind("<<DateEntrySelected>>", self.update_vawc_format)
        self.date_entry.bind("<KeyRelease>", self.on_report_date_key)
        self.date_entry.bind("<FocusOut>", self.on_report_date_focus_out)

        # Client Name
        col1_2, self.client_entry = create_field(row1, "Client Name", "Full name of client")
        col1_2.grid(row=0, column=1, sticky="nsew")
        self.client_entry.bind("<KeyRelease>", self.on_client_key_release)
        self.client_entry.bind("<FocusOut>", lambda e: self.after(100, lambda: self.hide_suggestion_dropdown("client")))

        row0 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row0.pack(fill="x", pady=5)
        ctk.CTkLabel(row0, text="VAWC Number *", font=("Arial", 12, "bold"), text_color=["#0f172a", "#f8fafc"]).pack(anchor="w", pady=(0, 5))

        vawc_row = ctk.CTkFrame(row0, fg_color="transparent")
        vawc_row.pack(fill="x")
        ctk.CTkLabel(vawc_row, text="VAWC-", font=("Arial", 12, "bold"), text_color=["#0f172a", "#f8fafc"]).grid(row=0, column=0, padx=(0, 4))
        self.vawc_year_label = ctk.CTkLabel(vawc_row, text=str(datetime.now().year), font=("Arial", 12, "bold"), text_color=["#0f172a", "#f8fafc"])
        self.vawc_year_label.grid(row=0, column=1, padx=(0, 4))
        ctk.CTkLabel(vawc_row, text="-", font=("Arial", 12, "bold"), text_color=["#0f172a", "#f8fafc"]).grid(row=0, column=2, padx=(0, 4))
        self.vawc_seq_entry = ctk.CTkEntry(vawc_row, placeholder_text=self.get_next_vawc_sequence_placeholder(), height=42, corner_radius=8, border_width=1, border_color=["#e2e8f0", "#333333"])
        self.vawc_seq_entry.grid(row=0, column=3, sticky="ew")
        vawc_row.grid_columnconfigure(3, weight=1)
        self.vawc_seq_entry.bind("<KeyRelease>", self.on_vawc_seq_key_release)
        self.vawc_seq_entry.bind("<FocusOut>", self.on_vawc_seq_focus_out)

        self.latest_vawc_label = ctk.CTkLabel(row0, text="Latest VAWC No: fetching...", font=("Arial", 11), text_color=["#64748b", "#cbd5e1"], fg_color="transparent")
        self.latest_vawc_label.pack(anchor="w", pady=(8, 0))

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
        self.create_section("Address", "📍")
        row3_2 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row3_2.pack(fill="x", pady=5)
        ctk.CTkLabel(row3_2, text="Complete Address *", font=("Arial", 12, "bold"), text_color=["#0f172a", "#f8fafc"]).pack(anchor="w", pady=(0, 5))
        self.address_text = ctk.CTkTextbox(row3_2, height=60, corner_radius=8, border_width=1, border_color=["#e2e8f0", "#333333"])
        self.address_text.pack(fill="x")

        # ⚖️ Case Information Section
        self.create_section("Case Information", "⚖️")
        
        # Respondent
        row4 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row4.pack(fill="x", pady=5)
        col4, self.respondent_entry = create_field(row4, "Name of Respondent", "Full name of respondent")
        col4.pack(fill="x")
        self.respondent_entry.bind("<KeyRelease>", self.on_respondent_key_release)
        self.respondent_entry.bind("<FocusOut>", lambda e: self.after(100, lambda: self.hide_suggestion_dropdown("respondent")))

        # Abuse Type (Autocomplete)
        row5 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row5.pack(fill="x", pady=(15, 10))
        ctk.CTkLabel(row5, text="Type of Abuse *", font=("Arial", 12, "bold"), text_color=["#0f172a", "#f8fafc"]).pack(anchor="w", pady=(0, 10))
        
        self.abuse_frame = ctk.CTkFrame(row5, fg_color="transparent")
        self.abuse_frame.pack(fill="x")

        self.abuse_selected_frame = ctk.CTkFrame(self.abuse_frame, fg_color="transparent")
        # Do not pack now; only show when there are selected abuse tags to avoid extra spacing

        self.abuse_entry = ctk.CTkEntry(self.abuse_frame, placeholder_text="Search or enter abuse type and press Enter", height=42, corner_radius=8, border_width=1, border_color=["#e2e8f0", "#333333"])
        self.abuse_entry.pack(fill="x")
        self.abuse_entry.bind("<KeyRelease>", self.on_abuse_key_release)
        self.abuse_entry.bind("<Return>", lambda e: self.add_abuse_from_entry())
        self.abuse_entry.bind("<FocusOut>", lambda e: self.after(100, lambda: self.hide_suggestion_dropdown("abuse")))

        self.abuse_suggestion_popup = None
        self.abuse_suggestion_listbox = None
        self.selected_abuses = []
        self.abuse_order = get_abuse_types()
        self.render_selected_abuses()

        # Status & Referral
        row7 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row7.pack(fill="x", pady=10)
        row7.grid_columnconfigure((0, 1), weight=1)

        col7_1 = ctk.CTkFrame(row7, fg_color="transparent")
        col7_1.grid(row=0, column=0, padx=(0, 15), sticky="nsew")
        ctk.CTkLabel(col7_1, text="Case Status *", font=("Arial", 12, "bold"), text_color=["#0f172a", "#f8fafc"]).pack(anchor="w", pady=(0, 5))
        self.case_status_var = ctk.StringVar(value="Ongoing")
        self.case_status_menu = ctk.CTkOptionMenu(col7_1, values=["Ongoing", "Settled", "Issued BPO", "Referred"], variable=self.case_status_var, height=42, corner_radius=8, command=self.update_status_style)
        self.case_status_menu.pack(fill="x")
        self.update_status_style("Ongoing")

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
        self.create_section("Attachments", "📎")
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
        # Reduce top padding to tighten space between attachments and action buttons
        row9.pack(fill="x", pady=(10, 0))
        self.btn_save = ctk.CTkButton(row9, text="Save Record", font=("Arial", 14, "bold"), fg_color="#1a2a4a", hover_color="#0f1e35", height=45, width=160, corner_radius=8, command=self.save)
        self.btn_save.pack(side="right", padx=(15, 0))
        self.btn_clear = ctk.CTkButton(row9, text="Clear Form", font=("Arial", 14), fg_color="transparent", text_color="#64748b", border_width=1, border_color="#e2e8f0", height=45, width=140, corner_radius=8, command=self.clear)
        self.btn_clear.pack(side="right")

    def render_selected_abuses(self):
        # Clear existing children first
        for widget in self.abuse_selected_frame.winfo_children():
            widget.destroy()

        # If there are no selected abuses, ensure the frame is not packed (no vertical space)
        if not self.selected_abuses:
            try:
                if self.abuse_selected_frame.winfo_ismapped():
                    self.abuse_selected_frame.pack_forget()
            except Exception:
                pass
            return

        # Ensure the frame is visible when there are selected tags
        try:
            if not self.abuse_selected_frame.winfo_ismapped():
                self.abuse_selected_frame.pack(fill="x", pady=(0, 8))
        except Exception:
            # Fallback: pack if any error querying map state
            self.abuse_selected_frame.pack(fill="x", pady=(0, 8))

        for abuse in self.selected_abuses:
            pill = ctk.CTkFrame(self.abuse_selected_frame, fg_color=["#e2e8f0", "#334155"], corner_radius=14)
            pill.pack(side="left", padx=4, pady=2)
            ctk.CTkLabel(pill, text=abuse, font=("Arial", 11), text_color=["#0f172a", "#f8fafc"]).pack(side="left", padx=(10, 6))
            ctk.CTkButton(pill, text="✕", width=24, height=24, fg_color="transparent", hover_color=["#fee2e2", "#4b0000"], text_color="#b91c1c",
                          command=lambda a=abuse: self.remove_abuse_tag(a)).pack(side="left", padx=(0, 8))

    def add_abuse_tag(self, abuse):
        abuse = abuse.strip()
        if not abuse:
            return
        if abuse.lower() in [existing.lower() for existing in self.selected_abuses]:
            return
        self.selected_abuses.append(abuse)
        self.abuse_entry.delete(0, "end")
        self.render_selected_abuses()
        self.hide_suggestion_dropdown("abuse")

    def remove_abuse_tag(self, abuse):
        self.selected_abuses = [a for a in self.selected_abuses if a.lower() != abuse.lower()]
        self.render_selected_abuses()

    def add_abuse_from_entry(self):
        value = self.abuse_entry.get().strip()
        if value:
            self.add_abuse_tag(value)

    def query_abuse_suggestions(self, query):
        if not query or len(query.strip()) < 1:
            return []
        ignore = {a.lower() for a in self.selected_abuses}
        suggestions = [a for a in get_abuse_types() if query.lower() in a.lower() and a.lower() not in ignore]
        return suggestions[:10]

    def on_abuse_key_release(self, event=None):
        value = self.abuse_entry.get().strip()
        if not value:
            self.hide_suggestion_dropdown("abuse")
            return
        suggestions = self.query_abuse_suggestions(value)
        if suggestions:
            self.show_suggestion_dropdown("abuse", self.abuse_entry, suggestions)
        else:
            self.hide_suggestion_dropdown("abuse")

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
            if new_name.lower() == current_name.lower() and new_name != current_name:
                # Allow case-only update
                pass
            try:
                update_abuse_type(current_name, new_name)
                self.abuse_order = get_abuse_types()
                self.render_selected_abuses()
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
            self.render_selected_abuses()
            messagebox.showinfo("Deleted", f"'{abuse_name}' has been deleted")
        except ValueError as ve:
            messagebox.showwarning("Cannot Delete", str(ve))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def create_section(self, text, icon):
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        frame.pack(fill="x", pady=(20, 10))
        ctk.CTkLabel(frame, text=f"{icon}  {text}", font=("Arial", 16, "bold"), text_color=["#0f172a", "#f8fafc"]).pack(side="left")
        ctk.CTkFrame(frame, height=1, fg_color=["#e2e8f0", "#333333"]).pack(side="left", fill="x", expand=True, padx=(15, 0))

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

    def query_name_suggestions(self, query, column_name):
        if not query or len(query.strip()) < 1:
            return []
        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()
            search_text = f"%{query.strip().lower()}%"
            cursor.execute(f"""
                SELECT DISTINCT TRIM({column_name})
                FROM vawc_logs
                WHERE is_deleted = 0
                    AND {column_name} IS NOT NULL
                    AND {column_name} != ''
                    AND LOWER({column_name}) LIKE ?
                ORDER BY LOWER({column_name})
                LIMIT 15
            """, (search_text,))
            results = [row[0] for row in cursor.fetchall() if row[0]]
            return results
        except Exception:
            return []
        finally:
            if connection:
                connection.close()

    def show_suggestion_dropdown(self, field, entry_widget, suggestions):
        popup_attr = f"{field}_suggestion_popup"
        listbox_attr = f"{field}_suggestion_listbox"

        current_popup = getattr(self, popup_attr, None)
        if current_popup and current_popup.winfo_exists():
            current_popup.destroy()

        popup = Toplevel(self)
        popup.wm_overrideredirect(True)
        popup.wm_attributes("-topmost", True)
        popup.configure(background="#ffffff")

        listbox = Listbox(popup, activestyle="none", highlightthickness=1, bd=1, relief="solid", selectbackground="#1a73e8", selectforeground="#ffffff")
        listbox.pack(fill="both", expand=True)

        for suggestion in suggestions:
            listbox.insert("end", suggestion)

        listbox.bind("<<ListboxSelect>>", lambda e, f=field: self.on_suggestion_select(f))
        listbox.bind("<ButtonRelease-1>", lambda e, f=field: self.on_suggestion_select(f))
        listbox.bind("<Escape>", lambda e, f=field: self.hide_suggestion_dropdown(f))

        x = entry_widget.winfo_rootx()
        y = entry_widget.winfo_rooty() + entry_widget.winfo_height()
        width = max(entry_widget.winfo_width(), 200)
        height = min(len(suggestions), 10) * 24
        popup.geometry(f"{width}x{height}+{x}+{y}")

        setattr(self, popup_attr, popup)
        setattr(self, listbox_attr, listbox)

    def hide_suggestion_dropdown(self, field):
        popup_attr = f"{field}_suggestion_popup"
        listbox_attr = f"{field}_suggestion_listbox"
        popup = getattr(self, popup_attr, None)
        if popup and popup.winfo_exists():
            popup.destroy()
        setattr(self, popup_attr, None)
        setattr(self, listbox_attr, None)

    def on_suggestion_select(self, field):
        listbox = getattr(self, f"{field}_suggestion_listbox", None)
        if not listbox:
            return
        selection = listbox.curselection()
        if not selection:
            return
        value = listbox.get(selection[0])
        if field == "client":
            target = self.client_entry
            target.delete(0, "end")
            target.insert(0, value)
            target.focus_set()
            self.check_repeat_victim()
        elif field == "respondent":
            target = self.respondent_entry
            target.delete(0, "end")
            target.insert(0, value)
            target.focus_set()
        elif field == "abuse":
            self.add_abuse_tag(value)

        self.hide_suggestion_dropdown(field)

    def hide_suggestion_if_needed(self, field):
        popup = getattr(self, f"{field}_suggestion_popup", None)
        if not popup or not popup.winfo_exists():
            return
        focus_widget = self.focus_get()
        listbox = getattr(self, f"{field}_suggestion_listbox", None)
        if focus_widget not in (listbox, getattr(self, f"{field}_suggestion_popup", None)):
            self.hide_suggestion_dropdown(field)

    def on_client_key_release(self, event=None):
        self.check_repeat_victim()
        value = self.client_entry.get().strip()
        if not value:
            self.hide_suggestion_dropdown("client")
            return
        suggestions = self.query_name_suggestions(value, "client_name")
        if suggestions:
            self.show_suggestion_dropdown("client", self.client_entry, suggestions)
        else:
            self.hide_suggestion_dropdown("client")

    def on_respondent_key_release(self, event=None):
        value = self.respondent_entry.get().strip()
        if not value:
            self.hide_suggestion_dropdown("respondent")
            return
        suggestions = self.query_name_suggestions(value, "name_of_respondent")
        if suggestions:
            self.show_suggestion_dropdown("respondent", self.respondent_entry, suggestions)
        else:
            self.hide_suggestion_dropdown("respondent")

    # --- Admin: Add New Abuse Type Flow ---
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
            # Duplicate check (case-insensitive)
            existing = [x.lower() for x in self.abuse_order]
            if name.lower() in existing:
                err_label.configure(text="Type already exists")
                return
            try:
                add_abuse_type(name)
                # Update local list for future suggestions
                self.abuse_order.append(name)
                modal.destroy()
            except ValueError as ve:
                err_label.configure(text=str(ve))
            except Exception:
                err_label.configure(text="Failed to save new type")

        ctk.CTkButton(btn_frame, text="Save", fg_color="#1a2a4a", command=do_save).pack(side="right", padx=(8,0))
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="transparent", command=do_cancel).pack(side="right")

    def on_status_change_add(self, *args):
        status = self.case_status_var.get()
        if status == "Referred":
            self.referred_to_entry.configure(state="normal", fg_color="white", border_color="#1a2a4a")
        else:
            self.referred_to_entry.delete(0, "end")
            self.referred_to_entry.configure(state="disabled", fg_color="#f1f5f9", border_color="#e2e8f0")

    def update_vawc_preview(self, event=None):
        try:
            year = self.date_entry.get_date().year
            latest = self.get_latest_vawc_number(year)
            latest_text = f"Latest VAWC No: {latest}" if latest else f"Latest VAWC No: none yet for {year}"
            self.latest_vawc_label.configure(text=latest_text)
        except Exception:
            if hasattr(self, 'latest_vawc_label'):
                self.latest_vawc_label.configure(text="Latest VAWC No: unavailable")

    def on_vawc_seq_key_release(self, event=None):
        # Allow only digits in sequence entry
        cur = self.vawc_seq_entry.get()
        digits = ''.join(ch for ch in cur if ch.isdigit())
        if digits != cur:
            self.vawc_seq_entry.delete(0, 'end')
            self.vawc_seq_entry.insert(0, digits)
        # update latest display
        self.update_vawc_preview()

    def on_vawc_seq_focus_out(self, event=None):
        cur = self.vawc_seq_entry.get().strip()
        if cur.isdigit():
            self.vawc_seq_entry.delete(0, 'end')
            self.vawc_seq_entry.insert(0, f"{int(cur):04d}")

    def on_report_date_key(self, event=None):
        current = self.date_entry.get().strip()
        digits = ''.join(ch for ch in current if ch.isdigit())
        formatted = ""
        for idx, ch in enumerate(digits):
            if idx == 2 or idx == 4:
                formatted += "/"
            formatted += ch
        if formatted != current:
            self.date_entry.delete(0, 'end')
            self.date_entry.insert(0, formatted)

    def on_report_date_focus_out(self, event=None):
        date_str = self.date_entry.get().strip()
        if not date_str:
            return
        for fmt in ("%m/%d/%Y", "%m-%d-%Y", "%m.%d.%Y", "%Y-%m-%d"):
            try:
                parsed = datetime.strptime(date_str, fmt)
                self.date_entry.set_date(parsed)
                self.update_vawc_format()
                return
            except ValueError:
                continue

    def get_next_vawc_sequence_placeholder(self):
        # Determines next sequence for current year
        try:
            year = self.date_entry.get_date().year
            connection = get_connection()
            cursor = connection.cursor()
            prefix = f"VAWC-{year}-"
            cursor.execute("SELECT MAX(vawc_no) FROM vawc_logs WHERE vawc_no LIKE ? AND is_deleted = 0", (prefix + '%',))
            row = cursor.fetchone()
            if row and row[0]:
                last = int(row[0].split('-')[-1])
                return f"{last+1:04d}"
            return "0001"
        except Exception:
            return "0001"

    def update_vawc_format(self, event=None):
        # Update year label and placeholder when date changes
        year = self.date_entry.get_date().year
        self.vawc_year_label.configure(text=str(year))
        # Update placeholder to next seq for that year if possible
        try:
            connection = get_connection()
            cursor = connection.cursor()
            prefix = f"VAWC-{year}-"
            cursor.execute("SELECT MAX(vawc_no) FROM vawc_logs WHERE vawc_no LIKE ? AND is_deleted = 0", (prefix + '%',))
            row = cursor.fetchone()
            if row and row[0]:
                nxt = int(row[0].split('-')[-1]) + 1
                self.vawc_seq_entry.configure(placeholder_text=f"{nxt:04d}")
            else:
                self.vawc_seq_entry.configure(placeholder_text="0001")
        except Exception:
            self.vawc_seq_entry.configure(placeholder_text="0001")
        self.update_vawc_preview()

    def normalize_vawc_no(self, value, report_date=None):
        if report_date is None:
            report_date = datetime.now()
        value = (value or "").strip().upper().replace(" ", "")
        if not value:
            return ""

        match = re.match(r'^(?:VAWC-)?(\d{4})-(\d+)$', value)
        if match:
            year = match.group(1)
            num = int(match.group(2))
            return f"VAWC-{year}-{num:04d}"

        match = re.match(r'^(\d{4})$', value)
        if match:
            num = int(match.group(1))
            return f"VAWC-{report_date.year}-{num:04d}"

        match = re.match(r'^(\d+)$', value)
        if match:
            num = int(match.group(1))
            return f"VAWC-{report_date.year}-{num:04d}"

        return value

    def get_latest_vawc_number(self, year=None):
        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()
            if year is None:
                year = self.date_entry.get_date().year
            prefix = f"VAWC-{year}-"
            cursor.execute("SELECT vawc_no FROM vawc_logs WHERE vawc_no LIKE ? AND is_deleted = 0 ORDER BY created_at DESC, id DESC LIMIT 1", (prefix + '%',))
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception:
            return None
        finally:
            if connection:
                connection.close()

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
        self.vawc_seq_entry.delete(0, "end")
        self.address_text.delete("1.0", "end")
        self.selected_abuses = []
        self.render_selected_abuses()
        self.abuse_entry.delete(0, "end")
        self.hide_suggestion_dropdown("abuse")

        self.respondent_entry.delete(0, "end")
        self.case_status_var.set("Settled")
        self.update_status_style("Settled")
        self.attachments = []
        self.refresh_file_list()
        self.remarks_text.delete("1.0", "end")
        self.vawc_year_label.configure(text=str(self.date_entry.get_date().year))
        self.vawc_seq_entry.configure(placeholder_text=self.get_next_vawc_sequence_placeholder())

    def has_unsaved_changes(self):
        """Check if any primary field has input that hasn't been saved"""
        try:
            if self.client_entry.get().strip(): return True
            if self.respondent_entry.get().strip(): return True
            if self.address_text.get("1.0", "end").strip(): return True
            if self.selected_abuses: return True
            if self.abuse_entry.get().strip(): return True
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
        
        abuses = [abuse for abuse in self.selected_abuses if abuse.strip()]
        current_abuse = self.abuse_entry.get().strip()
        if current_abuse and current_abuse.lower() not in [a.lower() for a in abuses]:
            abuses.append(current_abuse)
        if not abuses: errors.append("Type of Abuse (select at least one)")

        if birthdate_str:
            parsed_birthdate = None
            for fmt in ("%m/%d/%Y", "%m-%d-%Y", "%m.%d.%Y", "%Y-%m-%d"):
                try:
                    parsed_birthdate = datetime.strptime(birthdate_str, fmt)
                    birthdate_str = parsed_birthdate.strftime("%m/%d/%Y")
                    age = str(calculate_age(parsed_birthdate))
                    self.age_entry.delete(0, "end")
                    self.age_entry.insert(0, age)
                    break
                except ValueError:
                    continue
            if parsed_birthdate is None:
                messagebox.showwarning("Invalid Birthdate", "Please enter a valid birthdate in MM/DD/YYYY format.")
                return
        
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
        for abuse in abuses:
            try:
                ensure_abuse_type(abuse)
            except Exception:
                pass
        seq_value = self.vawc_seq_entry.get().strip()
        if seq_value and seq_value.isdigit():
            vawc_no = f"VAWC-{self.date_entry.get_date().year}-{int(seq_value):04d}"
        else:
            vawc_no = generate_vawc_number(date)

        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()

            # If generated or entered VAWC already exists, fail gracefully or retry for auto-generated values.
            cursor.execute("SELECT id FROM vawc_logs WHERE vawc_no = ?", (vawc_no,))
            existing = cursor.fetchone()
            if existing:
                if seq_value:
                    messagebox.showwarning("Duplicate VAWC No", f"The VAWC Number {vawc_no} already exists. Please use a different VAWC Number.")
                    return
                vawc_no = generate_vawc_number(date)
                cursor.execute("SELECT id FROM vawc_logs WHERE vawc_no = ?", (vawc_no,))
                if cursor.fetchone():
                    messagebox.showwarning("VAWC Number Error", "Unable to generate a unique VAWC Number. Please try again.")
                    return

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
            self.update_vawc_preview()
            
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