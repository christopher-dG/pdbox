from pdbox.models import LocalFolder, RemoteFolder


def validate_src_dest(src, dest):
    """Check that at least one argument is a Dropbox URI."""
    return src.startswith("dbx://") or dest.startswith("dbx://")


def assert_is_folder(path, args=None):
    """Check that a given path points to a folder."""
    if path.startswith("dbx://"):
        try:
            RemoteFolder(path, args)
        except ValueError:
            return False
    else:
        try:
            LocalFolder(path, args)
        except ValueError:
            return False
    return True


from .cp import cp  # noqa
from .ls import ls  # noqa
from .rm import rm  # noqa
from .mv import mv  # noqa
from .mkdir import mkdir  # noqa
from .rmdir import rmdir  # noqa
