import os
import pdbox

from pdbox.models import get_local, get_remote, RemoteFolder, LocalFolder
from pdbox.utils import DropboxError, dbx_uri, overwrite


def mv(args):
    """
    Move one or  files or directories to/from/inside Dropbox.

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
    if len(args.src) > 1 and not pdbox.cli.assert_is_folder(args.dst):
        pdbox.error(
            "%s is not a folder; can't move multiple items here" % args.dst,
            args,
        )
        return False

    dest = args.dst
    success = True

    for src in args.src:
        if not pdbox.cli.validate_src_dest(src, args.dst):
            pdbox.error(
                "At least one of <source> or <destination> must be a Dropbox "
                "path with the prefix 'dbx://'",
                args,
            )
            success = False
            continue

        if src.startswith("dbx://") and args.dst.startswith("dbx://"):
            success &= mv_inside(src, args)
        elif src.startswith("dbx://"):
            success &= mv_from(src, args)
        else:
            success &= mv_to(src, args)

        args.dst = dest  # The inner functions may have changed this.

    return success


def mv_inside(src, args):
    """Move a file or directory inside Dropbox."""
    try:
        remote_src = get_remote(src, args)
    except (ValueError, TypeError):  # No file, nothing to move.
        pdbox.error("%s couldn't be found" % dbx_uri(src), args)
        return False
    else:  # Something exists to be downloaded.
        if isinstance(remote_src, RemoteFolder) and not args.recursive:
            pdbox.error(
                "%s is a folder and --recursive is not set" % remote_src.uri,
                args,
            )
            return False

    try:
        remote_dest = get_remote(args.dst, args)
    except (ValueError, TypeError):  # Nothing found at the destination.
        delete = False  # TypeError may cause problems, but ignore it for now.
    else:
        if isinstance(remote_dest, RemoteFolder):
            # Move the source into the folder.
            args.dst = "%s/%s" % (remote_dest.path, remote_src.name)
            return mv_inside(src, args)
        else:
            # Overwrite the existing file.
            if not overwrite(remote_dest.uri, args):
                pdbox.error("Cancelled", args)
                return False
            else:
                delete = True

    # Now that the path is clear, we can move the file.
    try:
        remote_src.move(args.dst, args, overwrite=delete)
    except DropboxError:
        pdbox.error(
            "%s could not be moved to %s" %
            (remote_src.uri, dbx_uri(args.dst)),
            args,
        )
        return False
    else:
        return True


def mv_from(src, args):
    """Move a file from Dropbox."""
    try:
        remote = get_remote(src, args)
    except (ValueError, TypeError):  # No file, can't download anything.
        pdbox.error("%s could not be found" % dbx_uri(src), args)
        return False

    if isinstance(remote, RemoteFolder) and not args.recursive:
        pdbox.error(
            "%s is a folder and --recursive is not set" % remote.uri,
            args,
        )
        return False

    try:
        local = get_local(args.dst, args)
    except ValueError:  # Nothing exists here, so we're clear to download.
        delete = False
    else:  # Something exists here.
        if isinstance(local, LocalFolder):
            # Move the file inside the folder.
            args.dst = os.path.join(local.path, remote.name)
            return mv_from(src, args)
        else:
            # Overwrite the existing file.
            if not overwrite(local.path, args):
                pdbox.error("Cancelled", args)
                return False
            else:
                delete = True

    try:
        remote.download(args.dst, args, overwrite=delete)
    except DropboxError:
        pdbox.error("Couldn't download %s" % remote.uri, args)
        return False
    except Exception as e:  # Some other exception, probably FS related.
        pdbox.debug(e, args)
        pdbox.error(
            "Something went wrong, check %s for your download" %
            pdbox.TMP_DOWNLOAD_DIR,
            args,
        )
        return False

    try:
        remote.delete(args)
    except DropboxError:
        pdbox.error("%s couldn't be deleted" % remote.uri, args)
        return False
    else:
        return True


def mv_to(src, args):
    """Move a file to Dropbox."""
    try:
        local = get_local(src, args)
    except ValueError:
        pdbox.error("%s could not be found" % os.path.abspath(src), args)
        return False

    if local.islink and not args.follow_symlinks:
        pdbox.error(
            "%s is a symlink and --no-follow-symlinks is set" %
            os.path.abspth(src),
            args,
        )
        return False
    if isinstance(local, LocalFolder) and not args.recursive:
        pdbox.error(
            "%s is a folder and --recursive is not set" % local.path,
            args,
        )
        return False

    try:
        remote = get_remote(args.dst, args)
    except ValueError:  # Remote file probably doesn't exist.
        delete = False
    except TypeError:
        pdbox.error(
            "Something exists at %s that can't be overwritten" %
            dbx_uri(args.dst),
            args,
        )
        return False
    else:
        if isinstance(remote, RemoteFolder):
            # Place the file inside the folder.
            args.dst = "%s/%s" % (remote.path, local.name)
            return mv_to(src, args)
        else:
            # Overwrite the existing file.
            if not overwrite(remote.uri, args):
                pdbox.error("Cancelled", args)
                return False
            else:
                delete = True

    try:
        local.upload(args.dst, args, overwrite=delete)
    except DropboxError:
        pdbox.error("Uploading %s to %s failed" % (local.path, args.dst), args)
        return False

    try:
        local.delete(args)
    except Exception as e:
        pdbox.debug(e, args)
        pdbox.error("%s could not be deleted" % local.path, args)
        return False
    else:
        return True
