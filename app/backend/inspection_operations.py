from backend.db_connection import get_connection


def _resolve_technician_id(cursor, full_name):
    parts = full_name.strip().split(" ", 1)
    first = parts[0]
    last = parts[1] if len(parts) > 1 else ""
    cursor.execute(
        """
        SELECT technician_id FROM Technician
        WHERE first_name = ? AND last_name = ?
        """,
        (first, last),
    )
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute(
        """
        SELECT technician_id FROM Technician
        WHERE first_name + ' ' + last_name = ?
        """,
        (full_name.strip(),),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def _site_id_for_unit(cursor, unit_id):
    cursor.execute("SELECT site_id FROM Power_Unit WHERE unit_id = ?", (unit_id,))
    row = cursor.fetchone()
    return row[0] if row else None


def get_all_inspections():
    """
    Rows suitable for a grid: unit_inspection_id, unit_id, technician name, date, unit_status.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT ui.unit_inspection_id,
               ui.unit_id,
               t.first_name + ' ' + t.last_name AS technician_name,
               CONVERT(VARCHAR(10), COALESCE(ir.conducted_date, ir.scheduled_date), 23) AS inspection_date,
               ui.unit_status
        FROM Unit_Inspection ui
        INNER JOIN Inspection_Round ir ON ui.inspection_id = ir.inspection_id
        INNER JOIN Technician t ON ir.technician_id = t.technician_id
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [tuple(row) for row in rows]


def add_inspection(unit_id, technician_full_name, inspection_date, unit_status, efficiency_reading=85.0, remarks=None):
    """
    Creates a completed Inspection_Round for the unit's site and a Unit_Inspection line.
    inspection_date: 'YYYY-MM-DD' string or date accepted by SQL Server.
    """
    conn = get_connection()
    cursor = conn.cursor()
    site_id = _site_id_for_unit(cursor, unit_id)
    tech_id = _resolve_technician_id(cursor, technician_full_name)
    if site_id is None or tech_id is None:
        conn.close()
        return False

    notes = remarks if remarks is not None else ""
    cursor.execute(
        """
        INSERT INTO Inspection_Round (site_id, technician_id, scheduled_date, conducted_date, status, notes)
        VALUES (?, ?, ?, ?, 'Completed', ?)
        """,
        (site_id, tech_id, inspection_date, inspection_date, notes),
    )
    cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
    insp_row = cursor.fetchone()
    if not insp_row or insp_row[0] is None:
        conn.close()
        return False
    inspection_id = insp_row[0]

    cursor.execute(
        """
        INSERT INTO Unit_Inspection (inspection_id, unit_id, efficiency_reading, unit_status, remarks)
        VALUES (?, ?, ?, ?, ?)
        """,
        (inspection_id, unit_id, efficiency_reading, unit_status, notes),
    )
    conn.commit()
    conn.close()
    return True


def delete_inspection(unit_inspection_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM Component_Replacement WHERE unit_inspection_id = ?",
        (unit_inspection_id,),
    )
    cursor.execute("DELETE FROM Unit_Inspection WHERE unit_inspection_id = ?", (unit_inspection_id,))
    conn.commit()
    conn.close()
    return True


def update_inspection(unit_inspection_id, unit_id, technician_full_name, inspection_date, unit_status, efficiency_reading=85.0, remarks=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT inspection_id FROM Unit_Inspection WHERE unit_inspection_id = ?",
        (unit_inspection_id,),
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
    inspection_id = row[0]

    site_id = _site_id_for_unit(cursor, unit_id)
    tech_id = _resolve_technician_id(cursor, technician_full_name)
    if site_id is None or tech_id is None:
        conn.close()
        return False

    notes = remarks if remarks is not None else ""
    cursor.execute(
        """
        UPDATE Inspection_Round
        SET site_id = ?, technician_id = ?, scheduled_date = ?, conducted_date = ?, status = 'Completed', notes = ?
        WHERE inspection_id = ?
        """,
        (site_id, tech_id, inspection_date, inspection_date, notes, inspection_id),
    )
    cursor.execute(
        """
        UPDATE Unit_Inspection
        SET unit_id = ?, efficiency_reading = ?, unit_status = ?, remarks = ?
        WHERE unit_inspection_id = ?
        """,
        (unit_id, efficiency_reading, unit_status, notes, unit_inspection_id),
    )
    conn.commit()
    conn.close()
    return True


def search_inspections(keyword):
    conn = get_connection()
    cursor = conn.cursor()
    like = f"%{keyword}%"
    cursor.execute(
        """
        SELECT ui.unit_inspection_id,
               ui.unit_id,
               t.first_name + ' ' + t.last_name AS technician_name,
               CONVERT(VARCHAR(10), COALESCE(ir.conducted_date, ir.scheduled_date), 23) AS inspection_date,
               ui.unit_status
        FROM Unit_Inspection ui
        INNER JOIN Inspection_Round ir ON ui.inspection_id = ir.inspection_id
        INNER JOIN Technician t ON ir.technician_id = t.technician_id
        WHERE CAST(ui.unit_id AS VARCHAR) LIKE ?
           OR t.first_name LIKE ? OR t.last_name LIKE ?
           OR ui.unit_status LIKE ?
           OR ir.notes LIKE ?
        """,
        (like, like, like, like, like),
    )
    rows = cursor.fetchall()
    conn.close()
    return [tuple(row) for row in rows]
