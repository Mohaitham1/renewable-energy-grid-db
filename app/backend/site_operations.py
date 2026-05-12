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
    """Delete a site and all dependent records.

    FK chain (none cascade automatically):
        Energy_Site <- Power_Unit <- Unit_Inspection <- Component_Replacement
        Energy_Site <- Inspection_Round -> Unit_Inspection (cascade on round)
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            DELETE FROM Component_Replacement
            WHERE unit_inspection_id IN (
                SELECT ui.unit_inspection_id
                FROM Unit_Inspection ui
                INNER JOIN Power_Unit pu ON ui.unit_id = pu.unit_id
                WHERE pu.site_id = ?
            )
            """,
            (site_id,),
        )
        cursor.execute(
            """
            DELETE FROM Unit_Inspection
            WHERE unit_id IN (SELECT unit_id FROM Power_Unit WHERE site_id = ?)
            """,
            (site_id,),
        )
        cursor.execute(
            "DELETE FROM Inspection_Round WHERE site_id = ?", (site_id,)
        )
        cursor.execute(
            "DELETE FROM Power_Unit WHERE site_id = ?", (site_id,)
        )
        cursor.execute("DELETE FROM Energy_Site WHERE site_id = ?", (site_id,))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


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