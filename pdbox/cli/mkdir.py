import pdbox

from pdbox.models import get_remote, RemoteFolder
from pdbox.utils import DropboxError, dbx_uri


def mkdir(**kwargs):
    """
    Create a new folder inside Dropbox.

    kwargs:
    - path (list[string])
    - dryrun (bool)
    """
    success = True

    for path in kwargs["path"]:
        try:
            remote = get_remote(path)
        except ValueError:  # Nothing exists here, no problem.
            pass
        else:
            pdbox.error("%s already exists" % remote.uri, **kwargs)
            success = False
            continue

        try:
            RemoteFolder.create(path, **kwargs)
        except (ValueError, DropboxError):
            pdbox.error("%s could not be created" % dbx_uri(path), **kwargs)
            success = False

    return success
