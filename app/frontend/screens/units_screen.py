import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from frontend.screens.table_style import apply_modern_treeview_style

# ==================================================
# UI CONFIGURATION
# ==================================================
FONT_SIZE_HEADER = 20
FONT_SIZE_LABEL = 13
FONT_SIZE_TABLE = 12

# ==================================================
# MOCK BACKEND DATA
# ==================================================
units_data = [
    (101, "Sahara Solar", "PV Panel", "Active", "250kW"),
    (102, "Sahara Solar", "PV Panel", "Maintenance", "0kW"),
    (201, "Zafarana Wind", "Turbine", "Active", "2.1MW"),
    (202, "Zafarana Wind", "Turbine", "Active", "2.1MW"),
    (301, "Benban Solar", "Inverter", "Offline", "0kW")
]

def mock_get_units():
    return units_data

def mock_add_unit(site, type_, status, output):
    global units_data
    new_id = max([u[0] for u in units_data]) + 1 if units_data else 101
    units_data.append((new_id, site, type_, status, output))
    return True

def mock_delete_unit(unit_id):
    global units_data
    units_data = [u for u in units_data if u[0] != unit_id]
    return True

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
        ctk.CTkButton(self, text="Undo", fg_color="transparent", text_color="#1f538d", hover_color="#F0F0F0", width=60, font=("Arial", 13, "bold"), command=self.undo_clicked).pack(side="left", padx=10)
        ctk.CTkButton(self, text="✕", fg_color="transparent", text_color="#999999", hover_color="#F0F0F0", width=30, command=self.destroy).pack(side="left", padx=(0, 10))

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
# UNITS SCREEN COMPONENT
# ==================================================
class UnitsScreen(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._init_variables()
        self._setup_ui()
        self.load_data()

    def _init_variables(self):
        self.search_var = tk.StringVar()
        self.var_site = tk.StringVar()
        self.var_type = tk.StringVar(value="PV Panel")
        self.var_status = tk.StringVar(value="Active")
        self.var_output = tk.StringVar()

    def _setup_ui(self):
        self._create_table_section()
        self._create_form_section()

    def _create_table_section(self):
        container = ctk.CTkFrame(self)
        container.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        search_frame = ctk.CTkFrame(container, fg_color="transparent")
        search_frame.pack(fill="x", padx=15, pady=15)

        self.ent_search = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="Search units...",
            font=("Arial", FONT_SIZE_TABLE)
        )
        self.ent_search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.ent_search.bind("<Return>", self._on_search)

        ctk.CTkButton(search_frame, text="Search", width=100, command=self._on_search).pack(side="right")

        apply_modern_treeview_style()

        cols = ("id", "site", "type", "status", "output")
        self.table = ttk.Treeview(container, columns=cols, show="headings")
        for col, text in zip(cols, ["Unit ID", "Parent Site", "Unit Type", "Status", "Output"]):
            self.table.heading(col, text=text)
            self.table.column(col, anchor="center")
        self.table.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.table.bind("<<TreeviewSelect>>", self._on_row_select)

    def _on_search(self, event=None):
        self.load_data(self.search_var.get())

    def load_data(self, query=""):
        query = query.lower().strip()
        rows = mock_get_units()
        if query:
            rows = [
                row for row in rows
                if query in " ".join(map(str, row[1:])).lower()
            ]
        for row_id in self.table.get_children():
            self.table.delete(row_id)
        for item in rows:
            self.table.insert("", "end", values=item)

    def _on_row_select(self, event):
        selected = self.table.selection()
        if not selected: 
            return
        v = self.table.item(selected[0])['values']
        self.var_site.set(v[1]); self.var_type.set(v[2]); self.var_status.set(v[3]); self.var_output.set(v[4])

    def handle_add(self):
        if self.var_site.get():
            mock_add_unit(self.var_site.get(), self.var_type.get(), self.var_status.get(), self.var_output.get())
            self.load_data(); self.clear_form()

    def handle_delete(self):
        selected = self.table.selection()
        if not selected:
            return
        
        row_id = selected[0]
        unit_id = self.table.item(row_id)['values'][0]
        unit_name = self.table.item(row_id)['values'][1]
        
        self.table.detach(row_id)
        
        def undo_action():
            self.table.reattach(row_id, "", "end")
        
        def final_delete():
            mock_delete_unit(unit_id)
        
        UndoToast(self, f"'{unit_name}' deleted", on_undo=undo_action, on_timeout=final_delete)

    def clear_form(self):
        self.var_site.set(""); self.var_output.set("")
        self.table.selection_remove(self.table.selection())

    def _create_form_section(self):
        form_frame = ctk.CTkFrame(self, width=320)
        form_frame.grid(row=0, column=1, sticky="nsew")
        form_frame.grid_propagate(False)

        ctk.CTkLabel(
            form_frame,
            text="Unit Details",
            font=ctk.CTkFont(size=FONT_SIZE_HEADER, weight="bold")
        ).pack(pady=25)

        self._create_input(form_frame, "Parent Site:", self.var_site)
        self._create_input(form_frame, "Unit Type:", self.var_type)
        self._create_input(form_frame, "Status:", self.var_status)
        self._create_input(form_frame, "Output:", self.var_output)

        ctk.CTkButton(
            form_frame,
            text="Add Unit",
            fg_color="#28a745",
            hover_color="#218838",
            font=("Arial", FONT_SIZE_TABLE, "bold"),
            command=self.handle_add
        ).pack(fill="x", padx=25, pady=(10, 5))

        ctk.CTkButton(
            form_frame,
            text="Delete Selected",
            fg_color="#dc3545",
            hover_color="#c82333",
            font=("Arial", FONT_SIZE_TABLE, "bold"),
            command=self.handle_delete
        ).pack(fill="x", padx=25, pady=5)

        ctk.CTkButton(
            form_frame,
            text="Clear",
            fg_color="transparent",
            border_width=1,
            font=("Arial", FONT_SIZE_TABLE),
            command=self.clear_form
        ).pack(fill="x", padx=25, pady=20)

    def _create_input(self, parent, label, variable):
        ctk.CTkLabel(parent, text=label, font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25, pady=(10, 0))
        ctk.CTkEntry(parent, textvariable=variable, font=("Arial", FONT_SIZE_TABLE)).pack(fill="x", padx=25, pady=(0, 15))

    def clear_form(self):
        self.var_site.set("")
        self.var_type.set("PV Panel")
        self.var_status.set("Active")
        self.var_output.set("")
        self.table.selection_remove(self.table.selection())