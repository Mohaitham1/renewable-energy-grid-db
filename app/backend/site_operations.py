from backend.db_connection import get_connection


def get_all_sites():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT site_id, site_name, latitude, longitude, terrain_type, region, country, established_date
        FROM Energy_Site
    """)
    rows = cursor.fetchall()
    conn.close()
    return [tuple(row) for row in rows]


def add_site(site_name, latitude, longitude, terrain_type, region, country, established_date=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Energy_Site (site_name, latitude, longitude, terrain_type, region, country, established_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (site_name, latitude, longitude, terrain_type, region, country, established_date))
    conn.commit()
    conn.close()
    return True


def delete_site(site_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Energy_Site WHERE site_id = ?", (site_id,))
    conn.commit()
    conn.close()
    return True


def update_site(site_id, site_name, latitude, longitude, terrain_type, region, country, established_date=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Energy_Site
        SET site_name = ?, latitude = ?, longitude = ?, terrain_type = ?, region = ?, country = ?, established_date = ?
        WHERE site_id = ?
    """, (site_name, latitude, longitude, terrain_type, region, country, established_date, site_id))
    conn.commit()
    conn.close()
    return True


def search_sites(keyword):
    conn = get_connection()
    cursor = conn.cursor()
    like = f"%{keyword}%"
    cursor.execute("""
        SELECT site_id, site_name, latitude, longitude, terrain_type, region, country, established_date
        FROM Energy_Site
        WHERE site_name LIKE ? OR region LIKE ? OR country LIKE ? OR terrain_type LIKE ?
    """, (like, like, like, like))
    rows = cursor.fetchall()
    conn.close()
    return [tuple(row) for row in rows]
