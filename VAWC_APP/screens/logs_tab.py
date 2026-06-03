import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import os
import sqlite3
from tkcalendar import DateEntry
from datetime import datetime
from db import get_connection
from db import get_abuse_types, add_abuse_type, update_abuse_type, delete_abuse_type
from utils.helpers import calculate_age
from utils.pdf_export import export_single_pdf
from .view_record import ViewRecordWindow
from .edit_record import EditRecordWindow

class LogsTabFrame(ctk.CTkFrame):
    def __init__(self, parent, username, user_role="Staff"):
        super().__init__(parent, fg_color="transparent")

        self.username = username
        self.user_role = user_role
        self.page = 0
        self.limit = 20
        self.search_term = ""
        self.filter_abuse = ""
        self.filter_status = ""
        self.filter_year = ""
        self.filter_month = ""
        self.selection_mode = False
        self.selected_vawc_nos = set()
        self._filter_after_id = None

        # Main Layout Container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.main_container.pack(fill="both", expand=True)

        # Table View Container
        self.table_view = ctk.CTkFrame(self.main_container, fg_color="transparent", corner_radius=0)
        self.table_view.pack(fill="both", expand=True)

        # Edit/Detail View Container (hidden initially)
        self.edit_view = ctk.CTkFrame(self.main_container, fg_color="transparent", corner_radius=0)
        
        self.setup_table_ui()

    def setup_table_ui(self):
        # Clear table view
        for widget in self.table_view.winfo_children():
            widget.destroy()

        # ================= FILTER SECTION =================
        filter_card = ctk.CTkFrame(self.table_view, fg_color=["#ffffff", "#1f2937"], corner_radius=16, border_width=1, border_color=["#e2e8f0", "#334155"])
        filter_card.pack(fill="x", padx=20, pady=(20, 10))
        
        filter_grid = ctk.CTkFrame(filter_card, fg_color="transparent")
        filter_grid.pack(fill="x", padx=20, pady=18)

        # Row 1: Search & Abuse Filter
        row1 = ctk.CTkFrame(filter_grid, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 10))
        
        # Search
        search_container = ctk.CTkFrame(row1, fg_color="transparent")
        search_container.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry = ctk.CTkEntry(search_container, placeholder_text="🔍 Search by name, VAWC No, respondent...", 
                                        height=40, corner_radius=8, border_width=1, border_color=["#e2e8f0", "#333333"])
        self.search_entry.pack(fill="x")
        self.search_entry.bind("<KeyRelease>", self.schedule_filter)

        # Abuse Dropdown
        self.abuse_var = ctk.StringVar(value="Type of Abuse")
        self.abuse_combo = ctk.CTkComboBox(row1, variable=self.abuse_var, values=["Type of Abuse"] + self.get_abuse_types(), 
                                           height=40, corner_radius=8, border_width=1, border_color=["#e2e8f0", "#333333"], command=self.on_filter)
        self.abuse_combo.pack(side="left", padx=5)

        # Row 2: Status, Year, Month, Clear
        row2 = ctk.CTkFrame(filter_grid, fg_color="transparent")
        row2.pack(fill="x")

        self.status_var = ctk.StringVar(value="Status")
        self.status_combo = ctk.CTkComboBox(row2, variable=self.status_var, values=["Status", "Ongoing", "Settled", "Referred", "Archived", "Issued BPO"], 
                                            height=40, corner_radius=8, command=self.on_filter)
        self.status_combo.pack(side="left", padx=(0, 10))

        self.year_var = ctk.StringVar(value="Year")
        self.year_combo = ctk.CTkComboBox(row2, variable=self.year_var, values=["Year"] + [str(y) for y in range(datetime.now().year, 2019, -1)], 
                                          height=40, corner_radius=8, command=self.on_filter)
        self.year_combo.pack(side="left", padx=5)

        self.month_var = ctk.StringVar(value="Month")
        self.month_combo = ctk.CTkComboBox(row2, variable=self.month_var, values=["Month", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"], 
                                           height=40, corner_radius=8, command=self.on_filter)
        self.month_combo.pack(side="left", padx=5)

        self.btn_clear = ctk.CTkButton(row2, text="Clear Filters", command=self.clear_filters, fg_color=["#f1f5f9", "#111827"], 
                                       text_color=["#0f172a", "#f8fafc"], border_width=1, border_color=["#cbd5e1", "#334155"], height=40, corner_radius=10)
        self.btn_clear.pack(side="left", padx=10)

        # Record Count Label
        self.count_label = ctk.CTkLabel(row2, text="Showing 0 records", font=("Arial", 12), text_color=["#64748b", "#94a3b8"])
        self.count_label.pack(side="right", padx=10)

        # ================= TABLE SECTION =================
        table_card = ctk.CTkFrame(self.table_view, fg_color=["#ffffff", "#1f2937"], corner_radius=16, border_width=1, border_color=["#e2e8f0", "#334155"])
        table_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Action Toolbar
        toolbar = ctk.CTkFrame(table_card, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=15)
        
        if not self.selection_mode:
            self.btn_delete_trigger = ctk.CTkButton(toolbar, text="🗑 Delete", command=self.toggle_selection_mode, 
                                                    fg_color="transparent", text_color="#dc2626", border_width=1, border_color=["#fecaca", "#7f1d1d"], 
                                                    height=32, corner_radius=6, font=("Arial", 12, "bold"))
            self.btn_delete_trigger.pack(side="left")
        else:
            self.btn_confirm_del = ctk.CTkButton(toolbar, text="Confirm Delete", command=self.delete_selected, 
                                                 fg_color="#dc2626", hover_color="#b91c1c", height=32, corner_radius=6)
            self.btn_confirm_del.pack(side="left")
            
            self.btn_cancel_del = ctk.CTkButton(toolbar, text="Cancel", command=self.toggle_selection_mode, 
                                                fg_color="transparent", text_color=["#64748b", "#94a3b8"], height=32, corner_radius=6)
            self.btn_cancel_del.pack(side="left", padx=10)

        # Treeview (Professional Style)
        table_frame = ctk.CTkFrame(table_card, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Theme-aware Treeview styling (match other screens)
        is_dark = ctk.get_appearance_mode() == "Dark"
        tree_bg = "#ffffff" if not is_dark else "#2b2b2b"
        tree_fg = "#000000" if not is_dark else "#ffffff"
        heading_bg = "#f1f5f9" if not is_dark else "#1a1a1a"

        style = ttk.Style()
        style.configure(
            "Treeview",
            background=tree_bg,
            foreground=tree_fg,
            rowheight=38,
            fieldbackground=tree_bg,
            font=("Arial", 11),
            borderwidth=0,
        )
        style.map("Treeview", background=[("selected", "#1a2a4a")], foreground=[("selected", "#ffffff")])

        style.configure(
            "Treeview.Heading",
            background=heading_bg,
            foreground=tree_fg,
            font=("Arial", 11, "bold"),
            borderwidth=0,
        )

        # Improve separator/row look slightly in both themes
        style.configure("Treeview", highlightthickness=0)

        self.tree = ttk.Treeview(
            table_frame,
            columns=("Select", "ID", "VAWC No", "Date", "Client Name", "Age", "Type of Abuse", "Respondent", "Case Status", "Referred To"),
            show="headings",
            selectmode="browse"
        )

        # Configure tags with single strings (ttk doesn't support tuples)
        # Base row styling
        self.tree.tag_configure("evenrow", background="#242424" if is_dark else "#ffffff", foreground="#ffffff" if is_dark else "#000000")
        self.tree.tag_configure("oddrow", background="#1e1e1e" if is_dark else "#f8fafc", foreground="#ffffff" if is_dark else "#000000")

        # Status-only coloring
        # We will use symbols/emojis for status to provide color without coloring the whole row
        # Since standard ttk.Treeview doesn't support per-cell coloring, we'll use colored symbols
        self.tree.tag_configure("status_ongoing", foreground="#16a34a") # Green
        self.tree.tag_configure("status_settled", foreground="#dc2626") # Red
        self.tree.tag_configure("status_referred", foreground="#2563eb") # Blue

        # Column alignment (readability)
        self.tree.column("Select", width=40, anchor="center")
        self.tree.column("ID", width=70, anchor="center")
        self.tree.column("VAWC No", width=140, anchor="w")
        self.tree.column("Date", width=100, anchor="center")
        self.tree.column("Client Name", width=180, anchor="w")
        self.tree.column("Age", width=50, anchor="center")
        self.tree.column("Type of Abuse", width=160, anchor="w")
        self.tree.column("Respondent", width=160, anchor="w")
        self.tree.column("Case Status", width=100, anchor="center")
        self.tree.column("Referred To", width=120, anchor="w")

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col if col != "Select" else "")

        if not self.selection_mode:
            self.tree.column("Select", width=0, stretch=False)

        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-1>", self.on_click)

        # Custom Scrollbar
        scrollbar = ctk.CTkScrollbar(table_frame, orientation="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Compact Pagination
        pagination = ctk.CTkFrame(table_card, fg_color="transparent")
        pagination.pack(fill="x", padx=20, pady=(0, 15))
        
        page_controls = ctk.CTkFrame(pagination, fg_color="transparent")
        page_controls.pack(side="right")

        self.btn_prev = ctk.CTkButton(page_controls, text="‹", width=32, height=32, command=self.prev_page, 
                                      fg_color="white", text_color="#0f172a", border_width=1, border_color="#e2e8f0")
        self.btn_prev.pack(side="left", padx=2)

        self.page_label = ctk.CTkLabel(page_controls, text="Page 1 of 1", font=("Arial", 11), text_color="#64748b")
        self.page_label.pack(side="left", padx=10)

        self.btn_next = ctk.CTkButton(page_controls, text="›", width=32, height=32, command=self.next_page, 
                                      fg_color="white", text_color="#0f172a", border_width=1, border_color="#e2e8f0")
        self.btn_next.pack(side="left", padx=2)

        self.load_data()

    # ================= FUNCTIONS =================

    def get_abuse_types(self):
        try:
            return get_abuse_types()
        except Exception:
            return [
                "Domestic Abuse", "Financial Abuse", "Material Abuse", "Modern Slavery",
                "Criminal Exploitation", "Neglect", "Acts of Omission", "Organisational Abuse",
                "Self-Neglect", "Hoarding", "Sexual Abuse", "Sexual Exploitation",
                "Emotional Abuse", "Psychological Abuse"
            ]

    def schedule_filter(self, event=None):
        if getattr(self, '_filter_after_id', None):
            try:
                self.after_cancel(self._filter_after_id)
            except Exception:
                pass
        self._filter_after_id = self.after(250, self.on_filter)

    def on_filter(self, event=None):
        self.search_term = self.search_entry.get().strip()
        self.filter_abuse = self.abuse_var.get().strip()
        self.filter_status = self.status_var.get().strip()
        self.filter_year = self.year_var.get().strip()
        self.filter_month = self.month_var.get().strip()

        if self.filter_abuse == "Type of Abuse":
            self.filter_abuse = ""
        if self.filter_status == "Status":
            self.filter_status = ""
        if self.filter_year == "Year":
            self.filter_year = ""
        if self.filter_month == "Month":
            self.filter_month = ""

        self.page = 0
        self.load_data()

    def clear_filters(self):
        self.search_entry.delete(0, 'end')
        self.abuse_var.set("Type of Abuse")
        self.status_var.set("Status")
        self.year_var.set("Year")
        self.month_var.set("Month")
        self.on_filter()

    def load_data(self):
        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()

            def escape_like(s):
                return s.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')

            # Get total count for pagination
            count_query = "SELECT COUNT(*) FROM vawc_logs WHERE is_deleted = 0"
            params = []

            if self.search_term:
                count_query += " AND (client_name LIKE ? ESCAPE '\\' OR vawc_no LIKE ? ESCAPE '\\' OR name_of_respondent LIKE ? ESCAPE '\\' OR CAST(id AS TEXT) LIKE ? ESCAPE '\\')"
                term = f"%{escape_like(self.search_term)}%"
                params.extend([term, term, term, term])

            if self.filter_abuse:
                count_query += " AND type_of_abuse LIKE ? ESCAPE '\\'"
                params.append(f"%{escape_like(self.filter_abuse)}%")

            if self.filter_status:
                count_query += " AND case_status = ?"
                params.append(self.filter_status)

            if self.filter_year:
                count_query += " AND strftime('%Y', date) = ?"
                params.append(self.filter_year)

            if self.filter_month:
                count_query += " AND strftime('%m', date) = ?"
                params.append(self.filter_month)

            cursor.execute(count_query, params)
            self.total_count = cursor.fetchone()[0]

            # Update pagination label
            total_pages = (self.total_count + self.limit - 1) // self.limit if self.total_count > 0 else 1
            if hasattr(self, 'page_label'):
                self.page_label.configure(text=f"Page {self.page + 1} of {total_pages}")

            # Fetch data
            query = "SELECT '☐', id, vawc_no, date, client_name, age, type_of_abuse, name_of_respondent, case_status, referred_to FROM vawc_logs WHERE is_deleted = 0"

            # Reuse filters from count_query
            if self.search_term:
                query += " AND (client_name LIKE ? ESCAPE '\\' OR vawc_no LIKE ? ESCAPE '\\' OR name_of_respondent LIKE ? ESCAPE '\\' OR CAST(id AS TEXT) LIKE ? ESCAPE '\\')"
            if self.filter_abuse:
                query += " AND type_of_abuse LIKE ? ESCAPE '\\'"
            if self.filter_status:
                query += " AND case_status = ?"
            if self.filter_year:
                query += " AND strftime('%Y', date) = ?"
            if self.filter_month:
                query += " AND strftime('%m', date) = ?"

            query += " ORDER BY date DESC, vawc_no DESC LIMIT ? OFFSET ?"
            params.extend([self.limit, self.page * self.limit])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            for item in self.tree.get_children():
                self.tree.delete(item)

            # Alternating row colors with checkbox state
            for i, row in enumerate(rows):
                vawc_no = row[2]
                check_char = "☑" if vawc_no in self.selected_vawc_nos else "☐"

                # Format Referred To with a symbol if present
                ref_to = row[9]
                display_ref = ref_to if ref_to and ref_to != "None" else ""

                display_row = (check_char, row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], display_ref)
                tag = "evenrow" if i % 2 == 0 else "oddrow"

                # Apply special tag for status colors
                status = row[8]
                if status == "Ongoing":
                    tags = (tag, "status_ongoing")
                elif status == "Settled":
                    tags = (tag, "status_settled")
                elif status == "Referred":
                    tags = (tag, "status_referred")
                else:
                    tags = (tag,)

                self.tree.insert("", "end", values=display_row, tags=tags)

            # Update count label
            if hasattr(self, 'count_label'):
                start = self.page * self.limit + 1 if self.total_count > 0 else 0
                end = min((self.page + 1) * self.limit, self.total_count)
                self.count_label.configure(text=f"Showing {start}-{end} of {self.total_count} records")

        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            if connection:
                connection.close()

    def prev_page(self):
        if self.page > 0:
            self.page -= 1
            self.load_data()

    def next_page(self):
        total_pages = (self.total_count + self.limit - 1) // self.limit
        if self.page < total_pages - 1:
            self.page += 1
            self.load_data()

    def refresh(self):
        """Refresh the logs data"""
        self.load_data()



    def on_double_click(self, event):
        if self.selection_mode:
            return
        selected = self.tree.selection()
        if selected:
            item = selected[0]
            values = self.tree.item(item, "values")
            self.open_inline_edit(values[2]) # Use VAWC No

    def on_click(self, event):
        """Handle checkbox clicks in selection mode"""
        if not self.selection_mode:
            return
        
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == "#1": # Select column
                item = self.tree.identify_row(event.y)
                if item:
                    vawc_no = self.tree.item(item, "values")[2]
                    if vawc_no in self.selected_vawc_nos:
                        self.selected_vawc_nos.remove(vawc_no)
                        self.tree.set(item, "Select", "☐")
                    else:
                        self.selected_vawc_nos.add(vawc_no)
                        self.tree.set(item, "Select", "☑")

    def toggle_selection_mode(self):
        self.selection_mode = not self.selection_mode
        self.selected_vawc_nos.clear()
        self.setup_table_ui()

    def delete_selected(self):
        if not self.selected_vawc_nos:
            messagebox.showwarning("Warning", "No records selected.")
            return

        count = len(self.selected_vawc_nos)
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to soft-delete {count} selected record(s)?\nRecords can be restored from Settings later."):
            connection = None
            try:
                connection = get_connection()
                cursor = connection.cursor()
                vawc_nos = list(self.selected_vawc_nos)
                cursor.executemany(
                    "UPDATE vawc_logs SET is_deleted = 1, deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE vawc_no = ?",
                    [(vawc_no,) for vawc_no in vawc_nos]
                )
                cursor.executemany(
                    "INSERT INTO audit_logs (username, action, target_record, details) VALUES (?, ?, ?, ?)",
                    [(self.username, "Delete Record", vawc_no, "Moved to Trash (Archived)") for vawc_no in vawc_nos]
                )
                connection.commit()
                messagebox.showinfo("Success", f"{count} records moved to Trash.")
                self.toggle_selection_mode()
                self.load_data()
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                if connection:
                    connection.close()

    def open_inline_edit(self, vawc_no=None):
        try:
            if not vawc_no:
                selected = self.tree.selection()
                if not selected:
                    messagebox.showwarning("Warning", "Please select a record to edit.")
                    return
                vawc_no = self.tree.item(selected[0], "values")[2]

            # Log view action
            from db import log_action
            log_action(self.username, "View Record", target_record=vawc_no)

            # Switch view
            self.table_view.pack_forget()
            self.edit_view.pack(fill="both", expand=True)
            
            # Setup Edit UI
            for widget in self.edit_view.winfo_children():
                widget.destroy()
                
            # Inline Edit Panel
            edit_panel = InlineEditPanel(self.edit_view, vawc_no, self.username, self.user_role, on_save=self.close_inline_edit, on_cancel=self.close_inline_edit)
            edit_panel.pack(fill="both", expand=True)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open edit view: {str(e)}")

    def close_inline_edit(self):
        self.edit_view.pack_forget()
        self.table_view.pack(fill="both", expand=True)
        self.load_data()

class InlineEditPanel(ctk.CTkFrame):
    def __init__(self, parent, vawc_no, username, user_role, on_save, on_cancel):
        super().__init__(parent, fg_color="transparent")
        self.vawc_no = vawc_no
        self.username = username
        self.user_role = user_role
        self.on_save_callback = on_save
        self.on_cancel_callback = on_cancel
        self.attachments = []
        self.is_editable = False # Default to view mode
        
        # Load Record
        self.record = self.load_record()
        if not self.record:
            self.on_cancel_callback()
            return

        # Main Layout
        self.setup_sticky_header()

        # Main scrollable container
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.setup_sticky_footer()

        # Form Card
        self.form_card = ctk.CTkFrame(self.scroll_container, fg_color=["white", "#242424"], corner_radius=15, border_width=1, border_color=["#e2e8f0", "#333333"])
        self.form_card.pack(fill="x", padx=40, pady=10)

        # Header Banner
        self.header_banner = ctk.CTkFrame(self.form_card, fg_color="#1a2a4a", corner_radius=15, height=80)
        self.header_banner.pack(fill="x", padx=0, pady=0)
        self.header_banner.pack_propagate(False)
        
        self.title_label = ctk.CTkLabel(self.header_banner, text=f"Record Details: {vawc_no}", font=("Arial", 20, "bold"), text_color="white")
        self.title_label.pack(pady=(15, 2))
        self.subtitle_label = ctk.CTkLabel(self.header_banner, text="Viewing record details", font=("Arial", 12), text_color="#e0e0e0")
        self.subtitle_label.pack()

        # Content Container
        self.content_frame = ctk.CTkFrame(self.form_card, fg_color="transparent", corner_radius=0)
        self.content_frame.pack(fill="x", padx=30, pady=25)

        self.setup_fields()
        self.set_editable(False) # Initial state

    def setup_sticky_header(self):
        self.header_actions = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.header_actions.pack(fill="x", padx=60, pady=(20, 10))
        
        # We'll use this for Edit/Save/Cancel buttons
        self.edit_btn_container = ctk.CTkFrame(self.header_actions, fg_color="transparent", corner_radius=0)
        self.edit_btn_container.pack(side="right")
        
        self.btn_save = ctk.CTkButton(self.edit_btn_container, text="Save Changes", font=("Arial", 13, "bold"), fg_color="#1a73e8", hover_color="#1557b0", height=40, width=140, command=self.save)
        self.btn_cancel_edit = ctk.CTkButton(self.edit_btn_container, text="Cancel", font=("Arial", 13), fg_color="#6c757d", hover_color="#5a6268", height=40, width=100, command=self.cancel_edit)
        self.btn_edit = ctk.CTkButton(self.edit_btn_container, text="📝 Edit Record", font=("Arial", 13, "bold"), fg_color="#1a2a4a", hover_color="#101a2e", height=40, width=140, command=lambda: self.set_editable(True))

    def setup_sticky_footer(self):
        self.footer_actions = ctk.CTkFrame(self, fg_color=["white", "#242424"], height=70, corner_radius=0, border_width=1, border_color=["#e2e8f0", "#333333"])
        self.footer_actions.pack(side="bottom", fill="x")
        
        inner_footer = ctk.CTkFrame(self.footer_actions, fg_color="transparent", corner_radius=0)
        inner_footer.pack(fill="x", padx=60, pady=15)

        self.btn_print = ctk.CTkButton(inner_footer, text="🖨 Print Record", font=("Arial", 13, "bold"), fg_color="#2c3e50", hover_color="#1a252f", height=40, width=140, command=self.print_record)
        self.btn_print.pack(side="left")

        ctk.CTkButton(inner_footer, text="Back to Logs", font=("Arial", 13), fg_color="transparent", text_color=["#333333", "#cbd5e1"], border_width=1, border_color=["#cccccc", "#555555"], height=40, width=120, command=self.on_cancel_callback).pack(side="right")

    def on_status_change(self, *args):
        if not hasattr(self, 'referred_entry'): return
        
        status = self.case_status_var.get()
        is_referred = (status == "Referred")
        
        # In edit mode, enable/disable based on status
        if self.is_editable:
            if is_referred:
                self.referred_entry.configure(state="normal", fg_color=["white", "#2b2b2b"], border_color="#1a2a4a")
                self.referred_hint.pack_forget() # Hide hint when enabled
            else:
                self.referred_entry.delete(0, "end") # Clear if not referred
                self.referred_entry.configure(state="disabled", fg_color=["#f1f5f9", "#1a1a1a"], border_color=["#e2e8f0", "#333333"])
                self.referred_hint.pack(anchor="w") # Show hint when disabled in edit mode

    def set_editable(self, editable):
        self.is_editable = editable
        state = "normal" if editable else "disabled"
        
        # Update Header
        self.header_banner.configure(fg_color=["#1a73e8", "#1e3a5f"] if editable else ["#1a2a4a", "#0f172a"])
        self.title_label.configure(text=f"{'Edit' if editable else 'Record Details'}: {self.vawc_no}")
        self.subtitle_label.configure(text="Update the information below and save changes" if editable else "Viewing record details")

        # Update Fields
        self.vawc_no_entry.configure(state=state)
        self.date_entry.configure(state=state)
        self.client_entry.configure(state=state)
        self.birthdate_entry.configure(state=state)
        self.age_entry.configure(state=state)
        self.contact_entry.configure(state=state)
        self.address_text.configure(state=state)
        self.respondent_entry.configure(state=state)
        self.remarks_text.configure(state=state)
        self.case_status_menu.configure(state=state)
        self.upload_btn.configure(state=state)

        # Referred To field handling
        if not editable:
            # View mode: always disabled
            self.referred_entry.configure(state="disabled", fg_color=["#f9f9f9", "#1a1a1a"], border_width=0, text_color=["#333333", "#cbd5e1"])
            self.referred_hint.pack_forget()
        else:
            # Edit mode: call on_status_change to set correct state
            self.on_status_change()

        # Update Checkboxes
        for var in self.abuse_vars.values():
            pill = var._pill_widget
            for widget in pill.winfo_children():
                if isinstance(widget, ctk.CTkCheckBox):
                    widget.configure(state=state)

        # Style updates for better read-only view
        input_bg = ["white", "#2b2b2b"] if editable else ["#f9f9f9", "#1a1a1a"]
        border_width = 2 if editable else 0
        text_color = ["black", "white"] if editable else ["#333333", "#cbd5e1"]

        for widget in [self.vawc_no_entry, self.client_entry, self.birthdate_entry, self.age_entry, self.contact_entry, self.respondent_entry]:
            widget.configure(fg_color=input_bg, border_width=border_width, text_color=text_color)
        
        self.address_text.configure(fg_color=input_bg, border_width=border_width, text_color=text_color)
        self.remarks_text.configure(fg_color=input_bg, border_width=border_width, text_color=text_color)

        # Update Buttons
        self.btn_save.pack_forget()
        self.btn_edit.pack_forget()
        self.btn_cancel_edit.pack_forget()
        
        if editable:
            self.btn_save.pack(side="right", padx=(10, 0))
            self.btn_cancel_edit.pack(side="right", padx=(10, 0))
        else:
            self.btn_edit.pack(side="right", padx=(10, 0))

    def load_record(self):
        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM vawc_logs WHERE vawc_no = ?", (self.vawc_no,))
            record = cursor.fetchone()
            return record
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return None
        finally:
            if connection:
                connection.close()

    def setup_fields(self):
        # Re-using the same professional layout from AddRecordFrame
        def create_label(parent, text):
            return ctk.CTkLabel(parent, text=text, font=("Arial", 11, "bold"), text_color=["#1a2a4a", "#f8fafc"], anchor="w")

        # Row 1: ID | VAWC No
        row0 = ctk.CTkFrame(self.content_frame, fg_color="transparent", corner_radius=0)
        row0.pack(fill="x", pady=10)
        row0.grid_columnconfigure((0, 1), weight=1)

        col0_1 = ctk.CTkFrame(row0, fg_color="transparent", corner_radius=0)
        col0_1.grid(row=0, column=0, padx=(0, 15), sticky="nsew")
        create_label(col0_1, "Record ID").pack(fill="x")
        self.id_entry = ctk.CTkEntry(col0_1, border_width=2, height=38, border_color=["#dce4ee", "#333333"], state="disabled")
        self.id_entry.pack(fill="x", pady=(5, 0))

        col0_2 = ctk.CTkFrame(row0, fg_color="transparent", corner_radius=0)
        col0_2.grid(row=0, column=1, sticky="nsew")
        create_label(col0_2, "VAWC Number").pack(fill="x")
        self.vawc_no_entry = ctk.CTkEntry(col0_2, border_width=2, height=38, border_color=["#dce4ee", "#333333"])
        self.vawc_no_entry.pack(fill="x", pady=(5, 0))

        # Row 2: Date | Client Name
        row1 = ctk.CTkFrame(self.content_frame, fg_color="transparent", corner_radius=0)
        row1.pack(fill="x", pady=10)
        row1.grid_columnconfigure((0, 1), weight=1)

        col1_1 = ctk.CTkFrame(row1, fg_color="transparent", corner_radius=0)
        col1_1.grid(row=0, column=0, padx=(0, 15), sticky="nsew")
        create_label(col1_1, "Date of Report").pack(fill="x")
        self.date_entry = DateEntry(col1_1, date_pattern="mm/dd/yyyy", font=("Arial", 11))
        self.date_entry.pack(fill="x", pady=(5, 0), ipady=3)

        col1_2 = ctk.CTkFrame(row1, fg_color="transparent", corner_radius=0)
        col1_2.grid(row=0, column=1, sticky="nsew")
        create_label(col1_2, "Client Name").pack(fill="x")
        self.client_entry = ctk.CTkEntry(col1_2, border_width=2, height=38, border_color=["#dce4ee", "#333333"])
        self.client_entry.pack(fill="x", pady=(5, 0))

        # Row 2: Birthdate | Age
        row2 = ctk.CTkFrame(self.content_frame, fg_color="transparent", corner_radius=0)
        row2.pack(fill="x", pady=10)
        row2.grid_columnconfigure((0, 1), weight=1)

        col2_1 = ctk.CTkFrame(row2, fg_color="transparent", corner_radius=0)
        col2_1.grid(row=0, column=0, padx=(0, 15), sticky="nsew")
        create_label(col2_1, "Birthdate (MM/DD/YYYY)").pack(fill="x")
        self.birthdate_entry = ctk.CTkEntry(col2_1, border_width=2, height=38, border_color=["#dce4ee", "#333333"])
        self.birthdate_entry.pack(fill="x", pady=(5, 0))
        self.birthdate_entry.bind("<KeyRelease>", self.on_birthdate_key)
        self.birthdate_entry.bind("<FocusOut>", self.on_birthdate_focus_out)

        col2_2 = ctk.CTkFrame(row2, fg_color="transparent", corner_radius=0)
        col2_2.grid(row=0, column=1, sticky="nsew")
        create_label(col2_2, "Age").pack(fill="x")
        self.age_entry = ctk.CTkEntry(col2_2, border_width=2, height=38, border_color=["#dce4ee", "#333333"])
        self.age_entry.pack(fill="x", pady=(5, 0))

        # Row 3: Contact | Address
        row3 = ctk.CTkFrame(self.content_frame, fg_color="transparent", corner_radius=0)
        row3.pack(fill="x", pady=10)
        row3.grid_columnconfigure((0, 1), weight=1)

        col3_1 = ctk.CTkFrame(row3, fg_color="transparent", corner_radius=0)
        col3_1.grid(row=0, column=0, padx=(0, 15), sticky="nsew")
        create_label(col3_1, "Contact Information").pack(fill="x")
        self.contact_entry = ctk.CTkEntry(col3_1, border_width=2, height=38, border_color=["#dce4ee", "#333333"])
        self.contact_entry.pack(fill="x", pady=(5, 0))

        col3_2 = ctk.CTkFrame(row3, fg_color="transparent", corner_radius=0)
        col3_2.grid(row=0, column=1, sticky="nsew")
        create_label(col3_2, "Complete Address").pack(fill="x")
        self.address_text = ctk.CTkTextbox(col3_2, height=38, border_width=2, border_color=["#dce4ee", "#333333"])
        self.address_text.pack(fill="x", pady=(5, 0))

        # Row 4: Respondent
        row4 = ctk.CTkFrame(self.content_frame, fg_color="transparent", corner_radius=0)
        row4.pack(fill="x", pady=10)
        create_label(row4, "Name of Respondent").pack(fill="x")
        self.respondent_entry = ctk.CTkEntry(row4, border_width=2, height=38, border_color=["#dce4ee", "#333333"])
        self.respondent_entry.pack(fill="x", pady=(5, 0))

        # Row 5: Abuse Grid
        row5 = ctk.CTkFrame(self.content_frame, fg_color="transparent", corner_radius=0)
        row5.pack(fill="x", pady=(15, 10))
        create_label(row5, "Type of Abuse").pack(fill="x", pady=(0, 10))
        
        self.abuse_vars = {}
        self.abuse_order = get_abuse_types()
        existing_abuses = set(self.record[8].split(", ")) if self.record[8] else set()
        self.abuse_frame = ctk.CTkFrame(row5, fg_color="transparent", corner_radius=0)
        self.abuse_frame.pack(fill="x")
        self.render_abuse_grid(existing_abuses)

        # Row 6: Remarks
        row6 = ctk.CTkFrame(self.content_frame, fg_color="transparent", corner_radius=0)
        row6.pack(fill="x", pady=10)
        create_label(row6, "Case Remarks / Notes").pack(fill="x")
        self.remarks_text = ctk.CTkTextbox(row6, height=100, border_width=2, border_color=["#dce4ee", "#333333"])
        self.remarks_text.pack(fill="x", pady=(5, 0))

        # Row 7: Case Status | Referred To
        row7 = ctk.CTkFrame(self.content_frame, fg_color="transparent", corner_radius=0)
        row7.pack(fill="x", pady=10)
        row7.grid_columnconfigure((0, 1), weight=1)

        col7_1 = ctk.CTkFrame(row7, fg_color="transparent", corner_radius=0)
        col7_1.grid(row=0, column=0, padx=(0, 15), sticky="nsew")
        create_label(col7_1, "Case Status").pack(fill="x")
        self.case_status_var = ctk.StringVar(value="Settled")
        self.case_status_menu = ctk.CTkOptionMenu(col7_1, values=["Ongoing", "Settled", "Issued BPO", "Referred"], 
                                                 variable=self.case_status_var, height=38, command=self.update_status_style)
        self.case_status_menu.pack(fill="x", pady=(5, 0))
        # Add trace to handle referred_to field
        self.case_status_var.trace_add("write", self.on_status_change)

        col7_2 = ctk.CTkFrame(row7, fg_color="transparent", corner_radius=0)
        col7_2.grid(row=0, column=1, sticky="nsew")
        create_label(col7_2, "Referred To (Agency)").pack(fill="x")
        self.referred_entry = ctk.CTkEntry(col7_2, border_width=2, height=38, border_color=["#dce4ee", "#333333"])
        self.referred_entry.pack(fill="x", pady=(5, 0))
        
        # Hint label for referred_to
        self.referred_hint = ctk.CTkLabel(col7_2, text="Set Case Status to 'Referred' to enable this field", 
                                          font=("Arial", 10), text_color="#94a3b8")
        self.referred_hint.pack(anchor="w")

        # Row 8: Attachments
        row8 = ctk.CTkFrame(self.content_frame, fg_color="transparent", corner_radius=0)
        row8.pack(fill="x", pady=15)
        create_label(row8, "Attachments").pack(fill="x", pady=(0, 5))
        
        # Thumbnail Preview Area
        self.thumbnail_frame = ctk.CTkFrame(row8, fg_color="transparent")
        self.thumbnail_frame.pack(fill="x", pady=(0, 10))

        self.upload_area = ctk.CTkFrame(row8, fg_color=["#f8f9fa", "#1a1a1a"], border_width=2, border_color=["#dce4ee", "#333333"], corner_radius=10, height=60)
        self.upload_area.pack(fill="x")
        self.upload_area.pack_propagate(False)
        self.upload_btn = ctk.CTkButton(self.upload_area, text="📎 Click to attach files", fg_color="transparent", text_color=["#1a2a4a", "#cbd5e1"], command=self.select_attachments)
        self.upload_btn.pack(expand=True)
        self.file_list_frame = ctk.CTkFrame(row8, fg_color="transparent", corner_radius=0)
        self.file_list_frame.pack(fill="x", pady=5)

        # Populate with initial values
        self.setup_field_values()

    def update_pill_style(self, abuse, pill, var):
        if not self.is_editable:
            # Revert change if not editable
            var.set(abuse in set(self.record[8].split(", ")) if self.record[8] else False)
            return

        if var.get():
            pill.configure(fg_color="#1a2a4a", border_width=0)
            for widget in pill.winfo_children():
                if isinstance(widget, ctk.CTkCheckBox): widget.configure(text_color="white")
        else:
            pill.configure(fg_color="white", border_width=1, border_color="#cccccc")
            for widget in pill.winfo_children():
                if isinstance(widget, ctk.CTkCheckBox): widget.configure(text_color="black")

    def print_record(self):
        try:
            path = export_single_pdf(self.record)
            if path:
                messagebox.showinfo("Success", f"Record exported successfully to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to print: {str(e)}")

    def cancel_edit(self):
        # Discard changes by re-loading and re-setting fields
        self.record = self.load_record()
        if self.record:
            self.setup_field_values()
            self.set_editable(False)

    def setup_field_values(self):
        # Date
        if self.record[2]:
            self.date_entry.set_date(datetime.strptime(self.record[2], "%Y-%m-%d"))
        
        # ID
        self.id_entry.delete(0, "end")
        self.id_entry.insert(0, str(self.record[0]) if self.record[0] is not None else "")

        # VAWC Number
        self.vawc_no_entry.delete(0, "end")
        self.vawc_no_entry.insert(0, self.record[1] or "")

        # Client Name
        self.client_entry.delete(0, "end")
        self.client_entry.insert(0, self.record[3] or "")

        # Birthdate
        self.birthdate_entry.delete(0, "end")
        if self.record[6]:
            try:
                bd_obj = datetime.strptime(self.record[6], "%Y-%m-%d")
                self.birthdate_entry.insert(0, bd_obj.strftime("%m/%d/%Y"))
            except:
                self.birthdate_entry.insert(0, self.record[6])

        # Age
        self.age_entry.delete(0, "end")
        self.age_entry.insert(0, str(self.record[4]) if self.record[4] else "")

        # Contact
        self.contact_entry.delete(0, "end")
        self.contact_entry.insert(0, self.record[5] or "")

        # Address
        self.address_text.delete("1.0", "end")
        self.address_text.insert("1.0", self.record[7] or "")

        # Respondent
        self.respondent_entry.delete(0, "end")
        self.respondent_entry.insert(0, self.record[9] or "")

        # Abuses
        existing_abuses = set(self.record[8].split(", ")) if self.record[8] else set()
        for abuse, var in self.abuse_vars.items():
            var.set(abuse in existing_abuses)
            # Need to update pill styles manually since update_pill_style checks is_editable
            # We temporarily set is_editable to True to allow the style update, or just update directly
            pill = var._pill_widget # We'll need to store this
            self.update_pill_style_direct(abuse, pill, var)

        # Remarks
        self.remarks_text.delete("1.0", "end")
        self.remarks_text.insert("1.0", self.record[12] or "")

        # Referred To
        self.referred_entry.configure(state="normal")
        self.referred_entry.delete(0, "end")
        self.referred_entry.insert(0, self.record[13] or "")
        if not self.is_editable:
            self.referred_entry.configure(state="disabled")

        # Status
        self.case_status_var.set(self.record[10] or "Settled")
        self.update_status_style(self.case_status_var.get())

        # Attachments
        if self.record[11]:
            self.attachments = self.record[11].split(";")
        else:
            self.attachments = []
        self.refresh_file_list()

    def render_abuse_grid(self, existing_abuses=None):
        existing_abuses = existing_abuses or set()
        self.abuse_order = get_abuse_types()
        for widget in self.abuse_frame.winfo_children():
            widget.destroy()

        for i, abuse in enumerate(self.abuse_order):
            var = self.abuse_vars.get(abuse) or ctk.BooleanVar(value=(abuse in existing_abuses))
            self.abuse_vars[abuse] = var
            pill = ctk.CTkFrame(self.abuse_frame, fg_color=["white", "#2b2b2b"], border_width=1, border_color=["#cccccc", "#555555"], corner_radius=20)
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
            add_pill = ctk.CTkFrame(self.abuse_frame, fg_color=["white", "#2b2b2b"], border_width=1, border_color=["#cccccc", "#555555"], corner_radius=20)
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

    def update_pill_style_direct(self, abuse, pill, var):
        if var.get():
            pill.configure(fg_color="#1a2a4a", border_width=0)
            for widget in pill.winfo_children():
                if isinstance(widget, ctk.CTkCheckBox): widget.configure(text_color="white")
        else:
            pill.configure(fg_color="white", border_width=1, border_color="#cccccc")
            for widget in pill.winfo_children():
                if isinstance(widget, ctk.CTkCheckBox): widget.configure(text_color="black")

    def update_status_style(self, choice):
        colors = {"Settled": ("#28a745", "#218838"), "Issued BPO": ("#1a73e8", "#1967d2")}
        fg, btn = colors.get(choice, ("#1a2a4a", "#101a2e"))
        self.case_status_menu.configure(fg_color=fg, button_color=btn)

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

    def select_attachments(self):
        files = filedialog.askopenfilenames()
        if files:
            for f in files:
                if f not in self.attachments: self.attachments.append(f)
            self.refresh_file_list()

    def refresh_file_list(self):
        for widget in self.file_list_frame.winfo_children():
            widget.destroy()
        for widget in self.thumbnail_frame.winfo_children():
            widget.destroy()

        from PIL import Image
        for i, file_path in enumerate(self.attachments):
            # File List Entry
            f_frame = ctk.CTkFrame(self.file_list_frame, fg_color="#eef0f4", corner_radius=5)
            f_frame.pack(fill="x", pady=2)
            
            ctk.CTkLabel(f_frame, text=os.path.basename(file_path), font=("Arial", 11)).pack(side="left", padx=10, pady=5)
            
            if self.is_editable:
                ctk.CTkButton(f_frame, text="❌", width=30, height=25, fg_color="#dc3545", hover_color="#c82333", 
                              command=lambda p=file_path: [self.attachments.remove(p), self.refresh_file_list()]).pack(side="right", padx=5)
            
            ctk.CTkButton(f_frame, text="👁 Open", width=60, height=25, fg_color="#1a2a4a", 
                          command=lambda p=file_path: os.startfile(p) if hasattr(os, 'startfile') else None).pack(side="right", padx=5)

            # Thumbnail Preview (Images only)
            ext = os.path.splitext(file_path)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                try:
                    img = Image.open(file_path)
                    img.thumbnail((100, 100))
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))
                    
                    thumb_container = ctk.CTkFrame(self.thumbnail_frame, fg_color="white", border_width=1, border_color="#dce4ee")
                    thumb_container.pack(side="left", padx=5)
                    
                    ctk.CTkLabel(thumb_container, image=ctk_img, text="").pack(padx=5, pady=5)
                    ctk.CTkLabel(thumb_container, text=os.path.basename(file_path)[:12]+"...", font=("Arial", 9)).pack(pady=(0, 5))
                except:
                    pass

    def save(self):
        connection = None
        try:
            date = self.date_entry.get_date()
            client = self.client_entry.get().strip()
            age = self.age_entry.get().strip()
            vawc_no = self.vawc_no_entry.get().strip()
            contact = self.contact_entry.get().strip()
            
            if not vawc_no:
                messagebox.showerror("Error", "VAWC Number is required.")
                return

            # Better birthdate parsing
            birthdate_str = self.birthdate_entry.get().strip()
            birthdate = None
            if birthdate_str:
                for fmt in ("%m/%d/%Y", "%m-%d-%Y", "%m.%d.%Y", "%Y-%m-%d"):
                    try:
                        birthdate = datetime.strptime(birthdate_str, fmt).date()
                        break
                    except ValueError:
                        continue
            
            address = self.address_text.get("1.0", "end").strip()
            abuses = ", ".join([k for k, v in self.abuse_vars.items() if v.get()])
            respondent = self.respondent_entry.get().strip()
            remarks = self.remarks_text.get("1.0", "end").strip()
            status = self.case_status_var.get()
            referred_to = self.referred_entry.get().strip()

            if not client:
                messagebox.showerror("Error", "Client Name is required.")
                return

            # Handle Attachments Vault
            vault_dir = os.path.join(os.getcwd(), "attachments")
            os.makedirs(vault_dir, exist_ok=True)
            
            final_attachments = []
            for f in self.attachments:
                # If already in vault, keep it
                if os.path.abspath(f).startswith(os.path.abspath(vault_dir)):
                    final_attachments.append(f)
                    continue
                
                try:
                    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(f)}"
                    dest = os.path.join(vault_dir, filename)
                    import shutil
                    shutil.copy2(f, dest)
                    final_attachments.append(dest)
                except:
                    final_attachments.append(f)
            
            attach = ";".join(final_attachments) if final_attachments else None

            connection = get_connection()
            cursor = connection.cursor()
            
            # Format dates for DB
            date_str = date.strftime("%Y-%m-%d")
            birthdate_db = birthdate.strftime("%Y-%m-%d") if birthdate else None
            age_int = int(age) if age and age.isdigit() else None
            
            cursor.execute("""
                UPDATE vawc_logs 
                SET vawc_no=?, date=?, client_name=?, age=?, contact=?, birthdate=?, address=?, type_of_abuse=?, name_of_respondent=?, case_status=?, attachments=?, remarks=?, referred_to=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (vawc_no, date_str, client, age_int, contact, birthdate_db, address, abuses, respondent, status, attach, remarks, referred_to, self.record[0]))
            connection.commit()

            # Log edit action
            from db import log_action
            log_action(self.username, "Edit Record", target_record=self.vawc_no, details=f"Status: {status}")
            
            messagebox.showinfo("Success", "Record updated successfully.")
            self.vawc_no = vawc_no
            
            # Update local record and return to view mode
            self.record = self.load_record()
            if self.record:
                self.setup_field_values()
                self.set_editable(False)
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "VAWC No already exists. Please choose a different VAWC number.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            if connection:
                connection.close()

    def _build(self):
        self.setup_fields()

    def _load_record(self):
        return self.load_record()

    def _enable_edit(self):
        self.set_editable(True)

    def _disable_edit(self):
        self.set_editable(False)

    def _save_changes(self):
        self.save()

    def _cancel_edit(self):
        self.cancel_edit()

    def _print_record(self):
        self.print_record()