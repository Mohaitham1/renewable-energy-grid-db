from backend.db_connection import get_connection


def _resolve_technician_id(cursor, name_or_id):
    """Resolve a Technician row.id from any of: a raw int, a numeric string,
    a "#N - First Last" dropdown label, or a plain "First Last" name.

    Name matching is whitespace-tolerant on both sides (LTRIM/RTRIM in SQL +
    normalized whitespace in Python), so a stray trailing space in either the
    DB row or the UI value won't break the lookup.
    """
    if isinstance(name_or_id, int):
        cursor.execute("SELECT technician_id FROM Technician WHERE technician_id = ?", (name_or_id,))
        row = cursor.fetchone()
        return row[0] if row else None

    s = (name_or_id or "").strip()
    if not s:
        return None

    # Dropdown label like "#3 - John Smith" → grab the id directly.
    if s.startswith("#"):
        head = s[1:].split(" ", 1)[0].strip()
        if head.isdigit():
            cursor.execute("SELECT technician_id FROM Technician WHERE technician_id = ?", (int(head),))
            row = cursor.fetchone()
            if row:
                return row[0]

    # Bare integer (e.g. user typed "3").
    if s.isdigit():
        cursor.execute("SELECT technician_id FROM Technician WHERE technician_id = ?", (int(s),))
        row = cursor.fetchone()
        if row:
            return row[0]

    # Name match — collapse internal whitespace and trim DB-side.
    normalized = " ".join(s.split())
    parts = normalized.split(" ", 1)
    first = parts[0]
    last = parts[1] if len(parts) > 1 else ""
    cursor.execute(
        """
        SELECT technician_id FROM Technician
        WHERE LTRIM(RTRIM(first_name)) = LTRIM(RTRIM(?))
          AND LTRIM(RTRIM(last_name))  = LTRIM(RTRIM(?))
        """,
        (first, last),
    )
    row = cursor.fetchone()
    if row:
        return row[0]

    # Last-ditch: full-name concat compare, also trimmed.
    cursor.execute(
        """
        SELECT technician_id FROM Technician
        WHERE LTRIM(RTRIM(first_name + ' ' + last_name)) = LTRIM(RTRIM(?))
        """,
        (normalized,),
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
    try:
        site_id = _site_id_for_unit(cursor, unit_id)
        if site_id is None:
            raise ValueError(
                f"Power_Unit id={unit_id} not found. Pick a unit from the dropdown — "
                f"its parent site is what anchors the inspection round."
            )
        tech_id = _resolve_technician_id(cursor, technician_full_name)
        if tech_id is None:
            raise ValueError(
                f"Technician '{technician_full_name}' not found. Pick a technician "
                f"from the dropdown (whitespace and IDs are tolerated)."
            )

        notes = remarks if remarks is not None else ""
        # Use OUTPUT INSERTED.inspection_id rather than a two-step
        # INSERT + SELECT SCOPE_IDENTITY(). Reasons:
        #   1. Single statement — there is no second cursor.execute boundary
        #      where pyodbc might consume an interim result set and leave
        #      SCOPE_IDENTITY() pointing at the wrong scope.
        #   2. Immune to AFTER/INSTEAD OF triggers reseating the identity scope.
        #   3. Returns the value as a real result row, which fetchone() reads
        #      directly — no CAST or extra round-trip needed.
        cursor.execute(
            """
            INSERT INTO Inspection_Round (site_id, technician_id, scheduled_date, conducted_date, status, notes)
            OUTPUT INSERTED.inspection_id
            VALUES (?, ?, ?, ?, 'Completed', ?)
            """,
            (site_id, tech_id, inspection_date, inspection_date, notes),
        )
        insp_row = cursor.fetchone()
        if not insp_row or insp_row[0] is None:
            raise RuntimeError(
                "Inspection_Round INSERT did not return an inspection_id via "
                "OUTPUT INSERTED. The row was not created — check FK validity "
                "for site_id/technician_id and any newly-added triggers."
            )
        inspection_id = insp_row[0]

        cursor.execute(
            """
            INSERT INTO Unit_Inspection (inspection_id, unit_id, efficiency_reading, unit_status, remarks)
            VALUES (?, ?, ?, ?, ?)
            """,
            (inspection_id, unit_id, efficiency_reading, unit_status, notes),
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_inspection(unit_inspection_id):
    """Delete a Unit_Inspection (and its Component_Replacement children), then
    clean up the parent Inspection_Round if it has no remaining inspections.

    add_inspection writes one Inspection_Round per Unit_Inspection, so without
    this cleanup we'd accumulate orphan rounds that still anchor FKs and clutter
    Inspections-on-site lookups.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT inspection_id FROM Unit_Inspection WHERE unit_inspection_id = ?",
            (unit_inspection_id,),
        )
        row = cursor.fetchone()
        if not row:
            # Nothing to delete — surface that to the caller so the UI can
            # show a sensible message instead of pretending success.
            return False
        inspection_id = row[0]

        cursor.execute(
            "DELETE FROM Component_Replacement WHERE unit_inspection_id = ?",
            (unit_inspection_id,),
        )
        cursor.execute(
            "DELETE FROM Unit_Inspection WHERE unit_inspection_id = ?",
            (unit_inspection_id,),
        )
        affected = cursor.rowcount

        # Only drop the round if it's now childless. If a future workflow puts
        # multiple Unit_Inspection rows under one round, we must not nuke the
        # siblings via the FK_UI_Inspection ON DELETE CASCADE side effect.
        cursor.execute(
            "SELECT COUNT(*) FROM Unit_Inspection WHERE inspection_id = ?",
            (inspection_id,),
        )
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "DELETE FROM Inspection_Round WHERE inspection_id = ?",
                (inspection_id,),
            )

        conn.commit()
        return affected > 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


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