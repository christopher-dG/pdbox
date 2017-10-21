import os
import pdbox

from pdbox.models import get_local, get_remote, RemoteFolder, LocalFolder
from pdbox.utils import DropboxError, dbx_uri, fail, overwrite


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
    """Move a file or directory inside Dropbox."""
    try:
        remote_src = get_remote(args.src, args)
    except (ValueError, TypeError) as e:  # No file, nothing to move.
        fail("%s couldn't be found" % dbx_uri(args.src), args)
    else:  # Something exists to be downloaded.
        if isinstance(remote_src, RemoteFolder) and not args.recursive:
            fail(
                "%s is a folder and --recursive is not set" % remote_src.uri,
                args,
            )

    try:
        remote_dest = get_remote(args.dst, args)
    except (ValueError, TypeError) as e:  # Nothing found at the destination.
        delete = False  # TypeError may cause problems, but ignore it for now.
    else:
        if isinstance(remote_dest, RemoteFolder):
            # Move the source into the folder.
            args.dst = "%s/%s" % (remote_dest.path, remote_src.name)
            mv_inside(args)
            return
        # Overwrite the existing file.
        overwrite(remote_dest.uri, args) or fail("Cancelled", args)
        delete = True

    # Now that the path is clear, we can move the file.
    try:
        remote_src.move(args.dst, args, overwrite=delete)
    except DropboxError:
        fail(
            "%s could not be moved to %s" %
            (remote_src.uri, dbx_uri(args.dst)),
            args,
        )


def mv_from(args):
    """Move a file from Dropbox."""
    try:
        remote = get_remote(args.src, args)
    except (ValueError, TypeError):  # No file, can't download anything.
        fail("%s could not be found" % dbx_uri(args.src), args)

    if isinstance(remote, RemoteFolder) and not args.recursive:
        fail("%s is a folder and --recursive is not set" % remote.uri, args)

    try:
        local = get_local(args.dst, args)
    except ValueError:  # Nothing exists here, so we're clear to download.
        delete = False
    else:  # Something exists here.
        if isinstance(local, LocalFolder):
            # Move the file inside the folder.
            args.dst = os.path.join(local.path, remote.name)
            mv_from(args)
            return
        # Overwrite the existing file.
        overwrite(local.path, args) or fail("Cancelled", args)
        delete = True

    try:
        remote.download(args.dst, args, overwrite=delete)
    except DropboxError:
        fail("Couldn't download %s" % remote.dbx_uri(), args)
    except Exception as e:  # Some other exception, probably FS related.
        pdbox.debug(e, args)
        fail(
            "Something went wrong, check %s for your download" %
            pdbox.TMP_DOWNLOAD_DIR,
            args,
        )

    try:
        remote.delete(args)
    except DropboxError:
        fail("%s couldn't be deleted" % remote.uri, args)


def mv_to(args):
    """Move a file to Dropbox."""
    try:
        local = get_local(args.src, args)
    except ValueError as e:
        fail("%s could not be found" % os.path.abspath(args.src), args)

    if local.islink and not args.follow_symlinks:
        fail(
            "%s is a symlink and --no-follow-symlinks is set" %
            os.path.abspth(args.src),
            args,
        )
    if isinstance(local, LocalFolder) and not args.recursive:
        fail("%s is a folder and --recursive is not set" % local.path, args)

    try:
        remote = get_remote(args.dst, args)
    except ValueError:  # Remote file probably doesn't exist.
        pass
    except TypeError:
        fail(
            "Something exists at %s that can't be overwritten" %
            dbx_uri(args.dst),
            args,
        )
    else:
        overwrite(remote.uri, args) or fail("Cancelled", args)

    try:
        local.upload(args.dst, args)
    except DropboxError:
        fail("Uploading %s to %s failed" % (dbx_uri(args.src), args.dst), args)

    try:
        local.delete(args)
    except Exception as e:
        pdbox.debug(e, args)
        fail("%s could not be deleted" % local.path, args)
