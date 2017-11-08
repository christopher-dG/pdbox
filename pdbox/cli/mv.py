import os
import pdbox

from pdbox.models import get_local, get_remote, RemoteFolder, LocalFolder
from pdbox.utils import DropboxError, dbx_uri, overwrite


def mv():
    """
    Move one or  files or directories to/from/inside Dropbox.

    pdbox._args:
    - src (string)
    - dst (string)
    - dryrun (bool)
    - quiet (bool)
    - follow_symlinks (bool)
    - only_show_errors (bool)
    - recursive (bool)
    - chunksize (float)
    """
    src_list, dest = pdbox._args["src"], pdbox._args["dest"]
    if len(src_list) > 1 and not pdbox.cli.assert_is_folder(dest):
        pdbox.error(
            "%s is not a folder; can't move multiple items here" % dest,
        )
        return False

    success = True

    for src in src_list:
        if not pdbox.cli.validate_src_dest(src, dest):
            pdbox.error(
                "At least one of <source> or <destination> must be a Dropbox "
                "path with the prefix 'dbx://'",
            )
            success = False
            continue

        if src.startswith("dbx://") and dest.startswith("dbx://"):
            func = mv_inside
        elif src.startswith("dbx://"):
            func = mv_from
        else:
            func = mv_to
        success &= func(src, dest)

    return success


def mv_inside(src, dest):
    """Move a file or directory inside Dropbox."""
    try:
        remote_src = get_remote(src)
    except ValueError:  # No file, nothing to move.
        pdbox.error("%s couldn't be found" % dbx_uri(src))
        return False

    if isinstance(remote_src, RemoteFolder) and not pdbox._args["recursive"]:
        pdbox.error(
            "%s is a folder and --recursive is not set" % remote_src.uri,
        )
        return False

    try:
        remote_dest = get_remote(dest)
    except ValueError:  # Nothing found at the destination.
        delete = False
    else:
        if isinstance(remote_dest, RemoteFolder):
            # Place the source inside the folder.
            dest = "%s/%s" % (remote_dest.path, remote_src.name)
            return mv_inside(src, dest)
        else:
            # Overwrite the existing file.
            if not overwrite(remote_dest.uri):
                pdbox.error("Cancelled")
                return False
            else:
                delete = True

    # Now that the path is clear, we can move the file.
    try:
        remote_src.move(dest, overwrite=delete)
    except DropboxError:
        pdbox.error(
            "%s could not be moved to %s" %
            (remote_src.uri, dbx_uri(dest)),
        )
        return False
    else:
        return True


def mv_from(src, dest):
    """Move a file from Dropbox."""
    try:
        remote = get_remote(src)
    except ValueError:  # No file, can't download anything.
        pdbox.error("%s could not be found" % dbx_uri(src))
        return False

    if isinstance(remote, RemoteFolder) and not pdbox._args["recursive"]:
        pdbox.error("%s is a folder and --recursive is not set" % remote.uri)
        return False

    try:
        local = get_local(dest)
    except ValueError:  # Nothing exists here, so we're clear to download.
        delete = False
    else:  # Something exists here.
        if isinstance(local, LocalFolder):
            # Place the source inside the folder.
            dest = os.path.join(local.path, remote.name)
            return mv_from(src, dest)
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
    except Exception as e:  # Some other exception, probably FS related.
        pdbox.debug(e)
        pdbox.error(
            "Something went wrong, check %s for your download" %
            pdbox.TMP_DOWNLOAD_DIR,
        )
        return False

    try:
        remote.delete()
    except DropboxError:
        pdbox.error("%s couldn't be deleted" % remote.uri)
        return False
    else:
        return True


def mv_to(src, dest):
    """Move a file to Dropbox."""
    try:
        local = get_local(src)
    except ValueError:
        pdbox.error("%s could not be found" % os.path.abspath(src))
        return False

    if local.islink and not pdbox._args["follow_symlinks"]:
        pdbox.error(
            "%s is a symlink and --no-follow-symlinks is set" %
            os.path.abspth(src),
        )
        return False
    if isinstance(local, LocalFolder) and not pdbox._args["recursive"]:
        pdbox.error("%s is a folder and --recursive is not set" % local.path)
        return False

    try:
        remote = get_remote(dest)
    except ValueError:  # Remote file probably doesn't exist.
        delete = False
    else:
        if isinstance(remote, RemoteFolder):
            # Place the source inside the folder.
            dest = "%s/%s" % (remote.path, local.name)
            return mv_to(src, dest)
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

    try:
        local.delete()
    except Exception as e:
        pdbox.debug(e)
        pdbox.error("%s could not be deleted" % local.path)
        return False
    else:
        return True
