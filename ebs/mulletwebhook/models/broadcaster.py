"""broadcaster.py."""

from dataclasses import dataclass

from sqlalchemy.orm import backref

from mulletwebhook.database import db


# pylint: disable=invalid-name
@dataclass
class Broadcaster(db.Model):  # type: ignore
    """Database model to store information about each channel/broadcaster."""

    id: int = db.Column(db.Integer, primary_key=True)
    layouts = db.relationship(
        "Layout", backref=backref("broadcaster", passive_deletes=True), lazy=True
    )
    current_layout: int = db.Column(db.Integer)
    editing_layout: int = db.Column(db.Integer)
