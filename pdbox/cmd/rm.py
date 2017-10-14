from pdbox.util import normpath


def rm(args):
    """Delete a file or directory inside Dropbox."""
    path = normpath(args.path)
