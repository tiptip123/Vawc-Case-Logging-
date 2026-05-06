import customtkinter as ctk
from tkinter import ttk, messagebox
from db import get_connection

class AuditLogFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        # Header
        title_container = ctk.CTkFrame(self, fg_color="transparent")
        title_container.pack(fill="x", padx=40, pady=(30, 10))
        ctk.CTkLabel(title_container, text="System Audit Logs", font=("Arial", 22, "bold"), text_color=["#1a2a4a", "#f8fafc"]).pack(side="left")
        ctk.CTkLabel(title_container, text="Track all user actions and system changes", font=("Arial", 12), text_color=["#64748b", "#94a3b8"]).pack(side="left", padx=20, pady=(5, 0))

        # Table Card
        container = ctk.CTkFrame(self, fg_color=["white", "#242424"], corner_radius=12, border_width=1, border_color=["#e2e8f0", "#333333"])
        container.pack(fill="both", expand=True, padx=40, pady=(0, 40))

        # Styling
        style = ttk.Style()
        style.theme_use("clam")
        
        is_dark = ctk.get_appearance_mode() == "Dark"
        tree_bg = "#ffffff" if not is_dark else "#2b2b2b"
        tree_fg = "#000000" if not is_dark else "#ffffff"
        
        style.configure("Treeview", background=tree_bg, foreground=tree_fg, rowheight=38, fieldbackground=tree_bg, font=("Arial", 10), borderwidth=0)
        style.map("Treeview", background=[("selected", "#1a2a4a")], foreground=[("selected", "#ffffff")])
        
        # Heading configuration
        heading_bg = "#f1f5f9" if not is_dark else "#1a1a1a"
        style.configure("Treeview.Heading", background=heading_bg, foreground=tree_fg, font=("Arial", 11, "bold"), borderwidth=0)

        # Custom Scrollbar
        scrollbar = ctk.CTkScrollbar(container, orientation="vertical")
        scrollbar.pack(side="right", fill="y", padx=2, pady=2)

        # Treeview
        self.tree = ttk.Treeview(container, columns=("User", "Action", "Record", "Details", "Timestamp"), 
                                 show="headings", yscrollcommand=scrollbar.set)
        
        # Configure tags
        self.tree.tag_configure("evenrow", background="#242424" if is_dark else "#ffffff", foreground="#ffffff" if is_dark else "#000000")
        self.tree.tag_configure("oddrow", background="#1e1e1e" if is_dark else "#f8fafc", foreground="#ffffff" if is_dark else "#000000")
        
        self.tree.heading("User", text="USER")
        self.tree.heading("Action", text="ACTION")
        self.tree.heading("Record", text="TARGET RECORD")
        self.tree.heading("Details", text="DETAILS")
        self.tree.heading("Timestamp", text="TIMESTAMP")

        self.tree.column("User", width=120)
        self.tree.column("Action", width=120)
        self.tree.column("Record", width=150)
        self.tree.column("Details", width=350)
        self.tree.column("Timestamp", width=180)

        self.tree.pack(fill="both", expand=True, padx=20, pady=20)
        scrollbar.configure(command=self.tree.yview)

        self.load_logs()

    def load_logs(self):
        try:
            # Clear existing
            for item in self.tree.get_children():
                self.tree.delete(item)

            connection = get_connection()
            cursor = connection.cursor()
            
            # Fetch latest 100 logs
            cursor.execute("SELECT username, action, target_record, details, timestamp FROM audit_logs ORDER BY timestamp DESC LIMIT 100")
            rows = cursor.fetchall()
            
            for i, row in enumerate(rows):
                tag = "evenrow" if i % 2 == 0 else "oddrow"
                self.tree.insert("", "end", values=row, tags=(tag,))

            # Tag configuration moved to __init__
            cursor.close()
            connection.close()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load logs: {str(e)}")
