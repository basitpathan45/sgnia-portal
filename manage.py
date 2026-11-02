#!/usr/bin/env python
"""
Utility script for one‑off maintenance tasks.

Current command:
    python manage.py purge_notifications
        – Deletes ALL Notification records and their PDFs from the filesystem.
"""

import sys
from pathlib import Path

# ------- Project root on import path ---------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[0]
sys.path.append(str(PROJECT_ROOT))

from staff_portal.app import create_app
from staff_portal.app.models import Notification, db

app = create_app()
app.app_context().push()


def _delete_pdf(pdf_path: str):
    """Remove a PDF file if it exists."""
    if not pdf_path:
        return
    file = Path(pdf_path)
    if file.is_file():
        try:
            file.unlink()
            print(f"[DELETED] PDF: {file}")
        except Exception as exc:
            print(f"[WARN] Could not delete {file}: {exc}")


def purge_notifications():
    """Delete every Notification (and cascade‑delete its versions) and PDFs."""
    notifications = Notification.query.all()
    count = len(notifications)
    if count == 0:
        print("[INFO] No notifications found – nothing to delete.")
        return
    # Delete PDFs first
    for n in notifications:
        _delete_pdf(n.pdf_path)
    # Delete DB rows (cascades to NotificationVersion)
    Notification.query.delete()
    db.session.commit()
    print(f"[INFO] Deleted {count} notification record(s) and their PDFs.")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] != "purge_notifications":
        print("Usage: python manage.py purge_notifications")
        sys.exit(1)
    purge_notifications()

