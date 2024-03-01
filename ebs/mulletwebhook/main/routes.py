"""Main routes."""
from datetime import datetime

from flask import Blueprint, Response, abort, jsonify, make_response, request, current_app
import requests

from mulletwebhook import verify
from mulletwebhook.models.layout import Layout
from mulletwebhook.models.element import Element, Image, Text, Webhook, ElementType

bp = Blueprint("main", __name__)


@bp.route("/redeem", methods=["POST"])
@verify.token_required
def redeem(channel_id: int, role: str) -> Response:

    current_app.logger.info("Redeem webhook %s %s", channel_id, role)

    data = request.get_json()

    current_app.logger.info("data: %s", data)

    #requests.post("https://api.mixitupapp.com/api/webhook/",json=data)

    resp = make_response("test")

    return resp

@bp.route("/image/<int:image_id>", methods=["GET"])
def image(image_id) -> Response:

    image = Image.query.filter(
        Image.id == image_id
    ).one()
    resp = make_response(image.data)
    resp.headers = {
        "Content-type": "image/png"
    }

    return resp

@bp.route("/layout/<int:layout_id>", methods=["GET"])
def layout(layout_id) -> Response:

    resp = make_response(jsonify(get_layout_json(layout_id)))

    return resp

def get_layout_json(layout_id):

    layout = Layout.query.filter(Layout.id == layout_id).one()
    current_app.logger.info(layout)
    elements = Element.query.filter(
        Element.layout == layout_id
    ).order_by(Element.position).all()
    current_app.logger.info(elements)

    elements_list = []
    for element in elements:
        current_app.logger.info(element)
        entry = {"type": element.element_type.name}
        if element.element_type == ElementType.image:
            current_app.logger.info("image")
            image = Image.query.filter(
                Image.element_id == element.id
            ).one()
            entry["id"] = image.id
        if element.element_type == ElementType.text:
            current_app.logger.info("text")
            text = Text.query.filter(
                Text.element_id == element.id
            ).one()
            entry["text"] = text.text
        elements_list.append(entry)

    layout_json = {
        "elements": elements_list,
        "layout": {
            "columns": layout.columns,
        }
    }

    return layout_json


