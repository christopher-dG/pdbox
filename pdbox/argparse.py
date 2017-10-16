import argparse
import logging
import pdbox


def parse_args():
    """Parse argv into an argparse Namespace."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="show debug messages",
    )
    subparsers = parser.add_subparsers(dest="cmd")
    subparsers.required = True
    parse_cp(subparsers)
    parse_ls(subparsers)
    parse_mf(subparsers)
    parse_mv(subparsers)
    parse_rf(subparsers)
    parse_rm(subparsers)
    parse_sync(subparsers)
    args = parser.parse_args()
    if args.debug:
        pdbox._logger.setLevel(logging.DEBUG)
    return args


def parse_cp(subparsers):
    """Add arguments for the cp command."""
    cp = subparsers.add_parser(
        "cp",
        help="copy a file to/from/inside Dropbox",
    )
    cp.set_defaults(func=pdbox.cmd.cp, follow_symlinks=True)
    cp.add_argument(
        "src",
        metavar="<source>",
        help="file or folder to copy",
    )
    cp.add_argument(
        "dst",
        metavar="<destination>",
        help="destination file or folder",
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
        "-c",
        "--chunksize",
        type=float,
        nargs="?",
        default=149,  # Dropbox maximum is 150 MB.
        help="chunk size in MB for splitting large uploads",
    )


def parse_ls(subparsers):
    """Add arguments for the ls command."""
    ls = subparsers.add_parser(
        "ls",
        help="list a folder inside Dropbox",
    )
    ls.set_defaults(func=pdbox.cmd.ls)
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
        "--maxdepth",
        type=int,
        nargs="?",
        default=-1,
        help="maximum depth of recursion",
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


def parse_mf(subparsers):
    """Add arguments for the mf command."""
    mf = subparsers.add_parser(
        "mf",
        help="create a new folder inside Dropbox",
    )
    mf.set_defaults(func=pdbox.cmd.mf)
    mf.add_argument(
        "path",
        metavar="<path>",
        help="path to the new folder",
    )
    mf.add_argument(
        "--dryrun",
        action="store_true",
        help="display operations without performing them",
    )


def parse_mv(subparsers):
    """Add arguments for the mv command."""
    mv = subparsers.add_parser(
        "mv",
        help="move a file or object inside Dropbox",
    )
    mv.set_defaults(func=pdbox.cmd.mv)
    mv.add_argument(
        "src",
        metavar="<source>",
        help="file or folder to move",
    )
    mv.add_argument(
        "dst",
        metavar="<destination>",
        help="destination file or folder",
    )
    mv.add_argument(
        "--dryrun",
        action="store_true",
        help="display operations without performing them",
    )
    mv.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="don't display operations",
    )
    # TODO: --include
    # TODO: --exclude
    symlinks = mv.add_mutually_exclusive_group()
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
    mv.add_argument(
        "--only-show-errors",
        action="store_true",
        help="only display errors and warnings",
    )
    mv.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="perform operations on all files under the specified folder",
    )
    mv.add_argument(
        "-c",
        "--chunksize",
        type=float,
        nargs="?",
        default=149,  # Dropbox maximum is 150 MB.
        help="chunk size in MB for splitting large uploads",
    )


def parse_rf(subparsers):
    """Add arguments for the rf command."""
    rf = subparsers.add_parser(
        "rf",
        help="delete a folder inside Dropbox",
    )
    rf.set_defaults(func=pdbox.cmd.rf)
    rf.add_argument(
        "path",
        metavar="<folder>",
        help="folder to remove",
    )
    rf.add_argument(
        "--dryrun",
        action="store_true",
        help="display operations without performing them",
    )

    rf.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="delete non-empty folders",
    )


def parse_rm(subparsers):
    """Add arguments for the rm command."""
    rm = subparsers.add_parser(
        "rm",
        help="delete a file or folder inside Dropbox",
    )
    rm.set_defaults(func=pdbox.cmd.rm)
    rm.add_argument(
        "path",
        metavar="<path>",
        help="path to remove",
    )
    rm.add_argument(
        "--dryrun",
        action="store_true",
        help="display operations without performing them",
    )
    rm.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="don't display operations",
    )
    rm.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="perform operations on all files under the specified folder",
    )
    # TODO: --include
    # TODO: --exclude
    rm.add_argument(
        "--only-show-errors",
        action="store_true",
        help="only display errors and warnings",
    )


def parse_sync(subparsers):
    """Add arguments for the sync command."""
    sync = subparsers.add_parser(
        "sync",
        help="synchronize a folder to/from/inside Dropbox",
    )
    sync.set_defaults(func=pdbox.cmd.sync)
    sync.add_argument(
        "src",
        metavar="<source>",
        help="file or folder to copy",
    )
    sync.add_argument(
        "dst",
        metavar="<destination>",
        help="destination file or folder",
    )
    sync.add_argument(
        "--dryrun",
        action="store_true",
        help="display operations without performing them",
    )
    sync.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="don't display operations",
    )
    # TODO: --include
    # TODO: --exclude
    symlinks = sync.add_mutually_exclusive_group()
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
    sync.add_argument(
        "--only-show-errors",
        action="store_true",
        help="only display errors and warnings",
    )
    sync.add_argument(
        "--delete",
        action="store_true",
        help="delete files present in <destination> but not <source>",
    )
    sync.add_argument(
        "-c",
        "--chunksize",
        type=float,
        nargs="?",
        default=149,  # Dropbox maximum is 150 MB.
        help="chunk size in MB for splitting large uploads",
    )
