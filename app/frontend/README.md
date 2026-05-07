# Frontend — GUI Screens

This folder contains all Tkinter/CustomTkinter screens.
Each screen is one Python file. The main window loads 
them dynamically when the user clicks a sidebar button.

---

## Files in This Folder

| File | Screen | Purpose |
|------|--------|---------|
| `main_window.py` | App shell | Sidebar navigation + content area |
| `sites_screen.py` | Energy Sites | View, add, edit, delete sites |
| `units_screen.py` | Power Units | View, add, edit, delete units |
| `technicians_screen.py` | Technicians | View, add, edit, delete technicians |
| `inspections_screen.py` | Inspections | Schedule and log inspections |
| `components_screen.py` | Components | Track replacements and parts |
| `queries_screen.py` | Reports | Run and display the 6 required queries |

---

## How Screens Connect to Backend

Each screen imports only what it needs from the backend:

```python
from backend.technician_operations import (
    get_all_technicians,
    add_technician,
    update_technician,
    delete_technician
)
```

The GUI never writes SQL directly.

---

## How to Launch

From the `app/` folder, run:

---

## Responsible Member

GUI/Frontend Developer: Karim Omar