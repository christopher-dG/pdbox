import dropbox
import os
import sys

from .util import normpath, size


def put(token, fn, dest=None, force=False, prompt=True):
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
        dest = normpath(dest)

    with open(fn, "rb") as f:
        data = f.read()
    sz = size(data)

    # Get confirmation.
    try:
        if prompt:
            confirm = input("Upload %s to %s (%s)? [Y/n] " % (fn, dest, sz))
        else:
            confirm = ""
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
            print("Error: %s" % e.error)
            sys.exit(1)
    else:
        print("Uploaded to %s" % dest)


def is_folder(e):
    """Determine if e was raised because a folder already exists at dest."""
    try:
        return e.error.get_path().reason.get_conflict().is_folder()
    except:
        return False
