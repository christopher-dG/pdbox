import os
import pdbox.utils as utils

from nose.tools import assert_raises
from . import nofile, testfile


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
    assert_raises(Exception, execute,  os.stat, nofile)
    assert isinstance(execute(os.stat, testfile), os.stat_result)


def test_dbx_uri():
    dbx_uri = utils.dbx_uri
    assert dbx_uri("") == "dbx://"
    assert dbx_uri("/") == "dbx://"
    assert dbx_uri(os.path.join("hello", "world")) == "dbx://hello/world"
