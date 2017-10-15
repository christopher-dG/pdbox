from pdbox.models import from_remote, File
from pdbox.util import fail, normpath


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
    remote = from_remote(path, args)

    if not remote:
        fail("dbx:/%s does not exist" % path, args)
    if not isinstance(remote, File) and not args.recursive:
        fail("dbx:/%s is a folder and --recursive is not set" % path, args)

    remote.delete(args)
