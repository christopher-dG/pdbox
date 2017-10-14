import appdirs
import logging
import os.path

logger = logging.getLogger("pdbox")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(levelname)s: %(message)s")
logger.setLevel(logging.ERROR)
handler.setFormatter(formatter)
logger.addHandler(handler)

TOKEN_PATH = os.path.join(appdirs.user_data_dir("pdbox"), "pdbox_token")
dbx = None  # To be populated on login.

from . import argparse  # noqa
from . import auth  # noqa
from . import models  # noqa
from . import cmd  # noqa
