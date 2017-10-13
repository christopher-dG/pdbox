from dropbox import Dropbox
from pdbox.util import normpath


def mv(token, args):
    """Move a file or directory inside Dropbox."""
    dbx = Dropbox(token)
    src = normpath(args.src)
    dst = normpath(args.dest)
