import os
import pdbox

from pdbox.models import get_local, get_remote, RemoteFolder, LocalFolder
from pdbox.utils import DropboxError, dbx_uri, overwrite


def mv(**kwargs):
    """
    Move one or  files or directories to/from/inside Dropbox.

    kwargs:
    - src (string)
    - dst (string)
    - dryrun (bool)
    - quiet (bool)
    - follow_symlinks (bool)
    - only_show_errors (bool)
    - recursive (bool)
    - chunksize (float)
    """
    if len(kwargs["src"]) > 1 and not (
            pdbox.cli.assert_is_folder(kwargs["dst"], **kwargs)):
        pdbox.error(
            "%s is not a folder; can't move multiple items here" %
            kwargs["dst"],
            **kwargs,
        )
        return False

    dest = kwargs["dst"]
    success = True

    for src in kwargs.pop("src"):
        if not pdbox.cli.validate_src_dest(src, dest):
            pdbox.error(
                "At least one of <source> or <destination> must be a Dropbox "
                "path with the prefix 'dbx://'",
                **kwargs,
            )
            success = False
            continue

        if src.startswith("dbx://") and dest.startswith("dbx://"):
            success &= mv_inside(src, **kwargs)
        elif src.startswith("dbx://"):
            success &= mv_from(src, **kwargs)
        else:
            success &= mv_to(src, **kwargs)

    return success


def mv_inside(src, **kwargs):
    """Move a file or directory inside Dropbox."""
    try:
        remote_src = get_remote(src, **kwargs)
    except ValueError:  # No file, nothing to move.
        pdbox.error("%s couldn't be found" % dbx_uri(src), **kwargs)
        return False
    else:  # Something exists to be downloaded.
        if isinstance(remote_src, RemoteFolder) and not kwargs["recursive"]:
            pdbox.error(
                "%s is a folder and --recursive is not set" % remote_src.uri,
                **kwargs,
            )
            return False

    try:
        remote_dest = get_remote(kwargs["dst"], **kwargs)
    except ValueError:  # Nothing found at the destination.
        delete = False
    else:
        if isinstance(remote_dest, RemoteFolder):
            # Place the source inside the folder.
            kwargs["dst"] = "%s/%s" % (remote_dest.path, remote_src.name)
            return mv_inside(src, **kwargs)
        else:
            # Overwrite the existing file.
            if not overwrite(remote_dest.uri, **kwargs):
                pdbox.error("Cancelled", **kwargs)
                return False
            else:
                delete = True

    # Now that the path is clear, we can move the file.
    try:
        remote_src.move(kwargs["dst"], overwrite=delete, **kwargs)
    except DropboxError:
        pdbox.error(
            "%s could not be moved to %s" %
            (remote_src.uri, dbx_uri(kwargs["dst"])),
            **kwargs,
        )
        return False
    else:
        return True


def mv_from(src, **kwargs):
    """Move a file from Dropbox."""
    try:
        remote = get_remote(src, **kwargs)
    except ValueError:  # No file, can't download anything.
        pdbox.error("%s could not be found" % dbx_uri(src), **kwargs)
        return False

    if isinstance(remote, RemoteFolder) and not kwargs["recursive"]:
        pdbox.error(
            "%s is a folder and --recursive is not set" % remote.uri,
            **kwargs,
        )
        return False

    try:
        local = get_local(kwargs["dst"], **kwargs)
    except ValueError:  # Nothing exists here, so we're clear to download.
        delete = False
    else:  # Something exists here.
        if isinstance(local, LocalFolder):
            # Place the source inside the folder.
            kwargs["dst"] = os.path.join(local.path, remote.name)
            return mv_from(src, **kwargs)
        else:
            # Overwrite the existing file.
            if not overwrite(local.path, **kwargs):
                pdbox.error("Cancelled", **kwargs)
                return False
            else:
                delete = True

    try:
        remote.download(kwargs["dst"], overwrite=delete, **kwargs)
    except DropboxError:
        pdbox.error("Couldn't download %s" % remote.uri, **kwargs)
        return False
    except Exception as e:  # Some other exception, probably FS related.
        pdbox.debug(e, **kwargs)
        pdbox.error(
            "Something went wrong, check %s for your download" %
            pdbox.TMP_DOWNLOAD_DIR,
            **kwargs,
        )
        return False

    try:
        remote.delete(**kwargs)
    except DropboxError:
        pdbox.error("%s couldn't be deleted" % remote.uri, **kwargs)
        return False
    else:
        return True


def mv_to(src, **kwargs):
    """Move a file to Dropbox."""
    try:
        local = get_local(src, **kwargs)
    except ValueError:
        pdbox.error("%s could not be found" % os.path.abspath(src), **kwargs)
        return False

    if local.islink and not kwargs["follow_symlinks"]:
        pdbox.error(
            "%s is a symlink and --no-follow-symlinks is set" %
            os.path.abspth(src),
            **kwargs,
        )
        return False
    if isinstance(local, LocalFolder) and not kwargs["recursive"]:
        pdbox.error(
            "%s is a folder and --recursive is not set" % local.path,
            **kwargs,
        )
        return False

    try:
        remote = get_remote(kwargs["dst"], **kwargs)
    except ValueError:  # Remote file probably doesn't exist.
        delete = False
    else:
        if isinstance(remote, RemoteFolder):
            # Place the source inside the folder.
            kwargs["dst"] = "%s/%s" % (remote.path, local.name)
            return mv_to(src, **kwargs)
        else:
            # Overwrite the existing file.
            if not overwrite(remote.uri, **kwargs):
                pdbox.error("Cancelled", **kwargs)
                return False
            else:
                delete = True

    try:
        local.upload(kwargs["dst"], overwrite=delete, **kwargs)
    except DropboxError:
        pdbox.error(
            "Uploading %s to %s failed" % (local.path, kwargs["dst"]),
            **kwargs,
        )
        return False

    try:
        local.delete(**kwargs)
    except Exception as e:
        pdbox.debug(e, **kwargs)
        pdbox.error("%s could not be deleted" % local.path, **kwargs)
        return False
    else:
        return True
