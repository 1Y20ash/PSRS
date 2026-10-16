"""Environment-based configuration for PSRS."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get("PSRS_SECRET_KEY", "local-development-only-change-me")
    DEBUG = os.environ.get("PSRS_DEBUG", "false").lower() == "true"
    DATABASE_PATH = os.environ.get("PSRS_DATABASE_PATH", str(BASE_DIR / "data" / "psrs.sqlite3"))
    DATA_DIRECTORY = os.environ.get("PSRS_DATA_DIRECTORY", str(BASE_DIR / "data" / "generated"))
    JSON_SORT_KEYS = False
