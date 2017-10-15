import os.path
import pdbox

from pdbox.models import from_local, from_remote, File, LocalFolder
from pdbox.util import fail, normpath


def sync(args):
    """
    Synchronize directories to/from/inside Dropbox.

    args fields:
    - src (string)
    - dst (string)
    - dryrun (bool)
    - quiet (bool)
    - follow_symlinks (bool)
    - only_show_errors (bool)
    - delete (bool)
    """
    if not args.src.startswith("dbx://") and not args.dst.startswith("dbx://"):
        fail(
            "At least one of <source> or <destination> must be a Dropbox path "
            "with the prefix 'dbx://'",
            args
        )

    if args.src.startswith("dbx://") and args.dst.startswith("dbx://"):
        sync_inside(args)
    elif args.src.startswith("dbx://"):
        sync_from(args)
    else:
        sync_to(args)


def sync_inside(args):
    """Synchronize directories inside Dropbox."""
    pass


def sync_from(args):
    """Synchronize a directory from Dropbox."""
    pass


def sync_to(args):
    """Synchronize a directory to Dropbox."""
    src = os.path.normpath(args.src)
    dest = normpath(args.dst)

    try:
        folder = from_local(src, args)
    except ValueError as e:
        fail(e, args)

    if not isinstance(folder, LocalFolder):
        fail("%s is not a folder, use cp to upload files", src, args)
    if folder.islink and not args.follow_symlinks:
        fail("%s is a symlink and --no-follow-symlinks is set", src, args)

    try:
        remote = from_remote(dest, args)
    except Exception as e:
        pdbox.debug(e, args)
        remote = None

    if remote and isinstance(remote, File):
        fail("%s already exists as a file" % remote.dbx_uri())

    try:
        folder.sync(dest, args)
    except Exception as e:
        pdbox.debug(e)
        fail("Upload failed")
