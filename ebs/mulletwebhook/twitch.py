"""Twitch related functions."""

import base64
import time
from typing import Any

import jwt
import requests
from flask import current_app


def create_pubsub_jwt_headers(broadcaster_id: int) -> dict[str, Any]:
    """Create a JWT that can be used to send pubsub messages.

    :param broadcaster_id: id of the broadcaster to create the token for
    :return: dictionary of JWT headers that can be used for pubsub messages
    """
    jwt_payload = {
        "exp": int(time.time() + 10),
        "user_id": str(broadcaster_id),
        "role": "external",
        "channel_id": str(broadcaster_id),
        "pubsub_perms": {"send": ["broadcast"]},
    }

    jwt_token = jwt.encode(
        payload=jwt_payload,
        key=base64.b64decode(current_app.config["EXTENSION_SECRET"]),
    )

    headers = {
        "Authorization": "Bearer " + jwt_token,
        "Client-Id": current_app.config["CLIENT_ID"],
    }
    return headers


def send_refresh_pubsub(broadcaster_id: int) -> None:
    """Send a refresh message to the extension owned by a specific broadcaster.

    :param broadcaster_id: id of the broadcaster to send pubsub message for
    """

    current_app.logger.debug("sending refresh pubsub message")

    jwt_headers = create_pubsub_jwt_headers(broadcaster_id)

    body = {
        "target": ["broadcast"],
        "broadcaster_id": str(broadcaster_id),
        "message": "refresh",
    }

    resp = requests.post(
        "https://api.twitch.tv/helix/extensions/pubsub",
        timeout=current_app.config["REQUEST_TIMEOUT"],
        json=body,
        headers=jwt_headers,
    )
    current_app.logger.debug("response_status=%s response_text=%s", resp.status_code, resp.text)
    resp.raise_for_status()
