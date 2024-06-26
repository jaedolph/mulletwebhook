"""Initialize the app."""

import logging
import sys

from flask import Flask
from flask_cors import CORS

from mulletwebhook.config import Config
from mulletwebhook.database import db

logging.basicConfig(
    stream=sys.stdout,
    format="%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s",
)


def create_app(config_class: type = Config) -> Flask:
    """Creates the mulletwebhook app.

    :param config_class: class to use for app configuration
    :return: initialized flask app
    """
    app = Flask(__name__)
    CORS(app)

    app.config.from_object(config_class)

    # set log level
    try:
        app.logger.setLevel(app.config["LOG_LEVEL"])
        app.logger.info("log level set to %s", app.config["LOG_LEVEL"])
    except ValueError as exp:
        app.logger.error("error setting log level: %s", exp)
        sys.exit(1)

    # initialize database
    db.init_app(app)

    # pylint: disable=import-outside-toplevel
    import mulletwebhook.main.routes as main_routes

    # pylint: disable=

    app.register_blueprint(main_routes.bp)

    return app
