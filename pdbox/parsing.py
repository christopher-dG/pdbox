import argparse
import logging
import pdbox
import pdbox.cli as cli
import pdbox.tui as tui


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
    parse_ls(subparsers)
    parse_cp(subparsers)
    parse_mv(subparsers)
    parse_mkdir(subparsers)
    parse_rm(subparsers)
    parse_rmdir(subparsers)
    parse_sync(subparsers)
    parse_tui(subparsers)
    args = parser.parse_args()
    if args.debug:
        pdbox._logger.setLevel(logging.DEBUG)
    return args


def parse_cp(subparsers):
    """Add arguments for the cp command."""
    cp = subparsers.add_parser(
        "cp",
        help="copy files",
    )
    cp.set_defaults(func=cli.cp, follow_symlinks=True)
    cp.add_argument(
        "src",
        metavar="<source ...>",
        nargs="+",
        help="file(s) or folder(s) to copy",
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
        help="list folders",
    )
    ls.set_defaults(func=cli.ls)
    ls.add_argument(
        "path",
        metavar="<path ...>",
        nargs="*",
        default=[""],
        help="folder(s) to list (empty lists the root folder)",
    )
    ls.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="perform operations on all files under the specified folder(s)",
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


def parse_mkdir(subparsers):
    """Add arguments for the mkdir command."""
    mkdir = subparsers.add_parser(
        "mkdir",
        help="create folders",
    )
    mkdir.set_defaults(func=cli.mkdir)
    mkdir.add_argument(
        "path",
        metavar="<path ...>",
        nargs="+",
        help="path(s) to the new folder(s)",
    )
    mkdir.add_argument(
        "--dryrun",
        action="store_true",
        help="display operations without performing them",
    )


def parse_mv(subparsers):
    """Add arguments for the mv command."""
    mv = subparsers.add_parser(
        "mv",
        help="move files or folders",
    )
    mv.set_defaults(func=cli.mv)
    mv.add_argument(
        "src",
        metavar="<source ...>",
        nargs="+",
        help="file(s) or folder(s) to move",
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
        help="perform operations on all files under the specified folder(s)",
    )
    mv.add_argument(
        "-c",
        "--chunksize",
        type=float,
        nargs="?",
        default=149,  # Dropbox maximum is 150 MB.
        help="chunk size in MB for splitting large uploads",
    )


def parse_rmdir(subparsers):
    """Add arguments for the rmdir command."""
    rmdir = subparsers.add_parser(
        "rmdir",
        help="delete folders",
    )
    rmdir.set_defaults(func=cli.rmdir)
    rmdir.add_argument(
        "path",
        metavar="<folder ...>",
        nargs="+",
        help="folder(s) to remove",
    )
    rmdir.add_argument(
        "--dryrun",
        action="store_true",
        help="display operations without performing them",
    )

    rmdir.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="delete non-empty folders",
    )


def parse_rm(subparsers):
    """Add arguments for the rm command."""
    rm = subparsers.add_parser(
        "rm",
        help="delete files or folders",
    )
    rm.set_defaults(func=cli.rm)
    rm.add_argument(
        "path",
        metavar="<path ...>",
        nargs="+",
        help="path(s) to remove",
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
        help="perform operations on all files under the specified folder(s)",
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
        help="synchronize a folder",
    )
    sync.set_defaults(func=cli.sync)
    sync.add_argument(
        "src",
        metavar="<source>",
        help="folder to sync",
    )
    sync.add_argument(
        "dst",
        metavar="<destination>",
        help="destination folder",
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


def parse_tui(subparsers):
    """Add arguments for the tui command."""
    ui = subparsers.add_parser(
        "tui",
        help="run pdbox in an interactive TUI",
    )
    ui.set_defaults(func=tui.run)
