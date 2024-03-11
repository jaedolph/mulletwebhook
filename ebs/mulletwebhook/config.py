"""Configuration for the app."""
import os

# pylint: disable=too-few-public-methods
class Config:
    """Parses application configuration from environment variables."""

    PREFIX = "MULLETWEBHOOK_"
    EXTENSION_SECRET = os.environ.get(f"{PREFIX}EXTENSION_SECRET") or ""
    #cast(str, os.environ.get(f"{PREFIX}EXTENSION_SECRET")) or ""
    SQLALCHEMY_DATABASE_URI = os.environ.get(f"{PREFIX}SQLALCHEMY_DATABASE_URI") or ""
    EBS_URL = os.environ.get(f"{PREFIX}EBS_URL") or ""
    #LOG_LEVEL = os.environ.get(f"{PREFIX}LOG_LEVEL") or "INFO"
