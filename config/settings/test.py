from .base import *  # noqa: F403

DEBUG = False
SECRET_KEY = "test-only-secret-key"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
AXES_ENABLED = False
DATABASES["default"]["CONN_MAX_AGE"] = 0  # noqa: F405
ANONYMIZATION_LEDGER_PATH = BASE_DIR / "var" / "test-anonymization-ledger.jsonl"  # noqa: F405

import os

if os.getenv("USE_SQLITE_FOR_TESTS") == "1":
    DATABASES = {
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "test.sqlite3"}
    }
