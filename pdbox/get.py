import dropbox
import os.path
import sys

from .util import normpath


def get(token, fn, dest=None, force=False, prompt=True):
    """Download a file from Dropbox."""
    dbx = dropbox.Dropbox(token)

    fn = normpath(fn)
    if not dest:
        dest = os.path.relpath(os.path.basename(fn))

    if not force and os.path.isfile(dest):
        print("A file already exists at %s; exiting" % dest)
        sys.exit(1)

    # Get confirmation.
    try:
        if prompt:
            confirm = input("Download %s to %s? [Y/n]) " % (fn, dest))
        else:
            confirm = ""
        if confirm.lower() in ["n", "no"]:
            raise KeyboardInterrupt
    except KeyboardInterrupt:
        print("Cancelled")
        sys.exit(1)

    # Download the file.
    try:
        dbx.files_download_to_file(dest, fn)
    except dropbox.exceptions.ApiError as e:
        print("Error: %s" % e.error)
        sys.exit(1)
    else:
        print("Downloaded %s to %s" % (fn, dest))
