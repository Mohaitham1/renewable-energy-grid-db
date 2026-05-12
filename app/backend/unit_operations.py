from backend.db_connection import get_connection


def get_all_units():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pu.unit_id, es.site_name, pu.unit_type, pu.status, pu.max_kwatt_output
        FROM Power_Unit pu
        INNER JOIN Energy_Site es ON pu.site_id = es.site_id
    """)
    rows = cursor.fetchall()
    conn.close()
    return [tuple(row) for row in rows]


def add_unit(site_name, unit_type, manufacturer, model, installation_date, max_kwatt_output, status, serial_number=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT site_id FROM Energy_Site WHERE site_name = ?", (site_name,))
    site_row = cursor.fetchone()
    if not site_row:
        conn.close()
        return False
    site_id = site_row[0]

    cursor.execute("""
        INSERT INTO Power_Unit (site_id, unit_type, manufacturer, model, installation_date, max_kwatt_output, status, serial_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (site_id, unit_type, manufacturer, model, installation_date, max_kwatt_output, status, serial_number))
    conn.commit()
    conn.close()
    return True


def delete_unit(unit_id):
    """Delete a unit and all dependent records.

    FK chain: Power_Unit <- Unit_Inspection <- Component_Replacement.
    Neither cascades, so we must clean from the leaf up.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            DELETE FROM Component_Replacement
            WHERE unit_inspection_id IN (
                SELECT unit_inspection_id FROM Unit_Inspection WHERE unit_id = ?
            )
            """,
            (unit_id,),
        )
        cursor.execute("DELETE FROM Unit_Inspection WHERE unit_id = ?", (unit_id,))
        cursor.execute("DELETE FROM Power_Unit WHERE unit_id = ?", (unit_id,))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_unit(unit_id, site_name, unit_type, manufacturer, model, installation_date, max_kwatt_output, status, serial_number=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT site_id FROM Energy_Site WHERE site_name = ?", (site_name,))
    site_row = cursor.fetchone()
    if not site_row:
        conn.close()
        return False
    site_id = site_row[0]

    cursor.execute("""
        UPDATE Power_Unit
        SET site_id = ?, unit_type = ?, manufacturer = ?, model = ?, installation_date = ?,
            max_kwatt_output = ?, status = ?, serial_number = ?
        WHERE unit_id = ?
    """, (site_id, unit_type, manufacturer, model, installation_date, max_kwatt_output, status, serial_number, unit_id))
    conn.commit()
    conn.close()
    return True


def search_units(keyword):
    conn = get_connection()
    cursor = conn.cursor()
    like = f"%{keyword}%"
    cursor.execute("""
        SELECT pu.unit_id, es.site_name, pu.unit_type, pu.status, pu.max_kwatt_output
        FROM Power_Unit pu
        INNER JOIN Energy_Site es ON pu.site_id = es.site_id
        WHERE es.site_name LIKE ? OR pu.unit_type LIKE ? OR pu.status LIKE ? OR pu.manufacturer LIKE ?
    """, (like, like, like, like))
    rows = cursor.fetchall()
    conn.close()
    return [tuple(row) for row in rows]