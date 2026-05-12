# Backend — Python Database Operations

This folder contains all Python files that communicate 
between the GUI and SQL Server. No SQL is written in the 
frontend — all database logic lives here.

---

## Files in This Folder

| File | Purpose |
|------|---------|
| `db_connection.py` | Single connection function used by all other files |
| `site_operations.py` | CRUD functions for Energy Sites |
| `unit_operations.py` | CRUD functions for Power Units |
| `technician_operations.py` | CRUD functions for Technicians |
| `inspection_operations.py` | CRUD functions for Inspections |
| `component_operations.py` | CRUD functions for Component Replacements |
| `query_operations.py` | Runs all 6 required SQL queries |

---

## How the Connection Works

All files import from `db_connection.py`:

```python
from backend.db_connection import get_connection
```

Before running the app, open `db_connection.py` and set:
```python
SERVER_NAME   = "YOUR_SERVER_NAME"
DATABASE_NAME = "renewable_energy"
```

---

## Pattern Used in Every File

```python
def get_all_X():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM X")
    rows = cursor.fetchall()
    conn.close()
    return rows
```

SELECT → fetchall() → close() → return  
INSERT/UPDATE/DELETE → execute() → commit() → close()

---

## Responsible Member

Backend Developer: Mahmoud Ahmed