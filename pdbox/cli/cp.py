import os.path
import pdbox

from pdbox.models import get_local, get_remote, RemoteFile, LocalFolder
from pdbox.utils import DropboxError, dbx_uri, overwrite


def cp(args):
    """
    Copy one or more files to/from/inside Dropbox.

    args fields:
    - src (string)
    - dst (string)
    - dryrun (bool)
    - quiet (bool)
    - follow_symlinks (bool)
    - only_show_errors (bool)
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
            success &= cp_inside(src, args)
        elif src.startswith("dbx://"):
            success &= cp_from(src, args)
        else:
            success &= cp_to(src, args)

        args.dst = dest  # The inner functions may have changed this.

    return success


def cp_inside(src, args):
    """Copy a file inside Dropbox."""
    try:
        remote_src = get_remote(src, args)
    except (ValueError, TypeError):
        pdbox.error("%s was not found" % dbx_uri(src), args)
        return False

    if not isinstance(remote_src, RemoteFile):
        pdbox.error(
            "%s is a folder, use sync to copy folders" % remote_src.uri,
            args,
        )
        return False

    try:
        remote_dest = get_remote(args.dst, args)
    except ValueError:
        delete = False
    except TypeError:
        pdbox.error(
            "Something exists at %s that can't be overwritten" %
            dbx_uri(args.dst),
            args,
        )
        return False
    else:  # Something exists here.
        if not isinstance(remote_dest, RemoteFile):
            # Place the file inside the folder.
            args.dst = "%s/%s" % (remote_dest.path, remote_src.name)
            return cp_inside(src, args)
        else:
            # Overwrite the existing file.
            if not overwrite(remote_dest.uri, args):
                pdbox.error("Cancelled", args)
                return False
            else:
                delete = True

    try:
        remote_src.copy(args.dst, args, overwrite=delete)
    except DropboxError:
        pdbox.error(
            "%s could not be copied to %s" %
            (dbx_uri(remote_src.uri), args.dest),
            args,
        )
        return False
    else:
        return True


def cp_from(src, args):
    """Copy a file from Dropbox."""
    try:
        remote = get_remote(src, args)
    except (ValueError, TypeError) as e:
        pdbox.debug(e, args)
        pdbox.error("Couldn't find %s" % dbx_uri(src), args)

    if not isinstance(remote, RemoteFile):
        pdbox.error(
            "%s is not a file, use sync to download folders" %
            remote.uri,
            args,
        )
        return False

    try:
        local = get_local(args.dst, args)
    except ValueError:
        delete = False
    else:  # Something exists here.
        if isinstance(local, LocalFolder):
            args.dst = os.path.join(local.path, remote.name)
            return cp_from(src, args)
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
    else:
        return True


def cp_to(src, args):
    """Copy a file to Dropbox."""
    try:
        local = get_local(src, args)
    except ValueError:
        pdbox.error("%s does not exist" % args.src, args)
        return False

    if isinstance(local, LocalFolder):
        pdbox.error(
            "%s is a folder, use sync to upload folders" % local.path,
            args,
        )
        return False
    if local.islink and not args.follow_symlinks:
        pdbox.error(
            "%s is a symlink and --no-follow-symlinks is set" % local.path,
            args,
        )

    try:
        remote = get_remote(args.dst, args)
    except ValueError:  # Remote file probably doesn't exist.
        delete = False
    except TypeError:
        pdbox.error("Something exists at %s" % dbx_uri(args.dst), args)
    else:
        if not isinstance(remote, RemoteFile):
            # Place the file inside the folder.
            args.dst = "%s/%s" % (remote.path, local.name)
            return cp_to(src, args)
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
    else:
        return True
