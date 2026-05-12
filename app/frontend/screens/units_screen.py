import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from frontend.screens.table_style import (
    apply_modern_treeview_style,
    apply_row_tags,
    refresh_row_tags,
)

# ==================================================
# REAL BACKEND INTEGRATION
# ==================================================
from backend.unit_operations import (
    get_all_units,
    add_unit,
    delete_unit,
    update_unit,
    search_units,
)
from backend.site_operations import get_all_sites

FONT_SIZE_HEADER = 20
FONT_SIZE_LABEL = 13
FONT_SIZE_TABLE = 12

UNIT_TYPES = ["PV Panel", "Wind Turbine", "Inverter", "Battery", "Transformer", "Generator"]
UNIT_STATUSES = ["Operational", "Active", "Maintenance", "Offline", "Faulty"]

# max_kwatt_output is DECIMAL(18,2): max abs value is 10^(18-2) - 0.01 = 9.99...e15.
# That's far beyond anything physically meaningful; clamp the UI to a saner ceiling.
MAX_KW_OUTPUT = 10 ** 16  # exclusive upper bound matching DECIMAL(18,2) integer capacity


# ==================================================
# UNDO TOAST
# ==================================================
class UndoToast(ctk.CTkFrame):
    def __init__(self, parent, message, on_undo, on_timeout):
        super().__init__(
            parent, fg_color="#FFFFFF", border_color="#E0E0E0",
            border_width=1, corner_radius=10,
        )
        self.on_undo = on_undo
        self.on_timeout = on_timeout
        self.timer_seconds = 5

        ctk.CTkLabel(self, text=message, text_color="#333333",
                     font=("Arial", 13)).pack(side="left", padx=(20, 15), pady=10)
        ctk.CTkFrame(self, width=1, height=20, fg_color="#E0E0E0").pack(side="left", padx=5)
        ctk.CTkButton(self, text="Undo", fg_color="transparent", text_color="#1f538d",
                      hover_color="#F0F0F0", width=60, font=("Arial", 13, "bold"),
                      command=self.undo_clicked).pack(side="left", padx=10)
        ctk.CTkButton(self, text="X", fg_color="transparent", text_color="#999999",
                      hover_color="#F0F0F0", width=30, command=self.destroy).pack(
            side="left", padx=(0, 10))

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
# UNITS SCREEN
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
        self.bind("<Destroy>", self._flush_pending_deletes)

    def _init_variables(self):
        self.search_var = tk.StringVar()
        self.selected_unit_id = None
        # Pending undo-toast deletions that must be committed if the user
        # switches tabs before the 5s timer fires.
        self._pending_deletes = []

        # Backend `add_unit` expects:
        #   (site_name, unit_type, manufacturer, model, installation_date,
        #    max_kwatt_output, status, serial_number=None)
        self.var_site = tk.StringVar()
        self.var_type = tk.StringVar(value=UNIT_TYPES[0])
        self.var_manufacturer = tk.StringVar()
        self.var_model = tk.StringVar()
        self.var_install_date = tk.StringVar(value="2026-05-12")
        self.var_output = tk.StringVar(value="0")
        self.var_status = tk.StringVar(value="Operational")
        self.var_serial = tk.StringVar()

    def _setup_ui(self):
        self._create_table_section()
        self._create_form_section()

    # --------------------------------------------------
    # Left: table
    # --------------------------------------------------
    def _create_table_section(self):
        container = ctk.CTkFrame(self)
        container.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        search_frame = ctk.CTkFrame(container, fg_color="transparent")
        search_frame.pack(fill="x", padx=15, pady=15)

        self.ent_search = ctk.CTkEntry(
            search_frame, textvariable=self.search_var,
            placeholder_text="Search units by site, type, status, or manufacturer...",
            font=("Arial", FONT_SIZE_TABLE),
        )
        self.ent_search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.ent_search.bind("<Return>", self._on_search)
        self.ent_search.bind("<KeyRelease>", self._on_search)

        ctk.CTkButton(search_frame, text="Search", width=100,
                      command=self._on_search).pack(side="right")

        apply_modern_treeview_style()

        cols = ("id", "site", "type", "status", "output")
        self.table = ttk.Treeview(container, columns=cols, show="headings")
        headers = ["Unit ID", "Parent Site", "Unit Type", "Status", "Max kW Output"]
        widths = [70, 200, 160, 130, 140]
        for col, text, w in zip(cols, headers, widths):
            self.table.heading(col, text=text)
            self.table.column(col, anchor="center", width=w)
        self.table.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.table.bind("<<TreeviewSelect>>", self._on_row_select)
        apply_row_tags(self.table)

    def _on_search(self, event=None):
        self.load_data(self.search_var.get())

    def load_data(self, query=""):
        try:
            q = (query or "").strip()
            rows = search_units(q) if q else get_all_units()

            for row_id in self.table.get_children():
                self.table.delete(row_id)
            for item in rows:
                self.table.insert("", "end", values=item)
            refresh_row_tags(self.table)
        except Exception as e:
            print(f"Error loading units: {e}")

    def _on_row_select(self, event):
        selected = self.table.selection()
        if not selected:
            return
        v = self.table.item(selected[0])["values"]
        # v = (unit_id, site_name, unit_type, status, max_kwatt_output)
        self.selected_unit_id = v[0]
        self.var_site.set(v[1] if v[1] is not None else "")
        # Only force OptionMenu values that exist in the option list, else keep
        # the dropdown displaying its current value but place the raw DB value
        # into the variable so it round-trips correctly on save.
        self.var_type.set(v[2] if v[2] is not None else UNIT_TYPES[0])
        self.var_status.set(v[3] if v[3] in UNIT_STATUSES else "Operational")
        self.var_output.set(str(v[4]) if v[4] is not None else "0")
        # manufacturer/model/install_date/serial are not in the table view;
        # the user supplies/edits them in the form when updating.

    def handle_save(self):
        site = self.var_site.get().strip()
        u_type = self.var_type.get().strip()
        manufacturer = self.var_manufacturer.get().strip()
        model = self.var_model.get().strip() or None
        install_date = self.var_install_date.get().strip()
        output_raw = self.var_output.get().strip() or "0"
        status = self.var_status.get().strip() or "Operational"
        serial = self.var_serial.get().strip() or None

        if not site or not u_type or not manufacturer or not install_date:
            messagebox.showwarning(
                "Input Error",
                "Site, Unit Type, Manufacturer, and Installation Date are required.",
            )
            return

        try:
            output = float(output_raw)
        except ValueError:
            messagebox.showwarning("Input Error", "Max kW Output must be a number.")
            return

        if output < 0:
            messagebox.showwarning("Input Error", "Max kW Output cannot be negative.")
            return
        if output >= MAX_KW_OUTPUT:
            messagebox.showwarning(
                "Input Error",
                f"Max kW Output must be less than {MAX_KW_OUTPUT:,} to fit DECIMAL(18,2).",
            )
            return

        try:
            if self.selected_unit_id:
                ok = update_unit(
                    self.selected_unit_id, site, u_type, manufacturer, model,
                    install_date, output, status, serial,
                )
                msg = "Unit updated."
            else:
                ok = add_unit(
                    site, u_type, manufacturer, model, install_date, output, status, serial,
                )
                msg = f"Unit added to {site}."

            if ok:
                self.load_data()
                self.clear_form()
                messagebox.showinfo("Success", msg)
            else:
                messagebox.showerror("Error", "Could not save unit. Ensure the Site exists.")
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def handle_delete(self):
        selected = self.table.selection()
        if not selected:
            return

        row_id = selected[0]
        unit_id = self.table.item(row_id)["values"][0]
        unit_label = self.table.item(row_id)["values"][2]  # unit_type for the toast label

        self.table.detach(row_id)
        refresh_row_tags(self.table)

        entry = {"state": "live"}

        def commit(quiet=False):
            if entry["state"] != "live":
                return
            entry["state"] = "committed"
            try:
                delete_unit(unit_id)
            except Exception as e:
                entry["state"] = "failed"
                if quiet:
                    print(f"Delete unit {unit_id} failed during flush: {e}")
                    return
                try:
                    self.table.reattach(row_id, "", "end")
                    refresh_row_tags(self.table)
                except Exception:
                    self.load_data()
                messagebox.showerror(
                    "Delete Failed",
                    f"Could not delete unit '{unit_label}'.\n\n{e}",
                )

        def undo_action():
            entry["state"] = "cancelled"
            self.table.reattach(row_id, "", "end")
            refresh_row_tags(self.table)

        entry["flush"] = lambda: commit(quiet=True)
        self._pending_deletes.append(entry)

        UndoToast(self, f"'{unit_label}' deleted",
                  on_undo=undo_action, on_timeout=commit)

    def _flush_pending_deletes(self, event=None):
        if event is not None and getattr(event, "widget", None) is not self:
            return
        for entry in self._pending_deletes:
            entry["flush"]()
        self._pending_deletes.clear()

    def clear_form(self):
        self.selected_unit_id = None
        self.var_site.set("")
        self.var_type.set(UNIT_TYPES[0])
        self.var_manufacturer.set("")
        self.var_model.set("")
        self.var_install_date.set("2026-05-12")
        self.var_output.set("0")
        self.var_status.set("Operational")
        self.var_serial.set("")
        self.table.selection_remove(self.table.selection())

    # --------------------------------------------------
    # Right: form (scrollable so all fields are reachable)
    # --------------------------------------------------
    def _create_form_section(self):
        form_frame = ctk.CTkScrollableFrame(self, width=340, label_text="")
        form_frame.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(form_frame, text="Unit Details",
                     font=ctk.CTkFont(size=FONT_SIZE_HEADER, weight="bold")).pack(pady=(15, 12))

        ctk.CTkLabel(form_frame, text="Parent Site:",
                     font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=20)
        try:
            site_names = [s[1] for s in get_all_sites()]
            if not site_names:
                site_names = ["No Sites Available"]
        except Exception:
            site_names = ["Database Error"]
        self.site_dropdown = ctk.CTkOptionMenu(
            form_frame, values=site_names, variable=self.var_site
        )
        self.site_dropdown.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(form_frame, text="Unit Type:",
                     font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=20)
        ctk.CTkOptionMenu(form_frame, values=UNIT_TYPES, variable=self.var_type).pack(
            fill="x", padx=20, pady=(0, 10))

        self._create_input(form_frame, "Manufacturer:", self.var_manufacturer)
        self._create_input(form_frame, "Model (optional):", self.var_model)
        self._create_input(form_frame, "Installation Date (YYYY-MM-DD):", self.var_install_date)
        self._create_input(form_frame, "Max kW Output:", self.var_output)

        ctk.CTkLabel(form_frame, text="Status:",
                     font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=20)
        ctk.CTkOptionMenu(form_frame, values=UNIT_STATUSES, variable=self.var_status).pack(
            fill="x", padx=20, pady=(0, 10))

        self._create_input(form_frame, "Serial Number (optional):", self.var_serial)

        ctk.CTkButton(form_frame, text="Save Unit", fg_color="#28a745",
                      font=("Arial", FONT_SIZE_TABLE, "bold"),
                      command=self.handle_save).pack(fill="x", padx=20, pady=(10, 5))

        ctk.CTkButton(form_frame, text="Delete Selected", fg_color="#dc3545",
                      font=("Arial", FONT_SIZE_TABLE, "bold"),
                      command=self.handle_delete).pack(fill="x", padx=20, pady=5)

        ctk.CTkButton(form_frame, text="Clear", fg_color="transparent", border_width=1,
                      command=self.clear_form).pack(fill="x", padx=20, pady=(5, 20))

    def _create_input(self, parent, label, variable):
        ctk.CTkLabel(parent, text=label, font=("Arial", FONT_SIZE_LABEL)).pack(
            anchor="w", padx=20, pady=(8, 0))
        ctk.CTkEntry(parent, textvariable=variable, font=("Arial", FONT_SIZE_TABLE)).pack(
            fill="x", padx=20, pady=(0, 10))