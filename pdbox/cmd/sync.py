import dropbox
import os.path
import pdbox

from pdbox.models import from_local, from_remote, File, LocalFolder
from pdbox.utils import fail, normpath


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
    src = normpath(args.src)
    dest = normpath(args.dst)

    try:
        remote_src = from_remote(src, args)
    except Exception as e:
        if not isinstance(e, dropbox.exceptions.ApiError):
            pdbox.debug(e, args)
        fail("dbx:/%s was not found" % src, args)

    if isinstance(remote_src, File):
        fail("%s is a file, use cp to copy files" % remote_src.dbx_uri(), args)

    try:
        remote_dest = from_remote(dest, args)
    except Exception as e:  # It probably doesn't exist, this is what we want.
        if not isinstance(e, dropbox.exceptions.ApiError):
            pdbox.debug(e, args)
        try:  # Since the destination doesn't exist, we can just copy it.
            remote_src.copy(dest, args)
        except dropbox.exceptions.ApiError:
            fail(
                "%s could not be synchronized to dbx:/%s" %
                (remote_src.dbx_uri(), dest),
                args,
            )
        return

    try:
        remote_src.sync(remote_dest, args)
    except dropbox.exceptions.ApiError:
        fail(
            "%s could not be synchronized to %s" %
            (remote_src.dbx_uri(), remote_dest.dbx_uri()),
            args,
        )

    try:
        remote_src.sync(remote_dest, args)
    except dropbox.exceptions.ApiError:
        fail(
            "%s could not be synchronized to %s" %
            (remote_src.dbx_uri(), remote_dest.dbx_uri()),
            args,
        )


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
