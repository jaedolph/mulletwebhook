"""Configuration for the app."""

# pylint: disable=too-few-public-methods
class Config:
    """Parses application configuration from environment variables."""

    #PREFIX = "MULLETWEBHOOK_"
    EXTENSION_SECRET = ""
    #cast(str, os.environ.get(f"{PREFIX}EXTENSION_SECRET")) or ""
    #SQLALCHEMY_DATABASE_URI = os.environ.get(f"{PREFIX}SQLALCHEMY_DATABASE_URI") or ""
    #LOG_LEVEL = os.environ.get(f"{PREFIX}LOG_LEVEL") or "INFO"
