from dropbox import Dropbox
from pdbox.util import normpath


def ls(token, args):
    """List a directory inside Dropbox."""
    path = normpath(args.path)
    dbx = Dropbox(token)
