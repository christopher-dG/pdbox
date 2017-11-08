import pdbox

from pdbox.models import get_remote, RemoteFile
from pdbox.utils import DropboxError, dbx_uri


def rm(**kwargs):
    """
    Delete one or more files or directories inside Dropbox.

    kwargs:
    - path(list[string])
    - dryrun (bool)
    - quiet (bool)
    - recursive (bool)
    - only_show_errors (bool)
    """
    success = True

    for path in kwargs["path"]:
        try:
            remote = get_remote(path, **kwargs)
        except ValueError:
            pdbox.error(
                "%s could not be found" % dbx_uri(kwargs["path"]),
                **kwargs,
            )
            success = False
            continue

        if not isinstance(remote, RemoteFile) and not kwargs["recursive"]:
            pdbox.error(
                "%s is a folder and --recursive is not set" % remote.uri,
                **kwargs,
            )
            success = False
            continue

        try:
            remote.delete(**kwargs)
        except DropboxError:
            pdbox.error("%s could not be deleted" % remote.uri, **kwargs)
            success = False

    return success
