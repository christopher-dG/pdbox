import os.path
import pdbox

from pdbox.newmodels import get_local, get_remote, RemoteFile, LocalFolder
from pdbox.utils import DropboxError, dbx_uri, fail, overwrite


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
    try:
        remote_src = get_remote(args.src, args)
    except (ValueError, TypeError):
        fail("%s was not found" % dbx_uri(args.src), args)

    if isinstance(remote_src, RemoteFile):
        fail("%s is a file, use cp to copy files" % remote_src.uri, args)

    try:
        remote_dest = get_remote(args.dst, args)
    except (ValueError, TypeError):
        # TypeError will probably cause failure, but leave as is for now.
        try:  # Since the destination doesn't exist, we can just copy it.
            remote_src.copy(args.dst, args)
        except DropboxError:
            fail(
                "%s could not be synchronized to %s" %
                (remote_src.uri, dbx_uri(args.dst)),
                args,
            )
        return

    try:
        remote_src.sync(remote_dest, args)
    except DropboxError:
        fail(
            "%s could not be synchronized to %s" %
            (remote_src.uri, remote_dest.uri),
            args,
        )


def sync_from(args):
    """Synchronize a directory from Dropbox."""
    pass


def sync_to(args):
    """Synchronize a directory to Dropbox."""
    try:
        local = get_local(args.src, args)
    except ValueError as e:
        fail("%s could not be found" % os.path.abspath(args.src), args)

    if not isinstance(local, LocalFolder):
        fail("%s is a file, use cp to upload files", local.path, args)
    if local.islink and not args.follow_symlinks:
        fail(
            "%s is a symlink and --no-follow-symlinks is set" % local.path,
            args,
        )

    try:
        remote = get_remote(args.dst, args)
    except (ValueError, TypeError) as e:
        remote = None
    else:
        if isinstance(remote, RemoteFile):
            overwrite(remote.uri, args) or fail("Cancelled", args)
            try:
                remote.delete(args)
            except DropboxError:
                fail("%s could not be overwritten" % remote.uri, args)

    try:
        local.sync(remote if remote else args.dst, args)
    except DropboxError:
        fail(
            "%s could not be synchronized to %s" %
            (local.path, dbx_uri(args.dst)),
            args,
        )
