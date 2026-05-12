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
from backend.technician_operations import (
    get_all_technicians,
    add_technician,
    delete_technician,
    update_technician,
    search_technicians,
)

FONT_SIZE_HEADER = 20
FONT_SIZE_LABEL = 13
FONT_SIZE_TABLE = 12

EMPLOYMENT_STATUSES = ["Active", "On-Leave", "Retired", "Suspended"]


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
# TECHNICIANS SCREEN
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
        self.bind("<Destroy>", self._flush_pending_deletes)

    def _init_variables(self):
        self.search_var = tk.StringVar()
        self.selected_tech_id = None
        # Pending undo-toast deletions that must be committed if the user
        # switches tabs before the 5s timer fires.
        self._pending_deletes = []

        self.var_name = tk.StringVar()
        self.var_email = tk.StringVar()
        self.var_phone = tk.StringVar()
        self.var_hire_date = tk.StringVar(value="2026-05-12")
        self.var_status = tk.StringVar(value="Active")

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
            placeholder_text="Search by name, email, or status...",
            font=("Arial", FONT_SIZE_TABLE),
        )
        self.ent_search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.ent_search.bind("<Return>", self._on_search)
        self.ent_search.bind("<KeyRelease>", self._on_search)

        ctk.CTkButton(search_frame, text="Search", width=100,
                      command=self._on_search).pack(side="right")

        apply_modern_treeview_style()

        cols = ("id", "name", "email", "phone", "hire_date", "status")
        self.table = ttk.Treeview(container, columns=cols, show="headings")
        headers = ["Tech ID", "Full Name", "Email", "Phone", "Hire Date", "Status"]
        widths = [70, 170, 200, 130, 110, 100]
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
            rows = search_technicians(q) if q else get_all_technicians()

            for row_id in self.table.get_children():
                self.table.delete(row_id)
            for item in rows:
                self.table.insert("", "end", values=item)
            refresh_row_tags(self.table)
        except Exception as e:
            print(f"Error loading technicians: {e}")

    def _on_row_select(self, event):
        selected = self.table.selection()
        if not selected:
            return
        v = self.table.item(selected[0])["values"]
        # v = (technician_id, full_name, email, phone, hire_date, employment_status)
        self.selected_tech_id = v[0]
        self.var_name.set(v[1])
        self.var_email.set(v[2] if v[2] is not None else "")
        self.var_phone.set(v[3] if v[3] is not None else "")
        self.var_hire_date.set(v[4] if v[4] is not None else "")
        # Only set the OptionMenu if the DB value is in the allowed list;
        # otherwise leave the default to avoid an invisible/empty menu.
        status = v[5] if v[5] in EMPLOYMENT_STATUSES else "Active"
        self.var_status.set(status)

    def handle_save(self):
        name = self.var_name.get().strip()
        email = self.var_email.get().strip()
        phone = self.var_phone.get().strip()
        hire_date = self.var_hire_date.get().strip()
        status = self.var_status.get().strip() or "Active"

        if not name or not hire_date:
            messagebox.showwarning("Input Error", "Full Name and Hire Date are required.")
            return

        try:
            if self.selected_tech_id:
                ok = update_technician(
                    self.selected_tech_id, name, email or None, phone or None,
                    hire_date, status,
                )
                msg = "Technician updated."
            else:
                ok = add_technician(name, email or None, phone or None, hire_date, status)
                msg = f"Technician '{name}' registered."

            if ok:
                self.load_data()
                self.clear_form()
                messagebox.showinfo("Success", msg)
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not save technician: {e}")

    def handle_delete(self):
        selected = self.table.selection()
        if not selected:
            return

        row_id = selected[0]
        tech_id = self.table.item(row_id)["values"][0]
        tech_name = self.table.item(row_id)["values"][1]

        self.table.detach(row_id)
        refresh_row_tags(self.table)

        entry = {"state": "live"}

        def commit(quiet=False):
            if entry["state"] != "live":
                return
            entry["state"] = "committed"
            try:
                delete_technician(tech_id)
            except Exception as e:
                entry["state"] = "failed"
                if quiet:
                    print(f"Delete technician {tech_id} failed during flush: {e}")
                    return
                try:
                    self.table.reattach(row_id, "", "end")
                    refresh_row_tags(self.table)
                except Exception:
                    self.load_data()
                messagebox.showerror(
                    "Delete Failed",
                    f"Could not delete technician '{tech_name}'.\n\n{e}",
                )

        def undo_action():
            entry["state"] = "cancelled"
            self.table.reattach(row_id, "", "end")
            refresh_row_tags(self.table)

        entry["flush"] = lambda: commit(quiet=True)
        self._pending_deletes.append(entry)

        UndoToast(self, f"'{tech_name}' deleted",
                  on_undo=undo_action, on_timeout=commit)

    def _flush_pending_deletes(self, event=None):
        if event is not None and getattr(event, "widget", None) is not self:
            return
        for entry in self._pending_deletes:
            entry["flush"]()
        self._pending_deletes.clear()

    def clear_form(self):
        self.selected_tech_id = None
        self.var_name.set("")
        self.var_email.set("")
        self.var_phone.set("")
        self.var_hire_date.set("2026-05-12")
        self.var_status.set("Active")
        self.table.selection_remove(self.table.selection())

    # --------------------------------------------------
    # Right: form
    # --------------------------------------------------
    def _create_form_section(self):
        form_frame = ctk.CTkFrame(self, width=340)
        form_frame.grid(row=0, column=1, sticky="nsew")
        form_frame.grid_propagate(False)

        ctk.CTkLabel(form_frame, text="Staff Manager",
                     font=ctk.CTkFont(size=FONT_SIZE_HEADER, weight="bold")).pack(pady=(25, 15))

        self._create_input(form_frame, "Full Name:", self.var_name)
        self._create_input(form_frame, "Email:", self.var_email)
        self._create_input(form_frame, "Phone:", self.var_phone)
        self._create_input(form_frame, "Hire Date (YYYY-MM-DD):", self.var_hire_date)

        ctk.CTkLabel(form_frame, text="Employment Status:",
                     font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25, pady=(8, 0))
        ctk.CTkOptionMenu(form_frame, values=EMPLOYMENT_STATUSES,
                          variable=self.var_status).pack(fill="x", padx=25, pady=(0, 12))

        ctk.CTkButton(form_frame, text="Save Technician", fg_color="#28a745",
                      font=("Arial", FONT_SIZE_TABLE, "bold"),
                      command=self.handle_save).pack(fill="x", padx=25, pady=(10, 5))

        ctk.CTkButton(form_frame, text="Delete Selected", fg_color="#dc3545",
                      font=("Arial", FONT_SIZE_TABLE, "bold"),
                      command=self.handle_delete).pack(fill="x", padx=25, pady=5)

        ctk.CTkButton(form_frame, text="Clear", fg_color="transparent", border_width=1,
                      command=self.clear_form).pack(fill="x", padx=25, pady=(5, 20))

    def _create_input(self, frame, label, var):
        ctk.CTkLabel(frame, text=label, font=("Arial", FONT_SIZE_LABEL)).pack(
            anchor="w", padx=25, pady=(8, 0))
        ctk.CTkEntry(frame, textvariable=var, font=("Arial", FONT_SIZE_TABLE)).pack(
            fill="x", padx=25, pady=(0, 10))