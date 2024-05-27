"""Main routes."""

# pylint: disable=too-many-lines
import base64
import json
import re
import textwrap
from uuid import uuid4
from typing import Optional

import jwt
import requests
from flask import Blueprint, Response, current_app, make_response, render_template, request
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired, FileSize
from sqlalchemy.exc import NoResultFound
from wtforms import BooleanField, FileField, SelectField, StringField, SubmitField, ValidationError
from wtforms.fields import Field
from wtforms.form import BaseForm
from wtforms.validators import URL, DataRequired, Length
from wtforms.widgets import TextArea

from mulletwebhook import twitch, utils, verify
from mulletwebhook.database import db
from mulletwebhook.models.broadcaster import Broadcaster
from mulletwebhook.models.element import Element, Image, Text, Webhook
from mulletwebhook.models.enums import BitsProduct, ElementType
from mulletwebhook.models.layout import Layout

bp = Blueprint("main", __name__)


class TextForm(FlaskForm):
    """Form for editing or creating a text element."""

    text = StringField("text", validators=[DataRequired(), Length(min=1, max=100)])


class ImageForm(FlaskForm):
    """Form for editing or creating an image element."""

    image = FileField(
        validators=[
            FileRequired(),
            FileAllowed(["png"]),
            FileSize(max_size=1048576, message="Images must be less than 1MiB in size"),
        ]
    )


def validate_is_json(form: BaseForm, field: Field):
    """Validator function to check if the input to a form is valid json.

    :param form: input form
    :param field: input field
    :raises: ValidationError if input is not valid json
    """
    del form
    try:
        json.loads(field.data)
    except json.decoder.JSONDecodeError as exp:
        raise ValidationError("Data must be valid json") from exp


def validate_is_https(form: BaseForm, field: Field):
    """Validator function to check if the url uses https.

    :param form: input form
    :param field: input field
    :raises: ValidationError if input url is not https
    """
    del form
    if not re.match(r"https://.*", field.data):
        raise ValidationError("URLs must use HTTPS")


class ElementForm(FlaskForm):
    """Form creating a new element."""

    element_type = SelectField("Type", choices=[(type.name, type.name) for type in ElementType])


class WebhookForm(FlaskForm):
    """Form for creating or editing a webhook."""

    name = StringField(validators=[DataRequired(), Length(min=1, max=100)])
    url = StringField(
        validators=[
            DataRequired(),
            URL(require_tld=True, allow_ip=False),
            validate_is_https,
            Length(min=1, max=2048),
        ]
    )
    bits_product = SelectField(
        "Bits cost", choices=[(product.name, product.value) for product in BitsProduct]
    )
    name = StringField(validators=[DataRequired(), Length(min=1, max=100)])
    include_transaction_data = BooleanField("include transaction data")
    extra_data = StringField(
        "data",
        validators=[DataRequired(), Length(min=1, max=2000), validate_is_json],
        widget=TextArea(),
    )
    test_webhook = SubmitField("Test Webhook")


class LayoutForm(FlaskForm):
    """Form for creating or editing a new layout."""

    name = StringField(validators=[DataRequired(), Length(min=1, max=100)])
    title = StringField(validators=[Length(min=0, max=26)])
    show_title = BooleanField("show title")


class LayoutSelectForm(FlaskForm):
    """Form to manage layouts."""

    layouts = SelectField("Select Layout", choices=[])
    edit = SubmitField("Edit Title")
    make_active = SubmitField("Activate")
    delete = SubmitField("Delete Layout")


@bp.route("/webhook/<int:webhook_id>", methods=["POST"])
@verify.token_required
@verify.owned_by_broadcaster
def redeem(channel_id: int, role: str, webhook_id: int) -> Response:
    """Redeem a webhook using bits. The receipt is verified to ensure a purchase has been made.

    :param channel_id: id of the channel the request was sent from
    :param role: role of the user making the request
    :param webhook_id: id of the webhook that is being redeemed
    :return: 200 response if the webhook was redeemed successfully
    """

    current_app.logger.debug("Redeem webhook %s %s", channel_id, role)

    data = request.get_json()

    current_app.logger.debug(data)
    transaction = data["transaction"]
    transaction_receipt = transaction["transactionReceipt"]
    receipt_decode = jwt.decode(
        transaction_receipt,
        key=base64.b64decode(current_app.config["EXTENSION_SECRET"]),
        algorithms=["HS256"],
    )
    current_app.logger.debug("decoded jwt: %s", receipt_decode)
    webhook = Webhook.query.filter(Webhook.id == webhook_id).one()

    webhook_data = webhook.data
    if webhook.include_transaction_data:
        webhook_data["transaction"] = transaction

    req = requests.post(
        webhook.url, json=webhook_data, timeout=current_app.config["REQUEST_TIMEOUT"]
    )
    req.raise_for_status()
    resp = make_response(req.text)

    return resp


@bp.route("/element/image/<int:image_id>", methods=["GET"])
def image_get(image_id: int) -> Response:
    """Serve static images.

    :params image_id: id of the image to serve
    :return: http response containing the image.
    """
    image = Image.query.filter(Image.id == image_id).one()
    resp = make_response(image.data)
    resp.headers = {
        "Content-type": "image/png",
        "Cache-Control": "public, max-age=86400",
    }

    return resp


@bp.route("/element/<int:element_id>/text/<int:text_id>/edit", methods=["GET", "PUT"])
@verify.token_required
@verify.is_broadcaster
@verify.owned_by_broadcaster
def text_edit(channel_id: int, role: str, element_id: int, text_id: int) -> Response:
    """Form for editing a text element.

    :param channel_id: id of the channel the request was sent from
    :param role: role of the user making the request
    :param element_id: underlying element id
    :param text_id: id of the text element being edited
    :return: text edit form or status message
    """
    del role

    current_app.logger.info("text_id=%s element_id=%s", text_id, element_id)

    form = TextForm()

    text = Text.query.filter(Text.id == text_id).one()

    if request.method == "PUT":
        if form.validate():
            current_app.logger.info("form valid")
            current_app.logger.info(form.data)
            text.text = form.text.data
            db.session.commit()
            twitch.send_refresh_pubsub(channel_id)

            resp = make_response("<p class='success-message'>Text updated</p>", 201)
            resp.headers["HX-Trigger-After-Swap"] = "layoutUpdate"
            resp.headers["Access-Control-Expose-Headers"] = "*"

            return resp

        current_app.logger.info("form invalid")
        current_app.logger.info(form.errors)
        errors_html = ""
        for field, error in form.errors.items():
            errors_html += f"{field}: {', '.join(error)}<br>"

        return make_response(f"<p class='error-message'>{errors_html}</p>", 400)

    if request.method == "GET":
        form.text.data = text.text

    return render_template(
        "text_form.html",
        form_type="edit",
        form_url=f"{current_app.config['EBS_URL']}/element/{element_id}/text/{text_id}/edit",
        form=form,
    )


@bp.route("/layout/<int:layout_id>/text/create", methods=["GET", "POST"])
@verify.token_required
@verify.is_broadcaster
@verify.owned_by_broadcaster
def text_create(channel_id: int, role: str, layout_id: int) -> Response:
    """Form for creating a text element.

    :param channel_id: id of the channel the request was sent from
    :param role: role of the user making the request
    :param layout_id: id of the layout to create the text element in
    :return: text create form or status message
    """
    del role
    current_app.logger.info("layout_id=%s", layout_id)

    form = TextForm()

    if request.method == "POST":
        if form.validate():
            current_app.logger.info("form valid")
            current_app.logger.info(form.data)
            element = Element(
                layout_id=layout_id,
                element_type=ElementType.text,
                position=utils.get_next_layout_position(layout_id),
            )
            db.session.add(element)
            db.session.commit()
            text = Text(text=form.text.data, element_id=element.id)
            db.session.add(text)
            db.session.commit()
            # re-order elements
            utils.ensure_layout_order(layout_id)

            twitch.send_refresh_pubsub(channel_id)

            resp = make_response("<p class='success-message'>Text created</p>", 200)
            resp.headers["HX-Trigger-After-Swap"] = "layoutUpdate"
            resp.headers["Access-Control-Expose-Headers"] = "*"
            return resp

        current_app.logger.info("form invalid")
        current_app.logger.info(form.errors)
        errors_html = ""
        for field, error in form.errors.items():
            errors_html += f"{field}: {', '.join(error)}<br>"

        return make_response(f"<p class='error-message'>{errors_html}</p>", 400)

    return render_template(
        "text_form.html",
        form_type="create",
        form_url=f"{current_app.config['EBS_URL']}/layout/{layout_id}/text/create",
        form=form,
    )


@bp.route("/element/<int:element_id>/image/<int:image_id>/edit", methods=["GET", "PUT"])
@verify.token_required
@verify.is_broadcaster
@verify.owned_by_broadcaster
def image_edit(channel_id: int, role: str, element_id: int, image_id: int) -> Response:
    """Form for editing an image element.

    :param channel_id: id of the channel the request was sent from
    :param role: role of the user making the request
    :param element_id: underlying element id
    :param image_id: id of the image element being edited
    :return: image edit form or status message
    """
    del role

    current_app.logger.info("image_id=%s element_id=%s", image_id, element_id)

    form = ImageForm()

    image = Image.query.filter(Image.id == image_id).one()

    if request.method == "PUT":
        if form.validate():
            current_app.logger.info("form valid")
            current_app.logger.info(form.data)
            image.data = form.image.data.read()
            image.filename = form.image.data.filename
            db.session.commit()
            twitch.send_refresh_pubsub(channel_id)

            resp = make_response("<p class='success-message'>Image updated</p>", 201)
            resp.headers["HX-Trigger-After-Swap"] = "layoutUpdate"
            resp.headers["Access-Control-Expose-Headers"] = "*"
            return resp

        current_app.logger.info("form invalid")
        current_app.logger.info(form.errors)
        errors_html = ""
        for field, error in form.errors.items():
            errors_html += f"{field}: {', '.join(error)}<br>"

        return make_response(f"<p class='error-message'>{errors_html}</p>", 400)

    return render_template(
        "image_form.html",
        form_type="edit",
        form_url=f"{current_app.config['EBS_URL']}/element/{element_id}/image/{image_id}/edit",
        form=form,
    )


@bp.route("/layout/<int:layout_id>/image/create", methods=["GET", "POST"])
@verify.token_required
@verify.is_broadcaster
@verify.owned_by_broadcaster
def image_create(channel_id: int, role: str, layout_id: int) -> Response:
    """Form for creating an image element.

    :param channel_id: id of the channel the request was sent from
    :param role: role of the user making the request
    :param layout_id: id of the layout to create the image element in
    :return: image create form or status message
    """

    del role

    form = ImageForm()

    if request.method == "POST":
        if form.validate():
            current_app.logger.info("form valid")
            current_app.logger.info(form.data)
            element = Element(
                layout_id=layout_id,
                element_type=ElementType.image,
                position=utils.get_next_layout_position(layout_id),
            )
            db.session.add(element)
            db.session.commit()
            image = Image(
                filename=form.image.data.filename,
                data=form.image.data.read(),
                element_id=element.id,
            )
            db.session.add(image)
            db.session.commit()
            # re-order elements
            utils.ensure_layout_order(layout_id)

            twitch.send_refresh_pubsub(channel_id)

            resp = make_response("<p class='success-message'>Image created</p>", 200)
            resp.headers["HX-Trigger-After-Swap"] = "layoutUpdate"
            resp.headers["Access-Control-Expose-Headers"] = "*"

            return resp

        current_app.logger.info("form invalid")
        current_app.logger.info(form.errors)
        errors_html = ""
        for field, error in form.errors.items():
            errors_html += f"{field}: {', '.join(error)}<br>"

        return make_response(f"<p class='error-message'>{errors_html}</p>", 400)

    return render_template(
        "image_form.html",
        form_type="create",
        form_url=f"{current_app.config['EBS_URL']}/layout/{layout_id}/image/create",
        form=form,
    )


@bp.route("/layout/<int:layout_id>/element/create", methods=["GET"])
@verify.token_required
@verify.is_broadcaster
@verify.owned_by_broadcaster
def element_create(channel_id: int, role: str, layout_id: int) -> Response:
    """Form for creating a new element.

    :param channel_id: id of the channel the request was sent from
    :param role: role of the user making the request
    :param layout_id: id of the layout to create the element in
    :return: element create form
    """

    del channel_id, role

    return render_template(
        "element_form.html",
        image_create_url=f"{current_app.config['EBS_URL']}/layout/{layout_id}/image/create",
        text_create_url=f"{current_app.config['EBS_URL']}/layout/{layout_id}/text/create",
        webhook_create_url=f"{current_app.config['EBS_URL']}/layout/{layout_id}/webhook/create",
    )


def test_webhook(form: WebhookForm) -> None:
    """Test a webhook based on data provided from a form.

    :param form: WebhookForm with data to test a new or modified webhook
    :raises: HTTPError if there was an error with the webhook
    """
    bits_product = form.bits_product.data
    bits_cost = BitsProduct[bits_product].value

    webhook_data = json.loads(form.extra_data.data)
    transaction_example = {
        "product": {
            "sku": form.bits_product.data,
            "displayName": f"{bits_cost} Bit Reward",
            "cost": {"amount": str(bits_cost), "type": "bits"},
            "inDevelopment": False,
        },
        "transactionId": str(uuid4()),
        "userId": "123456789",
        "displayName": "test_user",
        "initiator": "current_user",
        "transactionReceipt": "<jwt with transaction receipt goes here>",
    }

    if form.include_transaction_data:
        webhook_data["transaction"] = transaction_example

    req = requests.post(
        form.url.data, json=webhook_data, timeout=current_app.config["REQUEST_TIMEOUT"]
    )
    req.raise_for_status()


@bp.route("/element/<int:element_id>/webhook/<int:webhook_id>/edit", methods=["GET", "PUT"])
@verify.token_required
@verify.is_broadcaster
@verify.owned_by_broadcaster
def webhook_edit(channel_id: int, role: str, element_id: int, webhook_id: int) -> Response:
    """Form for editing a webhook element.

    :param channel_id: id of the channel the request was sent from
    :param role: role of the user making the request
    :param element_id: underlying element id
    :param webhook_id: id of the webhook element being edited
    :return: webhook edit form or status message
    """

    del role

    current_app.logger.info("webhook_id=%s element_id=%s", webhook_id, element_id)

    form = WebhookForm()

    webhook = Webhook.query.filter(Webhook.id == webhook_id).one()

    if request.method == "PUT":
        if form.validate():
            current_app.logger.info("form valid")
            current_app.logger.info(form.data)
            if form.test_webhook.data:
                try:
                    test_webhook(form)
                except requests.RequestException:
                    return make_response("<p class='error-message'>Webhook failed</p>", 500)
                return make_response("<p class='success-message'>Webhook OK</p>")

            webhook.url = form.url.data
            webhook.name = form.name.data
            webhook.bits_product = form.bits_product.data
            webhook.data = json.loads(form.extra_data.data)
            webhook.include_transaction_data = form.include_transaction_data.data
            db.session.commit()
            twitch.send_refresh_pubsub(channel_id)
            resp = make_response("<p class='success-message'>Webhook updated</p>", 201)
            resp.headers["HX-Trigger-After-Swap"] = "layoutUpdate"
            resp.headers["Access-Control-Expose-Headers"] = "*"
            return resp

        current_app.logger.info("form invalid")
        current_app.logger.info(form.errors)
        errors_html = ""
        for field, error in form.errors.items():
            errors_html += f"{field}: {', '.join(error)}<br>"

        return make_response(f"<p class='error-message'>{errors_html}</p>", 400)

    if request.method == "GET":
        form.name.data = webhook.name
        form.url.data = webhook.url
        form.bits_product.data = webhook.bits_product.name
        form.include_transaction_data.data = webhook.include_transaction_data
        form.extra_data.data = json.dumps(webhook.data, indent=2)

    return render_template(
        "webhook_form.html",
        form_type="edit",
        form_url=f"{current_app.config['EBS_URL']}/element/{element_id}/webhook/{webhook_id}/edit",
        form=form,
    )


@bp.route("/layout/<int:layout_id>/webhook/create", methods=["GET", "POST"])
@verify.token_required
@verify.is_broadcaster
@verify.owned_by_broadcaster
def webhook_create(channel_id: int, role: str, layout_id: int) -> Response:
    """Form for creating a webhook element.

    :param channel_id: id of the channel the request was sent from
    :param role: role of the user making the request
    :param layout_id: id of the layout to create the webhook element in
    :return: webhook create form or status message
    """

    del role
    current_app.logger.info("layout_id=%s", layout_id)

    form = WebhookForm()

    if request.method == "POST":
        if form.validate():
            current_app.logger.info("form valid")
            current_app.logger.info(form.data)
            if form.test_webhook.data:
                try:
                    test_webhook(form)
                except requests.RequestException:
                    return make_response("<p class='error-message'>Webhook failed</p>", 500)
                return make_response("<p class='success-message'>Webhook OK</p>")

            element = Element(
                layout_id=layout_id,
                element_type=ElementType.webhook,
                position=utils.get_next_layout_position(layout_id),
            )
            db.session.add(element)
            db.session.commit()
            webhook = Webhook(
                url=form.url.data,
                name=form.name.data,
                bits_product=form.bits_product.data,
                data=json.loads(form.extra_data.data),
                include_transaction_data=form.include_transaction_data.data,
                element_id=element.id,
            )
            db.session.add(webhook)
            db.session.commit()
            # re-order elements
            utils.ensure_layout_order(layout_id)
            twitch.send_refresh_pubsub(channel_id)

            resp = make_response("<p class='success-message'>Webhook created</p>", 200)
            resp.headers["HX-Trigger-After-Swap"] = "layoutUpdate"
            resp.headers["Access-Control-Expose-Headers"] = "*"
            return resp

        current_app.logger.info("form invalid")
        current_app.logger.info(form.errors)
        errors_html = ""
        for field, error in form.errors.items():
            errors_html += f"{field}: {', '.join(error)}<br>"

        return make_response(f"<p class='error-message'>{errors_html}</p>", 400)

    if request.method == "GET":
        form.extra_data.data = "{}"
        form.bits_product.data = BitsProduct.reward_100bits.name
        current_app.logger.info(form.bits_product.data)

    return render_template(
        "webhook_form.html",
        form_type="create",
        form_url=f"{current_app.config['EBS_URL']}/layout/{layout_id}/webhook/create",
        form=form,
    )


@bp.route("/element/<int:element_id>", methods=["DELETE"])
@verify.token_required
@verify.is_broadcaster
@verify.owned_by_broadcaster
def element_delete(channel_id: int, role: str, element_id: int) -> Response:
    """Delete a specific element.

    :param channel_id: id of the channel the request was sent from
    :param role: role of the user making the request
    :param element_id: id of element to delete
    :return: 200 response if the element was successfully deleted
    """
    del role
    current_app.logger.info("element_id=%s", element_id)

    element = Element.query.filter(Element.id == element_id).one()
    layout_id = element.layout_id
    db.session.delete(element)
    db.session.commit()

    # ensure element positions are sequential
    utils.ensure_layout_order(layout_id)

    twitch.send_refresh_pubsub(channel_id)

    resp = make_response("<p>Element deleted</p>")
    resp.headers["HX-Trigger-After-Swap"] = "layoutUpdate"
    resp.headers["Access-Control-Expose-Headers"] = "*"
    return resp


@bp.route("/layout/<int:layout_id>", methods=["DELETE"])
@verify.token_required
@verify.is_broadcaster
@verify.owned_by_broadcaster
def layout_delete(channel_id: int, role: str, layout_id: int) -> Response:
    """Delete a specific layout.

    :param channel_id: id of the channel the request was sent from
    :param role: role of the user making the request
    :param layout_id: id of layout to delete
    :return: 200 response if the layout was successfully deleted
    """
    del role
    current_app.logger.info("layout_id=%s", layout_id)

    layout_obj = Layout.query.filter(Layout.id == layout_id).one()
    db.session.delete(layout_obj)
    db.session.commit()

    twitch.send_refresh_pubsub(channel_id)
    resp = make_response("<p>Layout deleted</p>")
    resp.headers["HX-Trigger-After-Swap"] = "layoutUpdate, selectRefresh"
    resp.headers["Access-Control-Expose-Headers"] = "*"
    return resp


@bp.route("/element/<int:element_id>/confirm-delete", methods=["GET"])
@verify.token_required
@verify.is_broadcaster
@verify.owned_by_broadcaster
def element_confirm_delete(channel_id: int, role: str, element_id: int) -> Response:
    """Form for confirming the deletion of an element.

    :param channel_id: id of the channel the request was sent from
    :param role: role of the user making the request
    :param element_id: id of element to delete
    :return: delete confirmation form
    """
    del channel_id, role

    current_app.logger.info("element_id=%s", element_id)

    element = Element.query.filter(Element.id == element_id).one()

    element_name = ""
    if element.element_type == ElementType.image:
        element_name = element.image.filename
    if element.element_type == ElementType.text:
        element_name = textwrap.shorten(element.text.text, 30)
    if element.element_type == ElementType.webhook:
        element_name = element.webhook.name

    delete_url = f"{current_app.config['EBS_URL']}/element/{element_id}"
    delete_prompt = (
        f"Are you sure you want to delete this {element.element_type.name} "
        f"element?<br>({element_name})"
    )
    return render_template(
        "confirm_delete_form.html", delete_url=delete_url, delete_prompt=delete_prompt
    )


@bp.route("/layout/<int:layout_id>/confirm-delete", methods=["GET", "DELETE"])
@verify.token_required
@verify.is_broadcaster
@verify.owned_by_broadcaster
def layout_confirm_delete(channel_id: int, role: str, layout_id: int) -> Response:
    """Form for confirming the deletion of an layout.

    :param channel_id: id of the channel the request was sent from
    :param role: role of the user making the request
    :param layout_id: id of layout to delete
    :return: delete confirmation form
    """
    del channel_id, role

    current_app.logger.info("layout_id=%s", layout_id)

    layout_obj = Layout.query.filter(Layout.id == layout_id).one()

    delete_url = f"{current_app.config['EBS_URL']}/layout/{layout_obj.id}"
    delete_prompt = f"Are you sure you want to delete this layout?<br>({layout_obj.name})"
    return render_template(
        "confirm_delete_form.html", delete_url=delete_url, delete_prompt=delete_prompt
    )


@bp.route("/layout/<int:layout_id>/update-order", methods=["POST"])
@verify.token_required
@verify.is_broadcaster
@verify.owned_by_broadcaster
def layout_update_order(channel_id: int, role: str, layout_id: int) -> Response:
    """Update the order that the elements of a layout are displayed.

    :param channel_id: id of the channel the request was sent from
    :param role: role of the user making the request
    :param layout_id: id of layout to modify the order for
    :return: layout html with new order
    """
    del role

    current_app.logger.info(request.form.copy())

    layout_obj = Layout.query.filter(Layout.id == layout_id).one()

    elements = Element.query.filter(Element.layout_id == layout_id).order_by(Element.position).all()

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

    twitch.send_refresh_pubsub(channel_id)

    resp = make_response(get_layout_html(layout_obj, True))

    return resp


def ensure_broadcaster_exists(broadcaster_id: int) -> Broadcaster:
    """Ensure that a broadcaster exists in the database.

    :param broadcaster_id: id of the broadcaster
    :return: broadcaster object corresponding to the id
    """

    try:
        broadcaster = Broadcaster.query.filter(Broadcaster.id == broadcaster_id).one()
        return broadcaster
    except NoResultFound:
        pass

    broadcaster = Broadcaster(id=broadcaster_id)
    db.session.add(broadcaster)
    db.session.commit()

    return broadcaster


@bp.route("/layout/create", methods=["GET", "POST"])
@verify.token_required
@verify.is_broadcaster
def layout_create(channel_id: int, role: str) -> Response:
    """Form for creating a layout.

    :param channel_id: id of the channel the request was sent from
    :param role: role of the user making the request
    :return: layout create form or status message
    """
    del role

    form = LayoutForm()

    if request.method == "POST":
        if form.validate():
            ensure_broadcaster_exists(channel_id)
            current_app.logger.info("form valid")
            current_app.logger.info(form.data)

            layout_obj = Layout(
                broadcaster_id=channel_id,
                name=form.name.data,
                title=form.title.data,
                show_title=form.show_title.data,
            )

            db.session.add(layout_obj)
            db.session.commit()

            broadcaster = Broadcaster.query.filter(Broadcaster.id == channel_id).one()

            broadcaster.editing_layout = layout_obj.id
            db.session.commit()

            resp = make_response("<p class='success-message'>Layout created</p>", 200)
            resp.headers["HX-Trigger-After-Swap"] = "selectRefresh"
            resp.headers["Access-Control-Expose-Headers"] = "*"

            return resp

        current_app.logger.info("form invalid")
        current_app.logger.info(form.errors)
        errors_html = ""
        for field, error in form.errors.items():
            errors_html += f"{field}: {', '.join(error)}<br>"

        resp = make_response(f"<p class='error-message'>{errors_html}</p>", 400)

        return resp

    if request.method == "GET":
        form.show_title.data = True

    resp = make_response(
        render_template(
            "layout_form.html",
            form_type="create",
            form_url=f"{current_app.config['EBS_URL']}/layout/create",
            form=form,
        )
    )

    return resp


@bp.route("/layout/<int:layout_id>/edit", methods=["GET", "PUT"])
@verify.token_required
@verify.is_broadcaster
@verify.owned_by_broadcaster
def layout_edit(channel_id: int, role: str, layout_id: int) -> Response:
    """Form for editing a layout.

    :param channel_id: id of the channel the request was sent from
    :param role: role of the user making the request
    :param layout_id: _description_
    :return: layout edit form or status message
    """
    del channel_id, role

    form = LayoutForm()

    layout_obj = Layout.query.filter(Layout.id == layout_id).one()

    if request.method == "PUT":
        if form.validate():

            layout_obj.title = form.title.data
            layout_obj.show_title = form.show_title.data

            db.session.commit()

            resp = make_response("<p class='success-message'>Layout modified</p>", 200)
            resp.headers["HX-Trigger-After-Swap"] = "layoutUpdate"
            resp.headers["Access-Control-Expose-Headers"] = "*"

            return resp

        current_app.logger.info("form invalid")
        current_app.logger.info(form.errors)
        errors_html = ""
        for field, error in form.errors.items():
            errors_html += f"{field}: {', '.join(error)}<br>"

        resp = make_response(f"<p class='error-message'>{errors_html}</p>", 400)

        return resp

    if request.method == "GET":
        form.name.data = layout_obj.name
        form.show_title.data = layout_obj.show_title
        form.title.data = layout_obj.title

    resp = make_response(
        render_template(
            "layout_form.html",
            form_type="edit",
            form_url=f"{current_app.config['EBS_URL']}/layout/{layout_id}/edit",
            form=form,
        )
    )

    return resp


def get_current_layout(channel_id: int) -> Optional[Layout]:
    """_summary_

    :param channel_id: id of the channel to get the current layout for
    :return: layout object if a current layout is set, None otherwise
    """
    try:
        broadcaster = Broadcaster.query.filter(Broadcaster.id == channel_id).one()
        assert broadcaster.current_layout is not None
        layout_obj = Layout.query.filter(Layout.id == broadcaster.current_layout).one()
        return layout_obj
    except (NoResultFound, AssertionError):
        return None


@bp.route("/layout", methods=["GET"])
@verify.token_required
def layout(channel_id: int, role: str) -> Response:
    """Display the current layout.

    :param channel_id: id of the channel the request was sent from
    :param role: role of the user making the request
    :return: response with rendered layout
    """
    del channel_id, role

    edit = False
    if "edit" in request.args:
        edit = request.args["edit"] == "true"

    layout_obj = get_current_layout(channel_id)

    if not layout:
        current_app.logger.warning(
            "Could not display layout, layout_id=%s broadcaster=%s", layout_obj, channel_id
        )
        return make_response("<p class='centered'>Layout not configured</p>")

    return make_response(get_layout_html(layout_obj, edit))


@bp.route("/layouts", methods=["GET", "POST"])
@verify.token_required
@verify.is_broadcaster
def layouts(channel_id: int, role: str) -> Response:
    """Layout select form.

    :param channel_id: id of the channel the request was sent from
    :param role: role of the user making the request
    """
    del role

    form = LayoutSelectForm()

    ensure_broadcaster_exists(channel_id)

    layout_list = []
    try:
        broadcaster = Broadcaster.query.filter(Broadcaster.id == channel_id).one()

        layout_list = Layout.query.filter(Layout.broadcaster_id == broadcaster.id).all()
    except NoResultFound:
        pass

    layout_choices = []
    for layout_obj in layout_list:
        choice_text = layout.name
        if layout_obj.id == broadcaster.current_layout:
            choice_text += " (ACTIVE)"

        layout_choices.append((layout_obj.id, choice_text))

    form.layouts.choices = layout_choices

    if request.method == "POST":
        if form.validate():
            current_app.logger.info("form valid")
            current_app.logger.info(form.data)

            layout_obj = Layout.query.filter(Layout.id == form.layouts.data).one()

            broadcaster.editing_layout = layout_obj.id

            if form.delete.data:
                current_app.logger.info("delete")
                resp = make_response(
                    f"""
                    <div
                        hx-trigger="load"
                        hx-get=
                        "{current_app.config['EBS_URL']}/layout/{form.layouts.data}/confirm-delete"
                        hx-target="#dialog"
                    </div>"""
                )
                resp.headers["HX-Retarget"] = "#dialog"
                resp.headers["Access-Control-Expose-Headers"] = "*"
                return resp

            if form.edit.data:
                current_app.logger.info("edit")
                resp = make_response(
                    f"""
                    <div
                        hx-trigger="load"
                        hx-get="{current_app.config['EBS_URL']}/layout/{form.layouts.data}/edit"
                        hx-target="#dialog"
                    </div>"""
                )
                resp.headers["HX-Retarget"] = "#dialog"
                resp.headers["Access-Control-Expose-Headers"] = "*"
                return resp

            resp = make_response(get_layout_html(layout_obj, edit=True))
            resp.headers["Access-Control-Expose-Headers"] = "*"

            if form.make_active.data:
                broadcaster.current_layout = layout_obj.id
                current_app.logger.info(layout_obj.id)
                db.session.commit()
                twitch.send_refresh_pubsub(channel_id)
                resp.headers["HX-Trigger"] = "selectRefresh"

            return resp

        current_app.logger.info("form invalid")
        current_app.logger.info(form.data)
        current_app.logger.info(form.layouts.choices)
        current_app.logger.info(form.errors)
        resp = make_response("<p class='centered'>Please select or create a layout to edit</p>")
        return resp

    if request.method == "GET":
        current_app.logger.info("EDITING LAYOUT %s", broadcaster.editing_layout)
        form.layouts.data = str(broadcaster.editing_layout)

    return render_template(
        "select_layout_form.html",
        form_url=f"{current_app.config['EBS_URL']}/layouts",
        form=form,
    )


def get_layout_html(layout_obj: Layout, edit: bool) -> str:
    """Render the html for a given layout.

    :param layout_obj: layout object to render as html
    :param edit: render the layout with editing controls
    :return: rendered html of the layout
    """

    current_app.logger.debug(layout_obj)
    elements = (
        Element.query.filter(Element.layout_id == layout_obj.id).order_by(Element.position).all()
    )
    current_app.logger.debug(elements)
    elements_list = []
    edit_button = ""
    for element in elements:
        current_app.logger.debug(element)
        entry = None

        if edit:
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
            current_app.logger.debug("image")
            image = Image.query.filter(Image.element_id == element.id).one()
            image_url = (
                f"{current_app.config['EBS_URL']}/element/image/{image.id}"
                f"?version={image.date_modified.strftime('%s')}"
            )
            if edit:
                edit_url = (
                    f"{current_app.config['EBS_URL']}/element/{element.id}/image/{image.id}/edit"
                )
                edit_button = edit_button_template.format(element_id=element.id, edit_url=edit_url)
            entry = f"""
                <input type='hidden' name='element' value='{element.position}'/>
                <img id='image-{image.id}' src='{image_url}'>
            """
        if element.element_type == ElementType.text:
            current_app.logger.debug("text")
            text = Text.query.filter(Text.element_id == element.id).one()
            if edit:
                edit_url = (
                    f"{current_app.config['EBS_URL']}/element/{element.id}/text/{text.id}/edit"
                )
                edit_button = edit_button_template.format(element_id=element.id, edit_url=edit_url)
            entry = f"""
                <input type='hidden' name='element' value='{element.position}'/>
                <p id='text-{text.id}'>{text.text}</p>
                """
        if element.element_type == ElementType.webhook:
            current_app.logger.debug("webhook")
            webhook = Webhook.query.filter(Webhook.element_id == element.id).one()

            if edit:
                edit_url = (
                    f"{current_app.config['EBS_URL']}/element/{element.id}/"
                    f"webhook/{webhook.id}/edit"
                )
                edit_button = edit_button_template.format(element_id=element.id, edit_url=edit_url)

            entry = f"""
                <input type='hidden' name='element' value='{element.position}'/>
                <button
                    type="button"
                    class="webhook-button"
                    id="webhook-{webhook.id}"
                    data-id="{webhook.id}"
                    data-product="{webhook.bits_product.name}"
                >
                    <p style="display:inline;">
                        {webhook.name}<br><br>
                        {webhook.bits_product.value} <img src='bit.png' width='14' height='14'><br>
                    </p>
                </button>
            """

        if entry:
            if edit:
                entry += f"""
                    <div class='edit-overlay'>
                        {edit_button}
                        {delete_button}
                    </div>
                """
            elements_list.append(
                f"""
            <div class='element' id='element-{element.id}'>
                {entry}
            </div>
            """
            )

    if edit:
        add_new_button = f"""
        <div id="add-new-div" class="add-new-div">
            <button
                type="button"
                hx-get="{current_app.config['EBS_URL']}/layout/{layout_obj.id}/element/create"
                hx-target="#dialog"
                id="add-new-button"
                type="button"
                >Add new</button>
        </div>
        """
        elements_list.append(add_new_button)

    return render_template(
        "layout.html",
        show_title=layout.show_title,
        title=layout.title,
        update_order_url=f"{current_app.config['EBS_URL']}/layout/{layout_obj.id}/update-order",
        edit=edit,
        elements_list=elements_list,
    )
