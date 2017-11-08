import appdirs
import dropbox
import logging
import os.path

from . import auth

_logger = logging.getLogger("pdbox")
_handler = logging.StreamHandler()
_formatter = logging.Formatter("%(levelname)s: %(message)s")
_logger.setLevel(logging.INFO)
_handler.setFormatter(_formatter)
_logger.addHandler(_handler)


# The path to the OAuth2 token file.
TOKEN_PATH = os.path.join(appdirs.user_data_dir("pdbox"), "pdbox_token")
# The directory in which to store downloads before moving them.
TMP_DOWNLOAD_DIR = os.path.join(appdirs.user_data_dir("pdbox"), "tmp")
# dropbox.Dropbox to be populated on login.
dbx = None
# Place to store the command-line arguments.
_args = {}


def init(**kwargs):
    """
    Log into Dropbox and set some global variables.
    Raises: AssertionError
    """
    global _args, dbx
    _args = kwargs
    token = auth.get_token()
    dbx = dropbox.Dropbox(token, timeout=None)


def debug(s):
    """Log a debug message."""
    if not _args.get("quiet") and not _args.get("only_show_errors"):
        _logger.debug(s)


def info(s):
    """Log an info message."""
    if not _args.get("quiet") and not _args.get("only_show_errors"):
        _logger.info(s)


def warn(s):
    """Log a warning message."""
    if not _args.get("quiet") and not _args.get("only_show_errors"):
        _logger.warn(s)


def error(s):
    """Log an error message."""
    if not _args.get("quiet") and not _args.get("only_show_errors"):
        _logger.error(s)


if not os.path.exists(TMP_DOWNLOAD_DIR):
    os.makedirs(TMP_DOWNLOAD_DIR)  # This creates TOKEN_PATH's parent too.


from . import parsing  # noqa
from . import auth  # noqa
from . import models  # noqa
from . import cli  # noqa
