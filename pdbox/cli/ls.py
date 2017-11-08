import pdbox

from pdbox.models import get_remote, RemoteFolder
from pdbox.utils import DropboxError, isize, dbx_uri
from tabulate import tabulate


def ls():
    """
    List one or more directories inside Dropbox.

    pdbox._args:
    - path (list[string])
    - recursive (bool)
    - maxdepth (int)
    - human_readable (bool)
    - summarize (bool)
    """
    success = True

    for path in pdbox._args["path"]:
        try:
            folder = get_remote(path)
        except ValueError:  # The path probably doesn't exist.
            folder = None

        if not isinstance(folder, RemoteFolder):
            pdbox.error("%s is not a folder" % dbx_uri(path))
            success = False
            continue

        try:
            entries = folder.contents()
        except DropboxError:
            pdbox.error("%s could not be displayed" % folder.uri)
            success = False
        else:
            if not entries:
                print("%s: no files or folders" % folder.uri)
            else:
                success &= display(folder, entries)

    return success


def display(folder, entries, depth=1):
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
            sz = isize(e.size) if pdbox._args["human_readable"] else e.size
            rows.append([e.name, sz, e.modified])

    print(tabulate(rows, headers="firstrow"))

    if pdbox._args["summarize"]:
        def plur(n):
            return "" if n == 1 else "s"
        nfolders = len(entries) - nfiles
        sz = isize(tsize) if pdbox._args["human_readable"] else str(tsize)
        print(
            "%d file%s, %d folder%s, %s" %
            (nfiles, plur(nfiles), nfolders, plur(nfolders), sz),
        )

    print("")
    success = True

    if pdbox._args["recursive"] and (
            pdbox._args["maxdepth"] == -1 or depth < pdbox._args["maxdepth"]):
        for e in filter(lambda e: isinstance(e, RemoteFolder), entries):
            try:
                contents = e.contents()
            except DropboxError:
                pdbox.warn("%s could not be displayed" % e.uri)
                success = False
            else:
                success &= display(e, contents, depth=depth + 1)

    return success
