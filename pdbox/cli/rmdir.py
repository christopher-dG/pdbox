import pdbox

from pdbox.models import get_remote, RemoteFolder
from pdbox.utils import DropboxError, dbx_uri


def rmdir(args):
    """
    Delete one or more folders inside Dropbox.

    args fields:
    - path (string)
    - dryrun (bool)
    - force (bool)
    """
    success = True

    for path in args.path:
        try:
            remote = get_remote(path, args)
        except ValueError:
            pdbox.error("%s was not found" % dbx_uri(path), args)
            success = False
            continue

        if not isinstance(remote, RemoteFolder):
            pdbox.error(
                "%s is not a folder: use rm to delete files" % remote.uri,
                args,
            )
            success = False
            continue

        if args.force:
            try:
                remote.delete(args)
                continue
            except DropboxError:
                pdbox.error("%s could not be deleted" % remote.uri, args)
                success = False
                continue

        try:
            contents = remote.contents(args)
        except DropboxError:
            pdbox.error(
                "Not deleting: couldn't get contents of %s "
                "and --force is not set" % remote.uri,
                args,
            )
            success = False
            continue
        if contents:
            pdbox.error(
                "%s is not empty and --force is not set"
                % remote.uri,
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
