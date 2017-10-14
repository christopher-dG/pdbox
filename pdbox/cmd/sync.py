from pdbox.util import err


def sync(args):
    """Synchronize directories to/from/inside Dropbox."""
    if not args.src.startswith("dbx://") and not args.dst.startswith("dbx://"):
        err(
            "At least one of <source> or <destination> must be a Dropbox path "
            "with the prefix 'dbx://'"
        )

    if args.src.startswith("dbx://") and args.dst.startswith("dbx://"):
        sync_inside(args)
    elif args.src.startswith("dbx://"):
        sync_from(args)
    else:
        sync_to(args)


def sync_inside(args):
    """Copy a file or directory inside Dropbox."""
    pass


def sync_from(args):
    """Copy a file or directory from Dropbox."""
    pass


def sync_to(args):
    """Copy a file or directory to Dropbox."""
    pass
