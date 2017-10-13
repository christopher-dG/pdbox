from dropbox import Dropbox
from pdbox.util import err


def sync(token, args):
    """Synchronize directories to/from/inside Dropbox."""
    if not args.src.startswith("dbx://") and not args.dst.startswith("dbx://"):
        err(
            "At least one of <source> or <destination> must be a Dropbox path "
            "with the prefix 'dbx://'"
        )

    dbx = Dropbox(token)
    if args.src.startswith("dbx://") and args.dst.startswith("dbx://"):
        sync_inside(dbx, args)
    elif args.src.startswith("dbx://"):
        sync_from(dbx, args)
    else:
        sync_to(dbx, args)


def sync_inside(dbx, args):
    """Copy a file or directory inside Dropbox."""
    pass


def sync_from(dbx, args):
    """Copy a file or directory from Dropbox."""
    pass


def sync_to(dbx, args):
    """Copy a file or directory to Dropbox."""
    pass
