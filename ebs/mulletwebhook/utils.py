"""Utility functions."""

from flask import current_app

from sqlalchemy.exc import NoResultFound
from sqlalchemy import desc

from mulletwebhook.models.element import Element
from mulletwebhook.database import db


def ensure_layout_order(layout_id: int) -> None:
    elements = Element.query.filter(Element.layout_id == layout_id).order_by(Element.position).all()

    for index, element in enumerate(elements):
        if element.position != index:
            current_app.logger.info(
                "updating position of element %s from %s to %s",
                element.id,
                element.position,
                index,
            )
            element.position = index
    db.session.commit()


def get_next_layout_position(layout_id: int) -> None:
    try:
        element = (
            Element.query.filter(Element.layout_id == layout_id)
            .order_by(desc(Element.position))
            .limit(1)
            .one()
        )
    except NoResultFound:
        return 0

    return element.position + 1
