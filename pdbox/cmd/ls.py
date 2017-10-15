import dropbox
import pdbox

from pdbox.models import from_remote, Folder
from pdbox.util import fail, isize, normpath
from tabulate import tabulate


def ls(args):
    """List a directory inside Dropbox."""
    path = normpath(args.path)

    try:
        folder = from_remote(path, args)
    except Exception as e:  # The path probably doesn't exist.
        if not isinstance(e, dropbox.exceptions.ApiError):
            # We already logged the API error.
            pdbox.debug(e, args)
        folder = None

    if not isinstance(folder, Folder):
        fail("dbx:/%s is not a folder" % path, args)

    entries = folder.contents(args)

    if not entries:
        print("%s: no files or folders" % folder.dbx_uri())
    else:
        display(entries, args)


def display(entries, args, depth=1):
    """Given a list of folders and files, print them as a table."""
    if len(entries) == 1:  # The only entry is the folder itself.
        print("%s: no files or folders\n" % entries[0].path)
        return

    rows = [[entries[0].dbx_uri(), "size", "modified (UTC)"]]
    nfiles = 0
    tsize = 0

    for e in entries[1:]:  # Skip the first entry (the directory itself).
        if isinstance(e, Folder):
            rows.append([e.name + "/", 0, ""])
        else:
            nfiles += 1
            tsize += e.size
            sz = isize(e.size) if args.human_readable else e.size
            rows.append([e.name, sz, e.date])

    print(tabulate(rows, headers="firstrow"))

    if args.summarize:
        nfolders = len(entries) - nfiles
        sz = isize(tsize) if args.human_readable else str(tsize)
        print("%d files, %d folders, %s" % (nfiles, nfolders, sz))

    print()

    if args.recursive and (args.maxdepth == -1 or depth < args.maxdepth):
        for e in filter(lambda e: isinstance(e, Folder), entries[1:]):
            try:
                contents = e.contents(args)
            except dropbox.exceptions.ApiError:
                pdbox.warn("%s could not be displayed" % e.dbx_uri(), args)
            else:
                display(contents, args, depth=depth + 1)
