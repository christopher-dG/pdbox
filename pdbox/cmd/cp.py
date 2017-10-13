from pdbox import _dbx as dbx
from pdbox.util import err


def cp(args):
    """Copy a file or directory to/from/inside Dropbox."""
    if not args.src.startswith("dbx://") and not args.dst.startswith("dbx://"):
        err(
            "At least one of <source> or <destination> must be a Dropbox path "
            "with the prefix 'dbx://'"
        )

    if args.src.startswith("dbx://") and args.dst.startswith("dbx://"):
        cp_inside(dbx, args)
    elif args.src.startswith("dbx://"):
        cp_from(dbx, args)
    else:
        cp_to(dbx, args)


def cp_inside(dbx, args):
    """Copy a file or directory inside Dropbox."""
    pass


def cp_from(dbx, args):
    """Copy a file or directory from Dropbox."""
    pass


def cp_to(dbx, args):
    """Copy a file or directory to Dropbox."""
    pass
