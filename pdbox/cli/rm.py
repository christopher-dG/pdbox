import pdbox

from pdbox.models import get_remote, RemoteFile
from pdbox.utils import DropboxError, dbx_uri


def rm(args):
    """
    Delete one or more files or directories inside Dropbox.

    args fields:
    - dryrun (bool)
    - quiet (bool)
    - recursive (bool)
    - only_show_errors (bool)
    """
    success = True

    for path in args.path:
        try:
            remote = get_remote(path, args)
        except ValueError:
            pdbox.error("%s could not be found" % dbx_uri(args.path), args)
            success = False
            continue

        if not isinstance(remote, RemoteFile) and not args.recursive:
            pdbox.error(
                "%s is a folder and --recursive is not set" % remote.uri,
                args,
            )
            success = False
            continue

        try:
            remote.delete(args)
        except DropboxError:
            pdbox.error("%s could not be deleted" % remote.uri, args)
            success = False

    return success
