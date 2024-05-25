"""Functions related to verification of auth tokens."""

from functools import wraps
from typing import Callable, TypeVar, Tuple, cast
import base64

import jwt
from flask import Request, current_app, abort
from flask import request as flask_request
from mulletwebhook.models.broadcaster import Broadcaster
from mulletwebhook.models.layout import Layout
from mulletwebhook.models.element import Element, Image, Text, Webhook

R = TypeVar("R")


def token_required(func: Callable[[int, str], R]) -> Callable[[int, str], R]:
    """Decorator to validate JWT and get the associated channel_id and role.

    :param func: function to decorate
    :return: decorated function
    """

    @wraps(func)
    def decorated_function(*args, **kwargs) -> R:

        if not current_app.config["TESTING"]:
            try:
                channel_id, role = verify_jwt(flask_request)
            except PermissionError as exp:
                error_msg = f"authentication failed: {exp}"
                current_app.logger.debug(error_msg)
                return abort(401, error_msg)
        else:
            channel_id = 12345678
            role = "broadcaster"

        current_app.logger.debug(
            "authenticated request for channel_id=%s role=%s", channel_id, role
        )
        return func(*args, channel_id=channel_id, role=role, **kwargs)

    return cast(Callable[[int, str], R], decorated_function)


def owned_by_broadcaster(func: Callable[[int, str], R]) -> Callable[[int, str], R]:
    """ """

    @wraps(func)
    def decorated_function(*args, **kwargs) -> R:

        current_app.logger.info(kwargs)

        channel_id = kwargs["channel_id"]

        if "layout_id" in kwargs:
            layout_id = kwargs["layout_id"]
            layout = Layout.query.filter(Layout.id == layout_id).one()
            if layout.broadcaster.id != channel_id:
                return abort(
                    401,
                    f"layout with id={layout_id} is not owned by broadcaster={layout.broadcaster.name}",
                )

        if "element_id" in kwargs:
            element_id = kwargs["element_id"]
            element = Element.query.filter(Element.id == element_id).one()
            if element.layout.broadcaster.id != channel_id:
                return abort(
                    401,
                    f"element with id={element_id} is not owned by broadcaster={element.layout.broadcaster.name}",
                )

        if "image_id" in kwargs:
            image_id = kwargs["image_id"]
            image = Image.query.filter(Image.id == image_id).one()
            if image.element.layout.broadcaster.id != channel_id:
                return abort(
                    401,
                    f"image with id={image_id} is not owned by broadcaster={image.element.layout.broadcaster.name}",
                )

        if "text_id" in kwargs:
            text_id = kwargs["text_id"]
            text = Text.query.filter(Text.id == text_id).one()
            if text.element.layout.broadcaster.id != channel_id:
                return abort(
                    401,
                    f"text with id={text_id} is not owned by broadcaster={text.element.layout.broadcaster.name}",
                )

        if "webhook_id" in kwargs:
            webhook_id = kwargs["webhook_id"]
            webhook = Webhook.query.filter(Webhook.id == webhook_id).one()
            if webhook.element.layout.broadcaster.id != channel_id:
                return abort(
                    401,
                    f"webhook with id={webhook_id} is not owned by broadcaster={webhook.element.layout.broadcaster.name}",
                )

        return func(*args, **kwargs)

    return cast(Callable[[int, str], R], decorated_function)


def is_broadcaster(func: Callable[[int, str], R]) -> Callable[[int, str], R]:
    """ """

    @wraps(func)
    def decorated_function(*args, **kwargs) -> R:
        current_app.logger.info("role=%s", kwargs["role"])
        if kwargs["role"] != "broadcaster":
            abort(403, "user role is not broadcaster")

        return func(*args, **kwargs)

    return cast(Callable[[int, str], R], decorated_function)


def verify_jwt(request: Request) -> Tuple[int, str]:
    """Verifies and decodes auth information from a JWT.

    :param request: Request object containing the JWT
    :raises PermissionError: if verifying or decoding the JWT fails
    :return: the channel id the request was made for and the role of the user making the request
    """
    headers = request.headers

    try:
        auth_header = headers["Authorization"]
        current_app.logger.debug("auth_header=%s", auth_header)
        token = auth_header.split(" ")[1].strip()
        current_app.logger.debug("token=%s", token)
    except (KeyError, IndexError) as exp:
        error_msg = f"could not get auth token from headers, {exp.__class__.__name__}: {exp}"
        current_app.logger.debug(error_msg)
        raise PermissionError(error_msg) from exp

    payload = None
    try:
        payload = jwt.decode(
            token,
            key=base64.b64decode(current_app.config["EXTENSION_SECRET"]),
            algorithms=["HS256"],
        )
        current_app.logger.debug("payload: %s", payload)
        channel_id = int(payload["channel_id"])
        role = payload["role"]
        assert isinstance(channel_id, int)
        assert isinstance(role, str)
    except (jwt.exceptions.PyJWTError, AssertionError, KeyError, ValueError) as exp:
        error_message = f"could not validate jwt, {exp.__class__.__name__}: {exp}"
        current_app.logger.debug(error_message)
        raise PermissionError(error_message) from exp

    return channel_id, role
