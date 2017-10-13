import dropbox
import sys

from .util import isize, normpath


def ls(token, args):
    """List a directory's contents. args is a Namespace from argparse."""
    # TODO: I think that large folders will be truncated,
    # since the result has a `has_more` field.
    dbx = dropbox.Dropbox(token)

    try:
        result = dbx.files_list_folder(normpath(args.directory))
    except dropbox.exceptions.ApiError as e:
        print("Error: %s" % e.error)
        sys.exit(1)

    for entry in result.entries:
        if isinstance(entry, dropbox.files.FileMetadata):
            print("%s -- %s" % (entry.name, isize(entry.size)))
        else:
            print("%s/" % entry.name)
