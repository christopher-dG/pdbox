import pdbox


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
    if not pdbox.cli.validate_src_dest(args.src, args.dst):
        pdbox.error(
            "At least one of <source> or <destination> must be a Dropbox path "
            "with the prefix 'dbx://'",
            args
        )
        return False

    if args.src.startswith("dbx://") and args.dst.startswith("dbx://"):
        return sync_inside(args)
    elif args.src.startswith("dbx://"):
        return sync_from(args)
    else:
        return sync_to(args)


def sync_inside(args):
    """Synchronize directories inside Dropbox."""
    return False  # TODO


def sync_from(args):
    """Synchronize a directory from Dropbox."""
    return False  # TODO


def sync_to(args):
    """Synchronize a directory to Dropbox."""
    return False  # TODO
