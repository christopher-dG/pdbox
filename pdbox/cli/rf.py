from pdbox.newmodels import get_remote, RemoteFolder
from pdbox.utils import DropboxError, dbx_uri, fail


def rf(args):
    """
    Delete a folder inside Dropbox.

    args fields:
    - path (string)
    - dryrun (bool)
    - force (bool)
    """
    try:
        remote = get_remote(args.path, args)
    except (ValueError, TypeError) as e:
        fail("%s was not found" % dbx_uri(args.path), args)

    if not isinstance(remote, RemoteFolder):
        fail("%s is not a folder: use rm to delete files" % remote.uri, args)

    if args.force:
        try:
            remote.delete(args)
        except DropboxError:
            fail("%s could not be deleted" % remote.uri, args)
    else:
        try:
            contents = remote.contents(args)
        except DropboxError:
            fail(
                "Not deleting: couldn't get contents of %s "
                "and --force is not set" % remote.uri,
                args,
            )
        if contents:
            fail(
                "%s is not empty and --force is not set"
                % remote.uri,
                args,
            )
        try:
            remote.delete(args)
        except DropboxError:
            fail("%s could not be deleted" % remote.uri, args)
