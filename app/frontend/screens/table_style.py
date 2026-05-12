from tkinter import ttk

ROW_BG = "#2b2b2b"
ROW_ALT_BG = "#262626"
ROW_HOVER_BG = "#3a4a66"
ROW_HOVER_FG = "#ffffff"
ROW_SELECTED_BG = "#1f538d"
ROW_SELECTED_FG = "#ffffff"
TEXT_FG = "#ffffff"

HEADING_BG = "#333333"
HEADING_HOVER_BG = "#3d3d3d"
HEADING_PRESSED_BG = "#1f538d"


def _fix_treeview_state_specs(style: ttk.Style) -> None:
    """Strip ttk's `('!disabled', '!selected')` spec so per-row tag colors don't
    permanently win over the `selected` background. Without this, a selected
    row can stay dark instead of turning blue (known Tk 8.6 issue)."""
    for opt in ("foreground", "background"):
        spec = style.map("Treeview", query_opt=opt)
        cleaned = [t for t in spec if t[:2] != ("!disabled", "!selected")]
        style.map("Treeview", **{opt: cleaned})


def apply_modern_treeview_style():
    style = ttk.Style()
    style.theme_use("clam")

    style.configure(
        "Treeview",
        background=ROW_BG,
        foreground=TEXT_FG,
        fieldbackground=ROW_BG,
        borderwidth=0,
        relief="flat",
        rowheight=40,
        font=("Arial", 12),
        bordercolor="#444444",
        lightcolor="#444444",
        darkcolor="#444444",
    )

    style.configure(
        "Treeview.Heading",
        font=("Arial", 12, "bold"),
        background=HEADING_BG,
        foreground=TEXT_FG,
        borderwidth=1,
        bordercolor="#444444",
        relief="flat",
    )
    # Override clam's default pale-beige `active` (hover) and `pressed` colors
    # on column headers — those are what looked bad against the dark theme.
    style.map(
        "Treeview.Heading",
        background=[
            ("pressed", HEADING_PRESSED_BG),
            ("active", HEADING_HOVER_BG),
        ],
        foreground=[
            ("pressed", TEXT_FG),
            ("active", TEXT_FG),
        ],
        relief=[("pressed", "flat"), ("active", "flat")],
    )

    style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

    # NOTE: only map `selected`. Mapping `focus`/`active` here makes the whole
    # Treeview area flash blue, because in ttk those states are widget-wide,
    # not per-row. Per-row hover is handled via a tag bound to <Motion>.
    style.map(
        "Treeview",
        background=[("selected", ROW_SELECTED_BG)],
        foreground=[("selected", ROW_SELECTED_FG)],
    )

    _fix_treeview_state_specs(style)


def apply_row_tags(tree):
    """Set up alternating-row + hover tags and wire mouse events.

    Hover is intentionally NOT applied to selected rows so the selection
    highlight stays visible.
    """
    tree.tag_configure("odd", background=ROW_BG, foreground=TEXT_FG)
    tree.tag_configure("even", background=ROW_ALT_BG, foreground=TEXT_FG)
    tree.tag_configure("hover", background=ROW_HOVER_BG, foreground=ROW_HOVER_FG)

    state = {"last": None}

    def _restore(row):
        if not row or not tree.exists(row):
            return
        base = "even" if tree.index(row) % 2 == 0 else "odd"
        tree.item(row, tags=(base,))

    def on_motion(event):
        row = tree.identify_row(event.y)
        if row == state["last"]:
            return
        _restore(state["last"])
        if row and tree.exists(row) and row not in tree.selection():
            tree.item(row, tags=("hover",))
            state["last"] = row
        else:
            state["last"] = None

    def on_leave(_event):
        _restore(state["last"])
        state["last"] = None

    def on_select(_event):
        # When selection changes, drop the hover tag from any row that just got
        # selected so the blue selection highlight is the only visible state.
        if state["last"] in tree.selection():
            _restore(state["last"])
            state["last"] = None

    tree.bind("<Motion>", on_motion, add="+")
    tree.bind("<Leave>", on_leave, add="+")
    tree.bind("<<TreeviewSelect>>", on_select, add="+")


def refresh_row_tags(tree):
    """Re-apply odd/even tags after rows have been (re)loaded."""
    for idx, row in enumerate(tree.get_children("")):
        tree.item(row, tags=("even" if idx % 2 == 0 else "odd",))