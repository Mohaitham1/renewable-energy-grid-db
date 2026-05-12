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
from backend.component_operations import (
    get_all_components,
    add_component,
    delete_component,
    update_component,
    search_components,
    get_all_spare_parts,
    add_spare_part,
)
from backend.site_operations import get_all_sites

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
        self.selected_replacement_id = None

        # Backend `add_component` expects:
        #   (part_name_or_number, site_name, part_serial_number,
        #    replacement_date, quantity_used, notes=None)
        self.var_part = tk.StringVar()
        self.var_site = tk.StringVar()
        self.var_serial = tk.StringVar()
        self.var_date = tk.StringVar(value="2026-05-12")
        self.var_qty = tk.StringVar(value="1")
        self.var_notes = tk.StringVar()
        # display→part_id map so handle_save passes an unambiguous int instead
        # of trying to match free-text against part_name / part_number.
        self._part_display_to_id = {}
        self._part_id_to_display = {}

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
            placeholder_text="Search by part name, part number, or site...",
            font=("Arial", FONT_SIZE_TABLE),
        )
        self.ent_search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.ent_search.bind("<KeyRelease>", lambda e: self.load_data(self.search_var.get()))

        apply_modern_treeview_style()

        cols = ("id", "part_name", "part_number", "site", "unit_type", "date")
        self.table = ttk.Treeview(container, columns=cols, show="headings")
        headers = ["ID", "Part Name", "Part Number", "Site", "Unit Type", "Replacement Date"]
        widths = [60, 180, 140, 160, 140, 140]
        for col, text, w in zip(cols, headers, widths):
            self.table.heading(col, text=text)
            self.table.column(col, anchor="center", width=w)

        self.table.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.table.bind("<<TreeviewSelect>>", self._on_row_select)
        apply_row_tags(self.table)

    def load_data(self, query=""):
        try:
            if query.strip():
                rows = search_components(query)
            else:
                rows = get_all_components()

            for row_id in self.table.get_children():
                self.table.delete(row_id)
            for item in rows:
                self.table.insert("", "end", values=item)
            refresh_row_tags(self.table)
        except Exception as e:
            print(f"Error loading components: {e}")

    def _on_row_select(self, event):
        selected = self.table.selection()
        if not selected:
            return
        v = self.table.item(selected[0])["values"]
        # v = (replacement_id, part_name, part_number, site_name, unit_type, replacement_date)
        self.selected_replacement_id = v[0]
        part_name = (v[1] or "").strip()
        # Prefer the matching "#N - name" dropdown label so the backend gets an
        # unambiguous id; fall back to the raw name otherwise.
        matching = next(
            (display for display, _pid in self._part_display_to_id.items()
             if display.split(" - ", 1)[-1].startswith(part_name)),
            part_name,
        )
        self.var_part.set(matching)
        self.var_site.set((v[3] or "").strip())
        self.var_date.set((v[5] or "").strip())

    def handle_save(self):
        # Strip every text input — leading/trailing whitespace breaks lookups
        # and we don't want it persisted on serial numbers either.
        part = self.var_part.get().strip()
        site = self.var_site.get().strip()
        serial = self.var_serial.get().strip()
        date = self.var_date.get().strip()
        qty_text = self.var_qty.get().strip() or "1"
        notes_raw = self.var_notes.get().strip()
        notes = notes_raw or None

        if not part or part.startswith("No Spare Parts"):
            messagebox.showwarning(
                "Input Error",
                "Pick a Spare Part from the dropdown (or click + Add Part to seed one).",
            )
            return
        if not site or not serial or not date:
            messagebox.showwarning(
                "Input Error",
                "Site, Part Serial Number, and Replacement Date are required.",
            )
            return

        try:
            qty = int(qty_text)
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Input Error", "Quantity must be a positive integer.")
            return

        # Resolve to an int part_id where possible — pass it through as the
        # "part_name_or_number" arg; the backend resolver accepts ints.
        part_arg = self._part_display_to_id.get(part, part)

        try:
            if self.selected_replacement_id:
                ok = update_component(
                    self.selected_replacement_id, part_arg, site, serial, date, qty, notes
                )
                msg = "Component replacement updated."
            else:
                ok = add_component(part_arg, site, serial, date, qty, notes)
                msg = "Component replacement added."

            if ok:
                self.load_data()
                self.clear_form()
                messagebox.showinfo("Success", msg)
        except Exception as e:
            # Backend now raises ValueError with a specific reason (missing
            # spare part vs no inspection on site) — surface it verbatim.
            messagebox.showerror("Error", str(e))

    def handle_delete(self):
        if not self.selected_replacement_id:
            return
        if not messagebox.askyesno(
            "Confirm", "Are you sure you want to delete this component replacement?"
        ):
            return
        try:
            if delete_component(self.selected_replacement_id):
                self.load_data()
                self.clear_form()
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete: {e}")

    def clear_form(self):
        self.selected_replacement_id = None
        self.var_part.set("")
        self.var_site.set("")
        self.var_serial.set("")
        self.var_date.set("2026-05-12")
        self.var_qty.set("1")
        self.var_notes.set("")
        self.table.selection_remove(self.table.selection())

    # --------------------------------------------------
    # Right: form
    # --------------------------------------------------
    def _build_part_options(self):
        """Reload the Spare_Part list and rebuild the display↔id maps. Returns
        the list of dropdown labels."""
        self._part_display_to_id.clear()
        self._part_id_to_display.clear()
        try:
            parts = get_all_spare_parts()  # (part_id, part_name, part_number, qty_in_stock)
        except Exception as e:
            print(f"Loading spare parts for Components dropdown failed: {e}")
            parts = []
        displays = []
        for part_id, part_name, part_number, _qty in parts:
            display = f"#{part_id} - {(part_name or '').strip()} ({(part_number or '').strip()})"
            self._part_display_to_id[display] = part_id
            self._part_id_to_display[str(part_id)] = display
            displays.append(display)
        return displays or ["No Spare Parts — click + Add Part"]

    def _refresh_part_dropdown(self):
        """Re-fetch parts and update the CTkOptionMenu's choices in place."""
        new_values = self._build_part_options()
        if hasattr(self, "part_menu"):
            self.part_menu.configure(values=new_values)
            # Keep current selection if still valid; otherwise reset.
            if self.var_part.get() not in new_values:
                self.var_part.set(new_values[0])

    def _create_form_section(self):
        form_frame = ctk.CTkScrollableFrame(self, width=360, label_text="")
        form_frame.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(
            form_frame,
            text="Component Replacement",
            font=ctk.CTkFont(size=FONT_SIZE_HEADER, weight="bold"),
        ).pack(pady=(15, 12))

        # Spare Part dropdown (was a free-text Entry, which is why typing "6"
        # tried to match a part NAMED "6"). The "+ Add Part" button next to it
        # opens a small modal so users can seed Spare_Part inline.
        ctk.CTkLabel(form_frame, text="Spare Part:", font=("Arial", FONT_SIZE_LABEL)).pack(
            anchor="w", padx=25, pady=(8, 0)
        )
        part_row = ctk.CTkFrame(form_frame, fg_color="transparent")
        part_row.pack(fill="x", padx=25, pady=(0, 10))
        part_displays = self._build_part_options()
        self.part_menu = ctk.CTkOptionMenu(
            part_row, values=part_displays, variable=self.var_part,
        )
        self.part_menu.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            part_row, text="+", width=32, fg_color="#1f538d",
            command=self._open_add_part_dialog,
        ).pack(side="left", padx=(6, 0))

        ctk.CTkLabel(form_frame, text="Site:", font=("Arial", FONT_SIZE_LABEL)).pack(
            anchor="w", padx=25
        )
        try:
            site_names = [s[1] for s in get_all_sites()]
            if not site_names:
                site_names = ["No Sites Available"]
        except Exception as e:
            print(f"Loading sites for Components dropdown failed: {e}")
            site_names = ["Database Error"]
        self.site_menu = ctk.CTkOptionMenu(form_frame, values=site_names, variable=self.var_site)
        self.site_menu.pack(fill="x", padx=25, pady=(0, 12))

        self._create_input(form_frame, "Part Serial Number:", self.var_serial)
        self._create_input(form_frame, "Replacement Date (YYYY-MM-DD):", self.var_date)
        self._create_input(form_frame, "Quantity Used:", self.var_qty)
        self._create_input(form_frame, "Notes (optional):", self.var_notes)

        ctk.CTkButton(
            form_frame, text="Save Replacement", fg_color="#28a745",
            font=("Arial", FONT_SIZE_TABLE, "bold"), command=self.handle_save,
        ).pack(fill="x", padx=25, pady=(10, 5))

        ctk.CTkButton(
            form_frame, text="Delete Selected", fg_color="#dc3545",
            font=("Arial", FONT_SIZE_TABLE, "bold"), command=self.handle_delete,
        ).pack(fill="x", padx=25, pady=5)

        ctk.CTkButton(
            form_frame, text="Clear", fg_color="transparent", border_width=1,
            command=self.clear_form,
        ).pack(fill="x", padx=25, pady=(5, 20))

    def _create_input(self, frame, label, var):
        ctk.CTkLabel(frame, text=label, font=("Arial", FONT_SIZE_LABEL)).pack(
            anchor="w", padx=25, pady=(8, 0)
        )
        ctk.CTkEntry(frame, textvariable=var, font=("Arial", FONT_SIZE_TABLE)).pack(
            fill="x", padx=25, pady=(0, 10)
        )

    # --------------------------------------------------
    # Inline "Add Spare Part" modal — minimum-viable seed UI so the user
    # doesn't need to leave the screen and open SSMS to populate Spare_Part.
    # --------------------------------------------------
    def _open_add_part_dialog(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Add Spare Part")
        dlg.geometry("420x360")
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()

        v_name = tk.StringVar()
        v_number = tk.StringVar()
        v_supplier = tk.StringVar()
        v_qty = tk.StringVar(value="0")
        v_reorder = tk.StringVar(value="5")

        def row(label, var):
            ctk.CTkLabel(dlg, text=label, font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=20, pady=(10, 0))
            ctk.CTkEntry(dlg, textvariable=var).pack(fill="x", padx=20)

        row("Part Name:", v_name)
        row("Part Number:", v_number)
        row("Supplier (optional):", v_supplier)
        row("Quantity in Stock:", v_qty)
        row("Reorder Level:", v_reorder)

        def submit():
            name = v_name.get().strip()
            number = v_number.get().strip()
            supplier = v_supplier.get().strip() or None
            if not name or not number:
                messagebox.showwarning("Input Error", "Part Name and Part Number are required.", parent=dlg)
                return
            try:
                qty = int(v_qty.get().strip() or "0")
                reorder = int(v_reorder.get().strip() or "5")
                if qty < 0 or reorder < 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Input Error", "Quantity and Reorder Level must be non-negative integers.", parent=dlg)
                return
            try:
                add_spare_part(name, number, supplier=supplier,
                               quantity_in_stock=qty, reorder_level=reorder)
            except Exception as e:
                messagebox.showerror("DB Error", f"Could not add spare part: {e}", parent=dlg)
                return
            dlg.destroy()
            self._refresh_part_dropdown()
            # Auto-select the row we just inserted (last by part_name asc may
            # not be it, so rebuild and find by name+number).
            for display, _pid in self._part_display_to_id.items():
                if name in display and number in display:
                    self.var_part.set(display)
                    break

        ctk.CTkButton(dlg, text="Add Part", fg_color="#28a745", command=submit).pack(fill="x", padx=20, pady=(20, 6))
        ctk.CTkButton(dlg, text="Cancel", fg_color="transparent", border_width=1,
                      command=dlg.destroy).pack(fill="x", padx=20, pady=(0, 20))