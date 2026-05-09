# Shared mock database
reports_db = [
    [901, "Monthly Energy Yield", "2026-04-30", "Summary", "Admin"],
    [902, "Maintenance Audit Q1", "2026-03-15", "Audit", "Sami Yassin"],
    [903, "Site Efficiency Rank", "2026-05-01", "Analytics", "Ahmed Ali"],
    [904, "Carbon Offset Report", "2026-02-28", "Environmental", "Laila Mahmoud"],
    [905, "Fault Frequency Analysis", "2026-05-07", "Technical", "Mona Hassan"]
]

archive_db = []

def get_reports():
    """Returns the current list of active reports."""
    return reports_db

def get_archived():
    """Returns the current list of archived reports."""
    return archive_db

def move_to_archive(report_id):
    """Moves a report from the active list to the archive."""
    global reports_db, archive_db
    for i, report in enumerate(reports_db):
        if report[0] == report_id:
            archive_db.append(reports_db.pop(i))
            return True
    return False

def restore_from_archive(report_id):
    """Moves a report from the archive back to the active list."""
    global reports_db, archive_db
    for i, report in enumerate(archive_db):
        if report[0] == report_id:
            reports_db.append(archive_db.pop(i))
            return True
    return False

def permanent_delete(report_id, from_archive=True):
    """Permanently removes a report from the specified database."""
    global reports_db, archive_db
    db = archive_db if from_archive else reports_db
    for i, report in enumerate(db):
        if report[0] == report_id:
            db.pop(i)
            return True
    return False