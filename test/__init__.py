import logging
import os
import pdbox
import shutil


nofile = ".pdboxnonexistent"
testfile = ".pdboxtestfile"
testdir = ".pdboxtestdir"
tempfile = ".pdboxtempfile"
tempdir = ".pdboxtempdir"


if "PDBOX_DEBUG" in os.environ:
    pdbox._logger.setLevel(logging.DEBUG)
else:
    pdbox._logger.setLevel(logging.ERROR)


class FakeArgs:
    """Helper class to simulate the Namespace passed around from argparse."""
    def __init__(self, **kwargs):
        self.src = kwargs["src"] if "src" in kwargs else ""
        self.dst = kwargs["dst"] if "dst" in kwargs else ""
        self.quiet = kwargs["quiet"] if "quiet" in kwargs else False
        self.only_show_errors = kwargs[  # I love PEP8.
            "only_show_errors"] if "only_show_errors" in kwargs else False
        self.dryrun = kwargs["dryrun"] if "dryrun" in kwargs else True


def setup():
    os.mknod(testfile)  # Guaranteed to always exist and be empty.
    os.mkdir(testdir)  # Guaranteed to always exist and be empty.
    os.mknod(tempfile)  # Guaranteed to always exist, no guaranteed contents.
    os.mkdir(tempdir)  # Guaranteed to always exist, no guaranteed contents.


def teardown():
    os.remove(testfile)
    os.rmdir(testdir)
    os.remove(tempfile)
    shutil.rmtree(tempdir)
