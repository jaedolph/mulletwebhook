"""broadcaster.py."""
from dataclasses import dataclass

from mulletwebhook.database import db


# pylint: disable=invalid-name
@dataclass
class Broadcaster(db.Model):  # type: ignore
    """Database model to store information about each channel/broadcaster."""

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String, nullable=False)

