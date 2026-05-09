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
sites_data = [
    (1, "Sahara Solar Park", "Solar", "Aswan", "500 MW"),
    (2, "Zafarana Wind Farm", "Wind", "Red Sea", "545 MW"),
    (3, "Benban Solar", "Solar", "Aswan", "1.8 GW"),
    (4, "Gabali El-Zeit", "Wind", "Red Sea", "580 MW")
]

def mock_get_sites():
    return sites_data

def mock_add_site(name, type_, location, capacity):
    global sites_data
    new_id = max([s[0] for s in sites_data]) + 1 if sites_data else 1
    sites_data.append((new_id, name, type_, location, capacity))
    return True

def mock_delete_site(site_id):
    global sites_data
    sites_data = [s for s in sites_data if s[0] != site_id]
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
# SITES SCREEN CLASS
# ==================================================
class SitesScreen(ctk.CTkFrame):
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
        self.var_name = tk.StringVar()
        self.var_type = tk.StringVar(value="Solar")
        self.var_loc = tk.StringVar()
        self.var_cap = tk.StringVar()

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
            placeholder_text="Search sites...",
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

        apply_modern_treeview_style()

        cols = ("id", "name", "type", "loc", "cap")
        self.table = ttk.Treeview(container, columns=cols, show="headings")
        for col, text in zip(cols, ["ID", "Site Name", "Energy Type", "Location", "Capacity"]):
            self.table.heading(col, text=text)
            self.table.column(col, anchor="center")
        self.table.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.table.bind("<<TreeviewSelect>>", self._on_row_select)

    def _on_search(self, event=None):
        self.load_data(self.search_var.get())

    def load_data(self, query=""):
        query = query.lower().strip()
        rows = mock_get_sites()
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
        vals = self.table.item(selected[0])['values']
        self.var_name.set(vals[1])
        self.var_type.set(vals[2])
        self.var_loc.set(vals[3])
        self.var_cap.set(vals[4])

    def handle_add(self):
        name, type_, loc, cap = self.var_name.get(), self.var_type.get(), self.var_loc.get(), self.var_cap.get()
        if name and loc:
            if mock_add_site(name, type_, loc, cap):
                self.load_data()
                self.clear_form()

    def handle_delete(self):
        selected = self.table.selection()
        if not selected:
            return
        
        row_id = selected[0]
        site_id = self.table.item(row_id)['values'][0]
        site_name = self.table.item(row_id)['values'][1]
        
        self.table.detach(row_id)
        
        def undo_action():
            self.table.reattach(row_id, "", "end")
        
        def final_delete():
            mock_delete_site(site_id)
        
        UndoToast(self, f"'{site_name}' deleted", on_undo=undo_action, on_timeout=final_delete)

    def clear_form(self):
        self.var_name.set("")
        self.var_type.set("Solar")
        self.var_loc.set("")
        self.var_cap.set("")
        self.table.selection_remove(self.table.selection())

    def _create_form_section(self):
        form_frame = ctk.CTkFrame(self, width=320)
        form_frame.grid(row=0, column=1, sticky="nsew")
        form_frame.grid_propagate(False)

        ctk.CTkLabel(
            form_frame,
            text="Site Details",
            font=ctk.CTkFont(size=FONT_SIZE_HEADER, weight="bold")
        ).pack(pady=25)

        self._create_input(form_frame, "Site Name:", self.var_name)
        self._create_input(form_frame, "Energy Type:", self.var_type)
        self._create_input(form_frame, "Location:", self.var_loc)
        self._create_input(form_frame, "Capacity:", self.var_cap)

        ctk.CTkButton(
            form_frame,
            text="Add Site",
            fg_color="#28a745",
            command=self.handle_add
        ).pack(fill="x", padx=25, pady=(10, 5))

        ctk.CTkButton(
            form_frame,
            text="Delete Selected",
            fg_color="#dc3545",
            command=self.handle_delete
        ).pack(fill="x", padx=25, pady=5)

        ctk.CTkButton(
            form_frame,
            text="Clear Form",
            fg_color="transparent",
            border_width=1,
            command=self.clear_form
        ).pack(fill="x", padx=25, pady=20)

    def _create_input(self, frame, label, var):
        ctk.CTkLabel(frame, text=label).pack(pady=5)
        ctk.CTkEntry(frame, textvariable=var, width=250).pack(pady=5)