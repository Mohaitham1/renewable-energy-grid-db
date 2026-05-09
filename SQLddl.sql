-- ============================================================
-- CREATE DATABASE
-- ============================================================
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'renewable_energy')
    CREATE DATABASE renewable_energy;
GO

USE renewable_energy;
GO

-- ============================================================
-- DROP TABLES IN REVERSE ORDER (To avoid Foreign Key errors)
-- ============================================================
IF OBJECT_ID('Component_Replacement', 'U') IS NOT NULL DROP TABLE Component_Replacement;
IF OBJECT_ID('Spare_Part', 'U') IS NOT NULL DROP TABLE Spare_Part;
IF OBJECT_ID('Unit_Inspection', 'U') IS NOT NULL DROP TABLE Unit_Inspection;
IF OBJECT_ID('Inspection_Round', 'U') IS NOT NULL DROP TABLE Inspection_Round;
IF OBJECT_ID('Technician_Certification', 'U') IS NOT NULL DROP TABLE Technician_Certification;
IF OBJECT_ID('Unit_Type_Certification', 'U') IS NOT NULL DROP TABLE Unit_Type_Certification;
IF OBJECT_ID('Technician', 'U') IS NOT NULL DROP TABLE Technician;
IF OBJECT_ID('Power_Unit', 'U') IS NOT NULL DROP TABLE Power_Unit;
IF OBJECT_ID('Energy_Site', 'U') IS NOT NULL DROP TABLE Energy_Site;
GO

-- ============================================================
-- 1. ENERGY_SITE
-- ============================================================
CREATE TABLE Energy_Site (
    site_id          INT            NOT NULL IDENTITY(1,1),
    site_name        VARCHAR(100)   NOT NULL,
    latitude         DECIMAL(9,6)   NOT NULL,
    longitude        DECIMAL(9,6)   NOT NULL,
    terrain_type     VARCHAR(50)    NOT NULL,
    region           VARCHAR(100)   NULL,
    country          VARCHAR(100)   NOT NULL,
    established_date DATE           NULL,
    CONSTRAINT PK_Energy_Site PRIMARY KEY (site_id)
);
GO

-- ============================================================
-- 2. POWER_UNIT
-- ============================================================
CREATE TABLE Power_Unit (
    unit_id           INT            NOT NULL IDENTITY(1,1),
    site_id           INT            NOT NULL,
    unit_type         VARCHAR(50)    NOT NULL,
    manufacturer      VARCHAR(100)   NOT NULL,
    model             VARCHAR(100)   NULL,
    installation_date DATE           NOT NULL,
    max_kwatt_output  DECIMAL(10,2)  NOT NULL,
    status            VARCHAR(30)    NOT NULL CONSTRAINT DF_PU_Status DEFAULT 'Operational',
    serial_number     VARCHAR(100)   NULL,
    CONSTRAINT PK_Power_Unit   PRIMARY KEY (unit_id),
    CONSTRAINT UQ_PU_Serial    UNIQUE      (serial_number),
    CONSTRAINT FK_PU_Site      FOREIGN KEY (site_id)
        REFERENCES Energy_Site(site_id)
);
GO

-- ============================================================
-- 3. TECHNICIAN
-- ============================================================
CREATE TABLE Technician (
    technician_id     INT            NOT NULL IDENTITY(1,1),
    first_name        VARCHAR(50)    NOT NULL,
    last_name         VARCHAR(50)    NOT NULL,
    email             VARCHAR(150)   NULL,
    phone             VARCHAR(30)    NULL,
    hire_date         DATE           NOT NULL,
    employment_status VARCHAR(20)    NOT NULL CONSTRAINT DF_Tech_Status DEFAULT 'Active',
    CONSTRAINT PK_Technician  PRIMARY KEY (technician_id),
    CONSTRAINT UQ_Tech_Email  UNIQUE      (email)
);
GO

-- ============================================================
-- 4. UNIT_TYPE_CERTIFICATION
-- ============================================================
CREATE TABLE Unit_Type_Certification (
    cert_type_id  INT           NOT NULL IDENTITY(1,1),
    unit_type     VARCHAR(50)   NOT NULL,
    description   VARCHAR(MAX)  NULL,
    CONSTRAINT PK_UTC         PRIMARY KEY (cert_type_id),
    CONSTRAINT UQ_UTC_UnitType UNIQUE     (unit_type)
);
GO

-- ============================================================
-- 5. TECHNICIAN_CERTIFICATION
-- ============================================================
CREATE TABLE Technician_Certification (
    technician_id  INT  NOT NULL,
    cert_type_id   INT  NOT NULL,
    issued_date    DATE NOT NULL,
    expiry_date    DATE NULL,
    CONSTRAINT PK_Tech_Cert PRIMARY KEY (technician_id, cert_type_id),
    CONSTRAINT FK_TC_Tech   FOREIGN KEY (technician_id)
        REFERENCES Technician(technician_id)
        ON DELETE CASCADE,
    CONSTRAINT FK_TC_Cert   FOREIGN KEY (cert_type_id)
        REFERENCES Unit_Type_Certification(cert_type_id)
);
GO

-- ============================================================
-- 6. INSPECTION_ROUND
-- ============================================================
CREATE TABLE Inspection_Round (
    inspection_id   INT           NOT NULL IDENTITY(1,1),
    site_id         INT           NOT NULL,
    technician_id   INT           NOT NULL,
    scheduled_date  DATE          NOT NULL,
    conducted_date  DATE          NULL,
    status          VARCHAR(20)   NOT NULL CONSTRAINT DF_IR_Status DEFAULT 'Scheduled',
    notes           VARCHAR(MAX)  NULL,
    CONSTRAINT PK_Inspection_Round PRIMARY KEY (inspection_id),
    CONSTRAINT FK_IR_Site          FOREIGN KEY (site_id)
        REFERENCES Energy_Site(site_id),
    CONSTRAINT FK_IR_Tech          FOREIGN KEY (technician_id)
        REFERENCES Technician(technician_id)
);
GO

-- ============================================================
-- 7. UNIT_INSPECTION
-- ============================================================
CREATE TABLE Unit_Inspection (
    unit_inspection_id  INT           NOT NULL IDENTITY(1,1),
    inspection_id       INT           NOT NULL,
    unit_id             INT           NOT NULL,
    efficiency_reading  DECIMAL(5,2)  NOT NULL,
    unit_status         VARCHAR(30)   NOT NULL,
    remarks             VARCHAR(MAX)  NULL,
    CONSTRAINT PK_Unit_Inspection  PRIMARY KEY (unit_inspection_id),
    CONSTRAINT UQ_UI_InspUnit      UNIQUE      (inspection_id, unit_id),
    CONSTRAINT FK_UI_Inspection    FOREIGN KEY (inspection_id)
        REFERENCES Inspection_Round(inspection_id)
        ON DELETE CASCADE,
    CONSTRAINT FK_UI_Unit          FOREIGN KEY (unit_id)
        REFERENCES Power_Unit(unit_id)
);
GO

-- ============================================================
-- 8. SPARE_PART
-- ============================================================
CREATE TABLE Spare_Part (
    part_id           INT           NOT NULL IDENTITY(1,1),
    part_name         VARCHAR(100)  NOT NULL,
    part_number       VARCHAR(100)  NOT NULL,
    compatible_types  VARCHAR(255)  NULL,
    unit_of_measure   VARCHAR(20)   NOT NULL CONSTRAINT DF_SP_UOM     DEFAULT 'piece',
    quantity_in_stock INT           NOT NULL CONSTRAINT DF_SP_Stock   DEFAULT 0,
    reorder_level     INT           NOT NULL CONSTRAINT DF_SP_Reorder DEFAULT 5,
    supplier          VARCHAR(150)  NULL,
    CONSTRAINT PK_Spare_Part   PRIMARY KEY (part_id),
    CONSTRAINT UQ_SP_PartNum   UNIQUE      (part_number),
    CONSTRAINT CHK_Stock       CHECK       (quantity_in_stock >= 0)
);
GO

-- ============================================================
-- 9. COMPONENT_REPLACEMENT
-- ============================================================
CREATE TABLE Component_Replacement (
    replacement_id      INT           NOT NULL IDENTITY(1,1),
    unit_inspection_id  INT           NOT NULL,
    part_id             INT           NOT NULL,
    part_serial_number  VARCHAR(100)  NOT NULL,
    replacement_date    DATE          NOT NULL,
    quantity_used       INT           NOT NULL CONSTRAINT DF_CR_Qty DEFAULT 1,
    notes               VARCHAR(MAX)  NULL,
    CONSTRAINT PK_Component_Replacement PRIMARY KEY (replacement_id),
    CONSTRAINT CHK_Qty                  CHECK       (quantity_used > 0),
    CONSTRAINT FK_CR_UnitInspection     FOREIGN KEY (unit_inspection_id)
        REFERENCES Unit_Inspection(unit_inspection_id),
    CONSTRAINT FK_CR_SparePart          FOREIGN KEY (part_id)
        REFERENCES Spare_Part(part_id)
);
GO

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX IDX_PU_Manufacturer ON Power_Unit(manufacturer);
CREATE INDEX IDX_UI_Efficiency   ON Unit_Inspection(efficiency_reading);
CREATE INDEX IDX_IR_SiteDate     ON Inspection_Round(site_id, conducted_date);
CREATE INDEX IDX_IR_TechDate     ON Inspection_Round(technician_id, conducted_date);
CREATE INDEX IDX_CR_Date         ON Component_Replacement(replacement_date);
CREATE INDEX IDX_UI_Unit         ON Unit_Inspection(unit_id);
GO