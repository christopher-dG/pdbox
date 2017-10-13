import dropbox
import os.path
import sys

from .util import normpath


# def get(token, fn, dest=None, force=False, prompt=True):
def get(token, args):
    """Download a file from Dropbox."""
    dbx = dropbox.Dropbox(token)

    fn = normpath(args.source)
    if args.destination:
        dest = args.destination
    else:
        dest = os.path.relpath(os.path.basename(fn))

    if not args.force and os.path.isfile(dest):
        print("A file already exists at %s; exiting" % dest)
        sys.exit(1)

    # Get confirmation.
    try:
        if not args.yes:
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
