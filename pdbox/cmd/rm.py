import dropbox
import pdbox

from pdbox.models import from_remote, File
from pdbox.utils import fail, normpath


def rm(args):
    """
    Delete a file or directory inside Dropbox.

    args fields:
    - dryrun (bool)
    - quiet (bool)
    - recursive (bool)
    - only_show_errors (bool)
    """
    path = normpath(args.path)
    try:
        remote = from_remote(path, args)
    except Exception as e:
        pdbox.debug(e)
        fail("dbx:/%s was not found" % path, args)

    if not isinstance(remote, File) and not args.recursive:
        fail("dbx:/%s is a folder and --recursive is not set" % path, args)

    try:
        remote.delete(args)
    except dropbox.exceptions.ApiError:
        fail("%s could not be deleted" % remote.dbx_uri(), args)
