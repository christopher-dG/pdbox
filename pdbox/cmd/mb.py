from dropbox import Dropbox
from pdbox.util import normpath


def mb(token, args):
    """Create a new folder inside Dropbox."""
    path = normpath(args.path)
    dbx = Dropbox(token)