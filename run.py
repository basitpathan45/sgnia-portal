import os
import sys
from pathlib import Path

portal_dir = Path(__file__).resolve().parent / "staff_portal"
if str(portal_dir) not in sys.path:
    sys.path.insert(0, str(portal_dir))

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
