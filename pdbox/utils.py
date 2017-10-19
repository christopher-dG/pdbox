import dropbox
import os.path
import pdbox
import sys


class DropboxError(BaseException):
    """A wrapper for dropbox.exceptions.ApiError contents."""
    pass


def execute(ns, func, *args, **kwargs):
    """
    Execute a method and return its output, logging its error if it raises.
    First argument is an argparse.Namespace, second is the method to call.
    Raises: DropboxError
    """
    try:
        return func(*args, **kwargs)
    except dropbox.exceptions.ApiError as e:
        pdbox.debug(
            "API error:\n  Function: dbx.%s\n  Arguments: %s\n  Error: %s" %
            (func.__name__, args, e.error),
            ns,
        )
        raise DropboxError(e.error)
    except dropbox.exceptions.BadInputError as e:
        pdbox.debug(e, ns)
        fail(
            "Your authentication token is invalid, "
            "delete %s and try again" % pdbox.TOKEN_PATH,
            args,
        )


def fail(s, args=None):
    """Log s as an error and exit."""
    pdbox.error(s, args)
    sys.exit(1)


def overwrite(path, args=None):
    """Get user confirmation for a file/folder overwrite."""
    try:
        if args.quiet or args.only_show_errors:
            return True
    except AttributeError:
        pass

    try:
        confirm = input("File %s exists: overwrite? [y/N] " % path)
    except KeyboardInterrupt:
        return False
    return confirm.lower() in ["y", "yes"]


def normpath(path):
    """Convert `path` into something that's compatible with Dropbox."""
    if path.startswith("dbx://"):
        path = path[6:]
    path = "/" + path.replace(os.path.sep, "/")
    while "//" in path:  # os.path.normpath won't work on Windows.
        path = path.replace("//", "/")
    return path


def dbx_uri(path):
    """Convert some path into dbx://path."""
    return "dbx:/%s" % normpath(path)


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
