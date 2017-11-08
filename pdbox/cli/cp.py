import os.path
import pdbox

from pdbox.models import get_local, get_remote, RemoteFile, LocalFolder
from pdbox.utils import DropboxError, dbx_uri, overwrite


def cp(**kwargs):
    """
    Copy one or more files to/from/inside Dropbox.

    kwargs:
    - src (list[string])
    - dst (string)
    - dryrun (bool)
    - quiet (bool)
    - follow_symlinks (bool)
    - only_show_errors (bool)
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
            success &= cp_inside(src, **kwargs)
        elif src.startswith("dbx://"):
            success &= cp_from(src, **kwargs)
        else:
            success &= cp_to(src, **kwargs)

    return success


def cp_inside(src, **kwargs):
    """Copy a file inside Dropbox."""
    try:
        remote_src = get_remote(src, **kwargs)
    except ValueError:
        pdbox.error("%s was not found" % dbx_uri(src), **kwargs)
        return False

    if not isinstance(remote_src, RemoteFile) and not kwargs["recursive"]:
        pdbox.error(
            "%s is a folder and --recursive is not set" % remote_src.uri,
            **kwargs,
        )
        return False

    try:
        remote_dest = get_remote(kwargs["dst"], **kwargs)
    except ValueError:
        delete = False
    else:  # Something exists here.
        if not isinstance(remote_dest, RemoteFile):
            # Place the source inside the folder.
            kwargs["dst"] = "%s/%s" % (remote_dest.path, remote_src.name)
            return cp_inside(src, **kwargs)
        else:
            # Overwrite the existing file.
            if not overwrite(remote_dest.uri, **kwargs):
                pdbox.error("Cancelled", **kwargs)
                return False
            else:
                delete = True

    try:
        remote_src.copy(kwargs["dst"], overwrite=delete, **kwargs)
    except DropboxError:
        pdbox.error(
            "%s could not be copied to %s" %
            (dbx_uri(remote_src.uri), kwargs["dst"]),
            **kwargs,
        )
        return False
    else:
        return True


def cp_from(src, **kwargs):
    """Copy a file from Dropbox."""
    try:
        remote = get_remote(src, **kwargs)
    except ValueError as e:
        pdbox.debug(e, **kwargs)
        pdbox.error("Couldn't find %s" % dbx_uri(src), **kwargs)

    if not isinstance(remote, RemoteFile) and not kwargs["recursive"]:
        pdbox.error(
            "%s is a folder and --recursive is not set" % remote.uri,
            **kwargs,
        )
        return False

    try:
        local = get_local(kwargs["dst"], **kwargs)
    except ValueError:
        delete = False
    else:  # Something exists here.
        if isinstance(local, LocalFolder):
            # Place the source inside the folder.
            kwargs["dst"] = os.path.join(local.path, remote.name)
            return cp_from(src, **kwargs)
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
    else:
        return True


def cp_to(src, **kwargs):
    """Copy a file to Dropbox."""
    try:
        local = get_local(src, **kwargs)
    except ValueError:
        pdbox.error("%s does not exist" % src, **kwargs)
        return False

    if isinstance(local, LocalFolder) and not kwargs["recursive"]:
        pdbox.error(
            "%s is a folder and --recursive is not set" % local.path,
            **kwargs,
        )
        return False
    if local.islink and not kwargs["follow_symlinks"]:
        pdbox.error(
            "%s is a symlink and --no-follow-symlinks is set" % local.path,
            **kwargs,
        )

    try:
        remote = get_remote(kwargs["dst"], **kwargs)
    except ValueError:  # Remote file probably doesn't exist.
        delete = False
    else:
        if not isinstance(remote, RemoteFile):
            # Place the source inside the folder.
            kwargs["dst"] = "%s/%s" % (remote.path, local.name)
            return cp_to(src, **kwargs)
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
    else:
        return True
