import customtkinter as ctk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from db import get_connection
from .view_record import ViewRecordWindow
from .edit_record import EditRecordWindow
from .screen_header import ScreenHeader

class LogsTabFrame(ctk.CTkFrame):
    def __init__(self, parent, user_role):
        super().__init__(parent, fg_color="#f5f5f5")

        self.user_role = user_role
        self.page = 0
        self.limit = 20
        self.search_term = ""
        self.filter_abuse = ""
        self.filter_status = ""
        self.filter_year = ""
        self.filter_month = ""

        ScreenHeader(self, "VAWC Logs").pack(fill="x")

        # ================= FILTER SECTION =================
        filter_frame = ctk.CTkFrame(self, fg_color="#eef0f4")
        filter_frame.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(filter_frame, text="Search", text_color="#1a2a4a").pack(fill="x", padx=10, pady=(10, 2))
        self.search_entry = ctk.CTkEntry(filter_frame, placeholder_text="Search by name, VAWC No, respondent")
        self.search_entry.pack(padx=10, pady=(0, 10), fill="x")
        self.search_entry.bind("<KeyRelease>", self.on_search)

        ctk.CTkLabel(filter_frame, text="Filter by Type of Abuse", text_color="#1a2a4a").pack(fill="x", padx=10)
        self.abuse_var = ctk.StringVar()
        self.abuse_combo = ctk.CTkComboBox(filter_frame, variable=self.abuse_var, values=[""] + self.get_abuse_types(), command=self.on_filter)
        self.abuse_combo.pack(padx=10, pady=(0, 10), fill="x")

        ctk.CTkLabel(filter_frame, text="Filter by Case Status", text_color="#1a2a4a").pack(fill="x", padx=10)
        self.status_var = ctk.StringVar()
        self.status_combo = ctk.CTkComboBox(filter_frame, variable=self.status_var, values=["", "Ongoing", "Resolved", "Referred", "Archived"], command=self.on_filter)
        self.status_combo.pack(padx=10, pady=(0, 10), fill="x")

        # ================= TABLE =================
        table_frame = ctk.CTkFrame(self, fg_color="#f5f5f5")
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # STYLE FIX (IMPORTANT)
        style = ttk.Style()
        style.theme_use("default")

        style.configure(
            "Treeview",
            background="#ffffff",
            foreground="#000000",  # FIX: readable text
            rowheight=28,
            fieldbackground="#ffffff",
            font=("Arial", 10)
        )

        style.map(
            "Treeview",
            background=[("selected", "#8b0000")],
            foreground=[("selected", "#ffffff")]
        )

        style.configure(
            "Treeview.Heading",
            background="#1a2a4a",
            foreground="#ffffff",
            font=("Arial", 11, "bold")
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=("VAWC No", "Date", "Client Name", "Age", "Contact", "Birthdate", "Address", "Type of Abuse", "Case Status", "Respondent", "Remarks"),
            show="headings",
            selectmode="browse"
        )

        col_widths = {
            "VAWC No": 140,
            "Date": 90,
            "Client Name": 180,
            "Age": 50,
            "Contact": 150,
            "Birthdate": 90,
            "Address": 260,
            "Type of Abuse": 140,
            "Case Status": 110,
            "Respondent": 170,
            "Remarks": 260
        }

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 130), minwidth=80, anchor="w", stretch=True)

        self.tree.bind("<Double-1>", self.on_double_click)

        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree.pack(side="top", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")

        # ================= PAGINATION =================
        nav_frame = ctk.CTkFrame(self, fg_color="#f5f5f5")
        nav_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.btn_prev = ctk.CTkButton(nav_frame, text="Previous", command=self.prev_page, fg_color="#8b0000")
        self.btn_prev.pack(side="left", padx=10)

        self.btn_next = ctk.CTkButton(nav_frame, text="Next", command=self.next_page, fg_color="#8b0000")
        self.btn_next.pack(side="right", padx=10)

        self.load_data()

    # ================= FUNCTIONS =================

    def get_abuse_types(self):
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT DISTINCT type_of_abuse FROM vawc_logs")
            types = [row[0] for row in cursor.fetchall()]
            cursor.close()
            connection.close()
            return types
        except:
            return []

    def on_search(self, event):
        self.search_term = self.search_entry.get()
        self.page = 0
        self.load_data()

    def on_filter(self, event=None):
        self.filter_abuse = self.abuse_var.get()
        self.filter_status = self.status_var.get()
        self.page = 0
        self.load_data()

    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            connection = get_connection()
            cursor = connection.cursor()

            query = """
            SELECT vawc_no, date, client_name, age, contact, birthdate, address,
                   type_of_abuse, case_status, name_of_respondent, remarks
            FROM vawc_logs WHERE 1=1
            """

            params = []

            if self.search_term:
                query += " AND (client_name LIKE ? OR vawc_no LIKE ? OR name_of_respondent LIKE ?)"
                params.extend([f"%{self.search_term}%"] * 3)

            if self.filter_abuse:
                query += " AND type_of_abuse = ?"
                params.append(self.filter_abuse)

            if self.filter_status:
                query += " AND case_status = ?"
                params.append(self.filter_status)

            query += " ORDER BY date DESC LIMIT ? OFFSET ?"
            params.extend([self.limit, self.page * self.limit])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Alternating row colors
            for i, row in enumerate(rows):
                tag = "evenrow" if i % 2 == 0 else "oddrow"
                self.tree.insert("", "end", values=row, tags=(tag,))

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

    def on_double_click(self, event):
        selected = self.tree.selection()
        if selected:
            item = selected[0]
            values = self.tree.item(item, "values")
            ViewRecordWindow(self, values[0])