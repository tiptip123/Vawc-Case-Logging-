import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import os
from tkcalendar import DateEntry
from datetime import datetime
from db import get_connection
from utils.helpers import calculate_age
from utils.pdf_export import export_single_pdf
from .view_record import ViewRecordWindow
from .edit_record import EditRecordWindow

class LogsTabFrame(ctk.CTkFrame):
    def __init__(self, parent, username):
        super().__init__(parent, fg_color="#f5f5f5")

        self.username = username
        self.page = 0
        self.limit = 20
        self.search_term = ""
        self.filter_abuse = ""
        self.filter_status = ""
        self.filter_year = ""
        self.filter_month = ""
        self.selection_mode = False
        self.selected_vawc_nos = set()

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
        filter_card = ctk.CTkFrame(self.table_view, fg_color="#FFFFFF", corner_radius=15)
        filter_card.pack(fill="x", padx=20, pady=(20, 10))
        
        # ... (Filters remain the same, just keeping structure) ...
        # Filter Title
        ctk.CTkLabel(filter_card, text="🔍 Search & Filter Logs", font=("Arial", 16, "bold"), text_color="#1a2a4a").pack(anchor="w", padx=20, pady=(15, 10))

        filter_grid = ctk.CTkFrame(filter_card, fg_color="transparent", corner_radius=0)
        filter_grid.pack(fill="x", padx=20, pady=(0, 15))

        # Search Bar (Top Row)
        search_frame = ctk.CTkFrame(filter_grid, fg_color="transparent", corner_radius=0)
        search_frame.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(search_frame, text="Search Record", font=("Arial", 12, "bold"), text_color="#1a2a4a").pack(side="left", padx=(0, 10))
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search by name, VAWC No, or respondent...", border_width=2, height=35)
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", self.on_filter)

        # Dropdowns (Bottom Row)
        dropdown_row = ctk.CTkFrame(filter_grid, fg_color="transparent", corner_radius=0)
        dropdown_row.pack(fill="x")

        # Type of Abuse
        abuse_col = ctk.CTkFrame(dropdown_row, fg_color="transparent", corner_radius=0)
        abuse_col.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkLabel(abuse_col, text="Type of Abuse", font=("Arial", 11, "bold"), text_color="#1a2a4a").pack(anchor="w")
        self.abuse_var = ctk.StringVar()
        self.abuse_combo = ctk.CTkComboBox(abuse_col, variable=self.abuse_var, values=[""] + self.get_abuse_types(), height=35, command=self.on_filter)
        self.abuse_combo.pack(fill="x", pady=2)

        # Case Status
        status_col = ctk.CTkFrame(dropdown_row, fg_color="transparent", corner_radius=0)
        status_col.pack(side="left", fill="x", expand=True, padx=10)
        ctk.CTkLabel(status_col, text="Case Status", font=("Arial", 11, "bold"), text_color="#1a2a4a").pack(anchor="w")
        self.status_var = ctk.StringVar()
        self.status_combo = ctk.CTkComboBox(status_col, variable=self.status_var, values=["", "Ongoing", "Settled", "Referred", "Archived", "Issued BPO"], height=35, command=self.on_filter)
        self.status_combo.pack(fill="x", pady=2)

        # Year
        year_col = ctk.CTkFrame(dropdown_row, fg_color="transparent", corner_radius=0)
        year_col.pack(side="left", fill="x", expand=True, padx=10)
        ctk.CTkLabel(year_col, text="Year", font=("Arial", 11, "bold"), text_color="#1a2a4a").pack(anchor="w")
        self.year_var = ctk.StringVar()
        self.year_combo = ctk.CTkComboBox(year_col, variable=self.year_var, values=[""] + [str(y) for y in range(datetime.now().year, 2019, -1)], height=35, command=self.on_filter)
        self.year_combo.pack(fill="x", pady=2)

        # Month
        month_col = ctk.CTkFrame(dropdown_row, fg_color="transparent", corner_radius=0)
        month_col.pack(side="left", fill="x", expand=True, padx=10)
        ctk.CTkLabel(month_col, text="Month", font=("Arial", 11, "bold"), text_color="#1a2a4a").pack(anchor="w")
        self.month_var = ctk.StringVar()
        months = ["", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
        self.month_combo = ctk.CTkComboBox(month_col, variable=self.month_var, values=months, height=35, command=self.on_filter)
        self.month_combo.pack(fill="x", pady=2)

        # Clear Button
        button_col = ctk.CTkFrame(dropdown_row, fg_color="transparent", corner_radius=0)
        button_col.pack(side="left", padx=(10, 0))
        ctk.CTkLabel(button_col, text="", font=("Arial", 11)).pack()
        self.btn_clear = ctk.CTkButton(button_col, text="Clear Filters", command=self.clear_filters, fg_color="#6c757d", hover_color="#5a6268", width=100, height=35)
        self.btn_clear.pack(pady=2)

        # ================= TABLE =================
        table_container = ctk.CTkFrame(self.table_view, fg_color="#ffffff", corner_radius=15)
        table_container.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Action Toolbar (New)
        toolbar = ctk.CTkFrame(table_container, fg_color="transparent", corner_radius=0)
        toolbar.pack(fill="x", padx=20, pady=10)
        
        if not self.selection_mode:
            self.btn_delete_trigger = ctk.CTkButton(toolbar, text="🗑 Delete Records", command=self.toggle_selection_mode, fg_color="#dc3545", hover_color="#c82333", height=35, width=140, font=("Arial", 12, "bold"))
            self.btn_delete_trigger.pack(side="left")
        else:
            self.btn_confirm_del = ctk.CTkButton(toolbar, text="⚠ Confirm Delete", command=self.delete_selected, fg_color="#8b0000", hover_color="#6b0000", height=35, width=140, font=("Arial", 12, "bold"))
            self.btn_confirm_del.pack(side="left")
            
            self.btn_cancel_del = ctk.CTkButton(toolbar, text="Cancel", command=self.toggle_selection_mode, fg_color="transparent", text_color="#333333", border_width=1, border_color="#cccccc", height=35, width=80)
            self.btn_cancel_del.pack(side="left", padx=10)

        # Treeview
        table_frame = ctk.CTkFrame(table_container, fg_color="transparent", corner_radius=0)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        style = ttk.Style()
        # Force a theme that allows heading background customization
        if "clam" in style.theme_names():
            style.theme_use("clam")
            
        style.configure("Treeview", background="#ffffff", foreground="#000000", rowheight=30, fieldbackground="#ffffff", font=("Arial", 10))
        style.map("Treeview", background=[("selected", "#1a2a4a")], foreground=[("selected", "#ffffff")])
        style.configure("Treeview.Heading", background="#000000", foreground="#ffffff", font=("Arial", 11, "bold"), borderwidth=1)
        style.map("Treeview.Heading", background=[("active", "#333333")])

        self.tree = ttk.Treeview(
            table_frame,
            columns=("Select", "VAWC No", "Date", "Client Name", "Age", "Type of Abuse", "Case Status", "Respondent"),
            show="headings",
            selectmode="browse"
        )

        col_widths = {"Select": 50, "VAWC No": 140, "Date": 100, "Client Name": 180, "Age": 60, "Type of Abuse": 160, "Case Status": 110, "Respondent": 170}
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col if col != "Select" else "")
            self.tree.column(col, width=col_widths.get(col, 130), anchor="center" if col in ["Select", "Age", "Date"] else "w")

        if not self.selection_mode:
            self.tree.column("Select", width=0, stretch=False)

        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-1>", self.on_click)

        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree.pack(side="top", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")

        # ================= COMPACT PAGINATION =================
        pagination_frame = ctk.CTkFrame(table_container, fg_color="transparent", corner_radius=0)
        pagination_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        page_controls = ctk.CTkFrame(pagination_frame, fg_color="transparent", corner_radius=0)
        page_controls.pack(side="right")

        btn_page_style = {"width": 60, "height": 28, "font": ("Arial", 11), "border_width": 1, "border_color": "#cccccc", "fg_color": "transparent", "text_color": "#333333", "hover_color": "#f0f0f0"}
        
        self.btn_prev = ctk.CTkButton(page_controls, text="‹ Prev", command=self.prev_page, **btn_page_style)
        self.btn_prev.pack(side="left", padx=5)

        total_pages = (self.total_count + self.limit - 1) // self.limit if hasattr(self, 'total_count') and self.total_count > 0 else 1
        self.page_label = ctk.CTkLabel(page_controls, text=f"Page {self.page + 1} of {total_pages}", font=("Arial", 10), text_color="#666666")
        self.page_label.pack(side="left", padx=10)

        self.btn_next = ctk.CTkButton(page_controls, text="Next ›", command=self.next_page, **btn_page_style)
        self.btn_next.pack(side="left", padx=5)

        self.load_data()

        self.load_data()

    # ================= FUNCTIONS =================

    def get_abuse_types(self):
        # Use a hardcoded list of abuse types to ensure the filter matches the individual types
        # This matches the list in AddRecordFrame and InlineEditPanel
        return [
             "Domestic Abuse", "Financial Abuse", "Material Abuse", "Modern Slavery",
             "Criminal Exploitation", "Neglect", "Acts of Omission", "Organisational Abuse",
             "Self-Neglect", "Hoarding", "Sexual Abuse", "Sexual Exploitation",
             "Emotional Abuse", "Psychological Abuse"
         ]

    def on_filter(self, event=None):
        self.search_term = self.search_entry.get()
        self.filter_abuse = self.abuse_var.get()
        self.filter_status = self.status_var.get()
        self.filter_year = self.year_var.get()
        self.filter_month = self.month_var.get()
        self.page = 0
        self.load_data()

    def clear_filters(self):
        self.search_entry.delete(0, 'end')
        self.abuse_var.set("")
        self.status_var.set("")
        self.year_var.set("")
        self.month_var.set("")
        self.on_filter()

    def load_data(self):
        try:
            connection = get_connection()
            cursor = connection.cursor()

            # Get total count for pagination
            count_query = "SELECT COUNT(*) FROM vawc_logs WHERE 1=1"
            params = []
            
            if self.search_term:
                count_query += " AND (client_name LIKE ? OR vawc_no LIKE ? OR name_of_respondent LIKE ?)"
                term = f"%{self.search_term}%"
                params.extend([term, term, term])
            
            if self.filter_abuse:
                # Use a custom function or LIKE with wildcards to handle multi-select fields
                count_query += " AND type_of_abuse LIKE ?"
                params.append(f"%{self.filter_abuse}%")

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
            query = "SELECT '☐', vawc_no, date, client_name, age, type_of_abuse, case_status, name_of_respondent FROM vawc_logs WHERE 1=1"
            
            # Reuse filters from count_query
            if self.search_term:
                query += " AND (client_name LIKE ? OR vawc_no LIKE ? OR name_of_respondent LIKE ?)"
            if self.filter_abuse:
                query += " AND type_of_abuse LIKE ?"
            if self.filter_status:
                query += " AND case_status = ?"
            if self.filter_year:
                query += " AND strftime('%Y', date) = ?"
            if self.filter_month:
                query += " AND strftime('%m', date) = ?"

            query += " ORDER BY date ASC, vawc_no ASC LIMIT ? OFFSET ?"
            params.extend([self.limit, self.page * self.limit])

            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Alternating row colors with checkbox state
            for i, row in enumerate(rows):
                vawc_no = row[1]
                check_char = "☑" if vawc_no in self.selected_vawc_nos else "☐"
                display_row = (check_char,) + row[1:]
                tag = "evenrow" if i % 2 == 0 else "oddrow"
                self.tree.insert("", "end", values=display_row, tags=(tag,))

            self.tree.tag_configure("evenrow", background="#ffffff")
            self.tree.tag_configure("oddrow", background="#eef0f4")

            cursor.close()
            connection.close()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def prev_page(self):
        if self.page > 0:
            self.page -= 1
            self.load_data()

    def next_page(self):
        self.page += 1
        self.load_data()

    def refresh(self):
        """Refresh the logs data"""
        self.load_data()

    def delete_entry(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a record to delete.")
            return

        item = selected[0]
        vawc_no = self.tree.item(item, "values")[0]

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete record {vawc_no}?"):
            try:
                connection = get_connection()
                cursor = connection.cursor()
                cursor.execute("DELETE FROM vawc_logs WHERE vawc_no = ?", (vawc_no,))
                connection.commit()
                cursor.close()
                connection.close()
                messagebox.showinfo("Success", "Record deleted successfully.")
                self.load_data()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def on_double_click(self, event):
        if self.selection_mode:
            return
        selected = self.tree.selection()
        if selected:
            item = selected[0]
            values = self.tree.item(item, "values")
            self.open_inline_edit(values[1]) # Use VAWC No

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
                    vawc_no = self.tree.item(item, "values")[1]
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
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {count} selected record(s)?"):
            try:
                connection = get_connection()
                cursor = connection.cursor()
                for vawc_no in self.selected_vawc_nos:
                    cursor.execute("DELETE FROM vawc_logs WHERE vawc_no = ?", (vawc_no,))
                connection.commit()
                cursor.close()
                connection.close()
                messagebox.showinfo("Success", f"{count} records deleted successfully.")
                self.toggle_selection_mode()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def open_inline_edit(self, vawc_no=None):
        try:
            if not vawc_no:
                selected = self.tree.selection()
                if not selected:
                    messagebox.showwarning("Warning", "Please select a record to edit.")
                    return
                vawc_no = self.tree.item(selected[0], "values")[1]

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
            edit_panel = InlineEditPanel(self.edit_view, vawc_no, self.username, on_save=self.close_inline_edit, on_cancel=self.close_inline_edit)
            edit_panel.pack(fill="both", expand=True)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open edit view: {str(e)}")

    def close_inline_edit(self):
        self.edit_view.pack_forget()
        self.table_view.pack(fill="both", expand=True)
        self.load_data()

class InlineEditPanel(ctk.CTkFrame):
    def __init__(self, parent, vawc_no, username, on_save, on_cancel):
        super().__init__(parent, fg_color="#f5f5f5")
        self.vawc_no = vawc_no
        self.username = username
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
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="#f5f5f5")
        self.scroll_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.setup_sticky_footer()

        # Form Card
        self.form_card = ctk.CTkFrame(self.scroll_container, fg_color="white", corner_radius=15)
        self.form_card.pack(fill="x", padx=40, pady=10)

        # Header Banner
        self.header_banner = ctk.CTkFrame(self.form_card, fg_color="#1a73e8", corner_radius=15, height=80)
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
        self.footer_actions = ctk.CTkFrame(self, fg_color="#ffffff", height=70, corner_radius=0)
        self.footer_actions.pack(side="bottom", fill="x")
        
        inner_footer = ctk.CTkFrame(self.footer_actions, fg_color="transparent", corner_radius=0)
        inner_footer.pack(fill="x", padx=60, pady=15)

        self.btn_print = ctk.CTkButton(inner_footer, text="🖨 Print Record", font=("Arial", 13, "bold"), fg_color="#2c3e50", hover_color="#1a252f", height=40, width=140, command=self.print_record)
        self.btn_print.pack(side="left")

        ctk.CTkButton(inner_footer, text="Back to Logs", font=("Arial", 13), fg_color="transparent", text_color="#333333", border_width=1, border_color="#cccccc", height=40, width=120, command=self.on_cancel_callback).pack(side="right")

    def set_editable(self, editable):
        self.is_editable = editable
        state = "normal" if editable else "disabled"
        
        # Update Header
        self.header_banner.configure(fg_color="#1a73e8" if editable else "#1a2a4a")
        self.title_label.configure(text=f"{'Edit' if editable else 'Record Details'}: {self.vawc_no}")
        self.subtitle_label.configure(text="Update the information below and save changes" if editable else "Viewing record details")

        # Update Fields
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

        # Update Checkboxes
        for var in self.abuse_vars.values():
            pill = var._pill_widget
            for widget in pill.winfo_children():
                if isinstance(widget, ctk.CTkCheckBox):
                    widget.configure(state=state)

        # Style updates for better read-only view
        input_bg = "white" if editable else "#f9f9f9"
        border_width = 2 if editable else 0
        text_color = "black" if editable else "#333333"

        for widget in [self.client_entry, self.birthdate_entry, self.age_entry, self.contact_entry, self.respondent_entry]:
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
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM vawc_logs WHERE vawc_no = ?", (self.vawc_no,))
            record = cursor.fetchone()
            cursor.close()
            connection.close()
            return record
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return None

    def setup_fields(self):
        # Re-using the same professional layout from AddRecordFrame
        def create_label(parent, text):
            return ctk.CTkLabel(parent, text=text, font=("Arial", 11, "bold"), text_color="#1a2a4a", anchor="w")

        # Row 1: Date | Client Name
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
        self.client_entry = ctk.CTkEntry(col1_2, border_width=2, height=38, border_color="#dce4ee")
        self.client_entry.pack(fill="x", pady=(5, 0))

        # Row 2: Birthdate | Age
        row2 = ctk.CTkFrame(self.content_frame, fg_color="transparent", corner_radius=0)
        row2.pack(fill="x", pady=10)
        row2.grid_columnconfigure((0, 1), weight=1)

        col2_1 = ctk.CTkFrame(row2, fg_color="transparent", corner_radius=0)
        col2_1.grid(row=0, column=0, padx=(0, 15), sticky="nsew")
        create_label(col2_1, "Birthdate (MM/DD/YYYY)").pack(fill="x")
        self.birthdate_entry = ctk.CTkEntry(col2_1, border_width=2, height=38, border_color="#dce4ee")
        self.birthdate_entry.pack(fill="x", pady=(5, 0))
        self.birthdate_entry.bind("<KeyRelease>", self.on_birthdate_key)
        self.birthdate_entry.bind("<FocusOut>", self.on_birthdate_focus_out)

        col2_2 = ctk.CTkFrame(row2, fg_color="transparent", corner_radius=0)
        col2_2.grid(row=0, column=1, sticky="nsew")
        create_label(col2_2, "Age").pack(fill="x")
        self.age_entry = ctk.CTkEntry(col2_2, border_width=2, height=38, border_color="#dce4ee")
        self.age_entry.pack(fill="x", pady=(5, 0))

        # Row 3: Contact | Address
        row3 = ctk.CTkFrame(self.content_frame, fg_color="transparent", corner_radius=0)
        row3.pack(fill="x", pady=10)
        row3.grid_columnconfigure((0, 1), weight=1)

        col3_1 = ctk.CTkFrame(row3, fg_color="transparent", corner_radius=0)
        col3_1.grid(row=0, column=0, padx=(0, 15), sticky="nsew")
        create_label(col3_1, "Contact Information").pack(fill="x")
        self.contact_entry = ctk.CTkEntry(col3_1, border_width=2, height=38, border_color="#dce4ee")
        self.contact_entry.pack(fill="x", pady=(5, 0))

        col3_2 = ctk.CTkFrame(row3, fg_color="transparent", corner_radius=0)
        col3_2.grid(row=0, column=1, sticky="nsew")
        create_label(col3_2, "Complete Address").pack(fill="x")
        self.address_text = ctk.CTkTextbox(col3_2, height=38, border_width=2, border_color="#dce4ee")
        self.address_text.pack(fill="x", pady=(5, 0))

        # Row 4: Respondent
        row4 = ctk.CTkFrame(self.content_frame, fg_color="transparent", corner_radius=0)
        row4.pack(fill="x", pady=10)
        create_label(row4, "Name of Respondent").pack(fill="x")
        self.respondent_entry = ctk.CTkEntry(row4, border_width=2, height=38, border_color="#dce4ee")
        self.respondent_entry.pack(fill="x", pady=(5, 0))

        # Row 5: Abuse Grid
        row5 = ctk.CTkFrame(self.content_frame, fg_color="transparent", corner_radius=0)
        row5.pack(fill="x", pady=(15, 10))
        create_label(row5, "Type of Abuse").pack(fill="x", pady=(0, 10))
        
        abuse_grid = ctk.CTkFrame(row5, fg_color="transparent", corner_radius=0)
        abuse_grid.pack(fill="x")
        
        self.abuse_vars = {}
        abuses = ["Domestic Abuse", "Financial Abuse", "Material Abuse", "Modern Slavery", "Criminal Exploitation", "Neglect", "Acts of Omission", "Organisational Abuse", "Self-Neglect", "Hoarding", "Sexual Abuse", "Sexual Exploitation", "Emotional Abuse", "Psychological Abuse"]

        for i, abuse in enumerate(abuses):
            var = ctk.BooleanVar(value=False)
            self.abuse_vars[abuse] = var
            pill = ctk.CTkFrame(abuse_grid, fg_color="white", border_width=1, border_color="#cccccc", corner_radius=20)
            pill.grid(row=i//4, column=i%4, padx=5, pady=5, sticky="ew")
            abuse_grid.grid_columnconfigure(i%4, weight=1)
            cb = ctk.CTkCheckBox(pill, text=abuse, variable=var, text_color="black", checkbox_width=18, checkbox_height=18, command=lambda a=abuse, p=pill, v=var: self.update_pill_style(a, p, v))
            cb.pack(padx=15, pady=8, side="left")
            var._pill_widget = pill # Store for direct updates

        # Row 6: Remarks
        row6 = ctk.CTkFrame(self.content_frame, fg_color="transparent", corner_radius=0)
        row6.pack(fill="x", pady=10)
        create_label(row6, "Case Remarks / Notes").pack(fill="x")
        self.remarks_text = ctk.CTkTextbox(row6, height=100, border_width=2, border_color="#dce4ee")
        self.remarks_text.pack(fill="x", pady=(5, 0))

        # Row 7: Case Status | Referred To
        row7 = ctk.CTkFrame(self.content_frame, fg_color="transparent", corner_radius=0)
        row7.pack(fill="x", pady=10)
        row7.grid_columnconfigure((0, 1), weight=1)

        col7_1 = ctk.CTkFrame(row7, fg_color="transparent", corner_radius=0)
        col7_1.grid(row=0, column=0, padx=(0, 15), sticky="nsew")
        create_label(col7_1, "Case Status").pack(fill="x")
        self.case_status_var = ctk.StringVar(value="Settled")
        self.case_status_menu = ctk.CTkOptionMenu(col7_1, values=["Settled", "Issued BPO", "Ongoing", "Referred", "Archived"], 
                                                 variable=self.case_status_var, height=38, command=self.update_status_style)
        self.case_status_menu.pack(fill="x", pady=(5, 0))

        col7_2 = ctk.CTkFrame(row7, fg_color="transparent", corner_radius=0)
        col7_2.grid(row=0, column=1, sticky="nsew")
        create_label(col7_2, "Referred To (Agency)").pack(fill="x")
        self.referred_to_var = ctk.StringVar()
        self.referred_menu = ctk.CTkOptionMenu(col7_2, values=["None", "PNP (Police)", "MSWDO", "Hospital", "Court", "Other"], 
                                              variable=self.referred_to_var, height=38)
        self.referred_menu.pack(fill="x", pady=(5, 0))

        # Row 8: Attachments
        row8 = ctk.CTkFrame(self.content_frame, fg_color="transparent", corner_radius=0)
        row8.pack(fill="x", pady=15)
        create_label(row8, "Attachments").pack(fill="x", pady=(0, 5))
        
        # Thumbnail Preview Area
        self.thumbnail_frame = ctk.CTkFrame(row8, fg_color="transparent")
        self.thumbnail_frame.pack(fill="x", pady=(0, 10))

        self.upload_area = ctk.CTkFrame(row8, fg_color="#f8f9fa", border_width=2, border_color="#dce4ee", corner_radius=10, height=60)
        self.upload_area.pack(fill="x")
        self.upload_area.pack_propagate(False)
        self.upload_btn = ctk.CTkButton(self.upload_area, text="📎 Click to attach files", fg_color="transparent", text_color="#1a2a4a", command=self.select_attachments)
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
        self.referred_to_var.set(self.record[13] or "None")

        # Status
        self.case_status_var.set(self.record[10] or "Settled")
        self.update_status_style(self.case_status_var.get())

        # Attachments
        if self.record[11]:
            self.attachments = self.record[11].split(";")
        else:
            self.attachments = []
        self.refresh_file_list()

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
        try:
            date = self.date_entry.get_date()
            client = self.client_entry.get().strip()
            age = self.age_entry.get().strip()
            contact = self.contact_entry.get().strip()
            birthdate = datetime.strptime(self.birthdate_entry.get(), "%m/%d/%Y").date() if self.birthdate_entry.get() else None
            address = self.address_text.get("1.0", "end").strip()
            abuses = ", ".join([k for k, v in self.abuse_vars.items() if v.get()])
            respondent = self.respondent_entry.get().strip()
            remarks = self.remarks_text.get("1.0", "end").strip()
            status = self.case_status_var.get()
            referred_to = self.referred_to_var.get()

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
            cursor.execute("""
                UPDATE vawc_logs 
                SET date=?, client_name=?, age=?, contact=?, birthdate=?, address=?, type_of_abuse=?, name_of_respondent=?, case_status=?, attachments=?, remarks=?, referred_to=?, updated_at=CURRENT_TIMESTAMP
                WHERE vawc_no=?
            """, (date, client, int(age) if age else None, contact, birthdate, address, abuses, respondent, status, attach, remarks, referred_to, self.vawc_no))
            connection.commit()

            # Log edit action
            from db import log_action
            log_action(self.username, "Edit Record", target_record=self.vawc_no, details=f"Status: {status}")

            cursor.close()
            connection.close()
            
            messagebox.showinfo("Success", "Record updated successfully.")
            
            # Update local record and return to view mode
            self.record = self.load_record()
            if self.record:
                self.setup_field_values()
                self.set_editable(False)
        except Exception as e:
            messagebox.showerror("Error", str(e))