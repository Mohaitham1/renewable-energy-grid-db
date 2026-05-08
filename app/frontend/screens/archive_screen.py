import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from frontend.screens.table_style import apply_modern_treeview_style
from frontend.screens.data_manager import get_archived, restore_from_archive, permanent_delete

# ==================================================
# UI CONFIGURATION
# ==================================================
FONT_SIZE_HEADER = 20
FONT_SIZE_LABEL = 13
FONT_SIZE_TABLE = 12

# ==================================================
# MODERN UNDO TOAST
# ==================================================
class UndoToast(ctk.CTkFrame):
    def __init__(self, parent, message, on_undo, on_timeout):
        super().__init__(
            parent, 
            fg_color="#FFFFFF", 
            border_color="#E0E0E0", 
            border_width=1, 
            corner_radius=10
        )
        self.on_undo = on_undo
        self.on_timeout = on_timeout
        self.timer_seconds = 5
        
        ctk.CTkLabel(self, text=message, text_color="#333333", font=("Arial", 13)).pack(side="left", padx=(20, 15), pady=10)
        ctk.CTkFrame(self, width=1, height=20, fg_color="#E0E0E0").pack(side="left", padx=5)
        
        ctk.CTkButton(
            self, text="Undo", fg_color="transparent", text_color="#1f538d", 
            hover_color="#F0F0F0", width=60, font=("Arial", 13, "bold"),
            command=self.undo_clicked
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            self, text="✕", fg_color="transparent", text_color="#999999", 
            hover_color="#F0F0F0", width=30, command=self.destroy
        ).pack(side="left", padx=(0, 10))

        self.place(relx=0.5, rely=0.9, anchor="s")
        self.after(self.timer_seconds * 1000, self.timeout_reached)

    def undo_clicked(self):
        self.on_undo()
        self.destroy()

    def timeout_reached(self):
        if self.winfo_exists():
            self.on_timeout()
            self.destroy()

# ==================================================
# ARCHIVE SCREEN COMPONENT
# ==================================================
class ArchiveScreen(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        # Grid Configuration (3:1 Ratio to match other screens)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        self._create_table_section()
        self._create_action_section()

    def _create_table_section(self):
        container = ctk.CTkFrame(self)
        container.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        # Title Header
        header_frame = ctk.CTkFrame(container, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(
            header_frame, 
            text="Archived Reports", 
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(side="left")

        # Table Styling
        apply_modern_treeview_style()

        cols = ("id", "title", "date", "type", "author")
        self.table = ttk.Treeview(container, columns=cols, show="headings")
        
        headers = ["ID", "Report Title", "Creation Date", "Category", "Author"]
        for col, text in zip(cols, headers):
            self.table.heading(col, text=text)
            self.table.column(col, anchor="center")

        self.table.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def _create_action_section(self):
        action_frame = ctk.CTkFrame(self, width=320)
        action_frame.grid(row=0, column=1, sticky="nsew")
        action_frame.grid_propagate(False)

        ctk.CTkLabel(
            action_frame, 
            text="Archive Actions", 
            font=ctk.CTkFont(size=FONT_SIZE_HEADER, weight="bold")
        ).pack(pady=25)

        ctk.CTkLabel(
            action_frame, 
            text="Select an item from the list\nto restore or delete it.",
            font=("Arial", FONT_SIZE_LABEL),
            text_color="gray"
        ).pack(pady=(0, 30))

        # Action Buttons
        ctk.CTkButton(
            action_frame, 
            text="Restore to Active", 
            fg_color="#28a745", 
            hover_color="#218838",
            font=("Arial", 12, "bold"),
            command=self.handle_restore
        ).pack(fill="x", padx=25, pady=10)

        ctk.CTkButton(
            action_frame, 
            text="Delete Permanently", 
            fg_color="#dc3545", 
            hover_color="#c82333",
            font=("Arial", 12, "bold"),
            command=self.handle_delete
        ).pack(fill="x", padx=25, pady=5)

    def load_data(self):
        """Refreshes the table with data from the archive database."""
        for row in self.table.get_children():
            self.table.delete(row)
        
        archived_items = get_archived()
        for item in archived_items:
            self.table.insert("", "end", values=item)

    def handle_restore(self):
        selected = self.table.selection()
        if not selected:
            return
        
        row_id = selected[0]
        rep_id = self.table.item(row_id)['values'][0]
        rep_name = self.table.item(row_id)['values'][1]
        
        self.table.detach(row_id)
        
        def undo_action():
            self.table.reattach(row_id, "", "end")
        
        def final_restore():
            if restore_from_archive(rep_id):
                # No need to reload table here as it's already detached
                pass
        
        UndoToast(self, f"'{rep_name}' restored", on_undo=undo_action, on_timeout=final_restore)

    def handle_delete(self):
        selected = self.table.selection()
        if not selected:
            return
        
        row_id = selected[0]
        rep_id = self.table.item(row_id)['values'][0]
        rep_name = self.table.item(row_id)['values'][1]
        
        self.table.detach(row_id)
        
        def undo_action():
            self.table.reattach(row_id, "", "end")
        
        def final_delete():
            permanent_delete(rep_id, from_archive=True)
        
        UndoToast(self, f"'{rep_name}' deleted forever", on_undo=undo_action, on_timeout=final_delete)