-- FILE: queries.sql

USE renewable_energy;
GO

-- INQUIRY 1: Manufacturer with Most Below Average Readings

WITH OverallAvg AS (
    SELECT AVG(efficiency_reading) AS avg_efficiency
    FROM Unit_Inspection
),
BelowAvgReadings AS (
    SELECT
        pu.manufacturer,
        ui.unit_inspection_id
    FROM Unit_Inspection ui
    INNER JOIN Power_Unit pu
        ON ui.unit_id = pu.unit_id
    CROSS JOIN OverallAvg oa
    WHERE ui.efficiency_reading < oa.avg_efficiency
)
SELECT TOP 1
    manufacturer,
    COUNT(unit_inspection_id) AS below_average_count
FROM BelowAvgReadings
GROUP BY manufacturer
ORDER BY below_average_count DESC;
GO


-- INQUIRY 2: Sites Without Inspections Last Month

SELECT
    es.site_id,
    es.site_name,
    es.country,
    es.region
FROM Energy_Site es
WHERE es.site_id NOT IN (
    SELECT DISTINCT ir.site_id
    FROM Inspection_Round ir
    WHERE ir.status        = 'Completed'
      AND ir.conducted_date >= DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()) - 1, 0)
      AND ir.conducted_date <  DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()),     0)
)
ORDER BY es.site_id;
GO

-- INQUIRY 3: Technician With Most Inspections Last Month

WITH LastMonthInspections AS (
    SELECT
        t.technician_id,
        t.first_name + ' ' + t.last_name  AS full_name,
        COUNT(ir.inspection_id)            AS inspection_count
    FROM Technician t
    INNER JOIN Inspection_Round ir
        ON t.technician_id = ir.technician_id
    WHERE ir.status        = 'Completed'
      AND ir.conducted_date >= DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()) - 1, 0)
      AND ir.conducted_date <  DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()),     0)
    GROUP BY
        t.technician_id,
        t.first_name,
        t.last_name
)
SELECT TOP 1 WITH TIES
    technician_id,
    full_name,
    inspection_count
FROM LastMonthInspections
ORDER BY inspection_count DESC;
GO

-- INQUIRY 4: Power Units With No Component Replacements

SELECT
    pu.unit_id,
    pu.serial_number,
    pu.unit_type,
    pu.manufacturer,
    pu.model,
    es.site_name,
    pu.status
FROM Power_Unit pu
INNER JOIN Energy_Site es
    ON pu.site_id = es.site_id
WHERE pu.unit_id NOT IN (
    SELECT DISTINCT ui.unit_id
    FROM Unit_Inspection    ui
    INNER JOIN Component_Replacement cr
        ON ui.unit_inspection_id = cr.unit_inspection_id
)
ORDER BY pu.unit_id;
GO

-- INQUIRY 5: Installed Components Per Site

SELECT
    es.site_id,
    es.site_name,
    es.country,
    COALESCE(SUM(cr.quantity_used), 0) AS total_components_installed
FROM Energy_Site es
LEFT JOIN Inspection_Round ir
    ON es.site_id = ir.site_id
LEFT JOIN Unit_Inspection ui
    ON ir.inspection_id = ui.inspection_id
LEFT JOIN Component_Replacement cr
    ON ui.unit_inspection_id = cr.unit_inspection_id
   AND cr.replacement_date >= DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()) - 1, 0)
   AND cr.replacement_date <  DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()),     0)
GROUP BY
    es.site_id,
    es.site_name,
    es.country
ORDER BY total_components_installed DESC;
GO

-- INQUIRY 6: Technician Profile  Total Inspected Units

SELECT
    t.technician_id,
    t.first_name + ' ' + t.last_name   AS full_name,
    t.email,
    t.phone,
    t.hire_date,
    t.employment_status,
    COUNT(DISTINCT ui.unit_id)          AS total_units_inspected
FROM Technician t
LEFT JOIN Inspection_Round ir
    ON t.technician_id = ir.technician_id
LEFT JOIN Unit_Inspection ui
    ON ir.inspection_id = ui.inspection_id
GROUP BY
    t.technician_id,
    t.first_name,
    t.last_name,
    t.email,
    t.phone,
    t.hire_date,
    t.employment_status
ORDER BY total_units_inspected DESC;
GO