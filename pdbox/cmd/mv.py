import dropbox
import os
import pdbox

from pdbox.models import from_local, from_remote, LocalFolder
from pdbox.util import fail, normpath, overwrite


def mv(args):
    """
    Move a file or directory to/from/inside Dropbox.

    args fields:
    - src (string)
    - dst (string)
    - dryrun (bool)
    - quiet (bool)
    - follow_symlinks (bool)
    - only_show_errors (bool)
    - recursive (bool)
    - chunksize (float)
    """
    if not args.src.startswith("dbx://") and not args.dst.startswith("dbx://"):
        fail(
            "At least one of <source> or <destination> must be a Dropbox path "
            "with the prefix 'dbx://'",
            args
        )

    if args.src.startswith("dbx://") and args.dst.startswith("dbx://"):
        mv_inside(args)
    elif args.src.startswith("dbx://"):
        mv_from(args)
    else:
        mv_to(args)


def mv_inside(args):
    pass


def mv_from(args):
    pass


def mv_to(args):
    """Move a file to Dropbox."""
    src = os.path.normpath(args.src)
    dest = normpath(args.dst)

    try:
        local = from_local(src, args)
    except ValueError as e:
        fail(e, args)

    if local.islink and not args.follow_symlinks:
        fail("%s is a symlink and --no-follow-symlinks is set", src, args)
    if isinstance(local, LocalFolder) and not args.recursive:
        fail("%s is a folder and --recursive is not set" % local.path, args)

    try:
        remote = from_remote(dest, args)
    except Exception as e:  # Remote file probably does not exist.
        if not isinstance(e, dropbox.exceptions.ApiError):
            pdbox.debug(e, args)
    else:
        if not overwrite(remote.dbx_uri(), args):
            fail("Cancelled", args)

    try:
        local.upload(dest, args)
    except dropbox.exceptions.ApiError:
        fail("Uploading %s to dbx:/%s failed" % (src, dest), args)

    try:
        local.delete(args)
    except Exception as e:
        pdbox.debug(e, args)
        pass
