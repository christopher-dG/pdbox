import dropbox
import os
import sys

from .util import size


def put(token, fn, dest, force, prompt=True):
    """Upload a file to Dropbox."""
    dbx = dropbox.Dropbox(token)

    # Make sure the file exists.
    if not os.path.isfile(fn):
        print("File %s does not exist; exiting" % fn)
        sys.exit(1)

    # If no destination is given, upload to the base directory.
    if not dest:
        dest = "/%s" % os.path.basename(fn)
    else:
        dest = "/%s" % dest.replace(os.path.sep, "/")
    while "//" in dest:  # normpath won't work on Windows.
        dest = dest.replace("//", "/")

    with open(fn, "rb") as f:
        data = f.read()
    sz = size(data)

    # Get confirmation.
    if prompt:
        confirm = input("Upload %s to %s (%s)? [Y/n] " % (fn, dest, sz))
    else:
        confirm = ""
    try:
        if confirm.lower() in ["n", "no"]:
            raise KeyboardInterrupt
    except KeyboardInterrupt:
        print("Cancelled.")
        sys.exit(1)

    # Upload the file.
    if force:
        mode = dropbox.files.WriteMode.overwrite
    else:
        mode = dropbox.files.WriteMode.add
    try:
        dbx.files_upload(data, dest, mode)
    except dropbox.exceptions.ApiError as e:
        if is_folder(e):  # Put the file into the folder.
            dest += "/" + os.path.basename(fn)
            put(token, fn, dest, force, prompt=False)
        else:
            print(identify_err(e))
            sys.exit(1)
    else:
        print("Uploaded to %s" % dest)


def is_folder(e):
    """Determine if e was raised because a folder already exists at dest."""
    try:
        return e.error.get_path().reason.get_conflict().is_folder()
    except:
        return False


def identify_err(e):
    """Parse an error to return a human-readable cause. This is spaghetti."""
    # TODO: There are tons of uncommon errors to potentially identify here.
    try:  # ApiError.
        e = e.error
    except AttributeError:
        pass
    try:  # UploadError.
        if e.is_path():
            e = e.get_path()
        elif e.is_other():
            return unknown(e.other)
    except AttributeError:
        pass
    try:  # UploadWriteFailed.
        e = e.reason
    except AttributeError:
        pass
    try:  # WriteConflict.
        if e.is_conflict():
            e = e.get_conflict()
        else:  # There are lots of cases here.
            return unknown(e)
    except AttributeError:
        pass
    try:  # WriteConflict.
        if e.is_file():
            return "Error: A file already exists at destination"
        elif e.is_folder():  # is_folder should catch this preemptively.
            return "Error: A folder already exists at destination"
        elif e.is_file_ancestor():
            return "Error: A file in the destination path already exists"
    except AttributeError:
        pass
    return unknown(e)


def unknown(e):
    """We tried, and failed."""
    return "Unknown error: %e" % e
