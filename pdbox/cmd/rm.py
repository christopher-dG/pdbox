from dropbox import Dropbox
from pdbox.util import normpath


def rm(token, args):
    """Delete a file or directory inside Dropbox."""
    dbx = Dropbox(token)
    path = normpath(args.path)
