import pdbox

from pdbox.models import get_remote, RemoteFolder
from pdbox.utils import DropboxError, dbx_uri


def mkdir():
    """
    Create a new folder inside Dropbox.

    pdbox._args:
    - path (list[string])
    - dryrun (bool)
    """
    success = True

    for path in pdbox._args["path"]:
        try:
            remote = get_remote(path)
        except ValueError:  # Nothing exists here, no problem.
            pass
        else:
            pdbox.error("%s already exists" % remote.uri)
            success = False
            continue

        try:
            RemoteFolder.create(path)
        except (ValueError, DropboxError):
            pdbox.error("%s could not be created" % dbx_uri(path))
            success = False

    return success
