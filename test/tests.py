import pdbox


def test_normpath():
    normpath = pdbox.util.normpath
    assert normpath("dbx://") == "/"
