import appdirs
import logging
import os.path

_logger = logging.getLogger("pdbox")
_handler = logging.StreamHandler()
_formatter = logging.Formatter("%(levelname)s: %(message)s")
_logger.setLevel(logging.INFO)
_handler.setFormatter(_formatter)
_logger.addHandler(_handler)


# This is all really gross and hacky.

def debug(s, args=None):
    """Log a debug message."""
    try:
        if not args.quiet and not args.only_show_errors:
            _logger.debug(s)
    except AttributeError:
        _logger.debug(s)


def info(s, args=None):
    """Log an info message."""
    try:
        if not args.quiet and not args.only_show_errors:
            _logger.info(s)
    except AttributeError:
        _logger.info(s)


def warn(s, args=None):
    """Log a warning message."""
    try:
        if not args.quiet:
            _logger.warn(s)
    except AttributeError:
        _logger.warn(s)


def error(s, args=None):
    """Log an error message."""
    try:
        if not args.quiet:
            _logger.error(s)
    except AttributeError:
        _logger.error(s)


TOKEN_PATH = os.path.join(appdirs.user_data_dir("pdbox"), "pdbox_token")
TMP_DOWNLOAD_DIR = os.path.join(appdirs.user_data_dir("pdbox"), "tmp")
dbx = None  # To be populated on login.

if not os.path.exists(TMP_DOWNLOAD_DIR):
    os.makedirs(TMP_DOWNLOAD_DIR)


from . import argparse  # noqa
from . import auth  # noqa
from . import models  # noqa
from . import cmd  # noqa
