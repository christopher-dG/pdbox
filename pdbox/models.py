import dropbox
import math
import os.path
import pdbox

from pdbox.util import fail, normpath


class DbxObj(object):
    """Either a file or folder in Dropbox."""
    def __init__(self, metadata):
        self.id = metadata.id
        self.name = metadata.name
        self.path = metadata.path_display

    def dbx_uri(self):
        return "dbx:/%s" % self.path

    def delete(self, args):
        if not args.dryrun:
            try:
                pdbox.dbx.files_delete_v2(self.path)
            except dropbox.exceptions.ApiError as e:
                pdbox.debug(e)
                pdbox.error("Deleting %s failed" % self.dbx_uri())
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

    def contents(self, args=None):
        """
        Get a list of this folder's contents (not recursive).
        The first entry is itself.
        """
        try:
            if self.path == "/":
                result = pdbox.dbx.files_list_folder("")
            else:
                result = pdbox.dbx.files_list_folder(self.path)
        except dropbox.exceptions.ApiError as e:
            pdbox.warn(e, args)
            return []
        return [self] + [gen_entry(e, args) for e in result.entries if e]


def from_remote(path, args=None):
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


def gen_entry(metadata, args=None):
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
        self.path = os.path.abspath(path)
        self.name = os.path.basename(self.path)
        self.islink = os.path.islink(self.path)


class LocalFile(LocalObject):
    """A file on disk."""
    def __init__(self, path, args=None):
        if not os.path.isfile(path):
            pdbox.debug(
                "Local file %s does not exist" % path,
                args,
            )
            raise ValueError("Local file %s does not exist" % path)
        self.size = os.path.getsize(path)
        super(LocalFile, self).__init__(path)

    def upload(self, dest, args):
        """
        Upload a file to Dropbox. This assumes that all appropriate checks
        have already been made. THIS WILL OVERWRITE EXISTING DATA!!!
        """
        if not args.dryrun:
            mode = dropbox.files.WriteMode.overwrite  # !!!
            chunk = int(args.chunksize * 1024 * 1024)
            pdbox.debug("Chunk size is %.2f MB" % args.chunksize, args)

            if self.size < chunk:
                with open(self.path, "rb") as f:

                    try:
                        meta = pdbox.dbx.files_upload(f.read(), dest, mode)
                    except dropbox.exceptions.ApiError as e:
                        pdbox.debug(e, args)
                        # Don't use fail here, we will still want to try
                        # uploading more files in a folder.
                        pdbox.error("Uploading dbx:/%s failed", dest, args)
                        return

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

        pdbox.info("Uploaded %s to dbx:/%s" % (self.path, dest), args)


class LocalFolder(LocalObject):
    """A folder on disk."""
    def __init__(self, path, args=None):
        if not os.path.isdir(path):
            pdbox.debug("Local folder %s does not exist" % path, args)
            raise ValueError("Local folder %s does not exist" % path)
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
        """
        existing = from_remote(dest, args)
        if not isinstance(existing, Folder):
            if not args.dryrun:
                try:
                    pdbox.dbx.files_create_folder_v2(dest)
                except dropbox.exceptions.ApiError as e:
                    pdbox.debug(e)
                    pdbox.error("Creating new folder dbx:/%s failed" % dest)
                    return
            pdbox.info("Created new folder dbx:/%s" % dest)

            remote_contents = []
        else:
            # Ignore the directory itself.
            remote_contents = existing.contents(args)[1:]

        # Ignore the folder itself, we've already created it.
        contents = self.contents(args)[1:]

        if args.delete and remote_contents:
            # Delete anything in the remote folder not in the local one.
            names = [e.name for e in contents]
            for entry in remote_contents:
                if entry.name not in names:
                    entry.delete(args)

        for entry in contents:
            # Upload the contents.
            func = entry.upload if isinstance(entry, LocalFile) else entry.sync
            func("%s/%s" % (dest, entry.name), args)


def from_local(path, args=None):
    """Get a local file or folder from a path."""
    if os.path.isfile(path):
        return LocalFile(path, args)
    elif os.path.isdir(path):
        return LocalFolder(path, args)
    else:
        pdbox.debug("%s does not exist on disk" % path, args)
        return None
