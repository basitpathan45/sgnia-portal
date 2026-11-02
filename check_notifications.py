import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parents[0]
sys.path.append(str(project_root))

from staff_portal.app import create_app
from staff_portal.app.models import Notification

app = create_app()
with app.app_context():
    count = Notification.query.count()
    print(f"Notification count: {count}")
