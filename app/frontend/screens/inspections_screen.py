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
inspections_data = [
    (501, 101, "Ahmed Ali", "2026-05-01", "Pass"),
    (502, 201, "Mona Hassan", "2026-05-03", "Pass"),
    (503, 102, "Ahmed Ali", "2026-05-05", "Fault Detected"),
    (504, 301, "Sami Yassin", "2026-05-07", "Pending")
]

def mock_get_inspections():
    return inspections_data

def mock_add_inspection(unit_id, tech_name, date, result):
    global inspections_data
    new_id = max([i[0] for i in inspections_data]) + 1 if inspections_data else 501
    inspections_data.append((new_id, unit_id, tech_name, date, result))
    return True

def mock_delete_inspection(insp_id):
    global inspections_data
    inspections_data = [i for i in inspections_data if i[0] != insp_id]
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
# INSPECTIONS SCREEN COMPONENT
# ==================================================
class InspectionsScreen(ctk.CTkFrame):
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
        self.var_unit = tk.StringVar()
        self.var_tech = tk.StringVar()
        self.var_date = tk.StringVar(value="2026-05-08")
        self.var_result = tk.StringVar(value="Pass")

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
            placeholder_text="Search inspections...",
            font=("Arial", FONT_SIZE_TABLE)
        )
        self.ent_search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.ent_search.bind("<Return>", self._on_search)

        ctk.CTkButton(search_frame, text="Search", width=100, command=self._on_search).pack(side="right")

        apply_modern_treeview_style()

        cols = ("id", "unit", "tech", "date", "result")
        self.table = ttk.Treeview(container, columns=cols, show="headings")
        for col, text in zip(cols, ["Insp ID", "Unit ID", "Technician", "Date", "Result"]):
            self.table.heading(col, text=text)
            self.table.column(col, anchor="center")
        self.table.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.table.bind("<<TreeviewSelect>>", self._on_row_select)

    def _on_search(self, event=None):
        self.load_data(self.search_var.get())

    def load_data(self, query=""):
        query = query.lower().strip()
        rows = mock_get_inspections()
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
        form_frame = ctk.CTkFrame(self, width=320)
        form_frame.grid(row=0, column=1, sticky="nsew")
        form_frame.grid_propagate(False)

        ctk.CTkLabel(form_frame, text="Log Inspection", font=ctk.CTkFont(size=FONT_SIZE_HEADER, weight="bold")).pack(pady=25)

        self._create_input(form_frame, "Unit ID:", self.var_unit)
        self._create_input(form_frame, "Technician Name:", self.var_tech)
        self._create_input(form_frame, "Date (YYYY-MM-DD):", self.var_date)
        
        ctk.CTkLabel(form_frame, text="Result:", font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25)
        ctk.CTkOptionMenu(
            form_frame, 
            values=["Pass", "Fail", "Fault Detected", "Requires Parts", "Pending"], 
            variable=self.var_result,
            font=("Arial", FONT_SIZE_TABLE)
        ).pack(fill="x", padx=25, pady=(0, 15))

        ctk.CTkButton(
            form_frame, text="Save Inspection", fg_color="#28a745", 
            font=("Arial", FONT_SIZE_TABLE, "bold"), command=self.handle_add
        ).pack(fill="x", padx=25, pady=10)
        
        ctk.CTkButton(
            form_frame, text="Delete Record", fg_color="#dc3545", 
            font=("Arial", FONT_SIZE_TABLE, "bold"), command=self.handle_delete
        ).pack(fill="x", padx=25, pady=5)
        
        ctk.CTkButton(
            form_frame, text="Clear Form", fg_color="transparent", 
            border_width=1, font=("Arial", FONT_SIZE_TABLE), command=self.clear_form
        ).pack(fill="x", padx=25, pady=20)

    def _create_input(self, parent, label, var):
        ctk.CTkLabel(parent, text=label, font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25)
        ctk.CTkEntry(parent, textvariable=var, font=("Arial", FONT_SIZE_TABLE)).pack(fill="x", padx=25, pady=(0, 15))

    def load_data(self):
        data = mock_get_inspections()
        for row in self.table.get_children(): 
            self.table.delete(row)
        for item in data: 
            self.table.insert("", "end", values=item)

    def _on_row_select(self, event):
        selected = self.table.selection()
        if not selected: 
            return
        v = self.table.item(selected[0])['values']
        self.var_unit.set(v[1]); self.var_tech.set(v[2]); self.var_date.set(v[3]); self.var_result.set(v[4])

    def handle_add(self):
        if self.var_unit.get() and self.var_tech.get():
            mock_add_inspection(self.var_unit.get(), self.var_tech.get(), self.var_date.get(), self.var_result.get())
            self.load_data(); self.clear_form()

    def handle_delete(self):
        selected = self.table.selection()
        if not selected:
            return
        
        row_id = selected[0]
        insp_id = self.table.item(row_id)['values'][0]
        insp_label = f"Inspection {insp_id}"
        
        self.table.detach(row_id)
        
        def undo_action():
            self.table.reattach(row_id, "", "end")
        
        def final_delete():
            mock_delete_inspection(insp_id)
        
        UndoToast(self, f"'{insp_label}' deleted", on_undo=undo_action, on_timeout=final_delete)

    def clear_form(self):
        self.var_unit.set(""); self.var_tech.set(""); self.var_date.set("2026-05-08")
        self.table.selection_remove(self.table.selection())