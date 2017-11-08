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
