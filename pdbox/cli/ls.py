import pdbox

from pdbox.models import get_remote, RemoteFolder
from pdbox.utils import DropboxError, isize, dbx_uri
from tabulate import tabulate


def ls(args):
    """List one or more directories inside Dropbox."""
    success = True

    for path in args.path:
        try:
            folder = get_remote(path, args)
        except (ValueError, TypeError):  # The path probably doesn't exist.
            folder = None

        if not isinstance(folder, RemoteFolder):
            pdbox.error("%s is not a folder" % dbx_uri(path), args)
            success = False
            continue

        try:
            entries = folder.contents(args)
        except DropboxError:
            pdbox.error("%s could not be displayed" % folder.uri, args)
            success = False
        else:
            if not entries:
                print("%s: no files or folders" % folder.uri)
            else:
                success &= display(folder, entries, args)

    return success


def display(folder, entries, args, depth=1):
    """Given a list of folders and files, print them as a table."""
    if not entries:
        print("%s: no files or folders\n" % folder.uri)
        return True

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
    success = True

    if args.recursive and (args.maxdepth == -1 or depth < args.maxdepth):
        for e in filter(lambda e: isinstance(e, RemoteFolder), entries):
            try:
                contents = e.contents(args)
            except DropboxError:
                pdbox.warn("%s could not be displayed" % e.uri, args)
                success = False
            else:
                success &= display(e, contents, args, depth=depth + 1)

    return success
