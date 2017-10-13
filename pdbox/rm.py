import dropbox
import sys

from .util import normpath, rsize


def rm(token, args):
    """Remove a file from Dropbox."""
    dbx = dropbox.Dropbox(token)

    path = normpath(args.path)
    size = rsize(token, path)
    prompt = "Delete %s" % path
    if size:
        prompt += "(%s)" % size
    prompt += "? [Y/n] "

    try:
        if args.yes:
            confirm = "yes"
        else:
            confirm = input(prompt)
    except KeyboardInterrupt:
        confirm = "no"
    if confirm.lower() in ["n", "no"]:
        print("Cancelled")
        sys.exit(1)

    try:
        dbx.files_delete(path)
    except dropbox.exceptions.ApiError as e:
        print("Error: %s" % e.error)
