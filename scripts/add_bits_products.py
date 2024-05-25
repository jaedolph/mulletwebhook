import base64
import json
import time

import jwt
import requests
from flask import current_app
from typing import Any

from mulletwebhook import create_app
from mulletwebhook.models.enums import BitsProduct


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


def get_bits_products(access_token: str) -> dict[str, Any]:

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Client-ID": current_app.config["CLIENT_ID"],
    }
    print(headers)
    resp = requests.get(
        "https://api.twitch.tv/helix/bits/extensions",
        timeout=current_app.config["REQUEST_TIMEOUT"],
        headers=headers,
    )
    print(resp.text)
    resp.raise_for_status()

    try:
        data = json.loads(resp.json()["data"])
    except Exception:
        data = None

    return data


def update_bits_product(access_token: str, product: BitsProduct) -> None:

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Client-ID": current_app.config["CLIENT_ID"],
    }
    product_json = {
        "sku": product.name,
        "cost": {
            "amount": product.value,
            "type": "bits",
        },
        "display_name": f"{product.value} Bit Reward",
        "in_development": False,
        "is_broadcast": False,
    }
    print(f"updating product: {product_json}")
    resp = requests.put(
        "https://api.twitch.tv/helix/bits/extensions",
        timeout=current_app.config["REQUEST_TIMEOUT"],
        json=product_json,
        headers=headers,
    )
    print(f"response: {resp.status_code}, {resp.text}")
    resp.raise_for_status()


def main():
    with create_app().app_context():
        access_token = get_app_access_token()
        current_bits_products = get_bits_products(access_token)

        for product in BitsProduct:
            update_bits_product(access_token, product)


if __name__ == "__main__":
    main()
