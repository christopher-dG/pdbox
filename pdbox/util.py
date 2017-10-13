import dropbox
import os.path


def normpath(path):
    """Convert a local path into one compatible with Dropbox."""
    path = "/%s" % path.replace(os.path.sep, "/")
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


def rsize(token, path):
    """Get the size of a remote file."""
    dbx = dropbox.Dropbox(token)
    try:
        result = dbx.files_get_metadata(path)
    except dropbox.exceptions.ApiError as e:
        return None
    else:
        return isize(result.size)
