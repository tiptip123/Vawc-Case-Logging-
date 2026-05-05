import customtkinter as ctk
from tkinter import ttk, messagebox
from db import get_connection

class AuditLogFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#f5f5f5")
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(60, 20))
        ctk.CTkLabel(header, text="📜 System Audit Logs", font=("Arial", 24, "bold"), text_color="#1a2a4a").pack(side="left")

        # Table Container
        container = ctk.CTkFrame(self, fg_color="white", corner_radius=15)
        container.pack(fill="both", expand=True, padx=40, pady=(0, 40))

        # Styling for Treeview
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", 
                        background="white", 
                        foreground="black", 
                        rowheight=35, 
                        fieldbackground="white",
                        font=("Arial", 10))
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"), background="#f8f9fa")
        style.map("Treeview", background=[('selected', '#1a73e8')])

        # Scrollbar
        tree_scroll = ctk.CTkScrollbar(container)
        tree_scroll.pack(side="right", fill="y")

        # Treeview
        self.tree = ttk.Treeview(container, columns=("User", "Action", "Record", "Details", "Timestamp"), 
                                 show="headings", yscrollcommand=tree_scroll.set)
        
        self.tree.heading("User", text="USER")
        self.tree.heading("Action", text="ACTION")
        self.tree.heading("Record", text="TARGET RECORD")
        self.tree.heading("Details", text="DETAILS")
        self.tree.heading("Timestamp", text="TIMESTAMP")

        self.tree.column("User", width=120)
        self.tree.column("Action", width=120)
        self.tree.column("Record", width=150)
        self.tree.column("Details", width=300)
        self.tree.column("Timestamp", width=180)

        self.tree.pack(fill="both", expand=True, padx=20, pady=20)
        tree_scroll.configure(command=self.tree.yview)

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

            self.tree.tag_configure("evenrow", background="#ffffff")
            self.tree.tag_configure("oddrow", background="#f8f9fa")

            cursor.close()
            connection.close()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load logs: {str(e)}")
