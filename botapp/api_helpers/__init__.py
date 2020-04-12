# Dictionary object storing updater objects for starting/stopping polling.
global running_bots
running_bots = {}

# Setup the logger
import logging
from logging.handlers import RotatingFileHandler

proc_logger = logging.getLogger(__name__)
proc_logger.setLevel(logging.INFO)

# Formatter for logs.
proc_log_format = logging.Formatter('%(asctime)s - %(name)s - '
                                    '%(levelname)s - %(message)s')

# Setup FileHandler for the logs.
proc_log_fh = RotatingFileHandler('logs/procedures.log', maxBytes=1000000,
                                  backupCount=5)
proc_log_fh.setLevel(logging.INFO)
proc_log_fh.setFormatter(proc_log_format)

# Setup StreamHandler for important logs.
proc_log_stream = logging.StreamHandler()
proc_log_stream.setLevel(logging.ERROR)

# Add handlers to the logger.
proc_logger.addHandler(proc_log_fh)
proc_logger.addHandler(proc_log_stream)
