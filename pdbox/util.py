import os.path


def normpath(path):
    """Convert a local path into one compatible with Dropbox."""
    path = "/%s" % path.replace(os.path.sep, "/")
    while "//" in path:  # os.path.normpath won't work on Windows.
        path = path.replace("//", "/")
    return path


def size(data):
    """Get the size of data."""
    size = len(data)
    if size > 1024**3:
        return "%.2f GB" % (size / 1024.0**3)
    elif size > 1024**2:
        return "%.2f MB" % (size / 1024.0**2)
    elif size > 1024:
        return "%.2f KB" % (size / 1024.0)
    else:
        return "%d B" % size
