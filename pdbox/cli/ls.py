import pdbox

from pdbox.models import get_remote, RemoteFolder
from pdbox.utils import DropboxError, fail, isize, dbx_uri
from tabulate import tabulate


def ls(args):
    """List a directory inside Dropbox."""
    try:
        folder = get_remote(args.path, args)
    except (ValueError, TypeError) as e:  # The path probably doesn't exist.
        folder = None

    if not isinstance(folder, RemoteFolder):
        fail("%s is not a folder" % dbx_uri(args.path), args)

    entries = folder.contents(args)

    if not entries:
        print("%s: no files or folders" % folder.uri)
    else:
        display(folder, entries, args)


def display(folder, entries, args, depth=1):
    """Given a list of folders and files, print them as a table."""
    if not entries:
        print("%s: no files or folders\n" % folder.uri)
        return

    rows = [[folder.uri, "size", "modified (UTC)"]]
    nfiles = 0
    tsize = 0

    for e in entries:
        if isinstance(e, RemoteFolder):
            rows.append([e.name + "/", 0, ""])
        else:
            nfiles += 1
            tsize += e.size
            sz = isize(e.size) if args.human_readable else e.size
            rows.append([e.name, sz, e.modified])

    print(tabulate(rows, headers="firstrow"))

    if args.summarize:
        def plur(s):
            return "" if s == 1 else "s"
        nfolders = len(entries) - nfiles
        sz = isize(tsize) if args.human_readable else str(tsize)
        print(
            "%d file%s, %d folder%s, %s" %
            (nfiles, plur(nfiles), nfolders, plur(nfolders), sz),
        )

    print("")

    if args.recursive and (args.maxdepth == -1 or depth < args.maxdepth):
        for e in filter(lambda e: isinstance(e, RemoteFolder), entries):
            try:
                contents = e.contents(args)
            except DropboxError:
                pdbox.warn("%s could not be displayed" % e.uri, args)
            else:
                display(e, contents, args, depth=depth + 1)
