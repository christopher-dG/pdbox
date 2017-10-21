from pdbox.models import get_remote, RemoteFile
from pdbox.utils import DropboxError, dbx_uri, fail


def rm(args):
    """
    Delete a file or directory inside Dropbox.

    args fields:
    - dryrun (bool)
    - quiet (bool)
    - recursive (bool)
    - only_show_errors (bool)
    """
    try:
        remote = get_remote(args.path, args)
    except (ValueError, TypeError):
        fail("%s could not be found" % dbx_uri(args.path), args)

    if not isinstance(remote, RemoteFile) and not args.recursive:
        fail("%s is a folder and --recursive is not set" % remote.uri, args)

    try:
        remote.delete(args)
    except DropboxError:
        fail("%s could not be deleted" % remote.uri, args)
