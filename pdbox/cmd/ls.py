from pdbox import _dbx as dbx
from pdbox.util import normpath


def ls(args):
    """List a directory inside Dropbox."""
    path = normpath(args.path)
