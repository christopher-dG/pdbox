from pdbox import _dbx as dbx
from pdbox.util import normpath


def mb(args):
    """Create a new folder inside Dropbox."""
    path = normpath(args.path)
