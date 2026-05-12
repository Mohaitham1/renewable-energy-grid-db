import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from frontend.screens.table_style import apply_modern_treeview_style

# ==================================================
# REAL BACKEND INTEGRATION
# ==================================================
from backend.inspection_operations import get_all_inspections, add_inspection, delete_inspection
from backend.unit_operations import get_all_units
from backend.technician_operations import get_all_technicians

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
        self.bind("<Destroy>", self._flush_pending_deletes)

    def _init_variables(self):
        self.search_var = tk.StringVar()
        self.var_unit = tk.StringVar()  # holds a display label resolvable to a unit_id
        self.var_tech = tk.StringVar()  # holds a display label resolvable to a tech_id
        self.var_date = tk.StringVar(value="2026-05-10")
        self.var_result = tk.StringVar(value="Pass")
        # Maps for the Power Unit dropdown: display label <-> unit_id.
        self._unit_display_to_id = {}
        self._unit_id_to_display = {}
        # Same pattern for technicians — eliminates first/last-name string matching.
        self._tech_display_to_id = {}
        self._tech_id_to_display = {}
        # Pending undo-toast deletions that must be committed if the user
        # switches tabs before the 5s timer fires (the screen frame, and the
        # toast's `after` callback, are destroyed on navigation).
        self._pending_deletes = []

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
            placeholder_text="Search inspections...",
            font=("Arial", FONT_SIZE_TABLE)
        )
        self.ent_search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.ent_search.bind("<Return>", lambda e: self.load_data(self.search_var.get()))

        ctk.CTkButton(search_frame, text="Search", width=100, 
                      command=lambda: self.load_data(self.search_var.get())).pack(side="right")

        apply_modern_treeview_style()

        cols = ("id", "unit", "tech", "date", "result")
        self.table = ttk.Treeview(container, columns=cols, show="headings")
        headers = ["Insp ID", "Unit ID", "Technician", "Date", "Result"]
        for col, text in zip(cols, headers):
            self.table.heading(col, text=text)
            self.table.column(col, anchor="center")
            
        self.table.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.table.bind("<<TreeviewSelect>>", self._on_row_select)

    def load_data(self, query=""):
        query = query.lower().strip()
        try:
            # REAL DATABASE CALL
            rows = get_all_inspections()
            
            if query:
                rows = [r for r in rows if query in " ".join(map(str, r)).lower()]
            
            for row_id in self.table.get_children():
                self.table.delete(row_id)
            for item in rows:
                self.table.insert("", "end", values=item)
        except Exception as e:
            print(f"Error loading inspections: {e}")

    def _on_row_select(self, event):
        selected = self.table.selection()
        if not selected: return
        v = self.table.item(selected[0])['values']
        # v = (unit_inspection_id, unit_id, technician_name, date, status)
        unit_id_str = str(v[1])
        self.var_unit.set(self._unit_id_to_display.get(unit_id_str, unit_id_str))
        # We only have the joined "First Last" name in the table; look up by
        # name to find the id-bearing display label. If no match, fall back to
        # the raw name (backend resolver will still handle it).
        tech_name = (v[2] or "").strip()
        matching = next(
            (display for display, tid in self._tech_display_to_id.items()
             if display.endswith(tech_name)),
            tech_name,
        )
        self.var_tech.set(matching)
        self.var_date.set(v[3]); self.var_result.set(v[4])

    def handle_add(self):
        unit_label = self.var_unit.get().strip()
        tech_label = self.var_tech.get().strip()
        date = self.var_date.get().strip()
        result = self.var_result.get().strip()

        unit_id = self._unit_display_to_id.get(unit_label)
        if unit_id is None:
            try:
                unit_id = int(unit_label)
            except (TypeError, ValueError):
                unit_id = None

        tech_id = self._tech_display_to_id.get(tech_label)
        if tech_id is None:
            # Allow a user who pasted a raw int or a "First Last" name.
            try:
                tech_id = int(tech_label)
            except (TypeError, ValueError):
                tech_id = None

        if not unit_id or (tech_id is None and not tech_label):
            messagebox.showwarning(
                "Input Error",
                "Please pick a Power Unit and a Technician before saving.",
            )
            return

        # If we have a tech_id, send the int (zero-ambiguity path). Otherwise
        # let the backend resolver fall back to name matching with LTRIM/RTRIM.
        tech_arg = tech_id if tech_id is not None else tech_label

        try:
            # REAL DATABASE CALL
            if add_inspection(unit_id, tech_arg, date, result):
                self.load_data()
                self.clear_form()
                messagebox.showinfo("Success", "Inspection logged successfully.")
            else:
                messagebox.showerror("Error", "Could not log inspection. Verify Unit and Technician exist.")
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def handle_delete(self):
        selected = self.table.selection()
        if not selected: return

        row_id = selected[0]
        insp_id = self.table.item(row_id)['values'][0]

        self.table.detach(row_id)

        entry = {"state": "live"}

        def commit(quiet=False):
            if entry["state"] != "live":
                return
            entry["state"] = "committed"
            try:
                delete_inspection(insp_id)
            except Exception as e:
                entry["state"] = "failed"
                if quiet:
                    print(f"Delete inspection {insp_id} failed during flush: {e}")
                    return
                try:
                    self.table.reattach(row_id, "", "end")
                except Exception:
                    self.load_data()
                messagebox.showerror(
                    "Delete Failed",
                    f"Could not delete inspection {insp_id}.\n\n{e}",
                )

        def undo_action():
            entry["state"] = "cancelled"
            self.table.reattach(row_id, "", "end")

        entry["flush"] = lambda: commit(quiet=True)
        self._pending_deletes.append(entry)

        UndoToast(self, f"Inspection {insp_id} deleted", on_undo=undo_action, on_timeout=commit)

    def _flush_pending_deletes(self, event=None):
        # <Destroy> bubbles for every descendant — only flush when the screen
        # frame itself is being torn down (e.g., tab switch).
        if event is not None and getattr(event, "widget", None) is not self:
            return
        for entry in self._pending_deletes:
            entry["flush"]()
        self._pending_deletes.clear()

    def clear_form(self):
        self.var_unit.set(""); self.var_tech.set(""); self.var_date.set("2026-05-10")
        self.table.selection_remove(self.table.selection())

    def _build_unit_options(self):
        """Populate the unit dropdown maps and return its display values."""
        self._unit_display_to_id.clear()
        self._unit_id_to_display.clear()
        try:
            units = get_all_units()  # (unit_id, site_name, unit_type, status, max_kwatt_output)
        except Exception as e:
            print(f"Loading units for Inspections dropdown failed: {e}")
            units = []
        displays = []
        for unit_id, site_name, unit_type, *_ in units:
            display = f"#{unit_id} - {unit_type} @ {site_name}"
            self._unit_display_to_id[display] = unit_id
            self._unit_id_to_display[str(unit_id)] = display
            displays.append(display)
        return displays or ["No Units Available"]

    def _build_technician_options(self):
        """Same idea as _build_unit_options, but for technicians. The display
        label includes the int id so handle_add can resolve without any string
        comparison against first/last name."""
        self._tech_display_to_id.clear()
        self._tech_id_to_display.clear()
        try:
            techs = get_all_technicians()  # (technician_id, full_name, email, phone, hire_date, status)
        except Exception as e:
            print(f"Loading technicians for Inspections dropdown failed: {e}")
            techs = []
        displays = []
        for tech_id, full_name, *_ in techs:
            display = f"#{tech_id} - {(full_name or '').strip()}"
            self._tech_display_to_id[display] = tech_id
            self._tech_id_to_display[str(tech_id)] = display
            displays.append(display)
        return displays or ["No Technicians Available"]

    def _create_form_section(self):
        form_frame = ctk.CTkFrame(self, width=320)
        form_frame.grid(row=0, column=1, sticky="nsew")
        form_frame.grid_propagate(False)

        ctk.CTkLabel(form_frame, text="Log Inspection", font=ctk.CTkFont(size=FONT_SIZE_HEADER, weight="bold")).pack(pady=25)

        # Fields matching the uploaded screenshot
        ctk.CTkLabel(form_frame, text="Power Unit:", font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25)
        unit_displays = self._build_unit_options()
        ctk.CTkOptionMenu(form_frame, values=unit_displays, variable=self.var_unit).pack(fill="x", padx=25, pady=(0, 15))

        ctk.CTkLabel(form_frame, text="Technician:", font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25)
        tech_displays = self._build_technician_options()
        ctk.CTkOptionMenu(form_frame, values=tech_displays, variable=self.var_tech).pack(fill="x", padx=25, pady=(0, 15))

        self._create_input(form_frame, "Date (YYYY-MM-DD):", self.var_date)
        
        ctk.CTkLabel(form_frame, text="Result:", font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25)
        ctk.CTkOptionMenu(form_frame, values=["Pass", "Fail", "Fault Detected", "Requires Parts", "Pending"], 
                          variable=self.var_result).pack(fill="x", padx=25, pady=(0, 15))

        ctk.CTkButton(form_frame, text="Save Inspection", fg_color="#28a745", font=("Arial", 12, "bold"), 
                      command=self.handle_add).pack(fill="x", padx=25, pady=(10, 5))

        ctk.CTkButton(form_frame, text="Delete Record", fg_color="#dc3545", font=("Arial", 12, "bold"), 
                      command=self.handle_delete).pack(fill="x", padx=25, pady=5)

        ctk.CTkButton(form_frame, text="Clear Form", fg_color="transparent", border_width=1, 
                      command=self.clear_form).pack(fill="x", padx=25, pady=20)

    def _create_input(self, frame, label, var):
        ctk.CTkLabel(frame, text=label, font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25, pady=(10, 0))
        ctk.CTkEntry(frame, textvariable=var, font=("Arial", FONT_SIZE_TABLE)).pack(fill="x", padx=25, pady=(0, 15))