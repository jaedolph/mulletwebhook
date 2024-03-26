import base64
import json
import time

import jwt
import requests
from flask import current_app
from typing import Any

from mulletwebhook import create_app
from mulletwebhook.models.enums import BitsProduct


def create_pubsub_jwt_headers(broadcaster_id: int):
    jwt_payload = {
        "exp": int(time.time() + 10),
        "user_id": str(broadcaster_id),
        "role": "external",
        "channel_id": str(broadcaster_id),
        "pubsub_perms": {
            "send":[
                "broadcast"
            ]
        }
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


def get_app_access_token() -> str:
    """Gets an app access token using the "client credentials" twitch oauth flow.

    :raises RequestException: if request fails
    :raises KeyError: if response doesn't contain expected values
    :raises AssertionError: if the access token is in the wrong format
    :return: valid access token
    """
    print(current_app.config["CLIENT_ID"], current_app.config["CLIENT_SECRET"])
    req = requests.post(
        "https://id.twitch.tv/oauth2/token",
        params={
            "client_id": current_app.config["CLIENT_ID"],
            "client_secret": current_app.config["CLIENT_SECRET"],
            "grant_type": "client_credentials",
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
        timeout=current_app.config["REQUEST_TIMEOUT"],
    )

    try:
        req.raise_for_status()
        auth = req.json()
        current_app.logger.debug("auth: %s", auth)

        access_token = auth["access_token"]
        assert isinstance(access_token, str)
    except (requests.RequestException, KeyError, AssertionError) as exp:
        raise exp

    return access_token

def send_refresh_pubsub(broadcaster_id) -> None:
    """
    """
    current_app.logger.debug("sending refresh pubsub message")

    jwt_headers = create_pubsub_jwt_headers(broadcaster_id)

    body = {
        "target": ["broadcast"],
        "broadcaster_id": broadcaster_id,
        "message": "refresh"
    }

    resp = requests.post(
        "https://api.twitch.tv/helix/extensions/pubsub",
        timeout=current_app.config["REQUEST_TIMEOUT"],
        json=body,
        headers=jwt_headers,
    )
    current_app.logger.debug("response_status=%s response_text=%s", resp.status_code, resp.text)
    resp.raise_for_status()
