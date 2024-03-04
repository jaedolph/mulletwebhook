"""Main routes."""
from datetime import datetime
import json
import jwt
import base64

from flask import Blueprint, Response, abort, jsonify, make_response, request, current_app
import requests

from mulletwebhook import verify
from mulletwebhook.models.layout import Layout
from mulletwebhook.models.element import Element, Image, Text, Webhook, ElementType

bp = Blueprint("main", __name__)


@bp.route("/webhook", methods=["POST"])
@verify.token_required
def redeem(channel_id: int, role: str) -> Response:

    current_app.logger.info("Redeem webhook %s %s", channel_id, role)

    data = request.get_json()

    webhook_id = data["webhook_id"]
    transaction_receipt = data["transaction"]["transactionReceipt"]
    receipt_decode = jwt.decode(
        transaction_receipt,
        key=base64.b64decode(current_app.config["EXTENSION_SECRET"]),
        algorithms=["HS256"],
    )
    webhook = Webhook.query.filter(
        Webhook.id == webhook_id
    ).one()
    # TODO: check if webhook belongs to the broadcaster

    current_app.logger.info(webhook.url)
    current_app.logger.info(webhook.data)
    current_app.logger.info(receipt_decode)
    current_app.logger.info("data: %s", data)

    req = requests.post(webhook.url, json=json.loads(webhook.data))
    req.raise_for_status()
    resp = make_response(req.text)

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
        entry = {"type": element.element_type.name, "id": element.id}
        if element.element_type == ElementType.image:
            current_app.logger.info("image")
            image = Image.query.filter(
                Image.element_id == element.id
            ).one()
            entry["image"] = {
                "id": image.id,
                "data": None,
            }
        if element.element_type == ElementType.text:
            current_app.logger.info("text")
            text = Text.query.filter(
                Text.element_id == element.id
            ).one()
            entry["text"] = {
                "id": text.id,
                "text": text.text
            }
        if element.element_type == ElementType.webhook:
            current_app.logger.info("webhook")
            webhook = Webhook.query.filter(
                Webhook.element_id == element.id
            ).one()
            entry["webhook"] = {
                "id": webhook.id,
                "text": webhook.text,
                "url": None,
                "bits_product": webhook.bits_product,
                "data": None,
                "cooldown": webhook.cooldown,
                "last_triggered": webhook.last_triggered,
            }

        elements_list.append(entry)

    layout_json = {
        "elements": elements_list,
        "layout": {
            "id": layout.id,
            "columns": layout.columns,
            "title": layout.title,
            "name": layout.name,
        }
    }

    return layout_json


