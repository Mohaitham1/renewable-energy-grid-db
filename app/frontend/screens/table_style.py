from tkinter import ttk

def apply_modern_treeview_style():
    style = ttk.Style()
    style.theme_use("clam")

    style.configure(
        "Treeview",
        background="#2b2b2b",
        foreground="white",
        fieldbackground="#2b2b2b",
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
        background="#333333",
        foreground="white",
        borderwidth=1,
        bordercolor="#444444",
    )

    style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

    style.map(
        "Treeview",
        background=[("selected", "#1f538d")],
        foreground=[("selected", "white")]
    )