from backend.db_connection import get_connection

def get_all_units():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Unit_ID, Site_Name, Unit_Type, Status, Output_kW
        FROM Power_Unit pu
        JOIN Energy_Site es ON pu.Site_ID = es.Site_ID
    """)
    rows = cursor.fetchall()
    conn.close()
    return [(row[0], row[1], row[2], row[3], row[4]) for row in rows]

def add_unit(site_name, unit_type, status, output):
    conn = get_connection()
    cursor = conn.cursor()
    # First get Site_ID from site name
    cursor.execute("SELECT Site_ID FROM Energy_Site WHERE Site_Name = ?", (site_name,))
    site_row = cursor.fetchone()
    if not site_row:
        conn.close()
        return False
    site_id = site_row[0]
    
    cursor.execute("""
        INSERT INTO Power_Unit (Site_ID, Unit_Type, Status, Output_kW)
        VALUES (?, ?, ?, ?)
    """, (site_id, unit_type, status, output))
    conn.commit()
    conn.close()
    return True

def delete_unit(unit_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Power_Unit WHERE Unit_ID = ?", (unit_id,))
    conn.commit()
    conn.close()
    return True

def update_unit(unit_id, site_name, unit_type, status, output):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Site_ID FROM Energy_Site WHERE Site_Name = ?", (site_name,))
    site_row = cursor.fetchone()
    if not site_row:
        conn.close()
        return False
    site_id = site_row[0]
    
    cursor.execute("""
        UPDATE Power_Unit
        SET Site_ID = ?, Unit_Type = ?, Status = ?, Output_kW = ?
        WHERE Unit_ID = ?
    """, (site_id, unit_type, status, output, unit_id))
    conn.commit()
    conn.close()
    return True

def search_units(keyword):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Unit_ID, Site_Name, Unit_Type, Status, Output_kW
        FROM Power_Unit pu
        JOIN Energy_Site es ON pu.Site_ID = es.Site_ID
        WHERE Site_Name LIKE ? OR Unit_Type LIKE ? OR Status LIKE ?
    """, (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
    rows = cursor.fetchall()
    conn.close()
    return [(row[0], row[1], row[2], row[3], row[4]) for row in rows]