import dropbox
import pdbox
from pdbox.util import normpath


class DbxObj(object):
    """Either a file or folder in Dropbox."""
    def __init__(self, metadata):
        self.id = metadata.id
        self.name = metadata.name
        self.path = metadata.path_display


class File(DbxObj):
    """A Dropbox file."""
    def __init__(self, metadata):
        super(File, self).__init__(metadata)
        components = self.path.split("/")
        if len(components) > 1:
            self.folder = "/".join(components[:-1])
        else:
            self.folder = "/"
        self.size = metadata.size
        self.date = metadata.client_modified

    def __repr__(self):
        return "File{%s}" % self.path


class Folder(DbxObj):
    """A Dropbox folder."""
    def __init__(self, metadata, root=False):
        if root:
            # When handling this folder, calls to dbx.files_list_folder
            # need to convert path to an empty string.
            self.id = -1
            self.name = "/"
            self.path = "/"
        else:
            super(Folder, self).__init__(metadata)

    def __repr__(self):
        return "Folder{%s}" % self.path

    def contents(self):
        """Get a list of this folder's contents (not recursive)."""
        try:
            if self.path == "/":
                result = pdbox.dbx.files_list_folder("")
            else:
                result = pdbox.dbx.files_list_folder(self.path)
        except dropbox.exceptions.ApiError as e:
            pdbox.logger.warn(e)
            return []
        return [self] + [gen_entry(e) for e in result.entries if e]


def from_path(path):
    """Generate a File or Folder from the given path, or None on failure."""
    path = normpath(path)
    if path == "/":  # get_metadata on the root folder is not supported.
        return Folder(None, root=True)

    try:
        metadata = pdbox.dbx.files_get_metadata(normpath(path))
    except dropbox.exceptions.ApiError as e:
        pdbox.logger.debug(e)
        return None
    if isinstance(metadata, dropbox.files.FileMetadata):
        return File(metadata)
    elif isinstance(metadata, dropbox.files.FolderMetadata):
        return Folder(metadata)
    else:
        pdbox.logger.warn(
            "Expected file or folder metadata, got %s" % type(metadata),
        )
        return None


def gen_entry(metadata):
    """Generate a File or Folder from a metadata object, or None on failure."""
    if isinstance(metadata, dropbox.files.FileMetadata):
        return File(metadata)
    elif isinstance(metadata, dropbox.files.FolderMetadata):
        return Folder(metadata)
    else:
        pdbox.logger.warn(
            "Expected file or folder metadata, got %s" % type(metadata),
        )
        return None
