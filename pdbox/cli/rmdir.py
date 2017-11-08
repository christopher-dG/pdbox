import pdbox

from pdbox.models import get_remote, RemoteFolder
from pdbox.utils import DropboxError, dbx_uri


def rmdir(**kwargs):
    """
    Delete one or more folders inside Dropbox.

    kwargs:
    - path (list[string])
    - dryrun (bool)
    - force (bool)
    """
    success = True

    for path in kwargs["path"]:
        try:
            remote = get_remote(path, **kwargs)
        except ValueError:
            pdbox.error("%s was not found" % dbx_uri(path), **kwargs)
            success = False
            continue

        if not isinstance(remote, RemoteFolder):
            pdbox.error(
                "%s is not a folder: use rm to delete files" % remote.uri,
                **kwargs,
            )
            success = False
            continue

        if kwargs["force"]:
            try:
                remote.delete(**kwargs)
                continue
            except DropboxError:
                pdbox.error("%s could not be deleted" % remote.uri, **kwargs)
                success = False
                continue

        try:
            contents = remote.contents(**kwargs)
        except DropboxError:
            pdbox.error(
                "Not deleting: couldn't get contents of %s "
                "and --force is not set" % remote.uri,
                **kwargs,
            )
            success = False
            continue
        if contents:
            pdbox.error(
                "%s is not empty and --force is not set"
                % remote.uri,
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
