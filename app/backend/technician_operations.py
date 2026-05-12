from backend.db_connection import get_connection


def get_all_technicians():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT technician_id,
               first_name + ' ' + last_name AS full_name,
               email,
               phone,
               hire_date,
               employment_status
        FROM Technician
    """)
    rows = cursor.fetchall()
    conn.close()
    return [tuple(row) for row in rows]


def add_technician(full_name, email, phone, hire_date, employment_status):
    conn = get_connection()
    cursor = conn.cursor()
    parts = full_name.strip().split(" ", 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else "-"

    cursor.execute("""
        INSERT INTO Technician (first_name, last_name, email, phone, hire_date, employment_status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (first_name, last_name, email, phone, hire_date, employment_status))
    conn.commit()
    conn.close()
    return True


def delete_technician(tech_id):
    """Delete a technician and all records that reference them.

    Foreign-key chain (none of these cascade automatically):
        Technician  <-  Inspection_Round (FK_IR_Tech)
        Inspection_Round  ->  Unit_Inspection (ON DELETE CASCADE)
        Unit_Inspection  <-  Component_Replacement (FK_CR_UnitInspection)
        Technician  <-  Technician_Certification (ON DELETE CASCADE)
    So we must purge Component_Replacement rows tied to this tech's
    Unit_Inspections before touching Inspection_Round.
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
                INNER JOIN Inspection_Round ir ON ui.inspection_id = ir.inspection_id
                WHERE ir.technician_id = ?
            )
            """,
            (tech_id,),
        )
        cursor.execute(
            "DELETE FROM Inspection_Round WHERE technician_id = ?", (tech_id,)
        )
        cursor.execute(
            "DELETE FROM Technician WHERE technician_id = ?", (tech_id,)
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_technician(tech_id, full_name, email, phone, hire_date, employment_status):
    conn = get_connection()
    cursor = conn.cursor()
    parts = full_name.strip().split(" ", 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else "-"

    cursor.execute("""
        UPDATE Technician
        SET first_name = ?, last_name = ?, email = ?, phone = ?, hire_date = ?, employment_status = ?
        WHERE technician_id = ?
    """, (first_name, last_name, email, phone, hire_date, employment_status, tech_id))
    conn.commit()
    conn.close()
    return True


def search_technicians(keyword):
    conn = get_connection()
    cursor = conn.cursor()
    like = f"%{keyword}%"
    cursor.execute("""
        SELECT technician_id,
               first_name + ' ' + last_name AS full_name,
               email,
               phone,
               hire_date,
               employment_status
        FROM Technician
        WHERE first_name LIKE ? OR last_name LIKE ? OR email LIKE ? OR employment_status LIKE ?
    """, (like, like, like, like))
    rows = cursor.fetchall()
    conn.close()
    return [tuple(row) for row in rows]