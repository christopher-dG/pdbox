import dropbox
import math
import os.path
import pdbox

from pdbox.util import execute, normpath


class DbxObj(object):
    """Either a file or folder in Dropbox."""
    def __init__(self, metadata):
        self.id = metadata.id
        self.name = metadata.name
        self.path = metadata.path_display

    def dbx_uri(self):
        return "dbx:/%s" % self.path

    def delete(self, args):
        """
        Delete ths file or folder.
        Raises: dropbox.exceptions.ApiError(dropbox.files.DeleteError)
        """
        if not args.dryrun:
            execute(args, pdbox.dbx.files_delete_v2, self.path)
        pdbox.info("Deleted %s" % self.dbx_uri())


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
        self.date = metadata.server_modified

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

    def contents(self, args=None):
        """
        Get a list of this folder's contents (not recursive).
        The first entry is itself.
        Raises: dropbox.exceptions.ApiError(dropbox.files.ListFolderError)
        """
        if self.path == "/":
            result = execute(args, pdbox.dbx.files_list_folder, "")
        else:
            result = execute(args, pdbox.dbx.files_list_folder, self.path)

        entries = [self]
        for entry in result.entries:
            try:
                entries.append(gen_entry(entry, args))
            except TypeError as e:
                pdbox.debug(e, args)
        return entries


def from_remote(path, args=None):
    """
    Generate a File or Folder from the given path.
    Raises:
    - dropbox.exceptions.ApiError(dropbox.files.GetMetadataError)
    - Exception
    """
    path = normpath(path)
    if path == "/":  # get_metadata on the root folder is not supported.
        return Folder(None, root=True)

    metadata = execute(args, pdbox.dbx.files_get_metadata, normpath(path))

    if isinstance(metadata, dropbox.files.FileMetadata):
        return File(metadata)
    elif isinstance(metadata, dropbox.files.FolderMetadata):
        return Folder(metadata)
    elif isinstance(metadata, dropbox.files.DeletedMetadata):
        raise Exception("File/folder does not exist, but was recently deleted")
    else:
        raise Exception("Unexpected return from get_metadata: %s" % metadata)


def gen_entry(metadata, args=None):
    """
    Generate a File or Folder from a metadata object.
    Raises: TypeError
    """
    if isinstance(metadata, dropbox.files.FileMetadata):
        return File(metadata)
    elif isinstance(metadata, dropbox.files.FolderMetadata):
        return Folder(metadata)
    else:
        raise TypeError(
            "Expected file/folder metadata, got %s " % type(metadata),
        )


class LocalObject(object):
    """
    A file or folder on disk.
    Paths are assumed to be real (not symlinks).
    """
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.name = os.path.basename(self.path)
        self.islink = os.path.islink(self.path)


class LocalFile(LocalObject):
    """A file on disk."""
    def __init__(self, path, args=None):
        """Raises: ValueError"""
        if not os.path.exists(path):
            raise ValueError("Local file %s does not exist" % path)
        if not os.path.isfile(path):
            raise ValueError("%s is a folder" % path)
        self.size = os.path.getsize(path)
        super(LocalFile, self).__init__(path)

    def upload(self, dest, args):
        """
        Upload a file to Dropbox. This assumes that all appropriate checks
        have already been made. THIS WILL OVERWRITE EXISTING DATA!!!
        Raises:
        - dropbox.exceptions.ApiError(dropbox.files.UploadError)
        - dropbox.exceptions.ApiError(dropbox.files.UploadSessionLookupError)
        - dropbox.exceptions.ApiError(dropbox.files.UploadSessionFinishError)
        """
        if not args.dryrun:
            mode = dropbox.files.WriteMode.overwrite  # !!!
            chunk = int(args.chunksize * 1024 * 1024)
            pdbox.debug("Chunk size is %.2f MB" % args.chunksize, args)

            if self.size < chunk:
                with open(self.path, "rb") as f:
                    meta = execute(
                        args,
                        pdbox.dbx.files_upload,
                        f.read(),
                        dest,
                        mode,
                    )
            else:
                meta = self.multipart_upload(dest, chunk, mode, args)
            pdbox.debug("Metadata response: %s" % meta, args)

        pdbox.info("Uploaded %s to dbx:/%s" % (self.path, dest), args)

    def multipart_upload(self, dest, chunk, mode, args):
        """
        Same as upload except it's done in multiple chunks.
        Raises:
        - dropbox.exceptions.ApiError(dropbox.files.UploadSessionLookupError)
        - dropbox.exceptions.ApiError(dropbox.files.UploadSessionFinishError)
        """
        nchunks = math.ceil(self.size / chunk)
        with open(self.path, "rb") as f:
            # Apparently session_start doesn't raise anything.
            start = pdbox.dbx.files_upload_session_start(f.read(1))
            cursor = dropbox.files.UploadSessionCursor(
                start.session_id,
                1,
            )
            i = 1

            while self.size - f.tell() > chunk:
                pdbox.debug("Chunk %d/%d" % (i, nchunks), args)
                i += 1
                execute(
                    args,
                    pdbox.dbx.files_upload_session_append_v2,
                    f.read(chunk),
                    cursor,
                )
                cursor.offset += chunk

            return execute(
                args,
                pdbox.dbx.files_upload_session_finish,
                f.read(),
                cursor,
                dropbox.files.CommitInfo(dest, mode),
            )


class LocalFolder(LocalObject):
    """A folder on disk."""
    def __init__(self, path, args=None):
        """Raises: ValueError"""
        if not os.path.exists(path):
            raise ValueError("Local folder %s does not exist" % path)
        if not os.path.isdir(path):
            raise ValueError("%s is a file" % path)
        super(LocalFolder, self).__init__(path)

    def contents(self, args=None):
        """
        Get a list of this folder's contents (not recursive).
        The first entry is the folder itself.
        """
        entries = [self]
        for entry in os.walk(self.path):
            entries.extend(
                LocalFolder(os.path.join(entry[0], f), args) for f in entry[1],
            )
            entries.extend(
                LocalFile(os.path.join(entry[0], f), args) for f in entry[2],
            )
        return entries

    def sync(self, dest, args=None):
        """
        Synchronize this folders's contents to Dropbox.
        THIS WILL OVERWRITE EXISTING DATA!!!
        Raises:
        - dropbox.exceptions.ApiError(dropbox.exceptions.CreateFolderError)
        """
        try:
            existing = from_remote(dest, args)
        except dropbox.exceptions.ApiError:
            existing = None

        if not isinstance(existing, Folder):
            if not args.dryrun:
                execute(args, pdbox.dbx.files_create_folder_v2, dest)
            pdbox.info("Created new folder dbx:/%s" % dest)
            remote_contents = []

        else:
            # Ignore the directory itself.
            try:
                remote_contents = existing.contents(args)[1:]
            except dropbox.exceptions.ApiError:
                remote_contents = []

        # Ignore the folder itself, we've already created it.
        contents = self.contents(args)[1:]

        if args.delete and remote_contents:
            # Delete anything in the remote folder not in the local one.
            names = [e.name for e in contents]
            for entry in remote_contents:
                if entry.name not in names:
                    try:
                        entry.delete(args)
                    except dropbox.exceptions.ApiError:
                        pdbox.warn(
                            "Couldn't delete %s" % entry.dbx_uri(),
                            args,
                        )

        for entry in contents:
            # Upload the contents.
            func = entry.upload if isinstance(entry, LocalFile) else entry.sync
            try:
                func("%s/%s" % (dest, entry.name), args)
            except dropbox.exceptions.ApiError:
                pdbox.warn("Couldn't upload dbx://%s" % entry.path, args)


def from_local(path, args=None):
    """
    Get a local file or folder from a path.
    Raises: ValueError
    """
    if os.path.isfile(path):
        return LocalFile(path, args)
    elif os.path.isdir(path):
        return LocalFolder(path, args)
    else:
        raise ValueError("%s does not exist locally" % path)
