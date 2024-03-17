"""element.py."""
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from mulletwebhook.database import db
from sqlalchemy.orm import backref

class ElementType(Enum):
    webhook = 1
    image = 2
    text = 3

class BitsProduct(Enum):
    reward_1bits = 1
    reward_5bits = 2
    reward_10bits = 3
    reward_20bits = 20
    reward_50bits = 50
    reward_100bits = 100
    reward_200bits = 200
    reward_300bits = 300
    reward_400bits = 400
    reward_500bits = 500
    reward_600bits = 600
    reward_700bits = 700
    reward_800bits = 800
    reward_900bits = 900
    reward_1000bits = 1000
    reward_1500bits = 1500
    reward_2000bits = 2000
    reward_2500bits = 2500
    reward_5000bits = 5000
    reward_10000bits = 10000
    reward_15000bits = 15000
    reward_20000bits = 20000
    reward_25000bits = 25000
    reward_50000bits = 50000
    reward_100000bits = 100000

# pylint: disable=invalid-name
@dataclass
class Element(db.Model):  # type: ignore
    """Database model to store panel elements."""

    id: int = db.Column(db.Integer, primary_key=True)
    element_type: ElementType = db.Column(db.Enum(ElementType), nullable=False)
    layout_id: int = db.Column(db.Integer, db.ForeignKey('layout.id', ondelete='CASCADE'), nullable=False)
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
    cooldown: int = db.Column(db.Integer, default=0)
    last_triggered: datetime = db.Column(db.DateTime, default=datetime.fromtimestamp(0))
    element_id: int = db.Column(db.Integer, db.ForeignKey('element.id', ondelete='CASCADE'))
