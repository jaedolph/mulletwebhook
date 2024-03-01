"""element.py."""
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from mulletwebhook.database import db

class ElementType(Enum):
    webhook = 1
    image = 2
    text = 3

# pylint: disable=invalid-name
@dataclass
class Element(db.Model):  # type: ignore
    """Database model to store panel elements."""

    id: int = db.Column(db.Integer, primary_key=True)
    element_type: ElementType = db.Column(db.Enum(ElementType), nullable=False)
    layout: int = db.Column(db.Integer, nullable=False)
    position: int =  db.Column(db.Integer, nullable=False)

@dataclass
class Image(db.Model):  # type: ignore
    """Database model to store images."""

    id: int = db.Column(db.Integer, primary_key=True)
    data: bytes = db.Column(db.LargeBinary(), nullable=False)
    element_id: int = db.Column(db.Integer, nullable=False)

@dataclass
class Text(db.Model):  # type: ignore
    """Database model to store text."""

    id: int = db.Column(db.Integer, primary_key=True)
    text: str = db.Column(db.String(), nullable=False)
    element_id: int = db.Column(db.Integer, nullable=False)

@dataclass
class Webhook(db.Model):  # type: ignore
    """Database model to store webhook information."""

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String, nullable=False)
    url: str = db.Column(db.String, nullable=False)
    bits_product: str = db.Column(db.String, nullable=False)
    data: str = db.Column(db.String, nullable=False)
    cooldown: int = db.Column(db.Integer, default=0)
    last_triggered: datetime = db.Column(db.DateTime, default=datetime.fromtimestamp(0))
    element_id: int = db.Column(db.Integer, nullable=False)
