import os
import pdbox.utils as utils

from nose.tools import assert_raises
from . import FakeArgs, nofile, testfile


fa = FakeArgs(quiet=True)


def test_normpath():
    normpath = utils.normpath
    assert normpath("dbx://") == "/"
    assert normpath("asdf") == "/asdf"
    assert normpath("asdf////asdf") == "/asdf/asdf"


def test_isize():
    isize = utils.isize
    assert isize(1023) == "1023 B"
    assert isize(1023.6) == "1023 B"
    assert isize(1024) == "1.00 KB"
    assert isize(1024 * 1.5) == "1.50 KB"
    assert isize(1024 * 1024) == "1.00 MB"
    assert isize(1024 * 1024 * 3.643) == "3.64 MB"
    assert isize(1024 * 1024 * 1024 * 252.5913) == "252.59 GB"


def test_execute():
    execute = utils.execute
    assert_raises(FileNotFoundError, execute, fa, os.stat, nofile)
    assert isinstance(execute(fa, os.stat, testfile), os.stat_result)


def test_overwrite():
    # TODO: Find a way to write to stdin.
    overwrite = utils.overwrite
    assert overwrite(testfile, fa)
