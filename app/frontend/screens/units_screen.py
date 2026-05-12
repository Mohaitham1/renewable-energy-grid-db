import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from frontend.screens.table_style import apply_modern_treeview_style

# ==================================================
# REAL BACKEND INTEGRATION
# ==================================================
from backend.unit_operations import get_all_units, add_unit, delete_unit
from backend.site_operations import get_all_sites # To help with site selection

# UI CONFIGURATION
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
        ctk.CTkButton(self, text="Undo", fg_color="transparent", text_color="#1f538d", hover_color="#F0F0F0", 
                      width=60, font=("Arial", 13, "bold"), command=self.undo_clicked).pack(side="left", padx=10)
        ctk.CTkButton(self, text="✕", fg_color="transparent", text_color="#999999", hover_color="#F0F0F0", 
                      width=30, command=self.destroy).pack(side="left", padx=(0, 10))

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
            search_frame, textvariable=self.search_var,
            placeholder_text="Search units by site or type...",
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
        try:
            rows = get_all_units() # REAL DATABASE CALL
            
            if query:
                rows = [row for row in rows if query in " ".join(map(str, row)).lower()]
            
            for row_id in self.table.get_children():
                self.table.delete(row_id)
            for item in rows:
                self.table.insert("", "end", values=item)
        except Exception as e:
            print(f"Error loading units: {e}")

    def _on_row_select(self, event):
        selected = self.table.selection()
        if not selected: return
        v = self.table.item(selected[0])['values']
        self.var_site.set(v[1]); self.var_type.set(v[2]); self.var_status.set(v[3]); self.var_output.set(v[4])

    def handle_add(self):
        site = self.var_site.get()
        u_type = self.var_type.get()
        status = self.var_status.get()
        output = self.var_output.get()

        if site and u_type:
            try:
                # REAL DATABASE CALL
                if add_unit(site, u_type, status, output):
                    self.load_data()
                    self.clear_form()
                    messagebox.showinfo("Success", f"Unit added to {site}")
                else:
                    messagebox.showerror("Error", "Could not add unit. Ensure the Site exists.")
            except Exception as e:
                messagebox.showerror("DB Error", str(e))

    def handle_delete(self):
        selected = self.table.selection()
        if not selected: return
        
        row_id = selected[0]
        unit_id = self.table.item(row_id)['values'][0]
        unit_name = self.table.item(row_id)['values'][2] # Unit Type for the label
        
        self.table.detach(row_id)
        
        def undo_action():
            self.table.reattach(row_id, "", "end")
        
        def final_delete():
            try:
                # REAL DATABASE CALL
                delete_unit(unit_id)
            except Exception as e:
                print(f"Error deleting unit: {e}")
        
        UndoToast(self, f"'{unit_name}' deleted", on_undo=undo_action, on_timeout=final_delete)

    def clear_form(self):
        self.var_site.set(""); self.var_output.set("")
        self.var_type.set("PV Panel"); self.var_status.set("Active")
        self.table.selection_remove(self.table.selection())

    def _create_form_section(self):
        form_frame = ctk.CTkFrame(self, width=320)
        form_frame.grid(row=0, column=1, sticky="nsew")
        form_frame.grid_propagate(False)

        ctk.CTkLabel(form_frame, text="Unit Details", font=ctk.CTkFont(size=FONT_SIZE_HEADER, weight="bold")).pack(pady=25)

        # Better Site Selection: Use an OptionMenu with real site names
        ctk.CTkLabel(form_frame, text="Parent Site:", font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25)
        try:
            site_names = [s[1] for s in get_all_sites()] # REAL SITE NAMES
            if not site_names: site_names = ["No Sites Available"]
        except:
            site_names = ["Database Error"]

        self.site_dropdown = ctk.CTkOptionMenu(form_frame, values=site_names, variable=self.var_site)
        self.site_dropdown.pack(fill="x", padx=25, pady=(0, 15))

        self._create_input(form_frame, "Unit Type (e.g. Turbine):", self.var_type)
        
        ctk.CTkLabel(form_frame, text="Status:", font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25)
        ctk.CTkOptionMenu(form_frame, values=["Active", "Maintenance", "Offline", "Faulty"], variable=self.var_status).pack(fill="x", padx=25, pady=(0, 15))
        
        self._create_input(form_frame, "Output (e.g. 500kW):", self.var_output)

        ctk.CTkButton(form_frame, text="Save Unit", fg_color="#28a745", font=("Arial", FONT_SIZE_TABLE, "bold"), 
                      command=self.handle_add).pack(fill="x", padx=25, pady=(10, 5))

        ctk.CTkButton(form_frame, text="Delete Selected", fg_color="#dc3545", font=("Arial", FONT_SIZE_TABLE, "bold"), 
                      command=self.handle_delete).pack(fill="x", padx=25, pady=5)

        ctk.CTkButton(form_frame, text="Clear", fg_color="transparent", border_width=1, 
                      command=self.clear_form).pack(fill="x", padx=25, pady=20)

    def _create_input(self, parent, label, variable):
        ctk.CTkLabel(parent, text=label, font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25, pady=(10, 0))
        ctk.CTkEntry(parent, textvariable=variable, font=("Arial", FONT_SIZE_TABLE)).pack(fill="x", padx=25, pady=(0, 15))