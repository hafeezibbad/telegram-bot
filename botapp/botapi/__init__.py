"""
Initialize blueprint for Restapi module for application.
"""
from flask import Blueprint

botapi = Blueprint('botapi', __name__)

# Setup the logger
import logging
from logging.handlers import RotatingFileHandler

botapi_logger = logging.getLogger(__name__)
botapi_logger.setLevel(logging.INFO)

# Formatter for logs.
botapi_log_format = logging.Formatter('%(asctime)s - %(name)s - '
                                      '%(levelname)s - %(message)s')

# Setup FileHandler for the logs.
botapi_log_fh = RotatingFileHandler('logs/restapi.log', maxBytes=1000000,
                                    backupCount=5)
botapi_log_fh.setLevel(logging.INFO)
botapi_log_fh.setFormatter(botapi_log_format)

# Setup StreamHandler for important logs.
botapi_log_stream = logging.StreamHandler()
botapi_log_stream.setLevel(logging.ERROR)

# Add handlers to the logger.
botapi_logger.addHandler(botapi_log_fh)
botapi_logger.addHandler(botapi_log_stream)

from . import restapi_views
