from backend.db_connection import get_connection
from datetime import datetime, timedelta

def get_last_month_range():
    today = datetime.now()
    first_day_current_month = datetime(today.year, today.month, 1)
    last_month_end = first_day_current_month - timedelta(days=1)
    last_month_start = datetime(last_month_end.year, last_month_end.month, 1)
    return last_month_start.strftime('%Y-%m-%d'), last_month_end.strftime('%Y-%m-%d')

# ==================================================
# INQUIRY 1
# ==================================================
def query_manufacturer_most_below_avg():
    """Which power unit manufacturer had the highest number of efficiency readings below average?"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TOP 1 Manufacturer, COUNT(*) AS BelowAvgCount
        FROM Power_Unit pu
        JOIN Unit_Reading ur ON pu.Unit_ID = ur.Unit_ID
        WHERE ur.Efficiency_Reading < (SELECT AVG(Efficiency_Reading) FROM Unit_Reading)
        GROUP BY Manufacturer
        ORDER BY BelowAvgCount DESC
    """)
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"manufacturer": row[0], "below_average_count": row[1]}
    return None

# ==================================================
# INQUIRY 2
# ==================================================
def query_sites_with_no_inspection_last_month():
    """Which energy site had no inspection rounds conducted during the last month?"""
    start, end = get_last_month_range()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Site_ID, Site_Name
        FROM Energy_Site
        WHERE Site_ID NOT IN (
            SELECT DISTINCT Site_ID
            FROM Inspection_Round
            WHERE Inspection_Date BETWEEN ? AND ?
        )
    """, (start, end))
    rows = cursor.fetchall()
    conn.close()
    return [{"site_id": row[0], "site_name": row[1]} for row in rows]

# ==================================================
# INQUIRY 3
# ==================================================
def query_technician_max_inspections_last_month():
    """Who was the technician who completed the maximum number of inspections last month?"""
    start, end = get_last_month_range()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TOP 1 t.Technician_ID, t.First_Name, t.Last_Name, COUNT(*) AS InspectionCount
        FROM Inspection_Round ir
        JOIN Technician t ON ir.Technician_ID = t.Technician_ID
        WHERE ir.Inspection_Date BETWEEN ? AND ?
        GROUP BY t.Technician_ID, t.First_Name, t.Last_Name
        ORDER BY InspectionCount DESC
    """, (start, end))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"technician_id": row[0], "name": f"{row[1]} {row[2]}", "inspection_count": row[3]}
    return None

# ==================================================
# INQUIRY 4
# ==================================================
def query_units_without_component_replacement_last_month():
    """Identify power units that did not require any component replacements last month."""
    start, end = get_last_month_range()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Unit_ID, Unit_Type, Status
        FROM Power_Unit
        WHERE Unit_ID NOT IN (
            SELECT DISTINCT Unit_ID
            FROM Component
            WHERE Replacement_Date BETWEEN ? AND ?
        )
    """, (start, end))
    rows = cursor.fetchall()
    conn.close()
    return [{"unit_id": row[0], "unit_type": row[1], "status": row[2]} for row in rows]

# ==================================================
# INQUIRY 5
# ==================================================
def query_components_installed_last_month():
    """What were the specific components installed at each energy site last month?"""
    start, end = get_last_month_range()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT es.Site_ID, es.Site_Name, c.Component_ID, c.Component_Name, c.Category, c.Replacement_Date
        FROM Energy_Site es
        JOIN Power_Unit pu ON es.Site_ID = pu.Site_ID
        JOIN Component c ON pu.Unit_ID = c.Unit_ID
        WHERE c.Replacement_Date BETWEEN ? AND ?
        ORDER BY es.Site_Name, c.Replacement_Date
    """, (start, end))
    rows = cursor.fetchall()
    conn.close()
    return [{
        "site_id": row[0],
        "site_name": row[1],
        "component_id": row[2],
        "component_name": row[3],
        "category": row[4],
        "replacement_date": str(row[5])
    } for row in rows]

# ==================================================
# INQUIRY 6
# ==================================================
def query_technician_profile_and_units_inspected():
    """For each technician, retrieve their profile and the total number of power units they inspected."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            t.Technician_ID,
            t.First_Name,
            t.Last_Name,
            t.Specialty,
            t.Certification,
            t.Status,
            COUNT(DISTINCT ur.Unit_ID) AS TotalUnitsInspected
        FROM Technician t
        LEFT JOIN Inspection_Round ir ON t.Technician_ID = ir.Technician_ID
        LEFT JOIN Unit_Reading ur ON ir.Inspection_ID = ur.Inspection_ID
        GROUP BY t.Technician_ID, t.First_Name, t.Last_Name, t.Specialty, t.Certification, t.Status
        ORDER BY t.Technician_ID
    """)
    rows = cursor.fetchall()
    conn.close()
    return [{
        "technician_id": row[0],
        "first_name": row[1],
        "last_name": row[2],
        "specialty": row[3],
        "certification": row[4],
        "status": row[5],
        "total_units_inspected": row[6]
    } for row in rows]

# ==================================================
# HELPER: Run all queries at once (for dashboard)
# ==================================================
def run_all_queries():
    return {
        "inquiry_1": query_manufacturer_most_below_avg(),
        "inquiry_2": query_sites_with_no_inspection_last_month(),
        "inquiry_3": query_technician_max_inspections_last_month(),
        "inquiry_4": query_units_without_component_replacement_last_month(),
        "inquiry_5": query_components_installed_last_month(),
        "inquiry_6": query_technician_profile_and_units_inspected()
    }