import pdbox.util as util


def test_normpath():
    normpath = util.normpath
    assert normpath("dbx://") == "/"


def test_isize():
    isize = util.isize
    assert isize(1023) == "1023 B"
    assert isize(1023.6) == "1023 B"
    assert isize(1024) == "1.00 KB"
    assert isize(1024 * 1.5) == "1.50 KB"
    assert isize(1024 * 1024) == "1.00 MB"
    assert isize(1024 * 1024 * 3.643) == "3.64 MB"
    assert isize(1024 * 1024 * 1024 * 252.5913) == "252.59 GB"
