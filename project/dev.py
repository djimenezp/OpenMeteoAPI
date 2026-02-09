from .settings import *  # noqa

import os
from pathlib import Path

DEBUG = True

# In dev, allow everything (handy for Docker hostnames)
ALLOWED_HOSTS = ["*"]

# SQLite location for Docker (or local if you want)
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.environ.get("SQLITE_PATH", str(BASE_DIR / "dbdata" / "db.sqlite3"))

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DB_PATH,
    }
}

# Optional: slightly louder logs in dev
LOGGING["loggers"]['app']['level'] = "DEBUG"
