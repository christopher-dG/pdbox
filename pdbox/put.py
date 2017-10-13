import dropbox
import os
import sys

from .util import normpath, ssize


# def put(token, fn, dest=None, force=False, prompt=True):
def put(token, args):
    """Upload a file to Dropbox."""
    dbx = dropbox.Dropbox(token)

    # Make sure the file exists.
    if not os.path.isfile(args.source):
        print("File %s does not exist; exiting" % args.source)
        sys.exit(1)

    # If no destination is given, upload to the base directory.
    if args.destination:
        dest = args.destination
    else:
        dest = "/%s" % os.path.basename(args.source)
    dest = normpath(dest)

    with open(args.source, "rb") as f:
        data = f.read()
    sz = ssize(data)

    # Get confirmation.
    try:
        if not args.yes:
            confirm = input(
                "Upload %s to %s (%s)? [Y/n] "
                % (args.source, dest, sz)
            )
        else:
            confirm = ""
        if confirm.lower() in ["n", "no"]:
            raise KeyboardInterrupt
    except KeyboardInterrupt:
        print("Cancelled")
        sys.exit(1)

    # Upload the file.
    if args.force:
        mode = dropbox.files.WriteMode.overwrite
    else:
        mode = dropbox.files.WriteMode.add
    try:
        dbx.files_upload(data, dest, mode)
    except dropbox.exceptions.ApiError as e:
        if is_folder(e):  # Put the file into the folder.
            args.destination += "/" + os.path.basename(args.source)
            args.yes = True
            put(token, args)
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
