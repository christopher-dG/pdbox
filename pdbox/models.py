class DbxObj(object):
    """Either a file or folder in Dropbox."""
    def __init__(self, metadata):
        self.id = metadata.id
        self.name = metadata.name
        self.path = metadata.path_display


class File(DbxObj):
    """A Dropbox file."""
    def __init__(self, metadata):
        super(File).__init__(metadata)
        self.size = metadata.size


class Folder(DbxObj):
    """A Dropbox folder."""
    def __init__(self, metadata):
        super(Folder).__init__(metadata)
