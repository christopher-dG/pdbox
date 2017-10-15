import dropbox
import os.path

from pdbox.models import from_local, from_remote, File, LocalFolder
from pdbox.util import fail, normpath


def cp(args):
    """
    Copy a file to/from/inside Dropbox.

    args fields:
    - src (string)
    - dst (string)
    - dryrun (bool)
    - quiet (bool)
    - follow_symlinks (bool)
    - only_show_errors (bool)
    - chunksize (float)
    """
    if not args.src.startswith("dbx://") and not args.dst.startswith("dbx://"):
        fail(
            "At least one of <source> or <destination> must be a Dropbox path "
            "with the prefix 'dbx://'",
            args,
        )

    if args.src.startswith("dbx://") and args.dst.startswith("dbx://"):
        cp_inside(args)
    elif args.src.startswith("dbx://"):
        cp_from(args)
    else:
        cp_to(args)


def cp_inside(args):
    """Copy a file inside Dropbox."""
    pass


def cp_from(args):
    """Copy a file from Dropbox."""
    pass


def cp_to(args):
    """Copy a file to Dropbox."""
    src = os.path.normpath(args.src)
    dest = normpath(args.dst)

    try:
        local = from_local(src, args)
    except ValueError as e:
        fail(e, args)

    if isinstance(local, LocalFolder):
        fail("%s is a folder, use sync to upload folders", src, args)
    if local.islink and not args.follow_symlinks:
        fail("%s is a symlink and --no-follow-symlinks is set", src, args)

    try:
        remote = from_remote(dest, args)
    except Exception:  # Remote file probably does not exist.
        remote = None

    if remote and not isinstance(remote, File):  # Is a folder.
        fail("%s is a folder" % remote.dbx_uri(), args)

    if remote and not args.quiet and not args.only_show_errors:
        # File exists, prompt for overwrite confirmation.
        try:
            confirm = input(
                "File %s exists: overwrite? [y/N] " % remote.dbx_uri(),
            )
        except KeyboardInterrupt:
            confirm = "n"
        if confirm.lower() not in ["y", "yes"]:
            fail("Cancelled", args)

    try:
        local.upload(dest, args)
    except dropbox.exceptions.ApiError:
        fail("Uploading %s to dbx:/%s failed" % (src, dest), args)
