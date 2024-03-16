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

    app = Flask(__name__)
    CORS(app)

    app.config.from_object(config_class)
    app.logger.setLevel("DEBUG")

    # initialize database
    db.init_app(app)

    # pylint: disable=import-outside-toplevel
    import mulletwebhook.main.routes as main_routes
    # pylint: disable=

    app.register_blueprint(main_routes.bp)

    return app
