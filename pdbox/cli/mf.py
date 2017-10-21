from pdbox.models import get_remote, RemoteFolder
from pdbox.utils import DropboxError, dbx_uri, fail


def mf(args):
    """
    Create a new folder inside Dropbox.

    args fields:
    - path (string)
    - dryrun (bool)
    """
    try:
        remote = get_remote(args.path)
    except (ValueError, TypeError):
        pass
    else:
        fail("%s already exists" % remote.uri, args)

    try:
        RemoteFolder.create(args.path, args)
    except (ValueError, DropboxError):
        fail("%s could not be created" % dbx_uri(args.path), args)
