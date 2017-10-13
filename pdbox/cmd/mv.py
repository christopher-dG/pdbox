from pdbox import _dbx as dbx
from pdbox.util import normpath


def mv(args):
    """Move a file or directory inside Dropbox."""
    src = normpath(args.src)
    dst = normpath(args.dest)
