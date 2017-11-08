import os.path
import pdbox

from pdbox.models import get_local, get_remote, RemoteFile, LocalFolder
from pdbox.utils import DropboxError, dbx_uri, overwrite


def cp():
    """
    Copy one or more files to/from/inside Dropbox.

    pdbox._args:
    - src (list[string])
    - dst (string)
    - dryrun (bool)
    - quiet (bool)
    - follow_symlinks (bool)
    - only_show_errors (bool)
    - chunksize (float)
    """
    args = pdbox._args
    if len(args["src"]) > 1 and not pdbox.cli.assert_is_folder(args["dst"]):
        pdbox.error(
            "%s is not a folder; can't move multiple items here" %
            args["dst"],
        )
        return False

    dest = args["dst"]
    success = True

    for src in args["src"]:
        if not pdbox.cli.validate_src_dest(src, dest):
            pdbox.error(
                "At least one of <source> or <destination> must be a Dropbox "
                "path with the prefix 'dbx://'",
            )
            success = False
            continue

        if src.startswith("dbx://") and dest.startswith("dbx://"):
            func = cp_inside
        elif src.startswith("dbx://"):
            func = cp_from
        else:
            func = cp_to
        success &= func(src, dest)

    return success


def cp_inside(src, dest):
    """Copy a file inside Dropbox."""
    try:
        remote_src = get_remote(src)
    except ValueError:
        pdbox.error("%s was not found" % dbx_uri(src))
        return False

    if not isinstance(remote_src, RemoteFile) and not pdbox._args["recursive"]:
        pdbox.error(
            "%s is a folder and --recursive is not set" % remote_src.uri,
        )
        return False

    try:
        remote_dest = get_remote(dest)
    except ValueError:
        delete = False
    else:  # Something exists here.
        if not isinstance(remote_dest, RemoteFile):
            # Place the source inside the folder.
            dest = "%s/%s" % (remote_dest.path, remote_src.name)
            return cp_inside(src, dest)
        else:
            # Overwrite the existing file.
            if not overwrite(remote_dest.uri):
                pdbox.error("Cancelled")
                return False
            else:
                delete = True

    try:
        remote_src.copy(dest, overwrite=delete)
    except DropboxError:
        pdbox.error(
            "%s could not be copied to %s" % (dbx_uri(remote_src.uri), dest),
        )
        return False
    else:
        return True


def cp_from(src, dest):
    """Copy a file from Dropbox."""
    try:
        remote = get_remote(src)
    except ValueError as e:
        pdbox.debug(e)
        pdbox.error("Couldn't find %s" % dbx_uri(src))

    if not isinstance(remote, RemoteFile) and not pdbox._args["recursive"]:
        pdbox.error("%s is a folder and --recursive is not set" % remote.uri)
        return False

    try:
        local = get_local(dest)
    except ValueError:
        delete = False
    else:  # Something exists here.
        if isinstance(local, LocalFolder):
            # Place the source inside the folder.
            dest = os.path.join(local.path, remote.name)
            return cp_from(src, dest)
        else:
            # Overwrite the existing file.
            if not overwrite(local.path):
                pdbox.error("Cancelled")
                return False
            else:
                delete = True

    try:
        remote.download(dest, overwrite=delete)
    except DropboxError:
        pdbox.error("Couldn't download %s" % remote.uri)
        return False
    else:
        return True


def cp_to(src, dest):
    """Copy a file to Dropbox."""
    try:
        local = get_local(src)
    except ValueError:
        pdbox.error("%s does not exist" % src)
        return False

    if isinstance(local, LocalFolder) and not pdbox._args["recursive"]:
        pdbox.error("%s is a folder and --recursive is not set" % local.path)
        return False
    if local.islink and not pdbox._args["follow_symlinks"]:
        pdbox.error(
            "%s is a symlink and --no-follow-symlinks is set" % local.path,
        )

    try:
        remote = get_remote(dest)
    except ValueError:  # Remote file probably doesn't exist.
        delete = False
    else:
        if not isinstance(remote, RemoteFile):
            # Place the source inside the folder.
            dest = "%s/%s" % (remote.path, local.name)
            return cp_to(src, dest)
        else:
            # Overwrite the existing file.
            if not overwrite(remote.uri):
                pdbox.error("Cancelled")
                return False
            else:
                delete = True

    try:
        local.upload(dest, overwrite=delete)
    except DropboxError:
        pdbox.error("Uploading %s to %s failed" % (local.path, dest))
        return False
    else:
        return True
