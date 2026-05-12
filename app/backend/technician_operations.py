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
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Technician WHERE technician_id = ?", (tech_id,))
    conn.commit()
    conn.close()
    return True


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
