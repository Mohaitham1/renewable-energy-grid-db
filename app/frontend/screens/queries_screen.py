import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
from frontend.screens.table_style import apply_modern_treeview_style

# ==================================================
# REAL BACKEND INTEGRATION
# ==================================================
# Importing the exact functions from your provided backend/query_operations.py
from backend.query_operations import (
    query_manufacturer_most_below_avg,
    query_sites_with_no_inspection_last_month,
    query_technician_max_inspections_last_month,
    query_units_without_component_replacement_last_month,
    query_components_installed_last_month,
    query_technician_profile_and_units_inspected
)

# UI CONFIGURATION
FONT_SIZE_HEADER = 20
FONT_SIZE_LABEL = 13
FONT_SIZE_TABLE = 12

class QueriesScreen(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._init_variables()
        self._setup_ui()
        # Load the first query by default on startup
        self.run_query()

    def _init_variables(self):
        # Labels for the dropdown menu
        self.query_options = [
            "1. Manufacturer Efficiency Issues",
            "2. Sites Missing Last Month Inspections",
            "3. Top Performing Technician",
            "4. Units with No Replacements",
            "5. Last Month Component Installs",
            "6. Technician Productivity Profiles"
        ]
        self.var_query_type = tk.StringVar(value=self.query_options[0])
        self.current_data = [] # Stores last fetched data for PDF export

    def _setup_ui(self):
        self._create_table_section()
        self._create_sidebar_section()

    def _create_table_section(self):
        container = ctk.CTkFrame(self)
        container.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        # Header with Refresh Button
        header_frame = ctk.CTkFrame(container, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(header_frame, text="Database Analytics", font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        ctk.CTkButton(header_frame, text="🔄 Refresh", width=90, command=self.run_query).pack(side="right")

        apply_modern_treeview_style()
        self.table_container = container

    def _build_table(self, headers):
        """Rebuilds the table columns dynamically to match different query results."""
        if hasattr(self, 'table'):
            self.table.destroy()

        cols = [f"col{i}" for i in range(len(headers))]
        self.table = ttk.Treeview(self.table_container, columns=cols, show="headings")
        
        for col, text in zip(cols, headers):
            self.table.heading(col, text=text)
            self.table.column(col, anchor="center")
            
        self.table.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def run_query(self):
        """Executes the selected backend inquiry and updates the table."""
        selection = self.var_query_type.get()
        headers = []
        data_rows = []

        try:
            if "1." in selection:
                headers = ["Manufacturer", "Below Avg Efficiency Count"]
                res = query_manufacturer_most_below_avg() #
                data_rows = [(res['manufacturer'], res['below_average_count'])] if res else []

            elif "2." in selection:
                headers = ["Site ID", "Site Name"]
                res = query_sites_with_no_inspection_last_month() #
                data_rows = [(r['site_id'], r['site_name']) for r in res]

            elif "3." in selection:
                headers = ["Tech ID", "Technician Name", "Inspections (Last Month)"]
                res = query_technician_max_inspections_last_month() #
                data_rows = [(res['technician_id'], res['name'], res['inspection_count'])] if res else []

            elif "4." in selection:
                headers = ["Unit ID", "Unit Type", "Status"]
                res = query_units_without_component_replacement_last_month() #
                data_rows = [(r['unit_id'], r['unit_type'], r['status']) for r in res]

            elif "5." in selection:
                headers = ["Site Name", "Component", "Category", "Install Date"]
                res = query_components_installed_last_month() #
                data_rows = [(r['site_name'], r['component_name'], r['category'], r['replacement_date']) for r in res]

            elif "6." in selection:
                headers = ["Name", "Specialty", "Certification", "Status", "Units Inspected"]
                res = query_technician_profile_and_units_inspected() #
                data_rows = [(f"{r['first_name']} {r['last_name']}", r['specialty'], r['certification'], r['status'], r['total_units_inspected']) for r in res]

            self._build_table(headers)
            self.current_data = data_rows
            for row in data_rows:
                self.table.insert("", "end", values=row)
                
        except Exception as e:
            messagebox.showerror("SQL Query Error", f"Failed to retrieve data: {e}")

    def export_pdf(self):
        """Exports the current table data to a PDF file."""
        if not self.current_data:
            messagebox.showwarning("No Data", "Please run a query before exporting.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"Report_{self.var_query_type.get()[:5].replace('.', '')}"
        )
        if not file_path: return

        try:
            from fpdf import FPDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt=f"Analytics Report: {self.var_query_type.get()}", ln=True, align='C')
            pdf.ln(10)
            
            pdf.set_font("Arial", size=10)
            for row in self.current_data:
                line = " | ".join(map(str, row))
                pdf.cell(0, 10, txt=line, ln=True)
            
            pdf.output(file_path)
            messagebox.showinfo("Success", "Report exported successfully!")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not create PDF: {e}")

    def _create_sidebar_section(self):
        sidebar = ctk.CTkFrame(self, width=320)
        sidebar.grid(row=0, column=1, sticky="nsew")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(sidebar, text="Report Center", font=ctk.CTkFont(size=FONT_SIZE_HEADER, weight="bold")).pack(pady=25)

        ctk.CTkLabel(sidebar, text="Select Inquiry:", font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25)
        self.query_menu = ctk.CTkOptionMenu(
            sidebar, 
            values=self.query_options,
            variable=self.var_query_type,
            command=lambda _: self.run_query()
        )
        self.query_menu.pack(fill="x", padx=25, pady=(0, 20))

        ctk.CTkButton(sidebar, text="Generate Report", fg_color="#1f538d", font=("Arial", 12, "bold"), 
                      command=self.run_query).pack(fill="x", padx=25, pady=10)
        
        ctk.CTkButton(sidebar, text="Save as PDF", fg_color="#28a745", font=("Arial", 12, "bold"), 
                      command=self.export_pdf).pack(fill="x", padx=25, pady=5)
        
        ctk.CTkLabel(sidebar, text="────────────────", text_color="gray").pack(pady=10)
        
        ctk.CTkButton(sidebar, text="Archive Snapshot", fg_color="#E67E22", font=("Arial", 12, "bold"),
                      command=lambda: messagebox.showinfo("Archive", "Report snapshot moved to Archive.")).pack(fill="x", padx=25, pady=5)