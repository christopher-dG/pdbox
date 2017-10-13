import argparse
import pdbox


def get_parser():
    """Parse argv into an argparse Namespace."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd")
    subparsers.required = True
    parse_cp(subparsers)
    parse_ls(subparsers)
    parse_mb(subparsers)
    return parser


def parse_cp(subparsers):
    """Add arguments for the cp command."""
    cp = subparsers.add_parser(
        "cp",
        help="copy file to/from/inside Dropbox",
    )
    cp.set_defaults(func=pdbox.cp, follow_symlinks=True)
    cp.add_argument(
        "src",
        metavar="<source>",
        help="file or directory to copy",
    )
    cp.add_argument(
        "dst",
        metavar="<destination>",
        help="destination file or directory",
    )
    cp.add_argument(
        "--dryrun",
        action="store_true",
        help="display operations without performing them",
    )
    cp.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="don't display operations",
    )
    # TODO: --include
    # TODO: --exclude
    symlinks = cp.add_mutually_exclusive_group()
    symlinks.add_argument(
        "--follow-symlinks",
        dest="follow_symlinks",
        action="store_true",
        help="follow symbolic links on the local filesystem",
    )
    symlinks.add_argument(
        "--no-follow-symlinks",
        dest="follow_symlinks",
        action="store_false",
        help="don't follow symbolic links on the local filesystem",
    )
    cp.add_argument(
        "--only-show-errors",
        action="store_true",
        help="only display errors and warnings",
    )
    cp.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="perform operations on all files under the specified directory",
    )


def parse_ls(subparsers):
    """Add arguments for the ls command."""
    ls = subparsers.add_parser(
        "ls",
        help="list a folder inside Dropbox",
    )
    ls.set_defaults(func=pdbox.ls)
    ls.add_argument(
        "path",
        metavar="<path>",
        nargs="?",
        default="",
        help="folder to list (leave empty to list root folder)",
    )
    ls.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="perform operations on all files under the specified folder",
    )
    ls.add_argument(
        "--human-readable",
        action="store_true",
        help="display file sizes in human-readable format",
    )
    ls.add_argument(
        "--summarize",
        action="store_true",
        help="display summary information (number of objects, total size)",
    )


def parse_mb(subparsers):
    """Add arguments for the mb command."""
    mb = subparsers.add_parser(
        "mb",
        help="create a new folder inside Dropbox",
    )
    mb.set_defaults(func=pdbox.mb)
    mb.add_argument(
        "path",
        metavar="<path>",
        help="path to the new folder",
    )