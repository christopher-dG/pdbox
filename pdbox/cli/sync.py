import pdbox


def sync():
    """
    Synchronize directories to/from/inside Dropbox.

    pdbox._args:
    - src (string)
    - dst (string)
    - dryrun (bool)
    - quiet (bool)
    - follow_symlinks (bool)
    - only_show_errors (bool)
    - delete (bool)
    """
    src, dest = pdbox._args["src"], pdbox._args["dst"]
    if not pdbox.cli.validate_src_dest(src, dest):
        pdbox.error(
            "At least one of <source> or <destination> must be a Dropbox path "
            "with the prefix 'dbx://'",
        )
        return False

    if src.startswith("dbx://") and dest.startswith("dbx://"):
        return sync_inside(src, dest)
    elif src.startswith("dbx://"):
        return sync_from(src, dest)
    else:
        return sync_to(src, dest)


def sync_inside(src, dest):
    """Synchronize directories inside Dropbox."""
    return False  # TODO


def sync_from(src, dest):
    """Synchronize a directory from Dropbox."""
    return False  # TODO


def sync_to(src, dest):
    """Synchronize a directory to Dropbox."""
    return False  # TODO
