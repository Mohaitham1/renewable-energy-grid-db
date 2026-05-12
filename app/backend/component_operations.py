from backend.db_connection import get_connection


def get_all_components():
    """List component replacements with site and spare part context."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cr.replacement_id,
               sp.part_name,
               sp.part_number,
               es.site_name,
               pu.unit_type,
               cr.replacement_date
        FROM Component_Replacement cr
        INNER JOIN Unit_Inspection ui ON cr.unit_inspection_id = ui.unit_inspection_id
        INNER JOIN Power_Unit pu ON ui.unit_id = pu.unit_id
        INNER JOIN Energy_Site es ON pu.site_id = es.site_id
        INNER JOIN Spare_Part sp ON cr.part_id = sp.part_id
    """)
    rows = cursor.fetchall()
    conn.close()
    return [tuple(row) for row in rows]


def _resolve_part_id(cursor, part_name_or_number):
    cursor.execute(
        """
        SELECT part_id FROM Spare_Part
        WHERE part_name = ? OR part_number = ?
        """,
        (part_name_or_number, part_name_or_number),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def _resolve_latest_unit_inspection_id(cursor, site_name):
    cursor.execute(
        """
        SELECT TOP 1 ui.unit_inspection_id
        FROM Unit_Inspection ui
        INNER JOIN Power_Unit pu ON ui.unit_id = pu.unit_id
        INNER JOIN Energy_Site es ON pu.site_id = es.site_id
        WHERE es.site_name = ?
        ORDER BY ui.unit_inspection_id DESC
        """,
        (site_name,),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def add_component(part_name_or_number, site_name, part_serial_number, replacement_date, quantity_used, notes=None):
    """
    Inserts a Component_Replacement row using the latest Unit_Inspection at the given site
    and a spare part matched by name or part number.
    """
    conn = get_connection()
    cursor = conn.cursor()
    part_id = _resolve_part_id(cursor, part_name_or_number)
    unit_inspection_id = _resolve_latest_unit_inspection_id(cursor, site_name)
    if part_id is None or unit_inspection_id is None:
        conn.close()
        return False

    cursor.execute(
        """
        INSERT INTO Component_Replacement
            (unit_inspection_id, part_id, part_serial_number, replacement_date, quantity_used, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (unit_inspection_id, part_id, part_serial_number, replacement_date, quantity_used, notes),
    )
    conn.commit()
    conn.close()
    return True


def delete_component(replacement_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Component_Replacement WHERE replacement_id = ?", (replacement_id,))
    conn.commit()
    conn.close()
    return True


def update_component(replacement_id, part_name_or_number, site_name, part_serial_number, replacement_date, quantity_used, notes=None):
    conn = get_connection()
    cursor = conn.cursor()
    part_id = _resolve_part_id(cursor, part_name_or_number)
    unit_inspection_id = _resolve_latest_unit_inspection_id(cursor, site_name)
    if part_id is None or unit_inspection_id is None:
        conn.close()
        return False

    cursor.execute(
        """
        UPDATE Component_Replacement
        SET unit_inspection_id = ?, part_id = ?, part_serial_number = ?, replacement_date = ?, quantity_used = ?, notes = ?
        WHERE replacement_id = ?
        """,
        (
            unit_inspection_id,
            part_id,
            part_serial_number,
            replacement_date,
            quantity_used,
            notes,
            replacement_id,
        ),
    )
    conn.commit()
    conn.close()
    return True


def search_components(keyword):
    conn = get_connection()
    cursor = conn.cursor()
    like = f"%{keyword}%"
    cursor.execute(
        """
        SELECT cr.replacement_id,
               sp.part_name,
               sp.part_number,
               es.site_name,
               pu.unit_type,
               cr.replacement_date
        FROM Component_Replacement cr
        INNER JOIN Unit_Inspection ui ON cr.unit_inspection_id = ui.unit_inspection_id
        INNER JOIN Power_Unit pu ON ui.unit_id = pu.unit_id
        INNER JOIN Energy_Site es ON pu.site_id = es.site_id
        INNER JOIN Spare_Part sp ON cr.part_id = sp.part_id
        WHERE sp.part_name LIKE ? OR sp.part_number LIKE ? OR es.site_name LIKE ? OR CAST(cr.replacement_id AS VARCHAR) LIKE ?
        """,
        (like, like, like, like),
    )
    rows = cursor.fetchall()
    conn.close()
    return [tuple(row) for row in rows]
