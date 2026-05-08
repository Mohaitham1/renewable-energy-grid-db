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
technicians_data = [
    (1, "Ahmed Ali", "Solar Systems", "Expert", "Active"),
    (2, "Mona Hassan", "Wind Turbines", "Senior", "On-Site"),
    (3, "Sami Yassin", "Electrical Grid", "Junior", "Active"),
    (4, "Laila Mahmoud", "Solar Systems", "Senior", "Vacation")
]

def mock_get_technicians():
    """Simulates: SELECT * FROM Technicians"""
    return technicians_data

def mock_add_technician(name, spec, cert, status):
    """Simulates: INSERT INTO Technicians ..."""
    global technicians_data
    new_id = max([t[0] for t in technicians_data]) + 1 if technicians_data else 1
    technicians_data.append((new_id, name, spec, cert, status))
    return True

def mock_delete_technician(tech_id):
    """Simulates: DELETE FROM Technicians WHERE id = ..."""
    global technicians_data
    technicians_data = [t for t in technicians_data if t[0] != tech_id]
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
# TECHNICIANS SCREEN COMPONENT
# ==================================================
class TechniciansScreen(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._init_variables()
        self._setup_ui()
        self.load_data()

    def _init_variables(self):
        """Initialize Tkinter variables for the management form."""
        self.search_var = tk.StringVar()
        self.var_name = tk.StringVar()
        self.var_spec = tk.StringVar(value="Solar Systems")
        self.var_cert = tk.StringVar(value="Senior")
        self.var_status = tk.StringVar(value="Active")

    def _setup_ui(self):
        """Build the visual structure of the screen."""
        self._create_table_section()
        self._create_form_section()

    def _create_table_section(self):
        """Builds the left-side section with data display."""
        container = ctk.CTkFrame(self)
        container.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        search_frame = ctk.CTkFrame(container, fg_color="transparent")
        search_frame.pack(fill="x", padx=15, pady=15)

        self.ent_search = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="Search technicians...",
            font=("Arial", FONT_SIZE_TABLE)
        )
        self.ent_search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.ent_search.bind("<Return>", self._on_search)

        ctk.CTkButton(search_frame, text="Search", width=100, command=self._on_search).pack(side="right")

        apply_modern_treeview_style()

        cols = ("id", "name", "spec", "cert", "status")
        self.table = ttk.Treeview(container, columns=cols, show="headings")
        for col, text in zip(cols, ["Tech ID", "Technician", "Specialty", "Certification", "Status"]):
            self.table.heading(col, text=text)
            self.table.column(col, anchor="center")
        self.table.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.table.bind("<<TreeviewSelect>>", self._on_row_select)

    def _on_search(self, event=None):
        self.load_data(self.search_var.get())

    def load_data(self, query=""):
        query = query.lower().strip()
        rows = mock_get_technicians()
        if query:
            rows = [
                row for row in rows
                if query in " ".join(map(str, row[1:])).lower()
            ]
        for row_id in self.table.get_children():
            self.table.delete(row_id)
        for item in rows:
            self.table.insert("", "end", values=item)

    def _create_form_section(self):
        """Builds the right-side management form."""
        form_frame = ctk.CTkFrame(self, width=320)
        form_frame.grid(row=0, column=1, sticky="nsew")
        form_frame.grid_propagate(False)

        ctk.CTkLabel(
            form_frame, 
            text="Staff Management", 
            font=ctk.CTkFont(size=FONT_SIZE_HEADER, weight="bold")
        ).pack(pady=(25, 20))

        self._create_labeled_input(form_frame, "Full Name:", self.var_name)
        
        ctk.CTkLabel(form_frame, text="Specialization:", font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25)
        ctk.CTkOptionMenu(
            form_frame, 
            values=["Solar Systems", "Wind Turbines", "Electrical Grid", "Hydroelectric", "Safety Compliance"], 
            variable=self.var_spec,
            font=("Arial", FONT_SIZE_TABLE)
        ).pack(fill="x", padx=25, pady=(0, 15))

        ctk.CTkLabel(form_frame, text="Certification:", font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25)
        ctk.CTkOptionMenu(
            form_frame, 
            values=["Junior", "Mid-Level", "Senior", "Expert", "Lead"], 
            variable=self.var_cert,
            font=("Arial", FONT_SIZE_TABLE)
        ).pack(fill="x", padx=25, pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="Status:", font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25)
        ctk.CTkOptionMenu(
            form_frame, 
            values=["Active", "On-Site", "Off-Duty", "Vacation", "Suspended"], 
            variable=self.var_status,
            font=("Arial", FONT_SIZE_TABLE)
        ).pack(fill="x", padx=25, pady=(0, 15))

        ctk.CTkButton(
            form_frame, text="Add Technician", fg_color="#28a745", hover_color="#218838", 
            font=("Arial", FONT_SIZE_TABLE, "bold"), command=self.handle_add
        ).pack(fill="x", padx=25, pady=(10, 5))

        ctk.CTkButton(
            form_frame, text="Delete Record", fg_color="#dc3545", hover_color="#c82333", 
            font=("Arial", FONT_SIZE_TABLE, "bold"), command=self.handle_delete
        ).pack(fill="x", padx=25, pady=5)

        ctk.CTkButton(
            form_frame, text="Clear Form", fg_color="transparent", border_width=1, 
            font=("Arial", FONT_SIZE_TABLE), command=self.clear_form
        ).pack(fill="x", padx=25, pady=20)

    def _create_labeled_input(self, parent, label_text, variable):
        """Helper for creating uniform label/entry pairs."""
        ctk.CTkLabel(parent, text=label_text, font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25)
        ctk.CTkEntry(
            parent, 
            textvariable=variable, 
            font=("Arial", FONT_SIZE_TABLE)
        ).pack(fill="x", padx=25, pady=(0, 15))

    # --- Logic & Event Methods ---

    def load_data(self):
        """Refresh the data table."""
        data = mock_get_technicians()
        for row in self.table.get_children():
            self.table.delete(row)
        for item in data:
            self.table.insert("", "end", values=item)

    def _on_row_select(self, event):
        """Populate the form fields when a row is selected."""
        selected = self.table.selection()
        if not selected:
            return
        values = self.table.item(selected[0])['values']
        self.var_name.set(values[1])
        self.var_spec.set(values[2])
        self.var_cert.set(values[3])
        self.var_status.set(values[4])

    def handle_add(self):
        """Add a new technician."""
        if self.var_name.get():
            mock_add_technician(
                self.var_name.get(), 
                self.var_spec.get(), 
                self.var_cert.get(), 
                self.var_status.get()
            )
            self.load_data()
            self.clear_form()

    def handle_delete(self):
        """Remove record with undo grace period."""
        selected = self.table.selection()
        if not selected:
            return
        
        row_id = selected[0]
        tech_id = self.table.item(row_id)['values'][0]
        tech_name = self.table.item(row_id)['values'][1]
        
        self.table.detach(row_id)
        
        def undo_action():
            self.table.reattach(row_id, "", "end")
        
        def final_delete():
            mock_delete_technician(tech_id)
        
        UndoToast(self, f"'{tech_name}' deleted", on_undo=undo_action, on_timeout=final_delete)

    def clear_form(self):
        """Reset the form fields."""
        self.var_name.set("")
        self.table.selection_remove(self.table.selection())