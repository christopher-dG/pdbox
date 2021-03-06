import dropbox
import os.path
import pdbox
import sys


class DropboxError(BaseException):
    """A wrapper for dropbox.exceptions.ApiError contents."""
    pass


def execute(func, *args, **kwargs):
    """
    Execute a dropbox.Dropbox method and return its output, logging its error
    if it raises.
    Raises: DropboxError
    """
    try:
        return func(*args, **kwargs)
    except dropbox.exceptions.ApiError as e:
        pdbox.debug(
            "API error:\n  Function: dbx.%s\n  Arguments: %s %s\n  Error: %s" %
            (func.__name__, args, kwargs, e.error),
        )
        raise DropboxError(e.error)
    except dropbox.exceptions.BadInputError as e:
        # This is usually an invalid token.
        pdbox.debug(e)
        fail(
            "Your authentication token is invalid, "
            "delete %s and try again" % pdbox.TOKEN_PATH,
        )


def fail(s):
    """Log s as an error and exit."""
    pdbox.error(s)
    sys.exit(1)


def overwrite(path):
    """Get user confirmation for a file/folder overwrite."""
    if pdbox._args.get("quiet") or pdbox._args.get("only_show_errors"):
        return True

    try:
        confirm = input_compat("File %s exists: overwrite? [y/N] " % path)
    except KeyboardInterrupt:
        return False
    return confirm.lower() in ["y", "yes"]


def normpath(path):
    """Convert path into something that's compatible with Dropbox."""
    if path.startswith("dbx://"):
        path = path[6:]  # Remove the prefix.
    path = "/%s" % path.replace(os.path.sep, "/")  # Fix Windows paths.
    # os.path.normpath won't work on Windows because we need forward slashes.
    while "//" in path:  # Get rid of any double slashes.
        path = path.replace("//", "/")
    return path


def dbx_uri(path):
    """Convert some path into dbx://path."""
    return "dbx:/%s" % normpath(path)


def isize(n):
    """Get a readable size from a number of bytes."""
    if n >= 1024 ** 3:
        return "%.2f GB" % (n / 1024.0 ** 3)
    elif n >= 1024 ** 2:
        return "%.2f MB" % (n / 1024.0 ** 2)
    elif n >= 1024:
        return "%.2f KB" % (n / 1024.0)
    else:
        return "%d B" % n


def input_compat(prompt):
    """
    Get some user input.
    Raises: KeyboardInterrupt
    """
    try:  # Python 2's input function evaluates the input (bad).
        return raw_input(prompt).strip()
    except NameError:
        return input(prompt).strip()
