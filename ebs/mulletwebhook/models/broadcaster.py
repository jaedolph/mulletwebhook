"""broadcaster.py."""
from dataclasses import dataclass

from mulletwebhook.database import db
from mulletwebhook.models.layout import Layout
from sqlalchemy.orm import backref

# pylint: disable=invalid-name
@dataclass
class Broadcaster(db.Model):  # type: ignore
    """Database model to store information about each channel/broadcaster."""

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String, nullable=False)
    layouts = db.relationship('Layout', backref=backref('broadcaster', passive_deletes=True), lazy=True)
    current_layout: int = db.Column(db.Integer)
    editing_layout: int = db.Column(db.Integer)
