"""
Initialize blueprint for web api for application.
"""
from flask import Blueprint

web_ui = Blueprint('web_ui', __name__)

# Setup the logger
import logging
from logging.handlers import RotatingFileHandler

web_logger = logging.getLogger(__name__)
web_logger.setLevel(logging.INFO)

# Formatter for logs.
web_log_format = logging.Formatter('%(asctime)s - %(name)s - '
                                   '%(levelname)s - %(message)s')

# Setup FileHandler for the logs.
web_log_fh = RotatingFileHandler('logs/webapi.log', maxBytes=1000000,
                                 backupCount=5)
web_log_fh.setLevel(logging.INFO)
web_log_fh.setFormatter(web_log_format)

# Setup StreamHandler for important logs.
web_log_stream = logging.StreamHandler()
web_log_stream.setLevel(logging.ERROR)

# Add handlers to the logger.
web_logger.addHandler(web_log_fh)
web_logger.addHandler(web_log_stream)

from .import web_ui_views
