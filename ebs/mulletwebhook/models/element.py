"""element.py."""
from dataclasses import dataclass

from datetime import datetime
from mulletwebhook.database import db
from mulletwebhook.models.enums import ElementType, BitsProduct
from sqlalchemy.orm import backref
from sqlalchemy.sql import func

# pylint: disable=invalid-name
@dataclass
class Element(db.Model):  # type: ignore
    """Database model to store panel elements."""

    id: int = db.Column(db.Integer, primary_key=True)
    element_type: ElementType = db.Column(db.Enum(ElementType), nullable=False)
    layout_id: int = db.Column(db.Integer, db.ForeignKey('layout.id', ondelete='CASCADE'))
    position: int =  db.Column(db.Integer(), autoincrement=True)
    image = db.relationship('Image', uselist=False, backref=backref("element", passive_deletes=True))
    text = db.relationship('Text', uselist=False, backref=backref("element", passive_deletes=True))
    webhook = db.relationship('Webhook', uselist=False, backref=backref("element", passive_deletes=True))

@dataclass
class Image(db.Model):  # type: ignore
    """Database model to store images."""

    id: int = db.Column(db.Integer, primary_key=True)
    filename: str = db.Column(db.String(), nullable=False)
    data: bytes = db.Column(db.LargeBinary(), nullable=False)
    date_modified: datetime = db.Column(db.DateTime, onupdate=func.now(), server_default=func.now(), nullable=False)
    element_id: int = db.Column(db.Integer, db.ForeignKey('element.id', ondelete='CASCADE'))

@dataclass
class Text(db.Model):  # type: ignore
    """Database model to store text."""

    id: int = db.Column(db.Integer, primary_key=True)
    text: str = db.Column(db.String(), nullable=False)
    element_id: int = db.Column(db.Integer, db.ForeignKey('element.id', ondelete='CASCADE'))

@dataclass
class Webhook(db.Model):  # type: ignore
    """Database model to store webhook information."""

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String, nullable=False)
    url: str = db.Column(db.String, nullable=False)
    bits_product: BitsProduct = db.Column(db.Enum(BitsProduct), nullable=False)
    data: dict = db.Column(db.JSON, default={})
    include_transaction_data = db.Column(db.Boolean, default=False)
    cooldown: int = db.Column(db.Integer, default=0)
    last_triggered: datetime = db.Column(db.DateTime, default=datetime.fromtimestamp(0))
    element_id: int = db.Column(db.Integer, db.ForeignKey('element.id', ondelete='CASCADE'))
