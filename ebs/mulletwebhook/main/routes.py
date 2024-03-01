"""Main routes."""
from datetime import datetime

from flask import Blueprint, Response, abort, jsonify, make_response, request, current_app
import requests

from mulletwebhook import verify

bp = Blueprint("main", __name__)


@bp.route("/redeem", methods=["POST"])
@verify.token_required
def redeem(channel_id: int, role: str) -> Response:

    current_app.logger.info("Redeem webhook %s %s", channel_id, role)

    data = request.get_json()

    current_app.logger.info("data: %s", data)

    requests.post("https://api.mixitupapp.com/api/webhook/",json=data)

    resp = make_response("test")

    return resp
