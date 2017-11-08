import pdbox


def sync(**kwargs):
    """
    Synchronize directories to/from/inside Dropbox.

    kwargs:
    - src (string)
    - dst (string)
    - dryrun (bool)
    - quiet (bool)
    - follow_symlinks (bool)
    - only_show_errors (bool)
    - delete (bool)
    """
    if not pdbox.cli.validate_src_dest(kwargs["src"], kwargs["dst"]):
        pdbox.error(
            "At least one of <source> or <destination> must be a Dropbox path "
            "with the prefix 'dbx://'",
            **kwargs,
        )
        return False

    if kwargs["src"].startswith("dbx://") and (
            kwargs["dst"].startswith("dbx://")):
        return sync_inside(**kwargs)
    elif kwargs["src"].startswith("dbx://"):
        return sync_from(**kwargs)
    else:
        return sync_to(**kwargs)


def sync_inside(**kwargs):
    """Synchronize directories inside Dropbox."""
    return False  # TODO


def sync_from(**kwargs):
    """Synchronize a directory from Dropbox."""
    return False  # TODO


def sync_to(**kwargs):
    """Synchronize a directory to Dropbox."""
    return False  # TODO
