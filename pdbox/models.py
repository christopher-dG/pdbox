import dropbox
import math
import os.path
import pdbox
import shutil

from pdbox.util import execute, isize, normpath


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
        uri = self.dbx_uri()
        if isinstance(self, File):
            uri += "/"
        pdbox.info("Deleted %s" % uri, args)

    def copy(self, dest, args, force=False):
        """
        Copy this file/folder somewhere else inside Dropbox.
        It is assumed that there is nothing at dest, but if force is set,
        attempt to delete anyways.
        Raises: dropbox.exceptions.ApiError(dropbox.files.RelocationError)
        """
        if not args.dryrun:
            if force:
                try:
                    execute(args, pdbox.dbx.files_delete_v2, dest)
                except dropbox.exceptions.ApiError:
                    pass

            meta = execute(args, pdbox.dbx.files_copy, self.path, dest)
            pdbox.debug("Metadata response: %s" % meta, args)
            dest = meta.path_display

        pdbox.info("Copied %s to dbx:/%s" % (self.dbx_uri(), dest), args)

    def move(self, dest, args, force=False):
        """
        Move this file/folder somewhere else inside Dropbox.
        It is assumed that there is nothing at dest, but if force is set,
        attempt to delete anyways.
        Raises: dropbox.exceptions.ApiError(dropbox.files.RelocationError)
        """
        if not args.dryrun:
            if force:
                try:
                    execute(args, pdbox.dbx.files_delete_v2, dest)
                except dropbox.exceptions.ApiError:
                    pass

            meta = execute(
                args,
                pdbox.dbx.files_move_v2,
                self.path,
                dest,
            ).metadata
            pdbox.debug("Metadata response: %s" % meta, args)

        pdbox.info("Moved %s to dbx:/%s" % (self.dbx_uri(), dest), args)


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
        self.rev = metadata.rev

    def __repr__(self):
        return "File{%s}" % self.path

    def download(self, dest, args):
        """
        Download this file to dest.
        THIS WILL OVERWRITE EXISTING DATA!!!
        Raises:
        - dropbox.exceptions.ApiError(dropbox.files.DownloadError)
        - FileNotFoundError
        """
        tmp_dest = os.path.join(pdbox.TMP_DOWNLOAD_DIR, os.path.basename(dest))
        while os.path.exists(tmp_dest):
            tmp_dest += "_"
        meta = execute(
            args,
            pdbox.dbx.files_download_to_file,
            tmp_dest,
            self.path,
        )
        pdbox.debug("Metadata response: %s" % meta, args)

        if not args.dryrun:
            if os.path.isfile(dest):
                os.remove(dest)
            elif os.path.isdir(dest):
                shutil.rmtree(dest)
            else:
                dirname = os.path.dirname(dest)
                if dirname and not os.path.exists(dirname):
                    os.makedirs(dirname)

            if os.path.isfile(tmp_dest):
                os.rename(tmp_dest, dest)
            else:  # File disappeared somehow.
                raise FileNotFoundError(
                    "%s was downloaded to %s, but it can't be found there" %
                    (self.dbx_uri(), tmp_dest),
                )

        pdbox.info(
            "Downloaded %s to %s (%s)" %
            (self.dbx_uri(), dest, isize(self.size)),
            args,
        )


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

    def create(path, args=None):
        """
        Create a new folder inside Dropbox.
        Raises: dropbox.exceptions.ApiError(dropbox.files.CreateFolderError)
        Returns: The new Folder.
        """
        meta = execute(args, pdbox.dbx.files_create_folder_v2, path).metadata
        pdbox.debug("Metadata response: %s" % meta, args)
        pdbox.info("Created new folder dbx:/%s" % meta.path_display, args)
        return Folder(meta)

    def download(self, dest, args, tmp_dest=None):
        """
        Download this folder to dest.
        THIS WILL OVERWRITE EXISTING DATA!!!
        Raises:
        - dropbox.exceptions.ApiError(dropbox.files.DownloadError)
        - FileNotFoundErro
        """
        if not tmp_dest:
            tmp_dest = os.path.join(
                pdbox.TMP_DOWNLOAD_DIR,
                os.path.basename(dest),
            )
        else:
            tmp_dest = os.path.join(tmp_dest, os.path.basename(dest))
        while os.path.exists(tmp_dest):
            tmp_dest += "_"

        if not args.dryrun:
            os.mkdir(tmp_dest)  # We already know the parent exists.

        for entry in self.contents(args):
            if isinstance(entry, File):
                try:
                    entry.download(os.path.join(dest, entry.name), args)
                except dropbox.exceptions.ApiError:
                    pdbox.error("Couldn't download %s" % entry.dbx_uri(), args)
            else:
                entry.download(
                    os.path.join(dest, entry.name),
                    args,
                    tmp_dest=os.path.join(tmp_dest, entry.name),
                )

        pdbox.info("Downloaded %s to %s" % (self.dbx_uri(), dest), args)

        if not tmp_dest and not args.dryrun:
            # The call on the root folder being downloaded.
            if os.path.isfile(dest):
                os.remove(dest)
            elif os.path.isdir(dest):
                shutil.rmtree(dest)
            shutil.move(tmp_dest, dest)

    def contents(self, args=None):
        """
        Get a list of this folder's contents (not recursive).
        Does not contain itself.
        Raises: dropbox.exceptions.ApiError(dropbox.files.ListFolderError)
        """
        if self.path == "/":
            result = execute(args, pdbox.dbx.files_list_folder, "")
        else:
            result = execute(args, pdbox.dbx.files_list_folder, self.path)

        entries = []
        for entry in result.entries:
            try:
                entries.append(gen_entry(entry, args))
            except TypeError as e:
                pdbox.debug(e, args)
        return entries

    def sync(self, dest, args):
        """
        Synchronize this folder's contents to another Dropbox folder.
        dest can be a string or a DbxObj.
        THIS WILL OVERWRITE EXISTING DATA!!!
        Note that the caller is responsible for all error handling here.
        Raises:
        - dropbox.exceptions.ApiError(dropbox.files.ListFolderError)
        TODO: Make this way faster with some kind of registry. Right now
        it's basically just a bulk upload.
        """
        if isinstance(dest, str):
            # Convert to a DbxObject before proceeding.
            try:
                dest = from_remote(dest, args)
            except Exception as e:
                if not isinstance(e, dropbox.exceptions.ApiError):
                    pdbox.debug(e, args)
                # Since it would appear the the destination does not exist,
                # We can just copy this folder to that path.
                self.copy(dest, args)
                return

        if isinstance(dest, File):
            # All we need to do is clear the way, and then copy the contents.
            dest.delete(args)
            self.copy(dest.path, args)
            return

        # Here's the ugly part.

        src_contents = self.contents(args)
        dest_contents = dest.contents(args)

        if args.delete and dest_contents:
            # Delete anything in the destination folder not in this one.
            names = [e.name for e in src_contents]
            for entry in dest_contents:
                if entry.name not in names:
                    try:
                        entry.delete(args)
                    except dropbox.exceptions.ApiError:
                        pdbox.warn(
                            "Couldn't delete %s" % entry.dbx_uri(),
                            args,
                        )

        # Copy all files over into the destination folder.
        for entry in filter(lambda e: isinstance(e, File), src_contents):
            joined = "/".join([dest.path, entry.name])
            try:
                # We want to force overwriting (without a prompt).
                entry.copy(joined, args, force=True)
            except dropbox.exceptions.ApiError:
                pdbox.warn(
                    "%s could not be copied to dbx:/%s" %
                    (entry.dbx_uri(), joined),
                    args,
                )

        # Synchronize all the inner folders.
        for entry in filter(lambda e: isinstance(e, Folder), src_contents):
            joined = "/".join([dest.path, entry.name])
            try:
                entry.sync(joined, args)
            except dropbox.exceptions.ApiError:
                pdbox.error(
                    "Subfolder %s could not be synchronized" % entry.dbx_uri(),
                    args,
                )


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

    def delete(self, args):
        if not args.dryrun:
            os.remove(self.path)
        pdbox.debug("Deleted %s" % self.path)

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

        pdbox.info(
            "Uploaded %s to dbx:/%s" % (os.path.relpath(self.path), dest),
            args,
        )

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

    def delete(self, args):
        if not args.dryrun:
            shutil.rmtree(self.path)
        pdbox.debug("Deleted %s" % self.path)

    def contents(self, args=None):
        """
        Get a list of this folder's contents (not recursive).
        Does not contain itself.
        """
        entries = []
        for entry in os.walk(self.path):
            entries.extend(
                LocalFolder(os.path.join(entry[0], f), args) for f in entry[1],
            )
            entries.extend(
                LocalFile(os.path.join(entry[0], f), args) for f in entry[2],
            )
        return entries

    def upload(self, dest, args):
        """
        Upload this folder to Dropbox,
        without making any attempt to synchronize anything.
        THIS WILL OVERWRITE EXISTING DATA!!!
        Raises:
        - dropbox.exceptions.ApiError(dropbox.files.UploadError)
        - dropbox.exceptions.ApiError(dropbox.files.UploadSessionLookupError)
        - dropbox.exceptions.ApiError(dropbox.files.UploadSessionFinishError)
        """
        try:
            remote = from_remote(dest, args)
        except Exception as e:
            if not isinstance(e, dropbox.exceptions.ApiError):
                pdbox.debug(e, args)
        else:
            remote.delete(args)

        Folder.create(dest)
        for entry in self.contents(args):
            entry.upload("/".join([dest, entry.name]), args)

    def sync(self, dest, args):
        """
        Synchronize this folders's contents to Dropbox.
        THIS WILL OVERWRITE EXISTING DATA!!!
        Raises:
        - dropbox.exceptions.ApiError(dropbox.exceptions.CreateFolderError)
        TODO: Similar to the remote sync, this can be optimized a ton.
        """
        try:
            remote = from_remote(dest, args)
        except dropbox.exceptions.ApiError:
            remote_contents = []
        else:
            if not isinstance(remote, Folder):
                if not args.dryrun:
                    Folder.create(dest, args)
                remote_contents = []
            else:
                try:
                    remote_contents = remote.contents(args)
                except dropbox.exceptions.ApiError:
                    remote_contents = []

        contents = self.contents(args)

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
                func("/".join([dest, entry.name]), args)
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
