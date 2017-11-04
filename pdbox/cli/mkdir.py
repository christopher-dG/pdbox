import pdbox

from pdbox.models import get_remote, RemoteFolder
from pdbox.utils import DropboxError, dbx_uri


def mkdir(args):
    """
    Create a new folder inside Dropbox.

    args fields:
    - path (string)
    - dryrun (bool)
    """
    success = True

    for path in args.path:
        try:
            remote = get_remote(path)
        except (ValueError, TypeError):  # Nothing exists here, no problem.
            pass
        else:
            pdbox.error("%s already exists" % remote.uri, args)
            success = False
            continue

    try:
        RemoteFolder.create(args.path, args)
    except (ValueError, DropboxError):
        pdbox.error("%s could not be created" % dbx_uri(path), args)
        success = False

    return success
