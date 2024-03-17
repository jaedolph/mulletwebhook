"""Main routes."""
from datetime import datetime
import json
import jwt
import base64
import textwrap

from flask import Blueprint, Response, abort, jsonify, make_response, request, current_app, render_template
from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed, FileSize

from wtforms import StringField, FileField, SelectField, FieldList, FormField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, URL
from wtforms.widgets import TextArea

import requests
from sqlalchemy.exc import NoResultFound
from sqlalchemy import func

from mulletwebhook import verify, utils

from mulletwebhook.models.broadcaster import Broadcaster
from mulletwebhook.models.layout import Layout
from mulletwebhook.models.element import Element, Image, Text, Webhook, ElementType, BitsProduct
from mulletwebhook.database import db

bp = Blueprint("main", __name__)


class TextForm(FlaskForm):
    text = StringField('text', validators=[DataRequired(), Length(min=1, max=100)])

class ImageForm(FlaskForm):
    image = FileField(validators=[FileRequired(), FileAllowed(['png']), FileSize(max_size=1048576, message="Images must be less than 1MiB in size")])

def validate_is_json(form, field):
    del form
    try:
        json.loads(field.data)
    except json.decoder.JSONDecodeError as exp:
        raise ValidationError("Data must be valid json")

class ElementForm(FlaskForm):
    element_type = SelectField("Type", choices=[(type.name, type.name) for type in ElementType])

class WebhookForm(FlaskForm):
    name = StringField(validators=[DataRequired(), Length(min=1, max=100)])
    url = StringField(validators=[DataRequired(), URL(), Length(min=1, max=2048)])
    bits_product = SelectField("Bits cost", choices=[(product.name, product.value) for product in BitsProduct])
    extra_data = StringField('data', validators=[DataRequired(), Length(min=1, max=2000), validate_is_json], widget=TextArea())

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


@bp.route("/element/<int:element_id>/text/<int:text_id>/edit", methods=["GET", "PUT"])
@verify.token_required
def text_edit(channel_id: int, role: str, element_id: int, text_id: int) -> Response:
    current_app.logger.info("text_id=%s element_id=%s", text_id, element_id)

    form = TextForm()

    text = Text.query.filter(
        Text.id == text_id
    ).one()

    if request.method == "PUT":
        if form.validate():
            current_app.logger.info("form valid")
            current_app.logger.info(form.data)
            text.text = form.text.data
            db.session.commit()
            return make_response("<p>text updated</p>", 201)
        else:
            current_app.logger.info("form invalid")
            current_app.logger.info(form.errors)
            errors_html = ""
            for field, error in form.errors.items():
                errors_html += f"{field}: {', '.join(error)}<br>"

            return make_response(f"<p>{errors_html}</p>", 400)

    if request.method == "GET":
        form.text.data = text.text

    return render_template(
        "text_form.html",
        form_type="edit",
        form_url=f"{current_app.config['EBS_URL']}/element/{element_id}/text/{text_id}/edit",
        form=form)

@bp.route("/layout/<int:layout_id>/text/create", methods=["GET", "POST"])
@verify.token_required
def text_create(channel_id: int, role: str, layout_id: int) -> Response:
    current_app.logger.info("layout_id=%s", layout_id)

    form = TextForm()

    if request.method == "POST":
        if form.validate():
            current_app.logger.info("form valid")
            current_app.logger.info(form.data)
            element = Element(layout_id=layout_id, element_type=ElementType.text, position=utils.get_next_layout_position(layout_id))
            db.session.add(element)
            db.session.commit()
            text = Text(text=form.text.data, element_id=element.id)
            db.session.add(text)
            db.session.commit()
            # re-order elements
            utils.ensure_layout_order(layout_id)
            db.session.commit()
            return make_response("<p>text created</p>", 200)
        else:
            current_app.logger.info("form invalid")
            current_app.logger.info(form.errors)
            errors_html = ""
            for field, error in form.errors.items():
                errors_html += f"{field}: {', '.join(error)}<br>"

            return make_response(f"<p>{errors_html}</p>", 400)

    if request.method == "GET":
        form.text.data = text.text

    return render_template(
        "text_form.html",
        form_type="create",
        form_url=f"{current_app.config['EBS_URL']}/layout/{layout_id}/text/create",
        form=form)

@bp.route("/element/<int:element_id>/image/<int:image_id>/edit", methods=["GET", "PUT"])
@verify.token_required
def image_edit(channel_id: int, role: str, element_id: int, image_id: int) -> Response:
    current_app.logger.info("image_id=%s element_id=%s", image_id, element_id)

    form = ImageForm()

    image = Image.query.filter(
        Image.id == image_id
    ).one()

    if request.method == "PUT":
        if form.validate():
            current_app.logger.info("form valid")
            current_app.logger.info(form.data)
            image.data = form.image.data.read()
            image.filename = form.image.data.filename
            db.session.commit()
            return make_response("<p>image updated</p>", 201)
        else:
            current_app.logger.info("form invalid")
            current_app.logger.info(form.errors)
            errors_html = ""
            for field, error in form.errors.items():
                errors_html += f"{field}: {', '.join(error)}<br>"

            return make_response(f"<p>{errors_html}</p>", 400)

    return render_template(
        "image_form.html",
        form_type="edit",
        form_url=f"{current_app.config['EBS_URL']}/element/{element_id}/image/{image_id}/edit",
        form=form)

@bp.route("/layout/<int:layout_id>/image/create", methods=["GET", "POST"])
@verify.token_required
def image_create(channel_id: int, role: str, layout_id: int) -> Response:

    form = ImageForm()

    if request.method == "POST":
        if form.validate():
            current_app.logger.info("form valid")
            current_app.logger.info(form.data)
            element = Element(layout_id=layout_id, element_type=ElementType.image, position=utils.get_next_layout_position(layout_id))
            db.session.add(element)
            db.session.commit()
            image = Image(filename=form.image.data.filename, data=form.image.data.read(), element_id=element.id)
            db.session.add(image)
            db.session.commit()
            # re-order elements
            utils.ensure_layout_order(layout_id)
            return make_response("<p>image created</p>", 200)
        else:
            current_app.logger.info("form invalid")
            current_app.logger.info(form.errors)
            errors_html = ""
            for field, error in form.errors.items():
                errors_html += f"{field}: {', '.join(error)}<br>"

            return make_response(f"<p>{errors_html}</p>", 400)

    return render_template(
        "image_form.html",
        form_type="create",
        form_url=f"{current_app.config['EBS_URL']}/layout/{layout_id}/image/create",
        form=form)

@bp.route("/layout/<int:layout_id>/element/create", methods=["GET"])
@verify.token_required
def element_create(channel_id: int, role: str, layout_id: int) -> Response:

    return render_template(
        "element_form.html",
        image_create_url=f"{current_app.config['EBS_URL']}/layout/{layout_id}/image/create",
        text_create_url=f"{current_app.config['EBS_URL']}/layout/{layout_id}/text/create",
        webhook_create_url=f"{current_app.config['EBS_URL']}/layout/{layout_id}/webhook/create")


@bp.route("/element/<int:element_id>/webhook/<int:webhook_id>/edit", methods=["GET", "PUT"])
@verify.token_required
def webhook_edit(channel_id: int, role: str, element_id: int, webhook_id: int) -> Response:
    current_app.logger.info("webhook_id=%s element_id=%s", webhook_id, element_id)

    form = WebhookForm()

    webhook =  Webhook.query.filter(
         Webhook.id == webhook_id
    ).one()

    if request.method == "PUT":
        if form.validate():
            current_app.logger.info("form valid")
            current_app.logger.info(form.data)
            webhook.url = form.url.data
            webhook.name = form.name.data
            webhook.bits_product = form.bits_product.data
            webhook.data = json.loads(form.extra_data.data)
            db.session.commit()
            return make_response("<p>webhook updated</p>", 201)
        else:
            current_app.logger.info("form invalid")
            current_app.logger.info(form.errors)
            errors_html = ""
            for field, error in form.errors.items():
                errors_html += f"{field}: {', '.join(error)}<br>"

            return make_response(f"<p>{errors_html}</p>", 400)

    if request.method == "GET":
        form.name.data = webhook.name
        form.url.data = webhook.url
        form.bits_product.data = webhook.bits_product.name
        form.extra_data.data =  json.dumps(webhook.data, indent=2)

    return render_template(
        "webhook_form.html",
        form_type="edit",
        form_url=f"{current_app.config['EBS_URL']}/element/{element_id}/webhook/{webhook_id}/edit",
        form=form)

@bp.route("/layout/<int:layout_id>/webhook/create", methods=["GET", "POST"])
@verify.token_required
def webhook_create(channel_id: int, role: str, layout_id: int) -> Response:
    current_app.logger.info("layout_id=%s", layout_id)

    form = WebhookForm()

    if request.method == "POST":
        if form.validate():
            current_app.logger.info("form valid")
            current_app.logger.info(form.data)
            element = Element(layout_id=layout_id, element_type=ElementType.webhook, position=utils.get_next_layout_position(layout_id))
            db.session.add(element)
            db.session.commit()
            webhook = Webhook(
                url=form.url.data,
                name=form.name.data,
                bits_product=form.bits_product.data,
                data=json.loads(form.extra_data.data),
                element_id=element.id,
            )
            db.session.add(webhook)
            db.session.commit()
            # re-order elements
            utils.ensure_layout_order(layout_id)
            return make_response("<p>webhook created</p>", 200)
        else:
            current_app.logger.info("form invalid")
            current_app.logger.info(form.errors)
            errors_html = ""
            for field, error in form.errors.items():
                errors_html += f"{field}: {', '.join(error)}<br>"

            return make_response(f"<p>{errors_html}</p>", 400)

    if request.method == "GET":
        form.extra_data.data = "{}"

    return render_template(
        "webhook_form.html",
        form_type="create",
        form_url=f"{current_app.config['EBS_URL']}/layout/{layout_id}/webhook/create",
        form=form)

@bp.route("/element/<int:element_id>", methods=["DELETE"])
@verify.token_required
def element_delete(channel_id: int, role: str, element_id: int) -> Response:
    current_app.logger.info("element_id=%s",element_id)

    element = Element.query.filter(
        Element.id == element_id
    ).one()
    layout_id = element.layout_id
    db.session.delete(element)
    db.session.commit()

    # ensure element positions are sequential
    utils.ensure_layout_order(layout_id)

    return make_response("<p>Element deleted</p>")

@bp.route("/element/<int:element_id>/confirm-delete", methods=["GET", "DELETE"])
@verify.token_required
def element_confirm_delete(channel_id: int, role: str, element_id: int) -> Response:
    current_app.logger.info("element_id=%s",element_id)

    element = Element.query.filter(
        Element.id == element_id
    ).one()

    element_name = ""
    if element.element_type == ElementType.image:
        element_name = element.image.filename
    if element.element_type == ElementType.text:
        element_name = textwrap.shorten(element.text.text, 30)
    if element.element_type == ElementType.webhook:
        element_name = element.webhook.name

    element_delete_url = f"{current_app.config['EBS_URL']}/element/{element_id}"
    return render_template("confirm_delete_form.html", element_delete_url=element_delete_url, element_type=element.element_type.name, element_name=element_name)

@bp.route("/layout/<int:layout_id>/update-order", methods=["POST"])
@verify.token_required
def layout_update_order(channel_id: int, role: str, layout_id: int) -> Response:
    current_app.logger.info(request.form.copy())

    elements = Element.query.filter(
        Element.layout_id == layout_id
    ).order_by(Element.position).all()

    try:
        for new_pos, old_pos in enumerate(request.form.getlist("element")):
            current_app.logger.info("%s %s", new_pos, old_pos)
            if new_pos != int(old_pos):
                current_app.logger.info("switching element %s with %s", old_pos, new_pos)
                element_to_update = elements[int(old_pos)]
                element_to_update.position = new_pos

        db.session.commit()
    except IndexError as exp:
        current_app.logger.warning("could not re-order elements: %s", exp)

    resp = make_response(get_layout_html(layout_id))

    return resp


@bp.route("/layout/<int:layout_id>", methods=["GET"])
@verify.token_required
def layouts(channel_id: int, role: str, layout_id: int) -> Response:
    resp = make_response(get_layout_html(layout_id))

    return resp


def get_layout_html(layout_id):

    layout = Layout.query.filter(Layout.id == layout_id).one()
    current_app.logger.info(layout)
    elements = Element.query.filter(
        Element.layout_id == layout_id
    ).order_by(Element.position).all()
    current_app.logger.info(elements)
    elements_list = []
    for element in elements:
        current_app.logger.info(element)
        entry = None
        delete_button = f"""
        <button
            class='delete-button'
            type="button"
            id="delete-button-{element.id}"
            hx-get="{current_app.config['EBS_URL']}/element/{element.id}/confirm-delete"
            hx-target="#dialog"
            >Delete</button>
        """
        edit_button_template = """
        <button
            class='edit-button'
            type="button"
            id="edit-button-{element_id}"
            hx-get="{edit_url}"
            hx-target="#dialog"
            >Edit</button>
        """

        if element.element_type == ElementType.image:
            current_app.logger.info("image")
            image = Image.query.filter(
                Image.element_id == element.id
            ).one()
            image_url = f"{current_app.config['EBS_URL']}/element/image/{image.id}?timestamp={datetime.now().strftime('%s')}"
            edit_url = f"{current_app.config['EBS_URL']}/element/{element.id}/image/{image.id}/edit"
            edit_button = edit_button_template.format(element_id=element.id, edit_url=edit_url)
            entry = f"""
                <div class='element' id='element-{element.id}'>
                    <input type='hidden' name='element' value='{element.position}'/>
                    <img id='image-{image.id}' src='{image_url}'>
                    <div class='edit-overlay'>
                    {edit_button}
                    {delete_button}
                    </div>
                </div>
                """
        if element.element_type == ElementType.text:
            current_app.logger.info("text")
            text = Text.query.filter(
                Text.element_id == element.id
            ).one()
            edit_url = f"{current_app.config['EBS_URL']}/element/{element.id}/text/{text.id}/edit"
            edit_button = edit_button_template.format(element_id=element.id, edit_url=edit_url)
            entry = f"""
                <div class='element' id='element-{element.id}'>
                    <input type='hidden' name='element' value='{element.position}'/>
                    <p id='text-{text.id}'>{text.text}</p>
                    <div class='edit-overlay'>
                    {edit_button}
                    {delete_button}
                    </div>
                </div>
                """
        if element.element_type == ElementType.webhook:
            current_app.logger.info("webhook")
            webhook = Webhook.query.filter(
                Webhook.element_id == element.id
            ).one()


            edit_url = f"{current_app.config['EBS_URL']}/element/{element.id}/webhook/{webhook.id}/edit"
            edit_button = edit_button_template.format(element_id=element.id, edit_url=edit_url)
            entry = f"""
                <div class='element' id='element-{element.id}'>
                    <input type='hidden' name='element' value='{element.position}'/>
                    <p>
                    <button
                        type="button"
                        id='webhook-{webhook.id}'
                    > {webhook.bits_product.value}<img src='bit.gif' width='28' height='28'> {webhook.name}</button>
                    </p>
                    <div class='edit-overlay'>
                    {edit_button}
                    {delete_button}
                    </div>
                </div>
            """
        if entry:
            elements_list.append(entry)

    add_new_button = f"""
    <div id="add-new-div" class="add-new-div">
        <button
            type="button"
            hx-get="{current_app.config['EBS_URL']}/layout/{layout.id}/element/create"
            hx-target="#dialog"
            id="add-new-button"
            type="button"
            >Add new</button>
    </div>
    """
    elements_list.append(add_new_button)

    return "\n".join(elements_list)
