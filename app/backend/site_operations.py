from backend.db_connection import get_connection

def get_all_sites():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Site_ID, Site_Name, Energy_Type, Location, Capacity
        FROM Energy_Site
    """)
    rows = cursor.fetchall()
    conn.close()
    return [(row[0], row[1], row[2], row[3], row[4]) for row in rows]

def add_site(name, energy_type, location, capacity):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Energy_Site (Site_Name, Energy_Type, Location, Capacity)
        VALUES (?, ?, ?, ?)
    """, (name, energy_type, location, capacity))
    conn.commit()
    conn.close()
    return True

def delete_site(site_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Energy_Site WHERE Site_ID = ?", (site_id,))
    conn.commit()
    conn.close()
    return True

def update_site(site_id, name, energy_type, location, capacity):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Energy_Site
        SET Site_Name = ?, Energy_Type = ?, Location = ?, Capacity = ?
        WHERE Site_ID = ?
    """, (name, energy_type, location, capacity, site_id))
    conn.commit()
    conn.close()
    return True

def search_sites(keyword):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Site_ID, Site_Name, Energy_Type, Location, Capacity
        FROM Energy_Site
        WHERE Site_Name LIKE ? OR Location LIKE ? OR Energy_Type LIKE ?
    """, (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
    rows = cursor.fetchall()
    conn.close()
    return [(row[0], row[1], row[2], row[3], row[4]) for row in rows]