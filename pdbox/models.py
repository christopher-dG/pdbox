import dropbox
import math
import os.path
import pdbox

from pdbox.util import fail, isize, normpath


class DbxObj(object):
    """Either a file or folder in Dropbox."""
    def __init__(self, metadata):
        self.id = metadata.id
        self.name = metadata.name
        self.path = metadata.path_display

    def dbx_uri(self):
        return "dbx:/%s" % self.path


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

    def contents(self, args):
        """Get a list of this folder's contents (not recursive)."""
        try:
            if self.path == "/":
                result = pdbox.dbx.files_list_folder("")
            else:
                result = pdbox.dbx.files_list_folder(self.path)
        except dropbox.exceptions.ApiError as e:
            pdbox.warn(e, args)
            return []
        return [self] + [gen_entry(e, args) for e in result.entries if e]


def from_remote(path, args):
    """Generate a File or Folder from the given path, or None on failure."""
    path = normpath(path)
    if path == "/":  # get_metadata on the root folder is not supported.
        return Folder(None, root=True)

    try:
        metadata = pdbox.dbx.files_get_metadata(normpath(path))
    except dropbox.exceptions.ApiError as e:
        pdbox.debug(e, args)
        return None

    if isinstance(metadata, dropbox.files.FileMetadata):
        return File(metadata)
    elif isinstance(metadata, dropbox.files.FolderMetadata):
        return Folder(metadata)
    else:
        pdbox.debug(
            "Expected file/folder metadata, got %s" % type(metadata),
            args,
        )
        return None


def gen_entry(metadata, args):
    """Generate a File or Folder from a metadata object, or None on failure."""
    if isinstance(metadata, dropbox.files.FileMetadata):
        return File(metadata)
    elif isinstance(metadata, dropbox.files.FolderMetadata):
        return Folder(metadata)
    else:
        pdbox.debug(
            "Expected file/folder metadata, got %s " % type(metadata),
            args,
        )
        return None


class LocalObject(object):
    """
    A file or folder on disk.
    Paths are assumed to be real (not symlinks).
    """
    def __init__(self, path):
        self.path = os.path.normpath(path)


class LocalFile(LocalObject):
    """A file on disk."""
    def __init__(self, path, args):
        if not os.path.isfile(path):
            pdbox.debug(
                "Local file %s does not exist" % path,
                args,
            )
            return None
        self.size = os.path.getsize(path)
        super(LocalFile, self).__init__(path)

    def upload(self, dest, args):
        """
        Upload a file to Dropbox. This assumes that all appropriate checks
        have already been made. THIS WILL OVERWRITE EXISTING FILES!!!
        """
        pdbox.info(
            "Uploading %s to %s (%s)"
            % (self.path, dest, isize(self.size)),
            args
        )

        if not args.dryrun:
            mode = dropbox.files.WriteMode.overwrite  # !!!
            chunk = int(args.chunksize * 1024 * 1024)
            pdbox.debug("Chunk size is %f MB" % args.chunksize, args)

            if self.size < chunk:
                with open(self.path, "rb") as f:

                    try:
                        meta = pdbox.dbx.files_upload(f.read(), dest, mode)
                    except dropbox.exceptions.ApiError as e:
                        pdbox.debug(e, args)
                        fail("Upload failed", args)

            else:
                nchunks = math.ceil(self.size / chunk)
                with open(self.path, "rb") as f:
                    start = pdbox.dbx.files_upload_session_start(f.read(1))
                    cursor = dropbox.files.UploadSessionCursor(
                        start.session_id,
                        1,
                    )
                    i = 1
                    while self.size - f.tell() > chunk:
                        if not args.quiet and not args.only_show_errors:
                            pdbox.debug(
                                "Uploading chunk %d/%d" % (i, nchunks),
                                args,
                            )
                        i += 1

                        try:
                            pdbox.dbx.files_upload_session_append_v2(
                                f.read(chunk),
                                cursor,
                            )
                        except dropbox.exceptions.ApiError as e:
                            pdbox.debug(e, args)
                            fail("Upload failed", args)

                        cursor.offset += chunk

                    meta = pdbox.dbx.files_upload_session_finish(
                        f.read(),
                        cursor,
                        dropbox.files.CommitInfo(dest, mode),
                    )
            pdbox.debug("Metadata response: %s" % meta, args)

        pdbox.info("Uploaded %s to %s" % (self.path, dest), args)


class LocalFolder(LocalObject):
    """A folder on disk."""
    def __init__(self, path, args):
        if not os.path.isdir(path):
            pdbox.debug("Local folder %s does not exist" % path, args)
            return None
        super(LocalFolder, self).__init__(path)

    def contents(self, args):
        entries = []
        for entry in os.walk(self.path):
            entries.extend(
                LocalFolder(os.path.join(entry[0], f), args) for f in entry[1],
            )
            entries.extend(
                LocalFile(os.path.join(entry[0], f), args) for f in entry[2],
            )
        return entries


def from_local(path, args):
    """Get a local file or folder from a path."""
    if os.path.isfile(path):
        return LocalFile(path, args)
    elif os.path.isdir(path):
        return LocalFolder(path, args)
    else:
        pdbox.debug("%s does not exist on disk" % path, args)
        return None
