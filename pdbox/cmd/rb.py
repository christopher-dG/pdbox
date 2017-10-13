from dropbox import Dropbox
from pdbox.util import normpath


def rb(token, args):
    dbx = Dropbox(token)
    path = normpath(args.dir)
