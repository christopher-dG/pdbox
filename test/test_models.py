import os
import pdbox.models as models

from nose.tools import assert_raises
from . import FakeArgs, nofile, testfile, testdir, tempfile, tempdir


def test_local_file():
    LocalFile = models.LocalFile

    assert_raises(ValueError, LocalFile, nofile)

    assert_raises(ValueError, LocalFile, testdir)

    f = LocalFile(testfile)
    assert f.path == os.path.join(os.getcwd(), testfile)
    assert f.size == 0

    contents = "asdfjkl;"
    with open(tempfile, "w") as fd:
        fd.write(contents)
    f = LocalFile(tempfile)
    assert f.size == len(contents)

    assert f.upload("/", FakeArgs()) is None


def test_local_folder():
    LocalFolder = models.LocalFolder

    assert_raises(ValueError, LocalFolder, nofile)

    assert_raises(ValueError, LocalFolder, testfile)

    f = LocalFolder(testdir)
    assert f
    assert f.path == os.path.join(os.getcwd(), testdir)
    assert not f.contents()

    f = LocalFolder(tempdir)
    os.mknod(os.path.join(tempdir, "a"))
    os.mknod(os.path.join(tempdir, "b"))
    os.mkdir(os.path.join(tempdir, "c"))
    os.mknod(os.path.join(tempdir, "c", "d"))
    contents = f.contents()
    assert set([os.path.relpath(f.path) for f in contents]) == set([
        os.path.join(tempdir, "a"),
        os.path.join(tempdir, "b"),
        os.path.join(tempdir, "c"),
        os.path.join(tempdir, "c", "d"),
    ])
