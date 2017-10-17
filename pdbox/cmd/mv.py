import dropbox
import os
import pdbox

from pdbox.models import from_local, from_remote, File, LocalFolder
from pdbox.utils import fail, normpath, overwrite


def mv(args):
    """
    Move a file or directory to/from/inside Dropbox.

    args fields:
    - src (string)
    - dst (string)
    - dryrun (bool)
    - quiet (bool)
    - follow_symlinks (bool)
    - only_show_errors (bool)
    - recursive (bool)
    - chunksize (float)
    """
    if not args.src.startswith("dbx://") and not args.dst.startswith("dbx://"):
        fail(
            "At least one of <source> or <destination> must be a Dropbox path "
            "with the prefix 'dbx://'",
            args
        )

    if args.src.startswith("dbx://") and args.dst.startswith("dbx://"):
        mv_inside(args)
    elif args.src.startswith("dbx://"):
        mv_from(args)
    else:
        mv_to(args)


def mv_inside(args):
    src = normpath(args.src)
    dest = normpath(args.dst)

    try:
        remote_src = from_remote(src)
    except Exception as e:
        if not isinstance(e, dropbox.exceptions.ApiError):
            pdbox.debug(e, args)
        fail("dbx:/%s couldn't be found" % src, args)

    try:
        remote_dest = from_remote(dest)
    except Exception as e:
        if not isinstance(e, dropbox.exceptions.ApiError):
            pdbox.debug(e, args)
    else:
        if not isinstance(remote_dest, File) and not args.recursive:
            fail(
                "%s is a folder and --recursive is not set" %
                remote_dest.dbx_uri(),
                args,
            )
        if not overwrite(remote_dest.dbx_uri(), args):
            fail("Cancelled", args)

        try:
            remote_dest.delete(args)
        except dropbox.exceptions.ApiError:
            fail("%s could not be overwritten" % remote_dest.dbx_uri(), args)

    try:
        remote_src.move(dest, args)
    except dropbox.exceptions.ApiError:
        fail(
            "%s could not be moved to dbx:/%s" %
            (remote_src.dbx_uri(), dest),
            args,
        )


def mv_from(args):
    """Move a file from Dropbox."""
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

    if not isinstance(remote, File) and not args.recursive:
        fail(
            "%s is a folder and --recursive is not set" % remote.dbx_uri(),
            args,
        )

    try:
        remote.download(dest, args)
    except dropbox.exceptions.ApiError:
        fail("Couldn't download %s" % remote.dbx_uri(), args)
    except Exception as e:  # Some other exception, probably FS related.
        dropbox.debug(e, args)
        fail(
            "Something went wrong, check %s for your download" %
            pdbox.TMP_DOWNLOAD_DIR,
            args,
        )

    remote.delete(args)


def mv_to(args):
    """Move a file to Dropbox."""
    src = os.path.normpath(args.src)
    dest = normpath(args.dst)

    try:
        local = from_local(src, args)
    except ValueError as e:
        fail(e, args)

    if local.islink and not args.follow_symlinks:
        fail("%s is a symlink and --no-follow-symlinks is set", src, args)
    if isinstance(local, LocalFolder) and not args.recursive:
        fail("%s is a folder and --recursive is not set" % local.path, args)

    try:
        remote = from_remote(dest, args)
    except Exception as e:  # Remote file probably does not exist.
        if not isinstance(e, dropbox.exceptions.ApiError):
            pdbox.debug(e, args)
    else:
        if not overwrite(remote.dbx_uri(), args):
            fail("Cancelled", args)

    try:
        local.upload(dest, args)
    except dropbox.exceptions.ApiError:
        fail("Uploading %s to dbx:/%s failed" % (src, dest), args)

    try:
        local.delete(args)
    except Exception as e:
        pdbox.debug(e, args)
        pass
