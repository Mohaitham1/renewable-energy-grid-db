from backend.db_connection import get_connection

def get_all_technicians():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Technician_ID, First_Name + ' ' + Last_Name AS FullName,
               Specialty, Certification, Status
        FROM Technician
    """)
    rows = cursor.fetchall()
    conn.close()
    return [(row[0], row[1], row[2], row[3], row[4]) for row in rows]

def add_technician(full_name, specialty, certification, status):
    conn = get_connection()
    cursor = conn.cursor()
    parts = full_name.split(' ', 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ''
    
    cursor.execute("""
        INSERT INTO Technician (First_Name, Last_Name, Specialty, Certification, Status)
        VALUES (?, ?, ?, ?, ?)
    """, (first_name, last_name, specialty, certification, status))
    conn.commit()
    conn.close()
    return True

def delete_technician(tech_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Technician WHERE Technician_ID = ?", (tech_id,))
    conn.commit()
    conn.close()
    return True

def update_technician(tech_id, full_name, specialty, certification, status):
    conn = get_connection()
    cursor = conn.cursor()
    parts = full_name.split(' ', 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ''
    
    cursor.execute("""
        UPDATE Technician
        SET First_Name = ?, Last_Name = ?, Specialty = ?, Certification = ?, Status = ?
        WHERE Technician_ID = ?
    """, (first_name, last_name, specialty, certification, status, tech_id))
    conn.commit()
    conn.close()
    return True

def search_technicians(keyword):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Technician_ID, First_Name + ' ' + Last_Name AS FullName,
               Specialty, Certification, Status
        FROM Technician
        WHERE First_Name LIKE ? OR Last_Name LIKE ? OR Specialty LIKE ? OR Certification LIKE ?
    """, (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
    rows = cursor.fetchall()
    conn.close()
    return [(row[0], row[1], row[2], row[3], row[4]) for row in rows]