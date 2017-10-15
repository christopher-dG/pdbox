from pdbox.models import from_remote, Folder
from pdbox.util import fail, normpath


def rb(args):
    """
    Delete a folder inside Dropbox.

    args fields:
    - path (string)
    - force (bool)
    """
    path = normpath(args.src)
    remote = from_remote(path, args)

    if not remote:
        fail("dbx:/%s does not exist" % path)
    if not isinstance(remote, Folder):
        fail(
            "%s is not a folder: use rm to delete files" % remote.dbx_uri(),
            args,
        )

    if args.force:
        remote.delete(args)
    else:
        if len(remote.contents(args)) > 1:
            fail(
                "%s is not empty and --force is not set" % remote.dbx_uri(),
                args,
            )
        remote.delete(args)
