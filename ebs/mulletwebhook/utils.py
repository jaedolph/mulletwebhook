"""Utility functions."""

from flask import current_app
from sqlalchemy import desc
from sqlalchemy.exc import NoResultFound

from mulletwebhook.database import db
from mulletwebhook.models.element import Element


def ensure_layout_order(layout_id: int) -> None:
    """Make sure elements are in consecutive order in the database.

    :param layout_id: id of the layout to re-order
    """
    elements = Element.query.filter(Element.layout_id == layout_id).order_by(Element.position).all()

    for index, element in enumerate(elements):
        if element.position != index:
            current_app.logger.debug(
                "updating position of element %s from %s to %s",
                element.id,
                element.position,
                index,
            )
            element.position = index
    db.session.commit()


def get_next_layout_position(layout_id: int) -> int:
    """Get the next available index in a layout.

    :param layout_id: id of the layout to find a free index for
    """
    try:
        element = (
            Element.query.filter(Element.layout_id == layout_id)
            .order_by(desc(Element.position))  # type: ignore
            .limit(1)
            .one()
        )
    except NoResultFound:
        return 0

    return int(element.position) + 1
