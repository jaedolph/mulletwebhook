"""layouts.py."""

from dataclasses import dataclass

from sqlalchemy.orm import backref

from mulletwebhook.database import db


# pylint: disable=invalid-name
@dataclass
class Layout(db.Model):  # type: ignore
    """Database model to store panel layouts."""

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String, nullable=False)
    title: str = db.Column(db.String)
    show_title: bool = db.Column(db.Boolean, default=True)
    broadcaster_id: int = db.Column(
        db.Integer, db.ForeignKey("broadcaster.id", ondelete="CASCADE"), nullable=False
    )
    elements = db.relationship(
        "Element", backref=backref("layout", passive_deletes=True), lazy=True
    )
