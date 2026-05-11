

USE renewable_energy;
GO

-- 1. ENERGY_SITE (10 rows)
INSERT INTO Energy_Site (site_name, latitude, longitude, terrain_type, region, country, established_date)
VALUES
    ('Aswan Solar Complex',        23.6845,  32.8990, 'Desert',   'Upper Egypt',       'Egypt',        '2017-04-10'),
    ('Benban Solar Park',          24.4167,  32.7167, 'Desert',   'Aswan Governorate', 'Egypt',        '2019-01-15'),
    ('Gulf of Suez Wind Farm',     29.5000,  32.5500, 'Coastal',  'Suez Governorate',  'Egypt',        '2016-06-20'),
    ('Hurghada Wind Station',      27.2579,  33.8116, 'Coastal',  'Red Sea',           'Egypt',        '2018-03-05'),
    ('Gabal El-Zayt Wind Park',    28.5500,  33.0000, 'Coastal',  'Red Sea',           'Egypt',        '2015-11-30'),
    ('Lake Nasser Solar Hub',      22.9833,  32.8833, 'Desert',   'Upper Egypt',       'Egypt',        '2020-07-01'),
    ('Nile Delta Wind Farm',       31.1667,  31.0000, 'Flatland', 'Nile Delta',        'Egypt',        '2021-02-14'),
    ('Nairobi Green Energy Park',  -1.2921,  36.8219, 'Highland', 'Nairobi County',    'Kenya',        '2018-09-10'),
    ('Cape Wind & Solar Station', -33.9249,  18.4241, 'Coastal',  'Western Cape',      'South Africa', '2017-05-22'),
    ('Sahel Wind Corridor',        13.5137,   2.1098, 'Plains',   'Tillaberi',         'Niger',        '2020-11-03');
GO
-- 2. POWER_UNIT (10 rows)

INSERT INTO Power_Unit (site_id, unit_type, manufacturer, model, installation_date, max_kwatt_output, status, serial_number)
VALUES
    (1, 'Solar', 'SunPower',   'X22-370',     '2017-05-01', 370.00,   'Operational', 'SP-EG-001'),
    (1, 'Solar', 'SunPower',   'X22-370',     '2017-05-01', 370.00,   'Operational', 'SP-EG-002'),
    (2, 'Solar', 'FirstSolar', 'Series 6',    '2019-02-10', 420.00,   'Operational', 'FS-EG-001'),
    (2, 'Solar', 'FirstSolar', 'Series 6',    '2019-02-10', 420.00,   'Maintenance', 'FS-EG-002'),
    (3, 'Wind',  'Vestas',     'V150-4.5',    '2016-07-15', 4500.00,  'Operational', 'VS-EG-001'),
    (3, 'Wind',  'Vestas',     'V150-4.5',    '2016-07-15', 4500.00,  'Faulty',      'VS-EG-002'),
    (4, 'Wind',  'Siemens',    'SWT-3.6-120', '2018-04-01', 3600.00,  'Operational', 'SI-EG-001'),
    (5, 'Wind',  'GE',         'Haliade-X',   '2015-12-20', 12000.00, 'Operational', 'GE-EG-001'),
    (6, 'Solar', 'SunPower',   'P19-390',     '2020-08-05', 390.00,   'Operational', 'SP-EG-003'),
    (7, 'Wind',  'Siemens',    'SWT-6.0-154', '2021-03-10', 6000.00,  'Operational', 'SI-EG-002');
GO

-- 3. TECHNICIAN 
INSERT INTO Technician (first_name, last_name, email, phone, hire_date, employment_status)
VALUES
    ('Mohamed', 'El-Sayed',  'mohamed.elsayed@renew-eg.com',  '+20-100-1001', '2015-03-10', 'Active'),
    ('Fatima',  'Hassan',    'fatima.hassan@renew-eg.com',    '+20-111-1002', '2016-07-20', 'Active'),
    ('Ahmed',   'Khalil',    'ahmed.khalil@renew-eg.com',     '+20-122-1003', '2017-01-15', 'Active'),
    ('Nour',    'Ibrahim',   'nour.ibrahim@renew-eg.com',     '+20-100-1004', '2018-05-01', 'Active'),
    ('Youssef', 'Mansour',   'youssef.mansour@renew-eg.com',  '+20-115-1005', '2019-09-22', 'Active'),
    ('Amira',   'Abdallah',  'amira.abdallah@renew-eg.com',   '+20-128-1006', '2020-02-14', 'Active'),
    ('Kwame',   'Asante',    'kwame.asante@renew-af.com',     '+233-24-2001', '2018-11-05', 'Active'),
    ('Aisha',   'Diallo',    'aisha.diallo@renew-af.com',     '+221-77-2002', '2019-04-30', 'Active'),
    ('Tariq',   'Osman',     'tariq.osman@renew-af.com',      '+249-91-2003', '2017-08-18', 'Active'),
    ('Lena',    'Mwangi',    'lena.mwangi@renew-af.com',      '+254-72-2004', '2021-01-10', 'Inactive');
GO

-- 4. UNIT_TYPE_CERTIFICATIO
INSERT INTO Unit_Type_Certification (unit_type, description)
VALUES
    ('Solar', 'Certification for photovoltaic solar panel systems maintenance and inspection'),
    ('Wind',  'Certification for wind turbine systems maintenance and inspection'),
    ('Hydro', 'Certification for hydroelectric power systems maintenance and inspection');
GO

-- 5. TECHNICIAN_CERTIFICATIO
INSERT INTO Technician_Certification (technician_id, cert_type_id, issued_date, expiry_date)
VALUES
    (1, 1, '2015-04-01', '2025-04-01'),
    (1, 2, '2015-04-01', '2025-04-01'),
    (2, 1, '2016-08-01', '2026-08-01'),
    (3, 2, '2017-02-01', '2027-02-01'),
    (4, 1, '2018-06-01', '2028-06-01'),
    (5, 2, '2019-10-01', '2029-10-01'),
    (6, 1, '2020-03-01', '2030-03-01'),
    (7, 2, '2018-12-01', '2028-12-01'),
    (8, 1, '2019-05-01', '2029-05-01'),
    (9, 2, '2017-09-01', '2027-09-01');
GO

-- 6. INSPECTION_ROUND (10 rows)
INSERT INTO Inspection_Round (site_id, technician_id, scheduled_date, conducted_date, status, notes)
VALUES
    (1, 1, '2026-04-03', '2026-04-03', 'Completed', 'Quarterly solar panel check - Aswan'),
    (2, 2, '2026-04-10', '2026-04-10', 'Completed', 'Benban efficiency review'),
    (3, 3, '2026-04-15', '2026-04-15', 'Completed', 'Gulf of Suez turbine inspection'),
    (3, 3, '2026-04-22', '2026-04-22', 'Completed', 'Follow-up on faulty unit VS-EG-002'),
    (4, 5, '2026-03-08', '2026-03-08', 'Completed', 'Hurghada wind station - pre-season'),
    (5, 7, '2026-02-20', '2026-02-20', 'Completed', 'Gabal El-Zayt annual review'),
    (6, 4, '2026-04-18', '2026-04-18', 'Completed', 'Lake Nasser solar hub check'),
    (8, 7, '2026-03-25', '2026-03-25', 'Completed', 'Nairobi park performance review'),
    (9, 8, '2026-01-14', '2026-01-14', 'Completed', 'Cape station yearly inspection'),
    (7, 6, '2026-04-28', NULL,          'Scheduled', 'Nile Delta scheduled - not yet conducted');
GO

-- 7. UNIT

INSERT INTO Unit_Inspection (inspection_id, unit_id, efficiency_reading, unit_status, remarks)
VALUES
    (1,  1, 87.50, 'Operational', 'Good performance, minor dust accumulation'),
    (1,  2, 91.00, 'Operational', 'Excellent output for season'),
    (2,  3, 74.00, 'Operational', 'Output slightly reduced - check inverter'),
    (2,  4, 52.00, 'Maintenance', 'Panel degradation detected'),
    (3,  5, 89.00, 'Operational', 'Strong coastal winds, good yield'),
    (3,  6, 38.00, 'Faulty',      'Gearbox failure - replacement needed'),
    (4,  7, 82.00, 'Operational', 'Normal seasonal reading'),
    (7,  9, 78.50, 'Operational', 'Dust on panels, cleaning scheduled'),
    (8, 10, 93.00, 'Operational', 'Top performance this quarter'),
    (6,  8, 66.00, 'Operational', 'Below expected - blade wear suspected');
GO

-- 8. SPARE_PART 
INSERT INTO Spare_Part (part_name, part_number, compatible_types, unit_of_measure, quantity_in_stock, reorder_level, supplier)
VALUES
    ('Solar Panel Glass',     'SPG-001', 'Solar',      'piece', 60,  10, 'GlassTech Egypt'),
    ('Inverter Module',       'INV-002', 'Solar',      'piece', 25,   5, 'PowerCore Cairo'),
    ('Wind Turbine Blade',    'WTB-003', 'Wind',       'piece', 10,   3, 'BladeWorks GmbH'),
    ('Gearbox Assembly',      'GBX-004', 'Wind',       'piece',  5,   2, 'GearMaster Africa'),
    ('Anemometer Sensor',     'ANM-005', 'Wind',       'piece', 18,   5, 'SensorWorld Kenya'),
    ('Junction Box',          'JBX-006', 'Solar',      'piece', 35,   8, 'ElectroParts Egypt'),
    ('Yaw Drive Motor',       'YDM-007', 'Wind',       'piece',  7,   2, 'MotorDrive Ltd'),
    ('Solar Cell Array',      'SCA-008', 'Solar',      'piece', 20,   5, 'SunTech Alexandria'),
    ('Pitch Control System',  'PCS-009', 'Wind',       'piece',  4,   2, 'ControlTech SA'),
    ('Transformer Unit',      'TRF-010', 'Solar,Wind', 'piece', 12,   3, 'PowerTrans Johannesburg');
GO

-- 9. COMPONENT_REPLACEMENT
INSERT INTO Component_Replacement (unit_inspection_id, part_id, part_serial_number, replacement_date, quantity_used, notes)
VALUES
    (4,  1, 'SPG-001-EG01', '2026-04-11', 3, 'Replaced degraded panels on FS-EG-002 - Benban'),
    (4,  2, 'INV-002-EG01', '2026-04-11', 1, 'Inverter swap on Benban unit'),
    (6,  4, 'GBX-004-EG01', '2026-04-16', 1, 'Gearbox replaced on VS-EG-002 - Gulf of Suez'),
    (6,  3, 'WTB-003-EG01', '2026-04-16', 2, 'Two blades replaced after gearbox fault'),
    (8,  1, 'SPG-001-EG02', '2026-04-19', 4, 'Panel glass replaced - dust damage at Nasser'),
    (8,  6, 'JBX-006-EG01', '2026-04-19', 1, 'Junction box corrosion - Nasser solar hub'),
    (10, 7, 'YDM-007-AF01', '2026-02-21', 1, 'Yaw drive replaced - Gabal El-Zayt'),
    (10, 5, 'ANM-005-AF01', '2026-02-21', 1, 'Anemometer sensor faulty - Gabal El-Zayt'),
    (9,  8, 'SCA-008-AF01', '2026-01-15', 2, 'Cell array degraded - Cape station'),
    (7,  9, 'PCS-009-EG01', '2026-03-09', 1, 'Pitch control replaced - Hurghada');
GO
