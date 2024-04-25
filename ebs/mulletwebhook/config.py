"""Configuration for the app."""
import os
import uuid

# pylint: disable=too-few-public-methods
class Config:
    """Parses application configuration from environment variables."""

    PREFIX = "MULLETWEBHOOK_"
    EXTENSION_SECRET = os.environ.get(f"{PREFIX}EXTENSION_SECRET") or ""
    CLIENT_SECRET = os.environ.get(f"{PREFIX}CLIENT_SECRET") or ""
    CLIENT_ID = os.environ.get(f"{PREFIX}CLIENT_ID") or ""
    SQLALCHEMY_DATABASE_URI = os.environ.get(f"{PREFIX}SQLALCHEMY_DATABASE_URI") or ""
    EBS_URL = os.environ.get(f"{PREFIX}EBS_URL") or ""
    LOG_LEVEL = os.environ.get(f"{PREFIX}LOG_LEVEL") or "INFO"
    TESTING = (os.environ.get(f"{PREFIX}TESTING") == "True") or False
    REQUEST_TIMEOUT: int = int((os.environ.get(f"{PREFIX}REQUEST_TIMEOUT") or 5))
    WTF_CSRF_ENABLED = False
