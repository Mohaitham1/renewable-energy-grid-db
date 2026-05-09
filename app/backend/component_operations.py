from backend.db_connection import get_connection

def get_all_components():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Component_ID, Component_Name, Category, Site_Name, Condition_Status
        FROM Component c
        JOIN Power_Unit pu ON c.Unit_ID = pu.Unit_ID
        JOIN Energy_Site es ON pu.Site_ID = es.Site_ID
    """)
    rows = cursor.fetchall()
    conn.close()
    return [(row[0], row[1], row[2], row[3], row[4]) for row in rows]

def add_component(name, category, site_name, status):
    conn = get_connection()
    cursor = conn.cursor()
    # Need Unit_ID from site name (take first unit in that site)
    cursor.execute("""
        SELECT TOP 1 pu.Unit_ID
        FROM Power_Unit pu
        JOIN Energy_Site es ON pu.Site_ID = es.Site_ID
        WHERE es.Site_Name = ?
    """, (site_name,))
    unit_row = cursor.fetchone()
    if not unit_row:
        conn.close()
        return False
    unit_id = unit_row[0]
    
    cursor.execute("""
        INSERT INTO Component (Component_Name, Category, Unit_ID, Condition_Status)
        VALUES (?, ?, ?, ?)
    """, (name, category, unit_id, status))
    conn.commit()
    conn.close()
    return True

def delete_component(component_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Component WHERE Component_ID = ?", (component_id,))
    conn.commit()
    conn.close()
    return True

def update_component(component_id, name, category, site_name, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TOP 1 pu.Unit_ID
        FROM Power_Unit pu
        JOIN Energy_Site es ON pu.Site_ID = es.Site_ID
        WHERE es.Site_Name = ?
    """, (site_name,))
    unit_row = cursor.fetchone()
    if not unit_row:
        conn.close()
        return False
    unit_id = unit_row[0]
    
    cursor.execute("""
        UPDATE Component
        SET Component_Name = ?, Category = ?, Unit_ID = ?, Condition_Status = ?
        WHERE Component_ID = ?
    """, (name, category, unit_id, status, component_id))
    conn.commit()
    conn.close()
    return True

def search_components(keyword):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Component_ID, Component_Name, Category, Site_Name, Condition_Status
        FROM Component c
        JOIN Power_Unit pu ON c.Unit_ID = pu.Unit_ID
        JOIN Energy_Site es ON pu.Site_ID = es.Site_ID
        WHERE Component_Name LIKE ? OR Category LIKE ? OR Site_Name LIKE ? OR Condition_Status LIKE ?
    """, (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
    rows = cursor.fetchall()
    conn.close()
    return [(row[0], row[1], row[2], row[3], row[4]) for row in rows]