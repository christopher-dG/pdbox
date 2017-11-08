import pdbox

from pdbox.models import get_remote, RemoteFolder
from pdbox.utils import DropboxError, isize, dbx_uri
from tabulate import tabulate


def ls(**kwargs):
    """
    List one or more directories inside Dropbox.

    kwargs:
    - path (list[string])
    - recursive (bool)
    - maxdepth (int)
    - human_readable (bool)
    - summarize (bool)
    """
    success = True

    for path in kwargs.pop("path"):
        try:
            folder = get_remote(path, **kwargs)
        except ValueError:  # The path probably doesn't exist.
            folder = None

        if not isinstance(folder, RemoteFolder):
            pdbox.error("%s is not a folder" % dbx_uri(path), **kwargs)
            success = False
            continue

        try:
            entries = folder.contents(**kwargs)
        except DropboxError:
            pdbox.error("%s could not be displayed" % folder.uri, **kwargs)
            success = False
        else:
            if not entries:
                print("%s: no files or folders" % folder.uri)
            else:
                success &= display(folder, entries, **kwargs)

    return success


def display(folder, entries, depth=1, **kwargs):
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
            sz = isize(e.size) if kwargs["human_readable"] else e.size
            rows.append([e.name, sz, e.modified])

    print(tabulate(rows, headers="firstrow"))

    if kwargs["summarize"]:
        def plur(n):
            return "" if n == 1 else "s"
        nfolders = len(entries) - nfiles
        sz = isize(tsize) if kwargs["human_readable"] else str(tsize)
        print(
            "%d file%s, %d folder%s, %s" %
            (nfiles, plur(nfiles), nfolders, plur(nfolders), sz),
        )

    print("")
    success = True

    if kwargs["recursive"] and (
            kwargs["maxdepth"] == -1 or depth < kwargs["maxdepth"]):
        for e in filter(lambda e: isinstance(e, RemoteFolder), entries):
            try:
                contents = e.contents(**kwargs)
            except DropboxError:
                pdbox.warn("%s could not be displayed" % e.uri, **kwargs)
                success = False
            else:
                success &= display(e, contents, depth=depth + 1, **kwargs)

    return success
