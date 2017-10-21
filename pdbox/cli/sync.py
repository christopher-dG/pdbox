import os.path

from pdbox.models import get_local, get_remote, RemoteFile, LocalFolder
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
    pass  # TODO


def sync_from(args):
    """Synchronize a directory from Dropbox."""
    pass  # TODO


def sync_to(args):
    """Synchronize a directory to Dropbox."""
    pass  # TODO
