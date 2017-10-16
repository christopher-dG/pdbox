import dropbox
import pdbox

from pdbox.models import from_remote, Folder
from pdbox.util import fail, normpath


def rf(args):
    """
    Delete a folder inside Dropbox.

    args fields:
    - path (string)
    - dryrun (bool)
    - force (bool)
    """
    path = normpath(args.path)
    try:
        remote = from_remote(path, args)
    except Exception as e:
        pdbox.debug(e)
        fail("dbx:/%s was not found" % path, args)

    if not isinstance(remote, Folder):
        fail(
            "%s is not a folder: use rm to delete files" % remote.dbx_uri(),
            args,
        )

    if args.force:
        try:
            remote.delete(args)
        except dropbox.exceptions.ApiError:
            fail("%s could not be deleted" % remote.dbx_uri(), args)
    else:
        try:
            contents = remote.contents(args)
        except dropbox.exceptions.ApiError:
            fail(
                "Not deleting: couldn't get contents of %s "
                "and --force is not set" % remote.dbx_uri(),
                args,
            )
        if contents:
            fail(
                "%s is not empty and --force is not set"
                % remote.dbx_uri(),
                args,
            )
        try:
            remote.delete(args)
        except dropbox.exceptions.ApiError:
            fail("%s could not be deleted" % remote.dbx_uri(), args)
