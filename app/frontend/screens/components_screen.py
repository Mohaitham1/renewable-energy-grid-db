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
components_data = [
    (701, "Solar Panel X5", "Photovoltaic", "Sahara Solar", "Healthy"),
    (702, "Inverter Pro", "Electronics", "Benban Solar", "Warning"),
    (703, "Turbine Blade", "Mechanical", "Zafarana Wind", "Healthy"),
    (704, "Backup Battery", "Storage", "Sahara Solar", "Faulty"),
    (705, "Grid Switch", "Electrical", "Zafarana Wind", "Healthy")
]

def mock_get_components():
    return components_data

def mock_add_component(name, cat, site, status):
    global components_data
    new_id = max([c[0] for c in components_data]) + 1 if components_data else 701
    components_data.append((new_id, name, cat, site, status))
    return True

def mock_delete_component(comp_id):
    global components_data
    components_data = [c for c in components_data if c[0] != comp_id]
    return True

# ==================================================
# MODERN UNDO TOAST (GNOME/UBUNTU STYLE)
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
        
        # UI Elements
        ctk.CTkLabel(self, text=message, text_color="#333333", font=("Arial", 13)).pack(side="left", padx=(20, 15), pady=10)
        ctk.CTkFrame(self, width=1, height=20, fg_color="#E0E0E0").pack(side="left", padx=5) # Visual Separator
        
        ctk.CTkButton(
            self, text="Undo", fg_color="transparent", text_color="#1f538d", 
            hover_color="#F0F0F0", width=60, font=("Arial", 13, "bold"),
            command=self.undo_clicked
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            self, text="✕", fg_color="transparent", text_color="#999999", 
            hover_color="#F0F0F0", width=30, command=self.destroy
        ).pack(side="left", padx=(0, 10))

        # Position at bottom center
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
# COMPONENTS SCREEN COMPONENT
# ==================================================
class ComponentsScreen(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        # Grid Configuration (3:1 Ratio)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._init_variables()
        self._setup_ui()
        self.load_data()

    def _init_variables(self):
        self.search_var = tk.StringVar()
        self.var_name = tk.StringVar()
        self.var_cat = tk.StringVar(value="Photovoltaic")
        self.var_site = tk.StringVar()
        self.var_status = tk.StringVar(value="Healthy")

    def _setup_ui(self):
        self._create_table_section()
        self._create_form_section()

    def _create_table_section(self):
        """Builds the table section with consistent search and styling."""
        container = ctk.CTkFrame(self)
        container.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        # Search Bar
        search_frame = ctk.CTkFrame(container, fg_color="transparent")
        search_frame.pack(fill="x", padx=15, pady=15)

        self.ent_search = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="Filter components...",
            font=("Arial", FONT_SIZE_TABLE)
        )
        self.ent_search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.ent_search.bind("<Return>", self._on_search)

        ctk.CTkButton(
            search_frame,
            text="Search",
            width=100,
            command=self._on_search
        ).pack(side="right")

        # Apply Global Table Style (Gray Lines)
        apply_modern_treeview_style()

        cols = ("id", "name", "cat", "site", "status")
        self.table = ttk.Treeview(container, columns=cols, show="headings")
        
        headers = ["Comp ID", "Component Name", "Category", "Installation Site", "Status"]
        for col, text in zip(cols, headers):
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

    def _on_row_select(self, event):
        selected = self.table.selection()
        if not selected: return
        v = self.table.item(selected[0])['values']
        self.var_name.set(v[1]); self.var_cat.set(v[2]); self.var_site.set(v[3]); self.var_status.set(v[4])

    def handle_add(self):
        if self.var_name.get() and self.var_site.get():
            mock_add_component(self.var_name.get(), self.var_cat.get(), self.var_site.get(), self.var_status.get())
            self.load_data()
            self.clear_form()

    def handle_delete(self):
        selected = self.table.selection()
        if not selected: return
        
        row_id = selected[0]
        comp_id = self.table.item(row_id)['values'][0]
        comp_name = self.table.item(row_id)['values'][1]
        
        # UI Detach (Modern Hide)
        self.table.detach(row_id)
        
        def undo_action():
            self.table.reattach(row_id, "", "end")
        
        def final_delete():
            mock_delete_component(comp_id)
        
        UndoToast(self, f"'{comp_name}' deleted", on_undo=undo_action, on_timeout=final_delete)

    def clear_form(self):
        self.var_name.set("")
        self.var_site.set("")
        self.table.selection_remove(self.table.selection())

    def _create_form_section(self):
        """Right Side: Management Form."""
        form_frame = ctk.CTkFrame(self, width=320)
        form_frame.grid(row=0, column=1, sticky="nsew")
        form_frame.grid_propagate(False)

        ctk.CTkLabel(
            form_frame,
            text="Component Details",
            font=ctk.CTkFont(size=FONT_SIZE_HEADER, weight="bold")
        ).pack(pady=25)

        self._create_input(form_frame, "Component Name:", self.var_name)
        
        ctk.CTkLabel(form_frame, text="Category:", font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25)
        ctk.CTkOptionMenu(
            form_frame, 
            values=["Photovoltaic", "Mechanical", "Electrical", "Storage"], 
            variable=self.var_cat,
            font=("Arial", FONT_SIZE_TABLE)
        ).pack(fill="x", padx=25, pady=(0, 15))

        self._create_input(form_frame, "Installation Site:", self.var_site)
        
        ctk.CTkLabel(form_frame, text="Condition Status:", font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25)
        ctk.CTkOptionMenu(
            form_frame, 
            values=["Healthy", "Warning", "Faulty", "Decommissioned"], 
            variable=self.var_status,
            font=("Arial", FONT_SIZE_TABLE)
        ).pack(fill="x", padx=25, pady=(0, 15))

        ctk.CTkButton(
            form_frame, text="Add Component", fg_color="#28a745", font=("Arial", 12, "bold"),
            command=self.handle_add
        ).pack(fill="x", padx=25, pady=(10, 5))

        ctk.CTkButton(
            form_frame, text="Delete Selected", fg_color="#dc3545", font=("Arial", 12, "bold"),
            command=self.handle_delete
        ).pack(fill="x", padx=25, pady=5)

        ctk.CTkButton(
            form_frame, text="Clear Form", fg_color="transparent", border_width=1,
            command=self.clear_form
        ).pack(fill="x", padx=25, pady=20)

    def _create_input(self, frame, label, var):
        ctk.CTkLabel(frame, text=label, font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25)
        ctk.CTkEntry(frame, textvariable=var, font=("Arial", FONT_SIZE_TABLE)).pack(fill="x", padx=25, pady=(0, 15))