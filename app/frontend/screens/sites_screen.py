import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from frontend.screens.table_style import apply_modern_treeview_style

# ==================================================
# REAL BACKEND INTEGRATION
# ==================================================
from backend.site_operations import get_all_sites, add_site, delete_site #

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
        self.bind("<Destroy>", self._flush_pending_deletes)

    def _init_variables(self):
        self.search_var = tk.StringVar()
        # Mirrors Energy_Site columns one-for-one so handle_add can hand the
        # backend exactly what the schema needs.
        self.var_name = tk.StringVar()
        self.var_country = tk.StringVar()
        self.var_region = tk.StringVar()
        self.var_terrain = tk.StringVar(value="Desert")
        self.var_lat = tk.StringVar(value="0.0")
        self.var_lon = tk.StringVar(value="0.0")
        self.var_date = tk.StringVar()
        self.selected_site_id = None
        # get_all_sites returns 8 cols but the table only displays 6 — keep the
        # full row per iid so _on_row_select can populate every form field.
        self._row_data = {}
        # Pending undo-toast deletions that must be committed if the user
        # switches tabs before the 5s timer fires (the screen frame, and the
        # toast's `after` callback, are destroyed on navigation).
        self._pending_deletes = []

    TERRAIN_OPTIONS = ["Desert", "Coastal", "Mountain", "Plains", "Forest", "Urban", "Offshore"]

    # DECIMAL(12,6) holds |value| < 10^(12-6) = 1_000_000. Real-world lat/lon
    # ranges are much tighter; reject anything outside them so a typo can't
    # corrupt a row even within the column's capacity.
    LAT_MIN, LAT_MAX = -90.0, 90.0
    LON_MIN, LON_MAX = -180.0, 180.0

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
            placeholder_text="Search sites by name, type, or location...",
            font=("Arial", FONT_SIZE_TABLE)
        )
        self.ent_search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.ent_search.bind("<Return>", self._on_search)

        ctk.CTkButton(search_frame, text="Search", width=100, command=self._on_search).pack(side="right")

        apply_modern_treeview_style()

        cols = ("id", "name", "country", "region", "terrain", "established")
        self.table = ttk.Treeview(container, columns=cols, show="headings")
        headers = ["ID", "Site Name", "Country", "Region", "Terrain", "Established"]
        widths = [60, 200, 130, 140, 120, 110]
        for col, text, w in zip(cols, headers, widths):
            self.table.heading(col, text=text)
            self.table.column(col, anchor="center", width=w)
        self.table.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.table.bind("<<TreeviewSelect>>", self._on_row_select)

    def _on_search(self, event=None):
        self.load_data(self.search_var.get())

    def load_data(self, query=""):
        query = query.lower().strip()
        try:
            # REAL DATABASE CALL — row = (site_id, site_name, latitude, longitude,
            # terrain_type, region, country, established_date)
            rows = get_all_sites()

            if query:
                rows = [row for row in rows if query in " ".join(map(str, row)).lower()]

            self._row_data.clear()
            for row_id in self.table.get_children():
                self.table.delete(row_id)
            for item in rows:
                display = (
                    item[0],            # id
                    item[1],            # site_name
                    item[6] or "",      # country
                    item[5] or "",      # region
                    item[4] or "",      # terrain
                    str(item[7]) if item[7] is not None else "",
                )
                iid = self.table.insert("", "end", values=display)
                self._row_data[iid] = item
        except Exception as e:
            print(f"Error loading sites: {e}")

    def _on_row_select(self, event):
        selected = self.table.selection()
        if not selected:
            return
        full = self._row_data.get(selected[0])
        if not full:
            return
        self.selected_site_id = full[0]
        self.var_name.set(full[1] or "")
        self.var_lat.set("" if full[2] is None else str(full[2]))
        self.var_lon.set("" if full[3] is None else str(full[3]))
        terrain = full[4] or ""
        self.var_terrain.set(terrain if terrain in self.TERRAIN_OPTIONS else (terrain or "Desert"))
        self.var_region.set(full[5] or "")
        self.var_country.set(full[6] or "")
        self.var_date.set("" if full[7] is None else str(full[7]))

    def handle_add(self):
        name = self.var_name.get().strip()
        country = self.var_country.get().strip()
        region = self.var_region.get().strip() or None
        terrain = self.var_terrain.get().strip()
        date = self.var_date.get().strip() or None

        if not name or not country or not terrain:
            messagebox.showwarning(
                "Input Error",
                "Site Name, Country, and Terrain Type are required.",
            )
            return

        try:
            lat = float(self.var_lat.get().strip() or "0")
            lon = float(self.var_lon.get().strip() or "0")
        except ValueError:
            messagebox.showwarning(
                "Input Error", "Latitude and Longitude must be numbers."
            )
            return

        if not (self.LAT_MIN <= lat <= self.LAT_MAX):
            messagebox.showwarning(
                "Input Error",
                f"Latitude must be between {self.LAT_MIN} and {self.LAT_MAX}.",
            )
            return
        if not (self.LON_MIN <= lon <= self.LON_MAX):
            messagebox.showwarning(
                "Input Error",
                f"Longitude must be between {self.LON_MIN} and {self.LON_MAX}.",
            )
            return

        try:
            # REAL DATABASE CALL
            if add_site(name, lat, lon, terrain, region, country, date):
                self.load_data()
                self.clear_form()
                messagebox.showinfo("Success", f"Site '{name}' added successfully.")
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not add site: {e}")

    def handle_delete(self):
        selected = self.table.selection()
        if not selected: return

        row_id = selected[0]
        site_id = self.table.item(row_id)['values'][0]
        site_name = self.table.item(row_id)['values'][1]

        self.table.detach(row_id)

        entry = {"state": "live"}

        def commit(quiet=False):
            if entry["state"] != "live":
                return
            entry["state"] = "committed"
            try:
                delete_site(site_id)
            except Exception as e:
                entry["state"] = "failed"
                if quiet:
                    print(f"Delete site {site_id} failed during flush: {e}")
                    return
                try:
                    self.table.reattach(row_id, "", "end")
                except Exception:
                    self.load_data()
                messagebox.showerror(
                    "Delete Failed",
                    f"Could not delete site '{site_name}'.\n\n{e}",
                )

        def undo_action():
            entry["state"] = "cancelled"
            self.table.reattach(row_id, "", "end")

        entry["flush"] = lambda: commit(quiet=True)
        self._pending_deletes.append(entry)

        UndoToast(self, f"'{site_name}' deleted", on_undo=undo_action, on_timeout=commit)

    def _flush_pending_deletes(self, event=None):
        if event is not None and getattr(event, "widget", None) is not self:
            return
        for entry in self._pending_deletes:
            entry["flush"]()
        self._pending_deletes.clear()

    def clear_form(self):
        self.selected_site_id = None
        self.var_name.set("")
        self.var_country.set("")
        self.var_region.set("")
        self.var_terrain.set("Desert")
        self.var_lat.set("0.0")
        self.var_lon.set("0.0")
        self.var_date.set("")
        self.table.selection_remove(self.table.selection())

    def _create_form_section(self):
        # Scrollable so every Energy_Site field stays reachable in the side panel.
        form_frame = ctk.CTkScrollableFrame(self, width=340, label_text="")
        form_frame.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(form_frame, text="Site Details", font=ctk.CTkFont(size=FONT_SIZE_HEADER, weight="bold")).pack(pady=(15, 12))

        self._create_input(form_frame, "Site Name:", self.var_name)
        self._create_input(form_frame, "Country:", self.var_country)
        self._create_input(form_frame, "Region (optional):", self.var_region)

        ctk.CTkLabel(form_frame, text="Terrain Type:", font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25, pady=(8, 0))
        ctk.CTkOptionMenu(form_frame, values=self.TERRAIN_OPTIONS, variable=self.var_terrain).pack(fill="x", padx=25, pady=(0, 12))

        self._create_input(form_frame, "Latitude:", self.var_lat)
        self._create_input(form_frame, "Longitude:", self.var_lon)
        self._create_input(form_frame, "Established Date (YYYY-MM-DD, optional):", self.var_date)

        ctk.CTkButton(form_frame, text="Add Site", fg_color="#28a745", font=("Arial", FONT_SIZE_TABLE, "bold"),
                      command=self.handle_add).pack(fill="x", padx=25, pady=(10, 5))

        ctk.CTkButton(form_frame, text="Delete Selected", fg_color="#dc3545", font=("Arial", FONT_SIZE_TABLE, "bold"),
                      command=self.handle_delete).pack(fill="x", padx=25, pady=5)

        ctk.CTkButton(form_frame, text="Clear Form", fg_color="transparent", border_width=1,
                      command=self.clear_form).pack(fill="x", padx=25, pady=(5, 20))

    def _create_input(self, frame, label, var):
        ctk.CTkLabel(frame, text=label, font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25, pady=(8, 0))
        ctk.CTkEntry(frame, textvariable=var, font=("Arial", FONT_SIZE_TABLE)).pack(fill="x", padx=25, pady=(0, 10))