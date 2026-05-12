from backend.db_connection import get_connection
from datetime import datetime, timedelta


def get_last_month_range():
    """First and last calendar day of the previous month (YYYY-MM-DD)."""
    today = datetime.now()
    first_day_current_month = datetime(today.year, today.month, 1)
    last_month_end = first_day_current_month - timedelta(days=1)
    last_month_start = datetime(last_month_end.year, last_month_end.month, 1)
    return last_month_start.strftime("%Y-%m-%d"), last_month_end.strftime("%Y-%m-%d")


# ==================================================
# INQUIRY 1
# ==================================================
def query_manufacturer_most_below_avg():
    """Manufacturer with the most efficiency readings strictly below the global average."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT TOP 1 pu.manufacturer, COUNT(*) AS below_avg_count
        FROM Power_Unit pu
        INNER JOIN Unit_Inspection ui ON pu.unit_id = ui.unit_id
        WHERE ui.efficiency_reading < (SELECT AVG(efficiency_reading) FROM Unit_Inspection)
        GROUP BY pu.manufacturer
        ORDER BY below_avg_count DESC
        """
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"manufacturer": row[0], "below_average_count": row[1]}
    return None


# ==================================================
# INQUIRY 2
# ==================================================
def query_sites_with_no_inspection_last_month():
    """Sites with no completed inspection round in the previous calendar month."""
    start, end = get_last_month_range()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT es.site_id, es.site_name
        FROM Energy_Site es
        WHERE es.site_id NOT IN (
            SELECT DISTINCT ir.site_id
            FROM Inspection_Round ir
            WHERE ir.status = 'Completed'
              AND ir.conducted_date BETWEEN ? AND ?
        )
        """,
        (start, end),
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"site_id": row[0], "site_name": row[1]} for row in rows]


# ==================================================
# INQUIRY 3
# ==================================================
def query_technician_max_inspections_last_month():
    """Technician with the most completed inspection rounds last month."""
    start, end = get_last_month_range()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT TOP 1 t.technician_id, t.first_name, t.last_name, COUNT(*) AS inspection_count
        FROM Inspection_Round ir
        INNER JOIN Technician t ON ir.technician_id = t.technician_id
        WHERE ir.status = 'Completed'
          AND ir.conducted_date BETWEEN ? AND ?
        GROUP BY t.technician_id, t.first_name, t.last_name
        ORDER BY inspection_count DESC
        """,
        (start, end),
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "technician_id": row[0],
            "name": f"{row[1]} {row[2]}",
            "inspection_count": row[3],
        }
    return None


# ==================================================
# INQUIRY 4
# ==================================================
def query_units_without_component_replacement_last_month():
    """Power units that had no component replacement recorded in the previous calendar month."""
    start, end = get_last_month_range()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT pu.unit_id, pu.unit_type, pu.status
        FROM Power_Unit pu
        WHERE pu.unit_id NOT IN (
            SELECT DISTINCT ui.unit_id
            FROM Unit_Inspection ui
            INNER JOIN Component_Replacement cr ON ui.unit_inspection_id = cr.unit_inspection_id
            WHERE cr.replacement_date BETWEEN ? AND ?
        )
        """,
        (start, end),
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"unit_id": row[0], "unit_type": row[1], "status": row[2]} for row in rows]


# ==================================================
# INQUIRY 5
# ==================================================
def query_components_installed_last_month():
    """Component replacements (spare parts) per site in the previous calendar month."""
    start, end = get_last_month_range()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT es.site_id,
               es.site_name,
               cr.replacement_id,
               sp.part_name,
               sp.part_number,
               cr.replacement_date
        FROM Component_Replacement cr
        INNER JOIN Unit_Inspection ui ON cr.unit_inspection_id = ui.unit_inspection_id
        INNER JOIN Power_Unit pu ON ui.unit_id = pu.unit_id
        INNER JOIN Energy_Site es ON pu.site_id = es.site_id
        INNER JOIN Spare_Part sp ON cr.part_id = sp.part_id
        WHERE cr.replacement_date BETWEEN ? AND ?
        ORDER BY es.site_name, cr.replacement_date
        """,
        (start, end),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "site_id": row[0],
            "site_name": row[1],
            "component_id": row[2],
            "component_name": row[3],
            "category": row[4],
            "replacement_date": str(row[5]),
        }
        for row in rows
    ]


# ==================================================
# INQUIRY 6
# ==================================================
def query_technician_profile_and_units_inspected():
    """Technician profile fields and count of distinct units inspected (via inspection rounds)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT t.technician_id,
               t.first_name,
               t.last_name,
               t.email,
               t.phone,
               t.hire_date,
               t.employment_status,
               COUNT(DISTINCT ui.unit_id) AS total_units_inspected
        FROM Technician t
        LEFT JOIN Inspection_Round ir ON t.technician_id = ir.technician_id
        LEFT JOIN Unit_Inspection ui ON ir.inspection_id = ui.inspection_id
        GROUP BY t.technician_id, t.first_name, t.last_name, t.email, t.phone, t.hire_date, t.employment_status
        ORDER BY t.technician_id
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "technician_id": row[0],
            "first_name": row[1],
            "last_name": row[2],
            "email": row[3],
            "phone": row[4],
            "hire_date": str(row[5]) if row[5] is not None else None,
            "employment_status": row[6],
            "total_units_inspected": row[7],
        }
        for row in rows
    ]


# ==================================================
# AGGREGATES FOR CHARTING
# These return full lists where the corresponding top-level inquiry only
# returns a single winner — the table view still shows that winner, but the
# Reports → Chart tab needs the distribution.
# ==================================================
def query_manufacturer_below_avg_counts():
    """All manufacturers + how many of their efficiency readings are strictly
    below the global average. Sorted high → low so a bar chart reads naturally."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT pu.manufacturer, COUNT(*) AS below_avg_count
        FROM Power_Unit pu
        INNER JOIN Unit_Inspection ui ON pu.unit_id = ui.unit_id
        WHERE ui.efficiency_reading < (SELECT AVG(efficiency_reading) FROM Unit_Inspection)
        GROUP BY pu.manufacturer
        ORDER BY below_avg_count DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"manufacturer": r[0], "below_average_count": r[1]} for r in rows]


def query_technician_inspection_counts_last_month():
    """Every technician's count of completed inspection rounds last month —
    not just the winner. Zero-count techs are included so the bar chart shows
    the full team."""
    start, end = get_last_month_range()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT t.technician_id,
               t.first_name + ' ' + t.last_name AS full_name,
               COUNT(ir.inspection_id) AS inspection_count
        FROM Technician t
        LEFT JOIN Inspection_Round ir
            ON  ir.technician_id = t.technician_id
            AND ir.status = 'Completed'
            AND ir.conducted_date BETWEEN ? AND ?
        GROUP BY t.technician_id, t.first_name, t.last_name
        ORDER BY inspection_count DESC, t.technician_id
        """,
        (start, end),
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"technician_id": r[0], "name": r[1], "inspection_count": r[2]} for r in rows]


def query_total_site_count():
    """Total number of Energy_Site rows — for the 'inspected vs not' donut."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Energy_Site")
    n = cursor.fetchone()[0]
    conn.close()
    return int(n)


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
        "inquiry_6": query_technician_profile_and_units_inspected(),
    }