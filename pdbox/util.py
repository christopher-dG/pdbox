import dropbox
import os.path
import sys

from pdbox import logger


def err(s):
    """Log s as an error and exit."""
    logger.error(s)
    sys.exit(1)


def execute(func, *args, **kwargs):
    """Execute some function, and abort if it fails."""
    try:
        return func(args, kwargs)
    except dropbox.exceptions.ApiError as e:
        err(e)


def normpath(path):
    """Convert `path` into something that's compatible with Dropbox."""
    if path.startswith("dbx://"):
        path = path[6:]
    path = "/" + path.replace(os.path.sep, "/")
    while "//" in path:  # os.path.normpath won't work on Windows.
        path = path.replace("//", "/")
    return path


def ssize(data):
    """Get the size of a stream."""
    return isize(len(data))


def isize(n):
    """Get a readable size from a number of bytes."""
    if n > 1024**3:
        return "%.2f GB" % (n / 1024.0**3)
    elif n > 1024**2:
        return "%.2f MB" % (n / 1024.0**2)
    elif n > 1024:
        return "%.2f KB" % (n / 1024.0)
    else:
        return "%d B" % n


def rsize(dbx, path):
    """
    Get the size of a remote file.
    This may raise a `dropbox.exceptions.ApiError`.
    """
    result = dbx.files_get_metadata(path)
    return isize(result.size)
