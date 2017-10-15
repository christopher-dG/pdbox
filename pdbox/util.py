import os.path
import pdbox
import sys


def fail(s, args=None):
    """Log s as an error and exit."""
    pdbox.error(s, args)
    sys.exit(1)


def normpath(path):
    """Convert `path` into something that's compatible with Dropbox."""
    if path.startswith("dbx://"):
        path = path[6:]
    path = "/" + path.replace(os.path.sep, "/")
    while "//" in path:  # os.path.normpath won't work on Windows.
        path = path.replace("//", "/")
    return path


def isize(n):
    """Get a readable size from a number of bytes."""
    if n >= 1024**3:
        return "%.2f GB" % (n / 1024.0**3)
    elif n >= 1024**2:
        return "%.2f MB" % (n / 1024.0**2)
    elif n >= 1024:
        return "%.2f KB" % (n / 1024.0)
    else:
        return "%d B" % n
