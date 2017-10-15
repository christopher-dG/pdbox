from pdbox.util import fail


def sync(args):
    """Synchronize directories to/from/inside Dropbox."""
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
    pass
