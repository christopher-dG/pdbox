import os.path
import pdbox

from pdbox.models import get_local, get_remote, RemoteFile, LocalFolder
from pdbox.utils import DropboxError, dbx_uri, fail, overwrite


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
    try:
        remote_src = get_remote(args.src, args)
    except (ValueError, TypeError):
        fail("%s was not found" % dbx_uri(args.src), args)

    if not isinstance(remote_src, RemoteFile):
        fail("%s is a folder, use sync to copy folders" % remote_src.uri, args)

    try:
        remote_dest = get_remote(args.dst, args)
    except ValueError:
        delete = False
    except TypeError:
        fail(
            "Something exists at %s that can't be overwritten" %
            dbx_uri(args.dst),
            args,
        )
    else:  # Something exists here.
        if not isinstance(remote_dest, RemoteFile):
            args.dst = "%s/%s" % (remote_dest.path, remote_src.name)
            cp_inside(args)
            return
        else:
            # Overwrite the existing file.
            overwrite(remote_dest.uri, args) or fail("Cancelled", args)
            delete = True

    try:
        remote_src.copy(args.dst, args, overwrite=delete)
    except DropboxError:
        fail(
            "%s could not be copied to %s" %
            (dbx_uri(remote_src.uri), args.dest),
            args,
        )


def cp_from(args):
    """Copy a file from Dropbox."""
    try:
        remote = get_remote(args.src, args)
    except (ValueError, TypeError) as e:
        pdbox.debug(e, args)
        fail("Couldn't find %s" % dbx_uri(args.src), args)

    if not isinstance(remote, RemoteFile):
        fail(
            "%s is not a file, use sync to download folders" %
            remote.uri,
            args,
        )

    try:
        local = get_local(args.dst, args)
    except ValueError:
        delete = False
    else:  # Something exists here.
        if isinstance(local, LocalFolder):
            args.dst = os.path.join(local.path, remote.name)
            cp_from(args)
            return
        else:
            # Overwrite the existing file.
            overwrite(local.path, args) or fail("Cancelled", args)
            delete = True

    try:
        remote.download(args.dst, args, overwrite=delete)
    except DropboxError:
        fail("Couldn't download %s" % remote.uri, args)


def cp_to(args):
    """Copy a file to Dropbox."""
    try:
        local = get_local(args.src, args)
    except ValueError:
        fail("%s does not exist" % args.src, args)

    if isinstance(local, LocalFolder):
        fail("%s is a folder, use sync to upload folders", args.src, args)
    if local.islink and not args.follow_symlinks:
        fail("%s is a symlink and --no-follow-symlinks is set", args.src, args)

    try:
        remote = get_remote(args.dst, args)
    except ValueError:  # Remote file probably doesn't exist.
        delete = False
    except TypeError:
        fail("Something exists at %s" % dbx_uri(args.dst), args)
    else:
        if not isinstance(remote, RemoteFile):
            # Place the file inside the folder.
            args.dst = "%s/%s" % (remote.path, local.name)
            cp_to(args)
            return
        else:
            # Overwrite the existing file.
            overwrite(remote.uri, args) or fail("Cancelled", args)
            delete = True

    try:
        local.upload(args.dst, args, overwrite=delete)
    except DropboxError:
        fail("Uploading %s to %s failed" % (dbx_uri(args.src), args.dst), args)
