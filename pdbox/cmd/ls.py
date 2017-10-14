from pdbox.models import from_path, Folder, group
from pdbox.util import err, isize


def ls(args):
    """List a directory inside Dropbox."""
    folder = from_path(args.path)
    if not isinstance(folder, Folder):
        err("%s is not a folder")

    entries = folder.traverse(recursive=args.recursive)
    if not entries:
        print("%s: empty" % folder.path)

    if args.recursive:
        show_recursive(entries, args)
    else:
        show(entries, args)


def show(entries, args):
    """Display a folder non-recursively."""
    n_files, n_dirs, t_size = 0, 0, 0

    for entry in entries[1:]:  # Don't include the specified directory.
        if isinstance(entry, Folder):
            n_dirs += 1
            print("%s/" % entry.path)
        else:
            n_files += 1
            t_size += entry.size
            if args.human_readable:
                size = isize(entry.size)
            else:
                size = str(entry.size)
            print("%s -- %s" % (entry.name, size))

    if args.summarize:
        size = isize(t_size) if args.human_readable else str(size)
        print("\n%d file(s), %d folder(s), %s" % (n_files, n_dirs, size))


def show_recursive(entries, args):
    """Recursively display a folder."""
    groups = group(entries)
    t_files = sum(len(groups[f]) for f in groups)
    t_dirs = len(groups) - 1  # Don't include the specified directory.
    t_size = 0

    for folder in groups:
        print("%s:" % folder.path)
        for f in groups[folder]:
            t_size += f.size
            if args.human_readable:
                size = isize(f.size)
            else:
                size = str(f.size)
            print("  %s -- %s" % (f.name, size))
        if args.summarize:
            nfiles = len(groups[folder])
            size = sum(f.size for f in groups[folder])
            if args.human_readable:
                size = isize(size)
            print("%d files, %s" % (nfiles, size))
        print()

    if args.summarize:
        size = isize(t_size) if args.human_readable else str(t_size)
        print("%d file(s), %d folder(s), %s" % (t_files, t_dirs, size))
