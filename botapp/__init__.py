"""
Initialization of application and api blueprints and other modules.
"""
from flask import Flask
from config import config
from flask_moment import Moment
from flask_bootstrap import Bootstrap
from flask_pagedown import PageDown
from flask_mongoengine import MongoEngine

db = MongoEngine()              # MongoDB
bootstrap = Bootstrap()         # Styling of web interface.
moment = Moment()               # For displaying time when message was received.
pagedown = PageDown()           # For enabling HTML rendering of messages.


def create_app(config_name='default', **config_overrides):
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config[config_name])
    # Apply overrides
    app.config.update(config_overrides)
    # Override configurations **kwargs if any/
    config[config_name].init_app(app)

    # Initialize modules.
    db.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    pagedown.init_app(app)

    if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask_sslify import SSLify
        sslify = SSLify(app)

    # Register blueprints for restapi. All Restapi calls will be prefixed as
    # http(s)://<server_ip>:<server_port>/api/
    from .botapi import botapi as botapi_blueprint
    app.register_blueprint(botapi_blueprint, url_prefix='/api')

    # Register blueprints for web api. All Web calls will be prefixed as
    # http(s)://<server_ip>:<server_port>/web/
    from .web_ui import web_ui as web_ui_blueprint
    app.register_blueprint(web_ui_blueprint, url_prefix='/web')

    return app
