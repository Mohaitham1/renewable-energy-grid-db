import customtkinter as ctk
import tkinter as tk
# ==================================================
# MOCK BACKEND FUNCTIONS
# Isolated for easy replacement with real database calls
# ==================================================

def get_dashboard_stats():
    """Simulates fetching aggregated data from SQL Server."""
    return {
        "total_sites": 12,
        "active_units": 48,
        "technicians_on_call": 15,
        "pending_inspections": 7
    }

def get_recent_alerts():
    """Simulates fetching system alerts."""
    return [
        ("High Temp", "Unit 04 - Site A", "10:15 AM"),
        ("Maintenance Due", "Unit 12 - Site C", "09:30 AM"),
        ("Offline", "Unit 09 - Site B", "Yesterday")
    ]


# ==================================================
# MOCK BACKEND SERVICE
# Isolated logic to be replaced by actual database operations later.
# ==================================================

def mock_add_entry(name, category):
    """Simulates adding a new record to the database."""
    print(f"BACKEND: Successfully added {name} to {category}.")
    return True

def mock_delete_entry(entry_id):
    """Simulates deleting a record from the database."""
    print(f"BACKEND: Successfully deleted ID {entry_id}.")
    return True

# ==================================================
# SCREEN IMPORTS
# ==================================================

from frontend.screens.sites_screen import SitesScreen
from frontend.screens.units_screen import UnitsScreen
from frontend.screens.technicians_screen import TechniciansScreen
from frontend.screens.inspections_screen import InspectionsScreen
from frontend.screens.components_screen import ComponentsScreen
from frontend.screens.queries_screen import QueriesScreen
from frontend.screens.archive_screen import ArchiveScreen

# ==================================================
# DYNAMIC DASHBOARD SCREEN
# Includes Management Panel for Add/Delete functionality demonstration.
# ==================================================

class DashboardScreen(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._setup_header()
        self._setup_activity_feed()
        self._setup_management_panel()

    def _setup_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        ctk.CTkLabel(
            header, 
            text="Control Dashboard", 
            font=ctk.CTkFont(size=28, weight="bold")
        ).pack(side="left")

    def _setup_activity_feed(self):
        """Displays a scrollable list of system activities."""
        container = ctk.CTkFrame(self)
        container.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(container, text="Recent Activity", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        
        self.activity_list = ctk.CTkTextbox(container, state="disabled", fg_color="transparent")
        self.activity_list.pack(fill="both", expand=True, padx=10, pady=10)
        self._log_activity("System initialized.")
        self._log_activity("Connected to Renewable Network.")

    def _setup_management_panel(self):
        """Quick Actions Panel with Add/Delete inputs."""
        panel = ctk.CTkFrame(self, width=300)
        panel.grid(row=1, column=1, sticky="nsew")
        panel.grid_propagate(False)
        
        ctk.CTkLabel(panel, text="Quick Management", font=ctk.CTkFont(weight="bold")).pack(pady=15)

        # Form Fields
        ctk.CTkLabel(panel, text="Entity Name:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20)
        self.ent_name = ctk.CTkEntry(panel, placeholder_text="e.g. Solar Array 5")
        self.ent_name.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(panel, text="Category:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20)
        self.opt_category = ctk.CTkOptionMenu(panel, values=["Site", "Unit", "Technician"])
        self.opt_category.pack(fill="x", padx=20, pady=(0, 20))

        # Action Buttons
        self.btn_add = ctk.CTkButton(
            panel, 
            text="Add Record", 
            fg_color="#28a745", 
            hover_color="#218838",
            command=self.handle_add
        )
        self.btn_add.pack(fill="x", padx=20, pady=5)

        self.btn_delete = ctk.CTkButton(
            panel, 
            text="Delete Last", 
            fg_color="#dc3545", 
            hover_color="#c82333",
            command=self.handle_delete
        )
        self.btn_delete.pack(fill="x", padx=20, pady=5)

        self.lbl_status = ctk.CTkLabel(panel, text="", text_color="gray")
        self.lbl_status.pack(pady=20)

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

        try:
            if mock_add_entry(name, category):
                self._log_activity(f"Added {category}: {name}")
                self.ent_name.delete(0, 'end')
                self.lbl_status.configure(text="Success: Entry Added", text_color="#28a745")
        except Exception as e:
            self.lbl_status.configure(text=f"System Error: {e}", text_color="#dc3545")

    def handle_delete(self):
        # Implementation of deletion logic
        try:
            if mock_delete_entry("LATEST_ID"):
                self._log_activity("Deleted most recent entry.")
                self.lbl_status.configure(text="Success: Entry Removed", text_color="#28a745")
        except Exception as e:
            self.lbl_status.configure(text="Delete Failed", text_color="#dc3545")

# ==================================================
# MAIN APPLICATION
# ==================================================

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Renewable Energy Grid & Maintenance Network")
        self.geometry("1400x800")
        self.minsize(1200, 700)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.active_button = None
        self._build_layout()

    def _build_layout(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)

        # Content Wrapper
        self.main_view = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_view.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)

        # Navigation Header
        ctk.CTkLabel(
            self.sidebar, 
            text="GRID SYSTEM", 
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, pady=(40, 30))

        # Dynamic Menu Items
        menu = [
            (" 🏠  Dashboard", DashboardScreen), # Added this line
            (" 🌍  Energy Sites", SitesScreen),
            (" ⚙️  Power Units", UnitsScreen),
            (" 👷  Technicians", TechniciansScreen),
            (" 🔍  Inspections", InspectionsScreen),
            (" 🔧  Component Replacements", ComponentsScreen),
            (" 📊  Reports & Queries", QueriesScreen),
            (" 📦  Archive", ArchiveScreen) 
        ]

        self.nav_widgets = {}
        for i, (name, cls) in enumerate(menu):
            btn = ctk.CTkButton(
                self.sidebar, 
                text=name, 
                height=50, 
                fg_color="transparent", 
                anchor="w",
                corner_radius=8,
                font=ctk.CTkFont(size=16),
                command=lambda c=cls, n=name: self.show_screen(c, n)
            )
            btn.grid(row=i+1, column=0, padx=15, pady=4, sticky="ew")
            self.nav_widgets[name] = btn

        # Bottom Identity
        self.sidebar.grid_rowconfigure(len(menu)+1, weight=1)
        ctk.CTkLabel(
            self.sidebar, 
            text="Cairo University\nFCAI - 2026", 
            font=ctk.CTkFont(size=11), 
            text_color="gray"
        ).grid(row=len(menu)+2, column=0, pady=20)

        # Start with the first menu item selected
        first_name, first_cls = menu[0] 
        self.show_screen(first_cls, first_name)

    def show_screen(self, screen_class, name):
        """Dynamic content switching with button highlighting."""
        # Highlight active nav item
        if self.active_button:
            self.nav_widgets[self.active_button].configure(fg_color="transparent", height=50, font=ctk.CTkFont(size=16))
        
        self.nav_widgets[name].configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"], height=55, font=ctk.CTkFont(size=18))
        self.active_button = name

        # Swap Frame
        for child in self.main_view.winfo_children():
            child.destroy()
            
        instance = screen_class(self.main_view)
        instance.pack(fill="both", expand=True)

# if __name__ == "__main__":
#     ctk.set_appearance_mode("dark")
#     ctk.set_default_color_theme("dark-blue")
    
#     app = MainWindow()
#     app.mainloop()