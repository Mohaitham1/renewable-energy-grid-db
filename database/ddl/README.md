# DDL Scripts — Database Schema

This folder contains all SQL scripts needed to create the 
Renewable Energy Grid database from scratch.

---

## Files in This Folder

| File | Purpose |
|------|---------|
| `01_create_tables.sql` | Creates all tables in the correct order |
| `02_constraints.sql` | Adds all foreign keys and check constraints |
| `03_sample_data.sql` | Inserts realistic test data for development |

---

## How to Run These Scripts

Run them **in order** — the numbers matter because tables must 
exist before foreign keys can reference them.

1. Open SQL Server Management Studio (SSMS)
2. Connect to your local SQL Server instance
3. Open each file in order and press F5 to execute
4. You should see "Commands completed successfully" after each one

---

## Tables Created

- EnergySite
- Coordinates
- TerrainType
- PowerUnit
- Technician
- Certification
- TechnicianCertification
- Inspection
- EfficiencyReading
- ComponentReplacement
- SparePart

---

## Responsible Member

Database / DDL Developer: Abdo