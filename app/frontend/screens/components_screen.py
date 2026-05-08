import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from frontend.screens.table_style import apply_modern_treeview_style

class ComponentsScreen(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        title = ctk.CTkLabel(self, text="Components", font=ctk.CTkFont(size=28, weight="bold"))
        title.pack(pady=20)

        label = ctk.CTkLabel(self, text="Track spare parts and replacements")
        label.pack(pady=10)

    def handle_delete(self):
        selected = self.table.selection()
        if not selected:
            return

        row_id = selected[0]
        item_id = self.table.item(row_id)['values'][0]
        item_name = self.table.item(row_id)['values'][1]

        self.table.detach(row_id)
        self.table.selection_remove(row_id)

        def undo_action():
            self.table.reattach(row_id, "", "end")
            print(f"UNDO: Restored component {item_name}")

        def final_delete():
            if mock_delete_component(item_id):
                self.load_data()

        UndoToast(self, f"Deleted '{item_name}'", on_undo=undo_action, on_timeout=final_delete)

    def _init_variables(self):
        self.search_var = tk.StringVar()
        self.var_name = tk.StringVar()
        self.var_type = tk.StringVar(value="Photovoltaic")
        self.var_site = tk.StringVar()
        self.var_status = tk.StringVar(value="Healthy")

    def _create_table_section(self):
        container = ctk.CTkFrame(self)
        container.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        search_frame = ctk.CTkFrame(container, fg_color="transparent")
        search_frame.pack(fill="x", padx=15, pady=15)

        self.ent_search = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="Search components...",
            font=("Arial", FONT_SIZE_TABLE)
        )
        self.ent_search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.ent_search.bind("<Return>", self._on_search)

        ctk.CTkButton(search_frame, text="Search", width=100, command=self._on_search).pack(side="right")

        apply_modern_treeview_style()

        cols = ("id", "name", "type", "site", "status")
        self.table = ttk.Treeview(container, columns=cols, show="headings")
        for col, text in zip(cols, ["ID", "Name", "Category", "Site", "Status"]):
            self.table.heading(col, text=text)
            self.table.column(col, anchor="center")
        self.table.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.table.bind("<<TreeviewSelect>>", self._on_row_select)

    def _on_search(self, event=None):
        self.load_data(self.search_var.get())

    def load_data(self, query=""):
        query = query.lower().strip()
        rows = mock_get_components()
        if query:
            rows = [
                row for row in rows
                if query in " ".join(map(str, row[1:])).lower()
            ]
        for row_id in self.table.get_children():
            self.table.delete(row_id)
        for item in rows:
            self.table.insert("", "end", values=item)