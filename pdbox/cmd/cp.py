import os.path
import pdbox

from pdbox.models import from_local, from_remote, File, LocalFolder
from pdbox.util import fail, normpath


def cp(args):
    """Copy a file or directory to/from/inside Dropbox."""
    if not args.src.startswith("dbx://") and not args.dst.startswith("dbx://"):
        fail(
            "At least one of <source> or <destination> must be a Dropbox path "
            "with the prefix 'dbx://'",
            args,
        )

    if args.src.startswith("dbx://") and args.dst.startswith("dbx://"):
        cp_inside(args)
    elif args.src.startswith("dbx://"):
        cp_from(args)
    else:
        cp_to(args)


def cp_inside(args):
    """Copy a file or directory inside Dropbox."""
    pass


def cp_from(args):
    """Copy a file or directory from Dropbox."""
    pass


def cp_to(args):
    """Copy a file or directory to Dropbox."""
    src = os.path.normpath(args.src)
    dest = normpath(args.dst)
    if os.path.islink(src) and not args.follow_symlinks:
        fail(
            "Not uploading; %s is a symlink and --no-follow-symlinks is set"
            % src,
            args,
        )

    local = from_local(src, args)
    if not local:
        fail("%s does not exist locally" % src, args)
    elif isinstance(local, LocalFolder) and not args.recursive:
        fail(
            "Not uploading folder %s: --recursive is not set" % local.path,
            args,
        )
    elif isinstance(local, LocalFolder):  # Recursively upload the folder.
        for entry in local.contents(args):
            args.src = entry.path
            args.dst = "%s/%s" % (src, os.path.basename(entry.path))
            pdbox.debug("Recursing: %s to %s" % (args.src, args.dst))
            cp_to(args)
        return

    existing = from_remote(dest, args)
    if isinstance(existing, File) and not args.quiet:
        try:
            confirm = input(
                "File %s exists: overwrite? [y/N] " % existing.dbx_uri(),
            )
        except KeyboardInterrupt:
            confirm = "n"
        if confirm.lower() not in ["y", "yes"]:
            fail("Cancelled", args)
    elif existing:  # Is a folder.
        args.dst = "%s/%s" % (existing.path, os.path.basename(local.path))
        cp_to(args)
        return

    local.upload(dest, args)
