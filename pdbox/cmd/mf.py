import dropbox
import pdbox

from pdbox.models import from_remote, Folder
from pdbox.util import fail, normpath


def mf(args):
    """
    Create a new folder inside Dropbox.

    args fields:
    - path (string)
    - dryrun (bool)
    """
    path = normpath(args.path)

    try:
        remote = from_remote(path)
    except Exception as e:
        if not isinstance(e, dropbox.exceptions.ApiError):
            pdbox.debug(e)
    else:
        fail("%s already exists" % remote.dbx_uri(), args)

    try:
        Folder.create(path, args)
    except dropbox.exceptions.ApiError:
        fail("dbx:/%s could not be created" % path, args)
