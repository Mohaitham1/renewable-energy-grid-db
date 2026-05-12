import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
from frontend.screens.table_style import apply_modern_treeview_style

# ==================================================
# REAL BACKEND INTEGRATION
# ==================================================
from backend.query_operations import (
    query_manufacturer_most_below_avg,
    query_sites_with_no_inspection_last_month,
    query_technician_max_inspections_last_month,
    query_units_without_component_replacement_last_month,
    query_components_installed_last_month,
    query_technician_profile_and_units_inspected,
    # New aggregate helpers used only by the Chart tab.
    query_manufacturer_below_avg_counts,
    query_technician_inspection_counts_last_month,
    query_total_site_count,
)

# matplotlib embedding. We import lazily-but-eagerly here so a missing install
# degrades the Chart tab only (showing an install hint) instead of crashing the
# whole app at module-load time — that's what happens when this is a plain
# `import matplotlib` and the package isn't installed.
try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
    MATPLOTLIB_IMPORT_ERROR = None
except Exception as _mpl_err:  # pragma: no cover — only fires when matplotlib is missing
    MATPLOTLIB_AVAILABLE = False
    MATPLOTLIB_IMPORT_ERROR = _mpl_err
    Figure = None
    FigureCanvasTkAgg = None

# UI CONFIGURATION
FONT_SIZE_HEADER = 20
FONT_SIZE_LABEL = 13
FONT_SIZE_TABLE = 12

# Chart palette tuned to the dark theme used elsewhere in the app.
CHART_BG = "#2b2b2b"
CHART_FG = "#ffffff"
CHART_GRID = "#3a3a3a"
CHART_ACCENT = "#1f538d"      # primary bar / line color (matches button blue)
CHART_ACCENT_2 = "#28a745"    # complementary green for "good" slices
CHART_ACCENT_3 = "#dc3545"    # warning red for "bad" slices
CHART_PIE_COLORS = ["#1f538d", "#28a745", "#E67E22", "#9b59b6", "#dc3545", "#16a085"]


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
        self.query_options = [
            "1. Manufacturer Efficiency Issues",
            "2. Sites Missing Last Month Inspections",
            "3. Top Performing Technician",
            "4. Units with No Replacements",
            "5. Last Month Component Installs",
            "6. Technician Productivity Profiles",
        ]
        self.var_query_type = tk.StringVar(value=self.query_options[0])
        self.current_data = []       # rows currently shown in the table
        self.current_headers = []    # matching column headers, used by PDF export
        self.chart_canvas = None     # FigureCanvasTkAgg for the Chart tab, recreated on each render
        self.pie_canvas = None       # FigureCanvasTkAgg for the Pie tab

        # Default bar width — thinner than matplotlib's 0.8 default so the
        # chart doesn't feel crowded with only a handful of categories.
        self.bar_width = 0.45

    def _setup_ui(self):
        self._create_main_panel()
        self._create_sidebar_section()

    # ------------------------------------------------------------------
    # Main panel: tabview with Table + Chart
    # ------------------------------------------------------------------
    def _create_main_panel(self):
        container = ctk.CTkFrame(self)
        container.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        header_frame = ctk.CTkFrame(container, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=15)
        ctk.CTkLabel(
            header_frame, text="Database Analytics",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left")
        ctk.CTkButton(
            header_frame, text="Refresh", width=90, command=self.run_query,
        ).pack(side="right")

        # Tabview hosts Table + Chart (bars) + Pie. Each tab gets its own
        # matplotlib canvas so switching tabs doesn't redraw — the renders are
        # already eager when the query changes.
        self.tabs = ctk.CTkTabview(container)
        self.tabs.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.tab_table = self.tabs.add("Table")
        self.tab_chart = self.tabs.add("Chart")
        self.tab_pie = self.tabs.add("Pie")

        apply_modern_treeview_style()

        self.table = None  # built lazily by _build_table

        self.chart_frame = ctk.CTkFrame(self.tab_chart, fg_color=CHART_BG)
        self.chart_frame.pack(fill="both", expand=True)

        self.pie_frame = ctk.CTkFrame(self.tab_pie, fg_color=CHART_BG)
        self.pie_frame.pack(fill="both", expand=True)

    def _build_table(self, headers):
        """Rebuilds the table columns dynamically to match different query results."""
        if self.table is not None:
            self.table.destroy()

        cols = [f"col{i}" for i in range(len(headers))]
        self.table = ttk.Treeview(self.tab_table, columns=cols, show="headings")

        for col, text in zip(cols, headers):
            self.table.heading(col, text=text)
            self.table.column(col, anchor="center")

        self.table.pack(fill="both", expand=True, padx=5, pady=5)

    # ------------------------------------------------------------------
    # Query runner — keeps the original 6 inquiries intact and adds the
    # chart render call at the end.
    # ------------------------------------------------------------------
    def run_query(self):
        selection = self.var_query_type.get()
        headers = []
        data_rows = []

        try:
            if "1." in selection:
                headers = ["Manufacturer", "Below Avg Efficiency Count"]
                res = query_manufacturer_most_below_avg()
                data_rows = [(res["manufacturer"], res["below_average_count"])] if res else []

            elif "2." in selection:
                headers = ["Site ID", "Site Name"]
                res = query_sites_with_no_inspection_last_month()
                data_rows = [(r["site_id"], r["site_name"]) for r in res]

            elif "3." in selection:
                headers = ["Tech ID", "Technician Name", "Inspections (Last Month)"]
                res = query_technician_max_inspections_last_month()
                data_rows = [(res["technician_id"], res["name"], res["inspection_count"])] if res else []

            elif "4." in selection:
                headers = ["Unit ID", "Unit Type", "Status"]
                res = query_units_without_component_replacement_last_month()
                data_rows = [(r["unit_id"], r["unit_type"], r["status"]) for r in res]

            elif "5." in selection:
                headers = ["Site Name", "Component", "Category", "Install Date"]
                res = query_components_installed_last_month()
                data_rows = [(r["site_name"], r["component_name"], r["category"], r["replacement_date"]) for r in res]

            elif "6." in selection:
                headers = ["Name", "Specialty", "Certification", "Status", "Units Inspected"]
                res = query_technician_profile_and_units_inspected()
                data_rows = [
                    (
                        f"{r['first_name']} {r['last_name']}",
                        r.get("specialty"),
                        r.get("certification"),
                        r["employment_status"],
                        r["total_units_inspected"],
                    )
                    for r in res
                ]

            self._build_table(headers)
            self.current_headers = headers
            self.current_data = data_rows
            for row in data_rows:
                self.table.insert("", "end", values=row)

            self._render_chart(selection)
            self._render_pie(selection)

        except Exception as e:
            messagebox.showerror("SQL Query Error", f"Failed to retrieve data: {e}")

    # ------------------------------------------------------------------
    # Chart rendering
    # ------------------------------------------------------------------
    def _new_figure(self, grid=True):
        """Return a fresh themed Figure + Axes. Caller mounts it into a tab
        via _mount_figure(...). `grid=False` for pies — gridlines on a pie are
        visually noisy and serve no purpose.
        """
        fig = Figure(figsize=(6, 4), dpi=100, facecolor=CHART_BG)
        ax = fig.add_subplot(111)
        ax.set_facecolor(CHART_BG)
        for spine in ax.spines.values():
            spine.set_color(CHART_GRID)
        ax.tick_params(colors=CHART_FG, labelsize=9)
        ax.yaxis.label.set_color(CHART_FG)
        ax.xaxis.label.set_color(CHART_FG)
        ax.title.set_color(CHART_FG)
        if grid:
            ax.grid(True, color=CHART_GRID, linewidth=0.5, alpha=0.5)
        return fig, ax

    def _mount_figure(self, fig, frame, canvas_attr):
        """Mount `fig` into the given CTk frame, tearing down the previous
        canvas held under `canvas_attr` on this instance. Centralizing this
        means Chart and Pie tabs share the same lifecycle code.
        """
        old = getattr(self, canvas_attr, None)
        if old is not None:
            old.get_tk_widget().destroy()
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        setattr(self, canvas_attr, canvas)

    def _render_empty_chart(self, message):
        fig, ax = self._new_figure()
        ax.set_axis_off()
        ax.text(0.5, 0.5, message, color=CHART_FG, ha="center", va="center", fontsize=12)
        self._mount_figure(fig, self.chart_frame, "chart_canvas")

    def _render_empty_pie(self, message):
        fig, ax = self._new_figure(grid=False)
        ax.set_axis_off()
        ax.text(0.5, 0.5, message, color=CHART_FG, ha="center", va="center", fontsize=12)
        self._mount_figure(fig, self.pie_frame, "pie_canvas")

    def _matplotlib_install_hint(self, frame):
        """Render the missing-matplotlib hint inside the given frame."""
        for child in frame.winfo_children():
            child.destroy()
        ctk.CTkLabel(
            frame,
            text=(
                "Charts need matplotlib.\n\n"
                "Install it from a PowerShell in the project root:\n"
                "    pip install matplotlib\n\n"
                f"(Import error: {MATPLOTLIB_IMPORT_ERROR})"
            ),
            justify="center",
            text_color=CHART_FG,
            wraplength=520,
        ).pack(expand=True, padx=20, pady=20)

    def _render_chart(self, selection):
        """Pick the bar/line chart that fits each inquiry's shape."""
        if not MATPLOTLIB_AVAILABLE:
            self._matplotlib_install_hint(self.chart_frame)
            return
        try:
            if "1." in selection:
                self._chart_manufacturer_below_avg()
            elif "2." in selection:
                self._chart_sites_inspection_bar()
            elif "3." in selection:
                self._chart_technician_inspection_counts()
            elif "4." in selection:
                self._chart_units_no_replacement_by_type()
            elif "5." in selection:
                self._chart_components_by_site()
            elif "6." in selection:
                self._chart_technician_units_inspected()
            else:
                self._render_empty_chart("No chart available for this query.")
        except Exception as e:
            self._render_empty_chart(f"Chart unavailable:\n{e}")

    def _render_pie(self, selection):
        """Pie variant of each inquiry — useful for share/composition questions
        where the bar chart shows magnitudes."""
        if not MATPLOTLIB_AVAILABLE:
            self._matplotlib_install_hint(self.pie_frame)
            return
        try:
            if "1." in selection:
                self._pie_manufacturer_below_avg()
            elif "2." in selection:
                self._pie_sites_inspection()
            elif "3." in selection:
                self._pie_technician_inspection_counts()
            elif "4." in selection:
                self._pie_units_no_replacement_by_type()
            elif "5." in selection:
                self._pie_components_by_site()
            elif "6." in selection:
                self._pie_technician_units_inspected()
            else:
                self._render_empty_pie("No pie chart available for this query.")
        except Exception as e:
            self._render_empty_pie(f"Pie chart unavailable:\n{e}")

    def _chart_manufacturer_below_avg(self):
        data = query_manufacturer_below_avg_counts()
        if not data:
            return self._render_empty_chart("No efficiency readings recorded yet.")
        fig, ax = self._new_figure()
        labels = [d["manufacturer"] for d in data]
        values = [d["below_average_count"] for d in data]
        bars = ax.bar(labels, values, color=CHART_ACCENT_3, width=self.bar_width)
        ax.set_title("Below-Average Readings by Manufacturer")
        ax.set_ylabel("Readings")
        fig.autofmt_xdate(rotation=35)
        self._annotate_bars(ax, bars)
        fig.tight_layout()
        self._mount_figure(fig, self.chart_frame, "chart_canvas")

    def _chart_sites_inspection_bar(self):
        """Bar variant for the Chart tab — the donut version moved to the Pie
        tab. Two slim bars: inspected vs missing."""
        missing = len(self.current_data)
        try:
            total = query_total_site_count()
        except Exception:
            total = missing
        inspected = max(total - missing, 0)
        if total == 0:
            return self._render_empty_chart("No sites in the database.")
        fig, ax = self._new_figure()
        labels = ["Inspected", "Missing inspection"]
        values = [inspected, missing]
        bars = ax.bar(labels, values, color=[CHART_ACCENT_2, CHART_ACCENT_3], width=self.bar_width)
        ax.set_title("Sites inspected last month")
        ax.set_ylabel("Site count")
        self._annotate_bars(ax, bars)
        fig.tight_layout()
        self._mount_figure(fig, self.chart_frame, "chart_canvas")

    def _chart_technician_inspection_counts(self):
        data = query_technician_inspection_counts_last_month()
        if not data:
            return self._render_empty_chart("No technicians on record.")
        fig, ax = self._new_figure()
        names = [d["name"] for d in data]
        counts = [d["inspection_count"] for d in data]
        max_count = max(counts) if counts else 0
        colors = [CHART_ACCENT_2 if c == max_count and max_count > 0 else CHART_ACCENT for c in counts]
        # height (not width) controls thickness on horizontal bars.
        ax.barh(names, counts, color=colors, height=self.bar_width)
        ax.invert_yaxis()
        ax.set_title("Inspections completed last month")
        ax.set_xlabel("Count")
        for i, c in enumerate(counts):
            if c > 0:
                ax.text(c, i, f" {c}", va="center", color=CHART_FG, fontsize=9)
        fig.tight_layout()
        self._mount_figure(fig, self.chart_frame, "chart_canvas")

    def _chart_units_no_replacement_by_type(self):
        rows = self.current_data
        if not rows:
            return self._render_empty_chart("All units saw a replacement last month.")
        buckets = {}
        for _uid, unit_type, _status in rows:
            buckets[unit_type] = buckets.get(unit_type, 0) + 1
        labels = list(buckets.keys())
        values = [buckets[k] for k in labels]
        fig, ax = self._new_figure()
        bars = ax.bar(labels, values, color=CHART_ACCENT, width=self.bar_width)
        ax.set_title("Units missing a replacement last month — by type")
        ax.set_ylabel("Unit count")
        self._annotate_bars(ax, bars)
        fig.autofmt_xdate(rotation=20)
        fig.tight_layout()
        self._mount_figure(fig, self.chart_frame, "chart_canvas")

    def _chart_components_by_site(self):
        rows = self.current_data
        if not rows:
            return self._render_empty_chart("No component installs in the last month.")
        buckets = {}
        for site_name, _comp, _cat, _date in rows:
            buckets[site_name] = buckets.get(site_name, 0) + 1
        labels = list(buckets.keys())
        values = [buckets[k] for k in labels]
        fig, ax = self._new_figure()
        bars = ax.bar(labels, values, color=CHART_ACCENT, width=self.bar_width)
        ax.set_title("Components installed last month — by site")
        ax.set_ylabel("Installs")
        self._annotate_bars(ax, bars)
        fig.autofmt_xdate(rotation=25)
        fig.tight_layout()
        self._mount_figure(fig, self.chart_frame, "chart_canvas")

    def _chart_technician_units_inspected(self):
        rows = self.current_data
        if not rows:
            return self._render_empty_chart("No technicians on record.")
        ranked = sorted(rows, key=lambda r: r[4] or 0, reverse=True)
        names = [r[0] for r in ranked]
        counts = [r[4] or 0 for r in ranked]
        fig, ax = self._new_figure()
        ax.barh(names, counts, color=CHART_ACCENT, height=self.bar_width)
        ax.invert_yaxis()
        ax.set_title("Distinct units inspected per technician (all time)")
        ax.set_xlabel("Units inspected")
        for i, c in enumerate(counts):
            if c > 0:
                ax.text(c, i, f" {c}", va="center", color=CHART_FG, fontsize=9)
        fig.tight_layout()
        self._mount_figure(fig, self.chart_frame, "chart_canvas")

    # ------------------------------------------------------------------
    # Pie tab — one renderer per query. Each shares the same _pie_for
    # helper so labels / colors / percent formatting stay consistent.
    # ------------------------------------------------------------------
    def _pie_for(self, title, labels, values, colors=None):
        """Common pie body: themed Figure, no axes, percent + label per slice."""
        fig, ax = self._new_figure(grid=False)
        ax.set_axis_off()
        palette = colors or [
            CHART_PIE_COLORS[i % len(CHART_PIE_COLORS)] for i in range(len(values))
        ]
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            colors=palette,
            autopct="%1.1f%%",
            startangle=90,
            wedgeprops=dict(edgecolor=CHART_BG, linewidth=1),
            textprops=dict(color=CHART_FG, fontsize=9),
        )
        for at in autotexts:
            at.set_color("#ffffff")
            at.set_fontweight("bold")
        ax.set_title(title, color=CHART_FG)
        fig.tight_layout()
        self._mount_figure(fig, self.pie_frame, "pie_canvas")

    def _pie_manufacturer_below_avg(self):
        data = query_manufacturer_below_avg_counts()
        if not data:
            return self._render_empty_pie("No efficiency readings recorded yet.")
        labels = [d["manufacturer"] for d in data]
        values = [d["below_average_count"] for d in data]
        self._pie_for("Share of below-average readings by manufacturer", labels, values)

    def _pie_sites_inspection(self):
        missing = len(self.current_data)
        try:
            total = query_total_site_count()
        except Exception:
            total = missing
        inspected = max(total - missing, 0)
        if total == 0:
            return self._render_empty_pie("No sites in the database.")
        self._pie_for(
            "Sites inspected last month",
            ["Inspected", "Missing inspection"],
            [inspected, missing],
            colors=[CHART_ACCENT_2, CHART_ACCENT_3],
        )

    def _pie_technician_inspection_counts(self):
        data = query_technician_inspection_counts_last_month()
        # Drop zero-count techs from the pie — a 0% slice is just noise. The
        # Chart tab still shows them via horizontal bars.
        data = [d for d in data if d["inspection_count"] > 0]
        if not data:
            return self._render_empty_pie("No completed inspections last month.")
        labels = [d["name"] for d in data]
        values = [d["inspection_count"] for d in data]
        self._pie_for("Share of last-month inspections by technician", labels, values)

    def _pie_units_no_replacement_by_type(self):
        rows = self.current_data
        if not rows:
            return self._render_empty_pie("All units saw a replacement last month.")
        buckets = {}
        for _uid, unit_type, _status in rows:
            buckets[unit_type] = buckets.get(unit_type, 0) + 1
        self._pie_for(
            "Units missing a replacement — share by type",
            list(buckets.keys()),
            list(buckets.values()),
        )

    def _pie_components_by_site(self):
        rows = self.current_data
        if not rows:
            return self._render_empty_pie("No component installs in the last month.")
        buckets = {}
        for site_name, _comp, _cat, _date in rows:
            buckets[site_name] = buckets.get(site_name, 0) + 1
        self._pie_for(
            "Component installs last month — share by site",
            list(buckets.keys()),
            list(buckets.values()),
        )

    def _pie_technician_units_inspected(self):
        rows = self.current_data
        # Same zero-filter rationale as the technician inspection pie.
        ranked = [r for r in rows if (r[4] or 0) > 0]
        if not ranked:
            return self._render_empty_pie("No units inspected yet.")
        labels = [r[0] for r in ranked]
        values = [r[4] for r in ranked]
        self._pie_for("Distinct units inspected — share by technician", labels, values)

    @staticmethod
    def _annotate_bars(ax, bars):
        for bar in bars:
            height = bar.get_height()
            if height <= 0:
                continue
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{int(height)}",
                ha="center", va="bottom", color=CHART_FG, fontsize=9,
            )

    # ------------------------------------------------------------------
    # PDF export — now embeds the chart underneath the table.
    # ------------------------------------------------------------------
    def export_pdf(self):
        if not self.current_data:
            messagebox.showwarning("No Data", "Please run a query before exporting.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"Report_{self.var_query_type.get()[:5].replace('.', '')}",
        )
        if not file_path:
            return

        try:
            from fpdf import FPDF
            import os
            import tempfile

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, txt=f"Analytics Report: {self.var_query_type.get()}", ln=True, align="C")
            pdf.ln(6)

            # Header row.
            pdf.set_font("Arial", "B", 10)
            if self.current_headers:
                pdf.cell(0, 8, txt=" | ".join(self.current_headers), ln=True)
                pdf.ln(2)

            pdf.set_font("Arial", size=10)
            for row in self.current_data:
                pdf.cell(0, 8, txt=" | ".join(map(str, row)), ln=True)

            # Embed the current chart as a PNG below the table. Use a temp
            # file so fpdf can read it — fpdf2 doesn't accept BytesIO for
            # `image()` in older versions, and the temp file is cheap.
            if self.chart_canvas is not None:
                tmp_png = os.path.join(tempfile.gettempdir(), "report_chart.png")
                self.chart_canvas.figure.savefig(
                    tmp_png, facecolor=CHART_BG, bbox_inches="tight", dpi=120,
                )
                pdf.ln(6)
                pdf.set_font("Arial", "B", 11)
                pdf.cell(0, 8, txt="Chart:", ln=True)
                pdf.image(tmp_png, x=pdf.get_x(), y=pdf.get_y(), w=170)

            pdf.output(file_path)
            messagebox.showinfo("Success", "Report exported successfully!")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not create PDF: {e}")

    def _create_sidebar_section(self):
        sidebar = ctk.CTkFrame(self, width=320)
        sidebar.grid(row=0, column=1, sticky="nsew")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(
            sidebar, text="Report Center",
            font=ctk.CTkFont(size=FONT_SIZE_HEADER, weight="bold"),
        ).pack(pady=25)

        ctk.CTkLabel(sidebar, text="Select Inquiry:", font=("Arial", FONT_SIZE_LABEL)).pack(anchor="w", padx=25)
        self.query_menu = ctk.CTkOptionMenu(
            sidebar,
            values=self.query_options,
            variable=self.var_query_type,
            command=lambda _: self.run_query(),
        )
        self.query_menu.pack(fill="x", padx=25, pady=(0, 20))

        ctk.CTkButton(
            sidebar, text="Generate Report", fg_color="#1f538d",
            font=("Arial", 12, "bold"), command=self.run_query,
        ).pack(fill="x", padx=25, pady=10)

        ctk.CTkButton(
            sidebar, text="Save as PDF", fg_color="#28a745",
            font=("Arial", 12, "bold"), command=self.export_pdf,
        ).pack(fill="x", padx=25, pady=5)

        ctk.CTkLabel(sidebar, text="----------------", text_color="gray").pack(pady=10)

        ctk.CTkButton(
            sidebar, text="Archive Snapshot", fg_color="#E67E22",
            font=("Arial", 12, "bold"),
            command=lambda: messagebox.showinfo("Archive", "Report snapshot moved to Archive."),
        ).pack(fill="x", padx=25, pady=5)