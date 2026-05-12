# ⚡ Renewable Energy Grid & Maintenance Network

> A database-driven desktop application for managing green energy assets, field technicians, and maintenance operations across distributed power generation sites.
>
> **Faculty of Computers and Artificial Intelligence — Cairo University | 2026**

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [Setup & Installation](#setup--installation)
- [Running the App](#running-the-app)
- [SQL Queries](#sql-queries)
- [Team](#team)

---

## Overview

This system is built for a green energy corporation that operates a network of power-generation assets across rural and coastal landscapes. It provides a full desktop GUI to manage every layer of the operation — from GPS-tracked energy sites down to individual component replacements on a single turbine blade.

---

## Features

- **Energy Sites** — Register and manage sites with GPS coordinates, terrain type, region, and country
- **Power Units** — Track wind turbines and solar arrays per site, including manufacturer, model, output, and operational status
- **Technicians** — Manage field staff profiles, certifications, and employment status
- **Inspections** — Schedule and log inspection rounds; record per-unit efficiency readings and status
- **Component Replacements** — Track spare parts used during inspections, with serial numbers, quantities, and dates
- **Reports & Queries** — Run 6 built-in analytical SQL queries with results displayed in the GUI
- **Archive** — Move reports to an archive with undo support before permanent deletion
- **Search** — Live keyword search across every data screen

---

## Tech Stack

| Layer | Technology |
|---|---|
| Database | Microsoft SQL Server |
| Backend | Python 3.11 + pyodbc |
| GUI Framework | CustomTkinter 5.2.2 |
| Image Support | Pillow 10.3.0 |
| Version Control | Git / GitHub |

---

## Project Structure

```
renewable-energy-grid-db/
│
├── app/
│   ├── main.py                          # Entry point
│   │
│   ├── backend/
│   │   ├── db_connection.py             # Connection config & factory
│   │   ├── site_operations.py           # CRUD — Energy Sites
│   │   ├── unit_operations.py           # CRUD — Power Units
│   │   ├── technician_operations.py     # CRUD — Technicians
│   │   ├── inspection_operations.py     # CRUD — Inspections
│   │   ├── component_operations.py      # CRUD — Component Replacements
│   │   └── query_operations.py          # All 6 analytical queries
│   │
│   └── frontend/
│       ├── main_window.py               # App shell & sidebar navigation
│       └── screens/
│           ├── sites_screen.py
│           ├── units_screen.py
│           ├── technicians_screen.py
│           ├── inspections_screen.py
│           ├── components_screen.py
│           ├── queries_screen.py
│           ├── archive_screen.py
│           ├── table_style.py           # Shared Treeview dark theme
│           └── data_manager.py          # Shared in-memory data store
│
├── database/
│   ├── ddl/
│   │   └── SQLddl.sql                   # Full schema (CREATE + indexes)
│   └── queries/
│       ├── queries.sql                  # All 6 queries in plain SQL
│       └── insert_data.sql              # Realistic sample data (10 sites, 10 units, 10 technicians...)
│
├── docs/
│   └── project_documentation.pdf        # Phase 3 submission PDF
│
├── requirements.txt
└── README.md
```

---

## Database Schema

The database is named `renewable_energy` and contains 9 tables:

```
Energy_Site
    └── Power_Unit
            └── Unit_Inspection ──────────── Component_Replacement
                    │                                 │
            Inspection_Round                      Spare_Part
                    │
               Technician
                    └── Technician_Certification
                                │
                    Unit_Type_Certification
```

**Key relationships:**
- Each `Power_Unit` belongs to one `Energy_Site`
- Each `Inspection_Round` is assigned to one `Technician` and covers one `Energy_Site`
- Each `Unit_Inspection` links one `Power_Unit` to one `Inspection_Round`
- Each `Component_Replacement` records one `Spare_Part` used during a `Unit_Inspection`

---
## Running the App

From inside the `app/` folder:
```bash
cd app
python main.py
```

The app launches in dark mode with a sidebar for navigating between all screens.

---

## SQL Queries

Six analytical queries are built into the Reports screen and also available as plain SQL in `database/queries/queries.sql`:

| # | Query |
|---|---|
| 1 | Manufacturer with the most efficiency readings **below the global average** |
| 2 | Energy sites with **no completed inspection** in the previous calendar month |
| 3 | Technician with the **most completed inspections** last month |
| 4 | Power units that had **no component replacement** recorded last month |
| 5 | All component replacements **per site** in the previous calendar month |
| 6 | Full **technician profile** with total count of distinct units inspected |

---

## Team

| Role | Member |
|---|---|
| Leader / Reviewer | Mohamed Haithm |
| Database & DDL | Abdo |
| SQL Queries | Ahmed |
| Backend (Python) | Mahmoud Ahmed |
| Frontend (GUI) | Karim Omar |