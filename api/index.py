from __future__ import annotations

from pathlib import Path
import sys

api_app_path = Path(__file__).resolve().parents[1] / "apps" / "api"
sys.path.insert(0, str(api_app_path))

from app.main import app  # noqa: E402
