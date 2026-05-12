-- ============================================================
-- ALTER: widen DECIMAL columns to stop "Arithmetic overflow" (8115)
--   - Energy_Site.latitude            DECIMAL(9,6)  -> DECIMAL(12,6)
--   - Energy_Site.longitude           DECIMAL(9,6)  -> DECIMAL(12,6)
--   - Power_Unit.max_kwatt_output     DECIMAL(10,2) -> DECIMAL(18,2)
--   - Unit_Inspection.efficiency_reading DECIMAL(5,2) -> DECIMAL(10,2)
--
-- Run this against an EXISTING `renewable_energy` database.
-- If you're rebuilding from SQLddl.sql, you don't need this — the new
-- types are already in the CREATE TABLE statements.
-- ============================================================
USE renewable_energy;
GO

ALTER TABLE Energy_Site
    ALTER COLUMN latitude DECIMAL(12, 6) NOT NULL;
GO

ALTER TABLE Energy_Site
    ALTER COLUMN longitude DECIMAL(12, 6) NOT NULL;
GO

ALTER TABLE Power_Unit
    ALTER COLUMN max_kwatt_output DECIMAL(18, 2) NOT NULL;
GO

-- efficiency_reading is indexed by IDX_UI_Efficiency; SQL Server blocks
-- ALTER COLUMN on an indexed numeric column, so drop & recreate the index.
IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IDX_UI_Efficiency' AND object_id = OBJECT_ID('Unit_Inspection'))
    DROP INDEX IDX_UI_Efficiency ON Unit_Inspection;
GO

ALTER TABLE Unit_Inspection
    ALTER COLUMN efficiency_reading DECIMAL(10, 2) NOT NULL;
GO

CREATE INDEX IDX_UI_Efficiency ON Unit_Inspection(efficiency_reading);
GO

-- Verify the new precision/scale.
SELECT
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    NUMERIC_PRECISION,
    NUMERIC_SCALE,
    NUMERIC_PRECISION - NUMERIC_SCALE AS INTEGER_DIGITS_ALLOWED
FROM INFORMATION_SCHEMA.COLUMNS
WHERE (TABLE_NAME = 'Energy_Site'     AND COLUMN_NAME IN ('latitude', 'longitude'))
   OR (TABLE_NAME = 'Power_Unit'      AND COLUMN_NAME = 'max_kwatt_output')
   OR (TABLE_NAME = 'Unit_Inspection' AND COLUMN_NAME = 'efficiency_reading');