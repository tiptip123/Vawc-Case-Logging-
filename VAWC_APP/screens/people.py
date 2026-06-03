import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
from db import get_connection
from utils.helpers import get_scaled_font, parse_date_string
from .view_record import ViewRecordWindow


class PeopleScreen(ctk.CTkFrame):
    def __init__(self, parent, username=None, user_role="Staff"):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent
        self.username = username
        self.user_role = user_role

        # State
        self.mode = None  # 'victims' | 'respondents' | 'highrisk'
        self.search_term = ""

        # Card references
        self.cards = []

        # Colors
        self.colors = {
            "victims": "#1565c0",
            "respondents": "#0f2942",
            "highrisk": "#8b0000",
            "table_header": "#1a2a4a",
            "alt_row": "#f5f7fa",
            "row_hover": "#e3f2fd"
        }

        # Build UI components
        self.build_ui()

        # Load initial counts
        self.refresh()

    def _make_card(self, parent, icon, title, desc, accent, command, urgent=False):
        card = ctk.CTkFrame(parent, width=220, height=110, fg_color=["white", "#242424"], corner_radius=12, border_width=1, border_color=["#e2e8f0", "#333333"]) 
        card.pack(side="left", padx=10, pady=6, expand=False)
        card.pack_propagate(False)
        # Left accent bar
        accent_bar = ctk.CTkFrame(card, width=8, fg_color=accent, corner_radius=6)
        accent_bar.pack(side="left", fill="y", padx=(0,8), pady=8)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=(4, 8), pady=8)

        title_lbl = ctk.CTkLabel(content, text=icon + "  " + title, font=get_scaled_font(12, "bold"))
        title_lbl.pack(anchor="w")
        count_lbl = ctk.CTkLabel(content, text="0", font=get_scaled_font(20, "bold"), text_color=self.colors["table_header"])
        count_lbl.pack(anchor="w", pady=(6,0))
        desc_lbl = ctk.CTkLabel(content, text=desc, font=get_scaled_font(11, "normal"), text_color="#64748b")
        desc_lbl.pack(anchor="w", pady=(6,0))

        # Click behavior
        def on_click(event=None):
            # set active visual state then load
            try:
                self._set_active_card(card)
            except Exception:
                pass
            command()

        card.bind("<Button-1>", on_click)
        content.bind("<Button-1>", on_click)
        accent_bar.bind("<Button-1>", on_click)
        title_lbl.bind("<Button-1>", on_click)
        count_lbl.bind("<Button-1>", on_click)
        desc_lbl.bind("<Button-1>", on_click)

        # Store count label for updates
        card.count_label = count_lbl
        # store accent color for selection toggling
        card._accent_bar = accent_bar
        card._accent_color = accent
        self.cards.append(card)
        return card

    def _set_active_card(self, card):
        # Visual indicator: set selected card border to blue and accent to lighter blue
        active_border = ["#63a4ff", "#63a4ff"]
        inactive_border = ["#e2e8f0", "#333333"]
        for c in self.cards:
            if c is card:
                try:
                    c.configure(border_color=active_border)
                    c._accent_bar.configure(fg_color="#63a4ff")
                except Exception:
                    pass
            else:
                try:
                    c.configure(border_color=inactive_border)
                    c._accent_bar.configure(fg_color=c._accent_color)
                except Exception:
                    pass

    def _clear_search(self):
        self.search_entry.delete(0, 'end')
        self.search_term = ""
        self.load_people(self.mode or "victims")

    def build_ui(self):
        # Destroy any existing main container before rebuilding
        if hasattr(self, 'main_container') and self.main_container.winfo_exists():
            self.main_container.destroy()

        # Layout
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header = ctk.CTkLabel(self.main_container, text="People Directory", font=get_scaled_font(18, "bold"), text_color=self.colors["table_header"]) 
        header.pack(anchor="w", pady=(0, 10))

        sub = ctk.CTkLabel(self.main_container, text="Overview of all individuals recorded in the system", font=get_scaled_font(12, "normal"), text_color="#64748b")
        sub.pack(anchor="w", pady=(0, 10))

        # Summary cards
        self.cards_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.cards_frame.pack(fill="x", pady=(10, 12))

        # create cards
        self.card_victims = self._make_card(self.cards_frame, "👩", "Victims", "Individuals who filed a case", self.colors["victims"], lambda: self.load_people("victims"))
        self.card_respondents = self._make_card(self.cards_frame, "👤", "Respondents", "Individuals reported in a case", self.colors["respondents"], lambda: self.load_people("respondents"))
        self.card_highrisk = self._make_card(self.cards_frame, "⚠️", "High Risk", "Respondents with 3 or more cases", self.colors["highrisk"], lambda: self.load_people("highrisk"), urgent=True)

        # Search & info area
        self.search_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.search_container.pack(fill="x", pady=(10, 6))
        self.search_entry = ctk.CTkEntry(self.search_container, placeholder_text="Search by full name...", height=36, corner_radius=8, border_width=1, border_color=["#e2e8f0", "#333333"]) 
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_people(self.mode))

        self.clear_btn = ctk.CTkButton(self.search_container, text="✕", width=36, height=36, corner_radius=8, fg_color="transparent", command=self._clear_search)
        self.clear_btn.pack(side="left", padx=(8, 0))

        self.search_info = ctk.CTkLabel(self.main_container, text="", font=get_scaled_font(11, "normal"), text_color="#64748b")
        self.search_info.pack(anchor="w", pady=(4, 8))

        # Person list (Treeview)
        table_card = ctk.CTkFrame(self.main_container, fg_color=["white", "#242424"], corner_radius=12, border_width=1, border_color=["#e2e8f0", "#333333"])
        table_card.pack(fill="both", expand=True)

        table_frame = ctk.CTkFrame(table_card, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        style = ttk.Style()
        style.configure("People.Treeview", rowheight=36, font=("Arial", 11))
        style.configure("People.Treeview.Heading", background=self.colors["table_header"], foreground="#000000", font=("Arial", 11, "bold"))

        self.tree = ttk.Treeview(table_frame, columns=("Full Name", "No. of Cases", "Last Case Date", "Latest Case No"), show="headings", selectmode="browse")
        for col in ("Full Name", "No. of Cases", "Last Case Date", "Latest Case No"):
            self.tree.heading(col, text=col)

        self.tree.column("Full Name", anchor="w", width=300)
        self.tree.column("No. of Cases", anchor="center", width=100)
        self.tree.column("Last Case Date", anchor="center", width=120)
        self.tree.column("Latest Case No", anchor="center", width=140)

        self.tree.bind("<Double-1>", self._on_person_double)

        scrollbar = ctk.CTkScrollbar(table_frame, orientation="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Detail view container (hidden until a person is clicked)
        self.detail_container = ctk.CTkFrame(self.main_container, fg_color="transparent")

    def refresh(self):
        # Recalculate counts
        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute("SELECT COUNT(DISTINCT LOWER(TRIM(client_name))) FROM vawc_logs WHERE is_deleted = 0 AND client_name IS NOT NULL AND client_name != ''")
            victims_count = cur.fetchone()[0] or 0

            cur.execute("SELECT COUNT(DISTINCT LOWER(TRIM(name_of_respondent))) FROM vawc_logs WHERE is_deleted = 0 AND name_of_respondent IS NOT NULL AND name_of_respondent != ''")
            respondents_count = cur.fetchone()[0] or 0

            cur.execute("SELECT COUNT(*) FROM (SELECT LOWER(TRIM(name_of_respondent)) AS nm, COUNT(*) AS c FROM vawc_logs WHERE is_deleted = 0 AND name_of_respondent IS NOT NULL AND name_of_respondent != '' GROUP BY LOWER(TRIM(name_of_respondent)) HAVING c >= 3)")
            highrisk_count = cur.fetchone()[0] or 0

            conn.close()
        except Exception:
            victims_count = respondents_count = highrisk_count = 0

        self.card_victims.count_label.configure(text=str(victims_count))
        self.card_respondents.count_label.configure(text=str(respondents_count))
        self.card_highrisk.count_label.configure(text=str(highrisk_count))

        if not self.mode:
            self.load_people("victims")
        else:
            self.load_people(self.mode)

    def load_people(self, mode):
        if mode not in ("victims", "respondents", "highrisk"):
            return
        self.mode = mode
        # highlight active card
        try:
            if mode == "victims":
                self._set_active_card(self.card_victims)
            elif mode == "respondents":
                self._set_active_card(self.card_respondents)
            else:
                self._set_active_card(self.card_highrisk)
        except Exception:
            pass
        term = self.search_entry.get().strip()
        like_term = f"%{term}%"

        if mode == "victims":
            query = """
SELECT 
    client_name AS full_name,
    COUNT(*) AS case_count,
    MAX(date) AS last_case_date,
    MAX(vawc_no) AS latest_case_no
FROM vawc_logs
WHERE is_deleted = 0
    AND client_name IS NOT NULL
    AND client_name != ''
    AND LOWER(client_name) LIKE LOWER(?)
GROUP BY LOWER(TRIM(client_name))
ORDER BY case_count DESC, client_name ASC
"""
        elif mode == "respondents":
            query = """
SELECT 
    name_of_respondent AS full_name,
    COUNT(*) AS case_count,
    MAX(date) AS last_case_date,
    MAX(vawc_no) AS latest_case_no
FROM vawc_logs
WHERE is_deleted = 0
    AND name_of_respondent IS NOT NULL
    AND name_of_respondent != ''
    AND LOWER(name_of_respondent) LIKE LOWER(?)
GROUP BY LOWER(TRIM(name_of_respondent))
ORDER BY case_count DESC, name_of_respondent ASC
"""
        else: # highrisk
            query = """
SELECT 
    name_of_respondent AS full_name,
    COUNT(*) AS case_count,
    MAX(date) AS last_case_date,
    MAX(vawc_no) AS latest_case_no
FROM vawc_logs
WHERE is_deleted = 0
    AND name_of_respondent IS NOT NULL
    AND name_of_respondent != ''
    AND LOWER(name_of_respondent) LIKE LOWER(?)
GROUP BY LOWER(TRIM(name_of_respondent))
HAVING case_count >= 3
ORDER BY case_count DESC
"""

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(query, (like_term,))
            rows = cur.fetchall()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            rows = []

        # Update search info
        total = len(rows)
        showing = total
        self.search_info.configure(text=f"Showing {showing} of {total} people")

        # Populate tree
        for i in self.tree.get_children():
            self.tree.delete(i)

        for i, r in enumerate(rows):
            full_name = r[0]
            case_count = r[1]
            last_date = r[2] or ""
            latest_no = r[3] or ""
            dt = parse_date_string(last_date)
            if dt:
                last_date = dt.strftime("%m/%d/%Y")

            display_count = str(case_count)
            if case_count >= 3:
                display_count = f"🔴 {case_count}"

            self.tree.insert("", "end", values=(full_name, display_count, last_date, latest_no))

    def _on_person_double(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        values = self.tree.item(item, "values")
        name = values[0]
        # Open detail view
        self.show_person_detail(name, self.mode)

    def show_person_detail(self, name, mode):
        # Clear main area and show detail
        for w in self.main_container.winfo_children():
            w.destroy()

        # Back button
        back_btn = ctk.CTkButton(self.main_container, text=f"← Back to {mode.title()}", command=lambda: self._back_to_list(mode), fg_color="transparent", text_color="#1a2a4a", hover_color="#eeeeee", width=180)
        back_btn.pack(anchor="w", pady=(0, 8))

        # Header
        hdr = ctk.CTkLabel(self.main_container, text=name, font=get_scaled_font(18, "bold"), text_color=self.colors["table_header"])
        hdr.pack(anchor="w")

        # Role badge + total cases
        try:
            conn = get_connection()
            cur = conn.cursor()
            if mode == "victims":
                cur.execute("SELECT COUNT(*), MAX(date) FROM vawc_logs WHERE is_deleted = 0 AND LOWER(TRIM(client_name)) = LOWER(TRIM(?))", (name,))
            else:
                cur.execute("SELECT COUNT(*), MAX(date) FROM vawc_logs WHERE is_deleted = 0 AND LOWER(TRIM(name_of_respondent)) = LOWER(TRIM(?))", (name,))
            res = cur.fetchone()
            total_cases = res[0] or 0
            conn.close()
        except Exception:
            total_cases = 0

        badge_text = "Victim" if mode == "victims" else ("⚠️ High Risk Respondent" if mode == "highrisk" else "Respondent")
        badge_color = self.colors["victims"] if mode == "victims" else (self.colors["highrisk"] if mode == "highrisk" else self.colors["respondents"])
        badge = ctk.CTkFrame(self.main_container, fg_color=badge_color, corner_radius=8)
        badge.pack(anchor="w", pady=(6, 4))
        ctk.CTkLabel(badge, text=badge_text, font=get_scaled_font(10, "bold"), text_color="white", padx=8, pady=3).pack()

        ctk.CTkLabel(self.main_container, text=f"{total_cases} case(s) on record", font=get_scaled_font(12, "normal"), text_color="#64748b").pack(anchor="w", pady=(6, 12))

        # Case history table
        table_card = ctk.CTkFrame(self.main_container, fg_color=["white", "#242424"], corner_radius=12, border_width=1, border_color=["#e2e8f0", "#333333"])
        table_card.pack(fill="both", expand=True)

        table_frame = ctk.CTkFrame(table_card, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("VAWC No", "Date", "Type of Abuse", "Case Status", "Co-involved")
        case_tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
        for col in cols:
            case_tree.heading(col, text=col)
        case_tree.column("VAWC No", width=160, anchor="center")
        case_tree.column("Date", width=120, anchor="center")
        case_tree.column("Type of Abuse", width=200, anchor="w")
        case_tree.column("Case Status", width=120, anchor="center")
        case_tree.column("Co-involved", width=200, anchor="w")

        case_tree.bind("<Double-1>", lambda e: self._on_case_double(e, case_tree))

        ctk.CTkScrollbar(table_frame, orientation="vertical", command=case_tree.yview).pack(side="right", fill="y")
        case_tree.configure(yscrollcommand=lambda *args: None)
        case_tree.pack(fill="both", expand=True)

        # Load cases
        if mode == "victims":
            query = """
SELECT 
    vawc_no, date, type_of_abuse,
    case_status, name_of_respondent AS co_involved
FROM vawc_logs
WHERE is_deleted = 0
    AND LOWER(TRIM(client_name)) = LOWER(TRIM(?))
ORDER BY date DESC
"""
        else:
            query = """
SELECT 
    vawc_no, date, type_of_abuse,
    case_status, client_name AS co_involved
FROM vawc_logs
WHERE is_deleted = 0
    AND LOWER(TRIM(name_of_respondent)) = LOWER(TRIM(?))
ORDER BY date DESC
"""

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(query, (name,))
            rows = cur.fetchall()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            rows = []

        for r in rows:
            v_no = r[0]
            date_s = r[1] or ""
            dt = parse_date_string(date_s)
            if dt:
                date_s = dt.strftime("%m/%d/%Y")
            case_tree.insert("", "end", values=(v_no, date_s, r[2] or "", r[3] or "", r[4] or ""))

    def _back_to_list(self, mode):
        # Preserve current search query so the same filter returns after returning from details
        current_search = self.search_entry.get() if hasattr(self, 'search_entry') else ""

        # Destroy and rebuild the whole UI container cleanly
        if hasattr(self, 'main_container') and self.main_container.winfo_exists():
            self.main_container.destroy()

        self.cards = []
        self.build_ui()
        self.refresh()

        # restore search text if any
        if current_search:
            self.search_entry.delete(0, 'end')
            self.search_entry.insert(0, current_search)

        # Restore mode view
        self.load_people(mode)

    def _on_case_double(self, event, tree):
        sel = tree.selection()
        if not sel:
            return
        vawc_no = tree.item(sel[0], "values")[0]
        try:
            ViewRecordWindow(self.master, vawc_no, user_role=self.user_role)
        except Exception as e:
            messagebox.showerror("Error", str(e))
