import json
import logging

from flask import Flask
from flask.ext.mongoengine import MongoEngine
from flask.ext.assets import Environment, Bundle


db = MongoEngine()
app = None
assets = None


def create_app(**config_overrides):
    from app.routes.base import register_error_handlers

    # we want to modify the global app, not a local copy
    global app
    global assets
    app = Flask(__name__)

    # Load config then apply overrides
    app.config.from_object('config.flask_config')
    app.config.update(config_overrides)

    # Initialize assets
    assets = Environment(app)
    register_scss()

    # Setup the database.
    db.init_app(app)

    # Attach Blueprints (routing) to the app
    register_blueprints(app)

    # Attache error handling functions to the app
    register_error_handlers(app)

    # Register the logger.
    register_logger(app)

    return app


def register_logger(app):
    max_bytes = int(app.config["LOG_FILE_MAX_SIZE"]) * 1024 * 1024   # MB to B
    # Use "# noqa" to silence flake8 warnings for creating a variable that is
    # uppercase.  (Here, we make a class, so uppercase is correct.)
    Handler = logging.handlers.RotatingFileHandler  # noqa
    f_str = ('%(levelname)s @ %(asctime)s @ %(filename)s '
             '%(funcName)s %(lineno)d: %(message)s')

    access_handler = Handler(app.config["WERKZEUG_LOG_NAME"],
                             maxBytes=max_bytes)
    access_handler.setLevel(logging.INFO)
    logging.getLogger("werkzeug").addHandler(access_handler)

    app_handler = Handler(app.config["APP_LOG_NAME"], maxBytes=max_bytes)
    formatter = logging.Formatter(f_str)
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(formatter)
    app.logger.addHandler(app_handler)


def register_blueprints(app):
    from app.routes import organizations, client, events, members
    app.register_blueprint(organizations, url_prefix="/organization")
    app.register_blueprint(client)
    app.register_blueprint(events, url_prefix="/events")
    app.register_blueprint(members, url_prefix="/members")


def register_scss():
    assets.url = app.static_url_path
    with open(app.config['SCSS_CONFIG_FILE']) as f:
        bundle_set = json.loads(f.read())
        output_folder = bundle_set['output_folder']
        depends = bundle_set['depends']
        for bundle_name, instructions in bundle_set['rules'].iteritems():
            bundle = Bundle(*instructions['inputs'],
                            output=output_folder + instructions['output'],
                            depends=depends,
                            filters='scss')
            assets.register(bundle_name, bundle)

def run():
    """Runs the app."""
    app.run(host=app.config.get('HOST'), port=app.config.get('PORT'))
