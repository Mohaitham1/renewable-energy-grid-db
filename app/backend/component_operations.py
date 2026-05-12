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
    """Resolve a Spare_Part.part_id from: a raw int, a numeric string, a
    "#N - …" dropdown label, or a part_name / part_number.

    Trims whitespace on both sides so stray spaces don't break the lookup.
    """
    if isinstance(part_name_or_number, int):
        cursor.execute("SELECT part_id FROM Spare_Part WHERE part_id = ?", (part_name_or_number,))
        row = cursor.fetchone()
        return row[0] if row else None

    s = (part_name_or_number or "").strip()
    if not s:
        return None

    # Dropdown label like "#6 - Inverter Board (INV-204)" → take the id.
    if s.startswith("#"):
        head = s[1:].split(" ", 1)[0].strip()
        if head.isdigit():
            cursor.execute("SELECT part_id FROM Spare_Part WHERE part_id = ?", (int(head),))
            row = cursor.fetchone()
            if row:
                return row[0]

    # Bare numeric → try part_id first, then part_number (some shops use
    # numeric part numbers, so we don't want to silently skip those).
    if s.isdigit():
        cursor.execute("SELECT part_id FROM Spare_Part WHERE part_id = ?", (int(s),))
        row = cursor.fetchone()
        if row:
            return row[0]

    cursor.execute(
        """
        SELECT part_id FROM Spare_Part
        WHERE LTRIM(RTRIM(part_name))   = LTRIM(RTRIM(?))
           OR LTRIM(RTRIM(part_number)) = LTRIM(RTRIM(?))
        """,
        (s, s),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def get_all_spare_parts():
    """Returns (part_id, part_name, part_number, quantity_in_stock) per row,
    ordered so the dropdown shows a stable list."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT part_id, part_name, part_number, quantity_in_stock
            FROM Spare_Part
            ORDER BY part_name, part_id
            """
        )
        rows = cursor.fetchall()
        return [tuple(row) for row in rows]
    finally:
        conn.close()


def add_spare_part(part_name, part_number, compatible_types=None,
                   unit_of_measure="piece", quantity_in_stock=0,
                   reorder_level=5, supplier=None):
    """Insert a Spare_Part row. Lets the Components UI seed parts inline so
    users don't have to leave the screen and SSMS to populate the table."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO Spare_Part
                (part_name, part_number, compatible_types, unit_of_measure,
                 quantity_in_stock, reorder_level, supplier)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (part_name, part_number, compatible_types, unit_of_measure,
             int(quantity_in_stock), int(reorder_level), supplier),
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


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

    Raises ValueError with a specific reason when a prerequisite is missing so the
    UI can surface "the part doesn't exist" vs "no inspection on this site yet"
    distinctly, instead of a generic failure.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        part_id = _resolve_part_id(cursor, part_name_or_number)
        if part_id is None:
            raise ValueError(
                f"Spare part '{part_name_or_number}' was not found. "
                f"Add it to Spare_Part first (matched on part_name or part_number)."
            )
        unit_inspection_id = _resolve_latest_unit_inspection_id(cursor, site_name)
        if unit_inspection_id is None:
            raise ValueError(
                f"No Unit_Inspection exists for site '{site_name}'. "
                f"Log an inspection on a unit at this site before recording a replacement."
            )

        cursor.execute(
            """
            INSERT INTO Component_Replacement
                (unit_inspection_id, part_id, part_serial_number, replacement_date, quantity_used, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (unit_inspection_id, part_id, part_serial_number, replacement_date, quantity_used, notes),
        )
        conn.commit()
        return True
    finally:
        conn.close()


def delete_component(replacement_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM Component_Replacement WHERE replacement_id = ?",
            (replacement_id,),
        )
        affected = cursor.rowcount
        conn.commit()
        return affected > 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_component(replacement_id, part_name_or_number, site_name, part_serial_number, replacement_date, quantity_used, notes=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        part_id = _resolve_part_id(cursor, part_name_or_number)
        if part_id is None:
            raise ValueError(
                f"Spare part '{part_name_or_number}' was not found. "
                f"Add it to Spare_Part first (matched on part_name or part_number)."
            )
        unit_inspection_id = _resolve_latest_unit_inspection_id(cursor, site_name)
        if unit_inspection_id is None:
            raise ValueError(
                f"No Unit_Inspection exists for site '{site_name}'. "
                f"Log an inspection on a unit at this site before recording a replacement."
            )

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
        return True
    finally:
        conn.close()


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