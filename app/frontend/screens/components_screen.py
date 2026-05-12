import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from frontend.screens.table_style import apply_modern_treeview_style

# ==================================================
# REAL BACKEND INTEGRATION
# ==================================================
from backend.component_operations import (
    get_all_components, 
    add_component, 
    delete_component, 
    update_component, 
    search_components
)
from backend.site_operations import get_all_sites

# UI CONFIGURATION
FONT_SIZE_HEADER = 20
FONT_SIZE_LABEL = 13
FONT_SIZE_TABLE = 12

class ComponentsScreen(ctk.CTkFrame):
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
        self.selected_comp_id = None
        
        # Form Variables
        self.var_name = tk.StringVar()
        self.var_cat = tk.StringVar(value="Electrical")
        self.var_site = tk.StringVar()
        self.var_status = tk.StringVar(value="Healthy")

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
            placeholder_text="Search components...",
            font=("Arial", FONT_SIZE_TABLE)
        )
        self.ent_search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.ent_search.bind("<KeyRelease>", lambda e: self.load_data(self.search_var.get()))

        apply_modern_treeview_style()

        cols = ("id", "name", "cat", "site", "status")
        self.table = ttk.Treeview(container, columns=cols, show="headings")
        headers = ["ID", "Component Name", "Category", "Site", "Status"]
        for col, text in zip(cols, headers):
            self.table.heading(col, text=text)
            self.table.column(col, anchor="center")

        self.table.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.table.bind("<<TreeviewSelect>>", self._on_row_select)

    def load_data(self, query=""):
        try:
            if query.strip():
                rows = search_components(query) #
            else:
                rows = get_all_components() #
            
            for row_id in self.table.get_children():
                self.table.delete(row_id)
            for item in rows:
                self.table.insert("", "end", values=item)
        except Exception as e:
            print(f"Error loading components: {e}")

    def _on_row_select(self, event):
        selected = self.table.selection()
        if not selected: return
        v = self.table.item(selected[0])['values']
        
        self.selected_comp_id = v[0]
        self.var_name.set(v[1])
        self.var_cat.set(v[2])
        self.var_site.set(v[3])
        self.var_status.set(v[4])

    def handle_save(self):
        name = self.var_name.get()
        cat = self.var_cat.get()
        site = self.var_site.get()
        status = self.var_status.get()

        if not name or not site:
            messagebox.showwarning("Input Error", "Please fill in all fields.")
            return

        try:
            if self.selected_comp_id:
                # UPDATE EXISTING
                success = update_component(self.selected_comp_id, name, cat, site, status)
                msg = "Component updated."
            else:
                # ADD NEW
                success = add_component(name, cat, site, status)
                msg = "Component added."

            if success:
                self.load_data()
                self.clear_form()
                messagebox.showinfo("Success", msg)
            else:
                messagebox.showerror("Error", "Operation failed. Check if Site exists.")
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def handle_delete(self):
        if not self.selected_comp_id: return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this component?"):
            try:
                if delete_component(self.selected_comp_id): #
                    self.load_data()
                    self.clear_form()
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete: {e}")

    def clear_form(self):
        self.selected_comp_id = None
        self.var_name.set("")
        self.var_cat.set("Electrical")
        self.var_site.set("")
        self.var_status.set("Healthy")
        self.table.selection_remove(self.table.selection())

    def _create_form_section(self):
        form_frame = ctk.CTkFrame(self, width=320)
        form_frame.grid(row=0, column=1, sticky="nsew")
        form_frame.grid_propagate(False)

        ctk.CTkLabel(form_frame, text="Component Details", font=ctk.CTkFont(size=FONT_SIZE_HEADER, weight="bold")).pack(pady=25)

        self._create_input(form_frame, "Component Name:", self.var_name)
        
        ctk.CTkLabel(form_frame, text="Category:", font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25)
        ctk.CTkOptionMenu(form_frame, values=["Electrical", "Mechanical", "Photovoltaic", "Sensor"], variable=self.var_cat).pack(fill="x", padx=25, pady=(0, 15))

        ctk.CTkLabel(form_frame, text="Installation Site:", font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25)
        try:
            site_names = [s[1] for s in get_all_sites()] #
            if not site_names: site_names = ["No Sites Available"]
        except:
            site_names = ["Database Error"]
        
        self.site_menu = ctk.CTkOptionMenu(form_frame, values=site_names, variable=self.var_site)
        self.site_menu.pack(fill="x", padx=25, pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="Condition Status:", font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25)
        ctk.CTkOptionMenu(form_frame, values=["Healthy", "Warning", "Faulty"], variable=self.var_status).pack(fill="x", padx=25, pady=(0, 15))

        ctk.CTkButton(form_frame, text="Save Component", fg_color="#28a745", command=self.handle_save).pack(fill="x", padx=25, pady=(10, 5))
        ctk.CTkButton(form_frame, text="Delete Selected", fg_color="#dc3545", command=self.handle_delete).pack(fill="x", padx=25, pady=5)
        ctk.CTkButton(form_frame, text="Clear", fg_color="transparent", border_width=1, command=self.clear_form).pack(fill="x", padx=25, pady=20)

    def _create_input(self, frame, label, var):
        ctk.CTkLabel(frame, text=label, font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25, pady=(10, 0))
        ctk.CTkEntry(frame, textvariable=var, font=("Arial", FONT_SIZE_TABLE)).pack(fill="x", padx=25, pady=(0, 15))