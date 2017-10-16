import dropbox
import os.path
import pdbox

from pdbox.models import from_local, from_remote, File, LocalFolder
from pdbox.util import fail, normpath, overwrite


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
    src = normpath(args.src)
    dest = normpath(args.dst)

    try:
        remote_src = from_remote(src, args)
    except Exception as e:
        if not isinstance(e, dropbox.exceptions.ApiError):
            pdbox.debug(e, args)
        fail("dbx:/%s was not found" % src, args)

    if not isinstance(remote_src, File):
        fail(
            "%s is a folder, use sync to copy folders" % remote_src.dbx_uri(),
            args,
        )

    try:
        remote_dest = from_remote(dest, args)
    except Exception as e:  # It probably doesn't exist, this is what we want.
        if not isinstance(e, dropbox.exceptions.ApiError):
            pdbox.debug(e, args)
    else:  # Something exists here.
        if not overwrite(remote_dest.dbx_uri(), args):
            fail("Cancelled", args)

        # There doesn't seem to be a way to copy and overwrite at the same
        # time, so we'll delete and then copy.
        try:
            remote_dest.delete(args)
        except dropbox.exceptions.ApiError:
            fail(
                "%s could not be copied to %s" %
                (remote_src.dbx_uri(), remote_dest.dbx_uri()),
                args,
            )

    try:
        remote_src.copy(dest, args)
    except dropbox.exceptions.ApiError:
        fail(
            "%s could not be copied to dbx:/%s" % (remote_src.dbx_uri(), dest),
            args,
        )


def cp_from(args):
    """Copy a file from Dropbox."""
    src = normpath(args.src)
    dest = os.path.normpath(args.dst)

    try:
        local = from_local(dest, args)
    except ValueError as e:
        pdbox.debug(e, args)
    else:  # Something exists here.
        if not overwrite(local.path, args):
            fail("Cancelled", args)

    try:
        remote = from_remote(src, args)
    except Exception as e:
        if not isinstance(e, dropbox.exceptions.ApiError):
            pdbox.debug(e)
        fail("Couldn't find dbx:/%s" % src, args)

    if not isinstance(remote, File):
        fail(
            "%s is not a file, use sync to download folders" %
            remote.dbx_uri(),
            args,
        )

    try:
        remote.download(dest, args)
    except dropbox.exceptions.ApiError:
        fail("Couldn't download %s" % remote.dbx_uri(), args)


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
    except Exception as e:  # Remote file probably does not exist.
        if not isinstance(e, dropbox.exceptions.ApiError):
            pdbox.debug(e, args)
    else:
        if not isinstance(remote, File):  # Is a folder.
            fail("%s is a folder" % remote.dbx_uri(), args)
        if not overwrite(remote.dbx_uri(), args):
            fail("Cancelled", args)

    try:
        local.upload(dest, args)
    except dropbox.exceptions.ApiError:
        fail("Uploading %s to dbx:/%s failed" % (src, dest), args)
