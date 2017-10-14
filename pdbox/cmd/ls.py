from pdbox import logger
from pdbox.models import from_path, Folder
from pdbox.util import err, isize
from tabulate import tabulate


def ls(args):
    """List a directory inside Dropbox."""
    try:
        folder = from_path(args.path)
    except Exception as e:  # The path probably doesn't exist.
        logger.debug(e)
        pass
    if not isinstance(folder, Folder):
        err("%s is not a folder" % args.path)
    entries = folder.contents()
    if not entries:
        print("%s: empty" % folder.path)
    else:
        display(entries, args)


def display(entries, args, depth=1):
    """Given a list of folders and files, print them as a table."""
    if len(entries) == 1:
        print("%s: no files or folders\n" % entries[0].path)
        return

    rows = [[entries[0].path, "t", "size", "date"]]
    nfiles = 0
    tsize = 0
    for e in entries[1:]:  # Skip the first entry (the directory itself).
        if isinstance(e, Folder):
            rows.append([e.name, "d", 0, ""])
        else:
            nfiles += 1
            tsize += e.size
            sz = isize(e.size) if args.human_readable else e.size
            rows.append([e.name, "f", sz, e.date])
    print(tabulate(rows, headers="firstrow"))

    if args.summarize:
        nfolders = len(entries) - nfiles
        sz = isize(tsize) if args.human_readable else str(tsize)
        print("%d files, %d folders, %s" % (nfiles, nfolders, sz))

    print()

    if args.recursive and depth < args.maxdepth:
        for e in filter(lambda e: isinstance(e, Folder), entries[1:]):
            display(e.contents(), args, depth=depth + 1)
