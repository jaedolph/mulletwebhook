"""layouts.py."""
from dataclasses import dataclass

from mulletwebhook.database import db
from mulletwebhook.models.element import Element
from sqlalchemy.orm import backref

# pylint: disable=invalid-name
@dataclass
class Layout(db.Model):  # type: ignore
    """Database model to store panel layouts."""

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String, nullable=False)
    title: str = db.Column(db.String, nullable=False)
    broadcaster_id: int = db.Column(db.Integer, db.ForeignKey('broadcaster.id', ondelete='CASCADE'), nullable=False)
    columns: int = db.Column(db.Integer, nullable=False)
    elements = db.relationship('Element', backref=backref("layout", passive_deletes=True), lazy=True)
