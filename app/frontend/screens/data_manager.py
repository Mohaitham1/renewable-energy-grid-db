# This file handles the 'Archive' logic which is currently 
# simulated as a local list to allow for the 'Undo' feature.

# Temporary storage for archived reports
_archived_reports = [
    (901, "Annual Efficiency Review", "2025-12-30", "Summary", "System Admin"),
    (902, "Winter Grid Stress Test", "2026-01-15", "Technical", "Eng. Ahmed")
]

def get_archived():
    """Returns the list of all currently archived reports."""
    return _archived_reports

def move_to_archive(report_id):
    """
    In a real scenario, this would mark a row in SQL as 'archived'.
    For now, it simulates moving a report from the active list.
    """
    # Logic to move from active to archive would go here
    return True

def restore_from_archive(report_id):
    """Removes a report from the archive so it can be moved back to active."""
    global _archived_reports
    _archived_reports = [r for r in _archived_reports if r[0] != report_id]
    return True

def permanent_delete(report_id, from_archive=True):
    """Permanently removes a report from the temporary archive list."""
    global _archived_reports
    if from_archive:
        _archived_reports = [r for r in _archived_reports if r[0] != report_id]
    return True