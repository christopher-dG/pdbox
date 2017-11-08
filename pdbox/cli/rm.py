import pdbox

from pdbox.models import get_remote, RemoteFile
from pdbox.utils import DropboxError, dbx_uri


def rm():
    """
    Delete one or more files or directories inside Dropbox.

    pdbox._args:
    - path(list[string])
    - dryrun (bool)
    - quiet (bool)
    - recursive (bool)
    - only_show_errors (bool)
    """
    success = True

    for path in pdbox._args["path"]:
        try:
            remote = get_remote(path)
        except ValueError:
            pdbox.error("%s could not be found" % dbx_uri(path))
            success = False
            continue

        if not isinstance(remote, RemoteFile) and not pdbox._args["recursive"]:
            pdbox.error(
                "%s is a folder and --recursive is not set" % remote.uri,
            )
            success = False
            continue

        try:
            remote.delete()
        except DropboxError:
            pdbox.error("%s could not be deleted" % remote.uri)
            success = False

    return success
