import customtkinter as ctk
import tkinter as tk

# ==================================================
# REAL BACKEND INTEGRATION
# =================)
# ==================================================
from backend.site_operations import get_all_sites, add_site
from backend.unit_operations import get_all_units, add_unit
from backend.technician_operations import get_all_technicians, add_technician
from backend.query_operations import run_all_queries # For advanced stats later

def get_dashboard_stats():
    """Fetches real aggregated data from the SQL Server backend."""
    try:
        sites = get_all_sites()
        units = get_all_units()
        techs = get_all_technicians()
        
        return {
            "total_sites": len(sites),
            "active_units": len([u for u in units if u[3] == 'Active']), # Filter by status
            "technicians_on_call": len([t for t in techs if t[4] in ['Active', 'On-Site']]),
            "pending_inspections": 0  # To be linked when inspections_operations is finalized
        }
    except Exception as e:
        print(f"DATABASE ERROR: {e}")
        return {"total_sites": 0, "active_units": 0, "technicians_on_call": 0, "pending_inspections": 0}

def get_recent_alerts():
    """Dynamically generates alerts based on unit maintenance status."""
    try:
        units = get_all_units()
        # Generate alerts for any units currently in 'Maintenance' or 'Offline'
        alerts = []
        for u in units:
            if u[3] in ['Maintenance', 'Offline']:
                alerts.append((u[3], f"{u[2]} at {u[1]}", "Now"))
        return alerts[:3] if alerts else [("All Clear", "No critical issues", "Today")]
    except:
        return [("Connection Error", "Check DB settings", "Now")]

# ==================================================
# QUICK MANAGEMENT DISPATCHER
# ==================================================

def real_add_entry(name, category):
    """Dispatches 'Quick Add' requests to the correct backend file."""
    if category == "Site":
        # real add_site requires (name, energy_type, location, capacity)
        return add_site(name, "Solar", "TBD", "0 MW")
    elif category == "Unit":
        # real add_unit requires (site_name, unit_type, status, output)
        # Note: This assumes 'General' is a valid unit type and uses placeholder site
        return add_unit("Sahara Solar", "General", "Active", "0")
    elif category == "Technician":
        # real add_technician requires (full_name, specialty, certification, status)
        return add_technician(name, "Generalist", "Junior", "Active")
    return False

# ==================================================
# SCREEN IMPORTS & DYNAMIC DASHBOARD
# ==================================================
from frontend.screens.sites_screen import SitesScreen
from frontend.screens.units_screen import UnitsScreen
from frontend.screens.technicians_screen import TechniciansScreen
from frontend.screens.inspections_screen import InspectionsScreen
from frontend.screens.components_screen import ComponentsScreen
from frontend.screens.queries_screen import QueriesScreen
from frontend.screens.archive_screen import ArchiveScreen

class DashboardScreen(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._setup_header()
        self._setup_activity_feed()
        self._setup_management_panel()
        self._refresh_dashboard_data()

    def _setup_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        ctk.CTkLabel(header, text="Control Dashboard", font=ctk.CTkFont(size=28, weight="bold")).pack(side="left")

    def _setup_activity_feed(self):
        container = ctk.CTkFrame(self)
        container.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(container, text="System Live Feed", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        self.activity_list = ctk.CTkTextbox(container, state="disabled", fg_color="transparent")
        self.activity_list.pack(fill="both", expand=True, padx=10, pady=10)

    def _setup_management_panel(self):
        panel = ctk.CTkFrame(self, width=300)
        panel.grid(row=1, column=1, sticky="nsew")
        panel.grid_propagate(False)
        ctk.CTkLabel(panel, text="Quick Management", font=ctk.CTkFont(weight="bold")).pack(pady=15)

        ctk.CTkLabel(panel, text="Entity Name:").pack(anchor="w", padx=20)
        self.ent_name = ctk.CTkEntry(panel, placeholder_text="e.g. Solar Array 5")
        self.ent_name.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(panel, text="Category:").pack(anchor="w", padx=20)
        self.opt_category = ctk.CTkOptionMenu(panel, values=["Site", "Unit", "Technician"])
        self.opt_category.pack(fill="x", padx=20, pady=(0, 20))

        self.btn_add = ctk.CTkButton(panel, text="Add Record", fg_color="#28a745", command=self.handle_add)
        self.btn_add.pack(fill="x", padx=20, pady=5)
        
        self.lbl_status = ctk.CTkLabel(panel, text="", text_color="gray")
        self.lbl_status.pack(pady=20)

    def _refresh_dashboard_data(self):
        stats = get_dashboard_stats()
        self._log_activity(f"Real Data Synced: {stats['total_sites']} Sites found in DB.")
        alerts = get_recent_alerts()
        for alert in alerts:
            self._log_activity(f"ALERT [{alert[0]}]: {alert[1]}")

    def _log_activity(self, message):
        self.activity_list.configure(state="normal")
        self.activity_list.insert("end", f"• {message}\n")
        self.activity_list.configure(state="disabled")
        self.activity_list.see("end")

    def handle_add(self):
        name = self.ent_name.get()
        category = self.opt_category.get()
        if not name:
            self.lbl_status.configure(text="Error: Name is required", text_color="#dc3545")
            return

        if real_add_entry(name, category):
            self._log_activity(f"Added {category}: {name}")
            self.ent_name.delete(0, 'end')
            self.lbl_status.configure(text="Success: Entry Added", text_color="#28a745")
        else:
            self.lbl_status.configure(text="Failed to write to DB", text_color="#dc3545")

# ==================================================
# MAIN APPLICATION WINDOW
# ==================================================

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Renewable Energy Grid & Maintenance Network")
        self.geometry("1400x800")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.active_button = None
        self._build_layout()

    def _build_layout(self):
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)

        self.main_view = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_view.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)

        ctk.CTkLabel(self.sidebar, text="GRID SYSTEM", font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, pady=(40, 30))

        menu = [
            ("🏠  Dashboard", DashboardScreen),
            ("🌍  Energy Sites", SitesScreen),
            ("⚙️  Power Units", UnitsScreen),
            ("👷  Technicians", TechniciansScreen),
            ("🔍  Inspections", InspectionsScreen),
            ("🔧  Component Replacements", ComponentsScreen),
            ("📊  Reports & Queries", QueriesScreen),
            ("📦  Archive", ArchiveScreen)
        ]

        self.nav_widgets = {}
        for i, (name, cls) in enumerate(menu):
            btn = ctk.CTkButton(self.sidebar, text=name, height=50, fg_color="transparent", anchor="w",
                                font=ctk.CTkFont(size=16), command=lambda c=cls, n=name: self.show_screen(c, n))
            btn.grid(row=i+1, column=0, padx=15, pady=4, sticky="ew")
            self.nav_widgets[name] = btn

        self.show_screen(DashboardScreen, "🏠  Dashboard")

    def show_screen(self, screen_class, name):
        if self.active_button:
            self.nav_widgets[self.active_button].configure(fg_color="transparent", height=50)
        self.nav_widgets[name].configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"], height=55)
        self.active_button = name

        for child in self.main_view.winfo_children():
            child.destroy()
            
        instance = screen_class(self.main_view)
        instance.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()