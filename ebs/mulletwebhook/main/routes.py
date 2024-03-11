"""Main routes."""
from datetime import datetime
import json
import jwt
import base64

from flask import Blueprint, Response, abort, jsonify, make_response, request, current_app
import requests
from sqlalchemy.exc import NoResultFound

from mulletwebhook import verify
from mulletwebhook.models.broadcaster import Broadcaster
from mulletwebhook.models.layout import Layout
from mulletwebhook.models.element import Element, Image, Text, Webhook, ElementType
from mulletwebhook.database import db

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

@bp.route("/element/image/<int:image_id>", methods=["GET"])
def image_get(image_id: int) -> Response:

    image = Image.query.filter(
        Image.id == image_id
    ).one()
    resp = make_response(image.data)
    resp.headers = {
        "Content-type": "image/png"
    }

    return resp

@bp.route("/element/image/<int:image_id>", methods=["PUT"])
@verify.token_required
def image_put(channel_id: int, role: str, image_id: int) -> Response:

    current_app.logger.info(request.form.get("image"))
    current_app.logger.info(request.files)
    image = Image.query.filter(
        Image.id == image_id
    ).one()
    current_app.logger.info(image.id)
    file = request.files.get("image")
    data = file.read()
    image.data = data

    db.session.commit()

    response = make_response("<p>Image Updated</p>")
    response.headers["HX-Trigger"] = "closeModal"
    response.status_code = 201

    return response


# @bp.route("/layouts/<int:layout_id>", methods=["GET"])
# def layout_id(layout_id: int) -> Response:

#     resp = make_response(jsonify(get_layout_json(layout_id)))

#     return resp

# @bp.route("/layouts", methods=["GET"])
# @verify.token_required
# def layout(channel_id: int, role: str) -> Response:

#     layouts = Layout.query.filter(
#         Layout.broadcaster_id == channel_id
#     ).all()
#     layout_list = []
#     for layout in layouts:
#         layout_list.append({
#             "id": layout.id,
#             "name": layout.name,
#         })

#     resp = make_response(jsonify({"layouts": layout_list}))

#     return resp

@bp.route("/layout/<int:layout_id>/update-order", methods=["POST"])
@verify.token_required
def update_order(channel_id: int, role: str, layout_id: int) -> Response:
    current_app.logger.info(request.form.copy())
    elements = Element.query.filter(
        Element.layout == layout_id
    ).order_by(Element.position).all()

    for new_pos, old_pos in enumerate(request.form.getlist("element")):
        current_app.logger.info("%s %s", new_pos, old_pos)
        if new_pos != int(old_pos):
            current_app.logger.info("switching element %s with %s", old_pos, new_pos)
            element_to_update = elements[int(old_pos)]
            element_to_update.position = new_pos

    db.session.commit()
    resp = make_response(get_layout_html(layout_id))

    return resp


@bp.route("/layout/<int:layout_id>", methods=["GET"])
@verify.token_required
def layouts(channel_id: int, role: str, layout_id: int) -> Response:

    # current_app.logger.info(request.args)
    # layout_id = int(request.args.get("id"))
    resp = make_response(get_layout_html(layout_id))

    return resp

# @bp.route("/element/image/<int:image_id>", methods=["PUT"])
# @verify.token_required
# def put_image(channel_id: int, role: str) -> Response:
#     current_app.logger.info(request.args)


#     resp = make_response(get_layout_html(layout_id))

#     return resp


@bp.route("/element/<int:element_id>/edit", methods=["GET"])
@verify.token_required
def test(channel_id: int, role: str, element_id: int) -> Response:
    current_app.logger.info(request.headers)

    element_form = None

    element = Element.query.filter(
        Element.id == element_id
    ).one()

    if element.element_type == ElementType.image:
        image = Image.query.filter(
            Image.element_id == element.id
        ).one()
        element_form = f"""
            <div><p>Editing image {image.id}</p></div>
            <form
                id="dialog-form"
                hx-put="{current_app.config['EBS_URL']}/element/image/{image.id}"
                hx-encoding="multipart/form-data"
                hx-swap="none">
                <label for="image_upload">Upload a new image:</label><br>
                <input type="file" name="image" form="dialog-form" accept="image/png" /><br><br>
                <input type="submit" value="Submit">
            </form><br>
        """
    if element.element_type == ElementType.text:
        text = Text.query.filter(
            Text.element_id == element.id
        ).one()
        element_form = f"""
            <div><p>Editing text {text.id}</p></div>
            <form id="dialog-form">
                <label for="text-input">text:</label>
                <input type="text" id="text-input" form="dialog-form" value="{text.text}" /><br><br>
                <input type="submit" value="Submit">
            </form><br>
        """
    if element.element_type == ElementType.webhook:
        webhook = Webhook.query.filter(
            Webhook.element_id == element.id
        ).one()
        element_form = f"""
            <div><p>Editing webhook {webhook.id}</p></div>
        """

    resp = make_response(f"""
        <dialog>
            {element_form}
            <button id="cancel-button">Cancel</button>
        </dialog>
        """)
    return resp


def get_layout_html(layout_id):

    layout = Layout.query.filter(Layout.id == layout_id).one()
    current_app.logger.info(layout)
    elements = Element.query.filter(
        Element.layout == layout_id
    ).order_by(Element.position).all()
    current_app.logger.info(elements)
    elements_list = []
    for element in elements:
        current_app.logger.info(element)
        entry = None
        edit_button = f"""
            <div class='edit-overlay'>
                <button
                    class='edit-button'
                    type="button"
                    id="edit-button-{element.id}"
                    hx-get="{current_app.config['EBS_URL']}/element/{element.id}/edit"
                    hx-target="#dialog"
                    >Edit</button>
            </div>
        """
        if element.element_type == ElementType.image:
            current_app.logger.info("image")
            image = Image.query.filter(
                Image.element_id == element.id
            ).one()
            image_url = f"{current_app.config['EBS_URL']}/element/image/{image.id}?timestamp={datetime.now().strftime('%s')}"
            entry = f"""
                <div class='element' id='element-{element.id}'>
                    <input type='hidden' name='element' value='{element.position}'/>
                    <img id='image-{image.id}' src='{image_url}'>
                    {edit_button}
                </div>
                """
        if element.element_type == ElementType.text:
            current_app.logger.info("text")
            text = Text.query.filter(
                Text.element_id == element.id
            ).one()
            entry = f"""
                <div class='element' id='element-{element.id}'>
                    <input type='hidden' name='element' value='{element.position}'/>
                    <p id='text-{text.id}'>{text.text}</p>
                    {edit_button}
                </div>
                """
        if element.element_type == ElementType.webhook:
            current_app.logger.info("webhook")
            webhook = Webhook.query.filter(
                Webhook.element_id == element.id
            ).one()
            entry = f"""
                <div class='element' id='element-{element.id}'>
                    <input type='hidden' name='element' value='{element.position}'/>
                    <p>
                    <button
                        type="button"
                        id='webhook-{webhook.id}'
                    > <img src='bit.gif' width='28' height='28'> {webhook.text}</button>
                    </p>
                    {edit_button}
                </div>
            """
        if entry:
            elements_list.append(entry)

    add_new_button = """
    <div id="add-new-div" class="add-new-div">
        <button id="add-new-button" type="button">Add new</button>
    </div>
    """
    elements_list.append(add_new_button)

    return "\n".join(elements_list)


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
