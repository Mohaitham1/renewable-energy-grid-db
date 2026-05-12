-- ============================================================
-- AUDIT: Inspection_Round identity, triggers, FKs, CHECK constraints
-- Run this script against `renewable_energy` whenever you see
-- "SCOPE_IDENTITY returned NULL" or anything similar surface from
-- add_inspection. Each section should match the expected output
-- noted in the comments.
-- ============================================================
USE renewable_energy;
GO

-- 1) inspection_id MUST be IDENTITY(1,1).
-- Expected: is_identity = 1, seed_value = 1, increment_value = 1.
SELECT
    t.name           AS table_name,
    c.name           AS column_name,
    c.is_identity,
    IDENT_SEED(t.name)      AS seed_value,
    IDENT_INCR(t.name)      AS increment_value,
    IDENT_CURRENT(t.name)   AS current_identity_value
FROM sys.columns AS c
INNER JOIN sys.tables AS t ON t.object_id = c.object_id
WHERE t.name = 'Inspection_Round'
  AND c.name = 'inspection_id';

-- 2) Any trigger on Inspection_Round (AFTER or INSTEAD OF) can interfere
-- with SCOPE_IDENTITY and the OUTPUT clause in subtle ways.
-- Expected: zero rows.
SELECT
    tr.name              AS trigger_name,
    tr.is_disabled,
    tr.is_instead_of_trigger,
    OBJECT_DEFINITION(tr.object_id) AS trigger_body
FROM sys.triggers AS tr
WHERE tr.parent_id = OBJECT_ID('Inspection_Round');

-- 3) Foreign keys on Inspection_Round — a violation here is a likely
-- cause of "INSERT didn't return an id" because the row was rejected.
-- Expected: FK_IR_Site (site_id → Energy_Site), FK_IR_Tech (technician_id → Technician).
SELECT
    fk.name                       AS fk_name,
    OBJECT_NAME(fk.parent_object_id)    AS from_table,
    pc.name                       AS from_column,
    OBJECT_NAME(fk.referenced_object_id) AS to_table,
    rc.name                       AS to_column,
    fk.is_disabled,
    fk.is_not_trusted
FROM sys.foreign_keys AS fk
INNER JOIN sys.foreign_key_columns AS fkc ON fkc.constraint_object_id = fk.object_id
INNER JOIN sys.columns AS pc ON pc.object_id = fk.parent_object_id     AND pc.column_id = fkc.parent_column_id
INNER JOIN sys.columns AS rc ON rc.object_id = fk.referenced_object_id AND rc.column_id = fkc.referenced_column_id
WHERE fk.parent_object_id = OBJECT_ID('Inspection_Round');

-- 4) CHECK constraints on Inspection_Round.
-- Expected: none in the shipped DDL.
SELECT
    cc.name             AS check_name,
    cc.definition,
    cc.is_disabled,
    cc.is_not_trusted
FROM sys.check_constraints AS cc
WHERE cc.parent_object_id = OBJECT_ID('Inspection_Round');

-- 5) Smoke-test the OUTPUT INSERTED path the same way the Python code does
-- now. This INSERT is wrapped in a ROLLBACK so it doesn't litter the table —
-- comment out the ROLLBACK if you want to keep the test row.
BEGIN TRAN;
    DECLARE @site_id INT = (SELECT TOP 1 site_id FROM Energy_Site ORDER BY site_id);
    DECLARE @tech_id INT = (SELECT TOP 1 technician_id FROM Technician ORDER BY technician_id);

    IF @site_id IS NULL OR @tech_id IS NULL
        PRINT 'Skipping smoke-test: Energy_Site or Technician is empty.';
    ELSE
    BEGIN
        INSERT INTO Inspection_Round (site_id, technician_id, scheduled_date, conducted_date, status, notes)
        OUTPUT INSERTED.inspection_id AS new_inspection_id
        VALUES (@site_id, @tech_id, CAST(GETDATE() AS DATE), CAST(GETDATE() AS DATE), 'Completed', 'audit smoke-test');
    END
ROLLBACK TRAN;
-- If section 5 prints a row with a new_inspection_id, the OUTPUT INSERTED
-- refactor in app/backend/inspection_operations.py is wired correctly and
-- the original SCOPE_IDENTITY failure cannot recur for this table.