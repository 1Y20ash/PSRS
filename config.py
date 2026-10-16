"""Environment-based configuration with safe defaults."""
import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
class Config:
    SECRET_KEY = os.environ.get("PSRS_SECRET_KEY")
    DEBUG = os.environ.get("PSRS_DEBUG", "false").lower() == "true"
    DATABASE_PATH = os.environ.get("PSRS_DATABASE_PATH", str(BASE_DIR / "data" / "psrs.sqlite3"))
    DATA_DIRECTORY = os.environ.get("PSRS_DATA_DIRECTORY", str(BASE_DIR / "data" / "generated"))
    JSON_SORT_KEYS = False
    MAX_CONTENT_LENGTH = 1024 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("PSRS_COOKIE_SECURE", "false").lower() == "true"
    TRUSTED_HOSTS = [h.strip() for h in os.environ.get("PSRS_TRUSTED_HOSTS", "").split(",") if h.strip()] or None
