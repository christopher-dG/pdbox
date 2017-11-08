import pdbox

from pdbox.models import get_remote, RemoteFolder
from pdbox.utils import DropboxError, dbx_uri


def rmdir():
    """
    Delete one or more folders inside Dropbox.

    pdbox._args:
    - path (list[string])
    - dryrun (bool)
    - force (bool)
    """
    success = True

    for path in pdbox._args["path"]:
        try:
            remote = get_remote(path)
        except ValueError:
            pdbox.error("%s was not found" % dbx_uri(path))
            success = False
            continue

        if not isinstance(remote, RemoteFolder):
            pdbox.error(
                "%s is not a folder: use rm to delete files" % remote.uri,
            )
            success = False
            continue

        if pdbox._args["force"]:
            try:
                remote.delete()
                continue
            except DropboxError:
                pdbox.error("%s could not be deleted" % remote.uri)
                success = False
                continue

        try:
            contents = remote.contents()
        except DropboxError:
            pdbox.error(
                "Not deleting: couldn't get contents of %s "
                "and --force is not set" % remote.uri,
            )
            success = False
            continue
        if contents:
            pdbox.error("%s is not empty and --force is not set" % remote.uri)
            success = False
            continue

        try:
            remote.delete()
        except DropboxError:
            pdbox.error("%s could not be deleted" % remote.uri)
            success = False

    return success
