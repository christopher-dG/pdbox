import dropbox
import hashlib
import math
import os
import pdbox
import shutil

from pdbox.utils import DropboxError, dbx_uri, execute, normpath


def get_remote(path, args=None, meta=None):
    """
    Get a RemoteFile or RemoteFolder from path.
    Raises:
    - ValueError
    - TypeError
    """
    if meta:
        if isinstance(meta, dropbox.files.FileMetadata):
            return RemoteFile(None, meta=meta)
        if isinstance(meta, dropbox.files.FolderMetadata):
            return RemoteFolder(None, meta=meta)

    path = normpath(path)
    if path == "/":
        return RemoteFolder(path)
    try:
        meta = execute(args, pdbox.dbx.files_get_metadata, path)
    except DropboxError:
        raise ValueError("%s could not be found" % dbx_uri(path))
    if isinstance(meta, dropbox.files.DeletedMetadata):
        pdbox.debug("%s was recently deleted" % dbx_uri(path), args)
        raise ValueError("%s does not exist" % dbx_uri(path))
    if isinstance(meta, dropbox.files.FileMetadata):
        return RemoteFile(None, args, meta=meta)
    if isinstance(meta, dropbox.files.FolderMetadata):
        return RemoteFolder(None, args, meta=meta)
    pdbox.debug("Got unexpected metadata response: %s" % meta, args)
    raise TypeError("Unexpected response type from %s" % dbx_uri(path))


def get_local(path, args=None):
    """
    Get a LocalFile or LocalFolder from path.
    Raises: ValueError
    """
    path = os.path.abspath(path)
    if os.path.isfile(path):
        return LocalFile(path, args)
    if os.path.isdir(path):
        return LocalFolder(path, args)
    raise ValueError("%s does not exist" % path)


def remote_assert_empty(path, args):
    """
    Assert that nothing exists at path in Dropbox.
    Raises: ValueError
    """
    path = normpath(path)
    try:
        remote = get_remote(path, args)
    except TypeError as e:
        pdbox.debug(e, args)
        raise ValueError("Something exists at %s" % dbx_uri(path))
    except ValueError:  # Nothing exists, which is what we want.
        pass
    else:
        raise ValueError("Something exists at %s" % remote.uri)


def local_assert_empty(path, args):
    """
    Assert that nothing exists at path locally.
    Raises: ValueError
    """
    path = os.path.abspath(path)
    if os.path.exists(path):
        raise ValueError("Something exists at %s" % path)


class RemoteObject(object):
    """A file or folder inside Dropbox."""
    def delete(self, args):
        """
        Delete a file or folder inside Dropbox.
        Raises: DropboxError
        """
        if not args.dryrun:
            result = execute(args, pdbox.dbx.files_delete_v2, self.path)
            pdbox.debug("Metadata response: %s" % result.metadata, args)
        pdbox.info("Deleted %s" % self.uri, args)

    def copy(self, dest, args, overwrite=False):
        """
        Copy a file or folder to dest inside Dropbox.
        Raises:
        - ValueError
        - TypeError
        - DropboxError
        """
        dest = normpath(dest)
        try:
            remote = get_remote(dest, args)
        except ValueError:
            remote = None
        except TypeError:
            raise ValueError(
                "Something exists at %s that can't be overwritten" %
                dbx_uri(dest),
            )
        else:
            if not overwrite:
                raise ValueError("Something exists at %s" % remote.uri)
            if self.hash == remote.hash:
                pdbox.info(
                    "%s and %s are identical" % (self.uri, remote.uri),
                    args,
                )
                return

        if not args.dryrun:
            if overwrite and remote:
                remote.delete(args)
            result = execute(args, pdbox.dbx.files_copy_v2, self.path, dest)
            pdbox.debug("Metadata respones: %s" % result.metadata)
        pdbox.info("Copied %s to %s" % (self.uri, dbx_uri(dest)), args)
        if not args.dryrun:
            return get_remote(None, args, meta=result.metadata)

    def move(self, dest, args, overwrite=False):
        """
        Move a file or folder to dest inside Dropbox.
        Raises:
        - ValueError
        - TypeError
        - DropboxError
        """
        dest = normpath(dest)
        remote_assert_empty(dest, args)

        if not args.dryrun:
            result = execute(args, pdbox.dbx.files_move_v2, self.path, dest)
            pdbox.debug("Metadata response: %s" % result.metadata)
        pdbox.info("Moved %s to %s" % (self.path, dbx_uri(dest)), args)
        if not args.dryrun:
            return get_remote(None, args, meta=result.metadata)


class RemoteFile(RemoteObject):
    """A file in Dropbox."""
    def __init__(self, path, args=None, meta=None):
        """Raises: ValueError"""
        if not meta:
            path = normpath(path)
            if path == "/":
                raise ValueError("The root folder is not a file")
            try:
                meta = execute(args, pdbox.dbx.files_get_metadata, path)
            except DropboxError:
                raise ValueError("%s could not be found" % dbx_uri(path))
            if isinstance(meta, dropbox.files.FolderMetadata):
                raise ValueError("%s is a folder" % dbx_uri(meta.path_display))
            if isinstance(meta, dropbox.files.DeletedMetadata):
                pdbox.debug("%s was recently deleted" % dbx_uri(path), args)
                raise ValueError("%s does not exist" % dbx_uri(path))

        self.id = meta.id  # File ID, not sure how this can be used.
        self.size = meta.size  # Size in bytes.
        self.path = meta.path_display  # Path, including the name.
        self.name = meta.name  # File name with extension.
        self.modified = meta.server_modified  # Last modified time.
        self.rev = meta.rev  # Revision, not sure how this can be used.
        self.hash = meta.content_hash  # Hash for comparing the contents.
        self.uri = dbx_uri(self.path)  # Convenience field for display.

    def download(self, dest, args, overwrite=False, is_r=False):
        """
        Download this file to dest locally.
        Raises:
        - ValueError
        - DropboxError
        - Exception
        is_r is just here to avoid having to do a bunch of manual type checks.
        """
        dest = os.path.abspath(dest)
        try:
            local = get_local(dest, args)
        except ValueError:
            pass
        else:
            if local.hash(args) == self.hash:
                pdbox.info(
                    "%s and %s are identical" % (self.uri, local.path),
                    args,
                )
                return
            if not overwrite:
                raise ValueError("%s already exists" % local.path)

        tmp_dest = os.path.join(
            pdbox.TMP_DOWNLOAD_DIR,
            os.path.basename(dest),
        )
        while os.path.exists(tmp_dest):
            tmp_dest += "_"

        if args.dryrun:
            pdbox.info("Downloaded %s to %s" % (self.uri, dest), args)
            return None

        # TODO: Progress bars.
        meta = execute(
            args,
            pdbox.dbx.files_download_to_file,
            tmp_dest,
            self.path,
        )
        pdbox.debug("Metadata response: %s" % meta)

        if not os.path.isdir(os.path.dirname(dest)):
            os.makedirs(os.path.dirname(dest))

        try:
            os.rename(tmp_dest, dest)
        except:
            raise Exception(
                "%s was downloaded to %s, but couldn't be moved to %s" %
                (self.uri, tmp_dest, dest),
            )

        pdbox.info("Downloaded %s to %s" % (self.uri, dest), args)
        return LocalFile(dest)


class RemoteFolder(RemoteObject):
    """A folder in Dropbox."""
    def __init__(self, path, args=None, meta=None):
        """Raises: ValueError"""
        if not meta:
            path = normpath(path)
            if path == "/":
                self.id = -1
                self.path = "/"
                self.name = "/"
                self.uri = "dbx://"
                return
            try:
                meta = execute(args, pdbox.dbx.files_get_metadata, path)
            except DropboxError:
                raise ValueError("%s could not be found" % dbx_uri(path))
            if isinstance(meta, dropbox.files.FileMetadata):
                raise ValueError("%s is a file" % dbx_uri(meta.path_display))
            if isinstance(meta, dropbox.files.DeletedMetadata):
                pdbox.debug("%s was recently deleted" % dbx_uri(path), args)
                raise ValueError("%s does not exist" % dbx_uri(path))

        self.id = meta.id  # Folder ID, not sure how this can be used.
        self.path = meta.path_display  # Path to the folder, including name.
        self.name = meta.name  # Base name of the folder.
        self.uri = dbx_uri(self.path)  # Convenience field for display.

    def create(path, args):
        """
        Create a new folder in Dropbox.
        Raises:
        - ValueError
        - DropboxError
        """
        path = normpath(path)
        remote_assert_empty(path, args)
        if not args.dryrun:
            result = execute(args, pdbox.dbx.files_create_folder_v2, path)
            pdbox.debug("Metadata response: %s" % result.metadata, args)
        pdbox.info("Created new folder %s" % dbx_uri(path), args)
        if not args.dryrun:
            return RemoteFolder(None, args, meta=result.metadata)

    def contents(self, args):
        """Get this folder's contents in Dropbox."""
        def process_entries(l, entries):
            """Add entries to l."""
            for entry in entries:
                try:
                    l.append(get_remote(None, args, meta=entry))
                except (TypeError, ValueError) as e:
                    pdbox.debug(e, args)

        arg = "" if self.path == "/" else self.path
        result = execute(args, pdbox.dbx.files_list_folder, arg)
        entries = []
        process_entries(entries, result.entries)

        # TODO: Verify that this works.
        while result.has_more:
            process_entries(
                entries,
                execute(
                    args,
                    pdbox.dbx.files_list_folder_continue,
                    result.cursor,
                ),
            )

        return entries

    def download(self, dest, args, is_r=False):
        """
        Download this folder to dest locally.
        Raises:
        - ValueError
        - DropboxError
        If is_r is set, then this call is occuring as part of a parent
        folder download, so don't move any files before returning.
        """
        dest = os.path.abspath(dest)
        local_assert_empty(dest, args)

        tmp_dest = os.path.join(
            pdbox.TMP_DOWNLOAD_DIR,
            os.path.basename(dest),
        )
        while os.path.exists(tmp_dest):
            dest += "_"

        try:
            LocalFolder.create(tmp_dest)
        except ValueError as e:
            # This shouldn't happen but also isn't a problem.
            pdbox.debug(e, args)

        for entry in self.contents(args):
            try:
                entry.download(
                    os.path.join(tmp_dest, entry.name),
                    args,
                    is_r=True,
                )
            except:
                pdbox.error("%s could not be downloaded" % self.uri, args)

        if not is_r and not args.dryrun:
            shutil.move(tmp_dest, dest)
        pdbox.info("Downloaded %s to %s" % (self.uri, dest), args)

    def sync(self, other, args):
        """
        Synchronize this folder to other.
        If dest is a LocalFolder or string, it is synchronized locally.
        If dest is a RemoteFolder, it is synchronized to that remote folder.
        """
        if isinstance(other, str) or isinstance(other, LocalFolder):
            return self.sync_local(other, args)
        else:
            return self.sync_remote(other, args)

    def sync_local(self, other, args):
        """
        Synchronize this folder to other locally.
        dest is either a string or a LocalFoler.
        """
        pass

    def sync_remote(self, other, args):
        """
        Synchronize this folder to other inside Dropbox.
        dest is a RemoteFolder.
        """
        pass


class LocalFile(object):
    """A file on disk."""
    def __init__(self, path, args=None):
        path = os.path.abspath(path)
        if not os.path.exists(path):
            raise ValueError("%s does not exist" % path)
        if not os.path.isfile(path):
            raise ValueError("%s is a folder" % path)

        self.path = path  # Path the the file, including name.
        self.name = os.path.basename(self.path)  # File name with extension.
        self.islink = os.path.islink(self.path)  # If the file is a symlink.
        self.size = os.path.getsize(self.path)  # Size in bytes.

    def hash(self, args=None):
        """Get this file's hash according to Dropbox's algorithm."""
        block = 1024 * 1024 * 4  # 4 MB.
        hasher = hashlib.sha256()
        with open(self.path, "rb") as f:
            while True:
                chunk = f.read(block)
                if not chunk:
                    break
                hasher.update(hashlib.sha256(chunk).digest())
        digest = hasher.hexdigest()
        pdbox.debug("Hash for %s: %s" % (self.path, digest), args)
        return digest

    def upload(self, dest, args, overwrite=False):
        """
        Upload this file to dest in Dropbox.
        Raises:
        - ValueError
        - DropboxError
        """
        dest = normpath(dest)
        try:
            remote = get_remote(dest, args)
        except ValueError:
            pass
        except TypeError:
            raise ValueError("Something exists at %s" % dbx_uri(dest))
        else:
            if self.hash(args) == remote.hash:
                pdbox.info(
                    "%s and %s are identical" % (self.path, remote.uri),
                    args,
                )
                return
            if not overwrite:
                raise ValueError("%s exists" % remote.uri)

        pdbox.debug("Chunk size: %.2f MB" % args.chunksize, args)
        if args.dryrun:
            pdbox.info("Uploaded %s to %s" % (self.path, dbx_uri(dest)), args)
            return None

        if overwrite:
            mode = dropbox.files.WriteMode.overwrite
        else:
            mode = dropbox.files.WriteMode.add

        chunk = int(args.chunksize * 1024 * 1024)  # Convert B to MB.

        with open(self.path, "rb") as f:
            data = f.read()
        sz = len(data)

        # TODO: Progress bars.
        if sz < chunk:  # One-shot upload.
            meta = execute(args, pdbox.dbx.files_upload, data, dest, mode)
        else:  # Multipart upload.
            nchunks = math.ceil(sz / chunk)
            start = execute(args, pdbox.dbx.files_upload_session_start, f[0])
            cursor = dropbox.files.UploadSessionCursor(start.session_id, 1)

            while sz - cursor.offset > chunk:
                pdbox.debug(
                    "Uploading chunk %d/%d" % (cursor.offset % chunk, nchunks),
                    args,
                )
                execute(
                    args,
                    pdbox.dbx.files_upload_session_append_v2,
                    data[cursor.offset:cursor.offset + chunk],
                    cursor,
                )
                cursor.offset += chunk
            meta = execute(
                args,
                pdbox.dbx.files_upload_session_finish,
                data[cursor.offset:],
                dropbox.files.CommitInfo(dest, mode),
            )

        pdbox.info("Uploaded %s to %s" % (self.path, dbx_uri(dest)), args)
        return RemoteFile(None, args, meta=meta)

    def delete(self, args):
        """Delete this file locally."""
        args.dryrun or os.remove(self.path)
        pdbox.info("Deleted %s" % self.path)


class LocalFolder(object):
    """A folder on disk."""
    def __init__(self, path, args=None):
        """Raises: ValueError"""
        path = os.path.abspath(path)
        if not os.path.exists(path):
            raise ValueError("%s does not exist" % path)
        if not os.path.isdir(path):
            raise ValueError("%s is a file" % path)

        self.path = path  # Path to the folder, including name.
        self.name = os.path.basename(self.path)  # Base name of the folder..
        self.islink = os.path.islink(self.path)  # If the path is a symlink.
        self.parent = os.path.dirname(self.path)  # Parent folder.

    def create(path, args):
        """
        Create a new folder locally.
        Raises: ValueError
        """
        path = os.path.abspath(path)
        if os.path.isfile(path):
            raise ValueError("%s is a file" % path)
        if os.path.isdir(path):
            raise ValueError("%s already exists" % path)
        args.dryrun or os.makedirs(path)
        pdbox.info("Created new folder %s" % path, args)
        return None if args.dryrun else LocalFolder(path)

    def contents(self, args):
        """Get this folder's contents locally."""
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
        Upload this folder to dest in Dropbox.
        Raises:
        - ValueError
        - DropboxError
        """
        dest = normpath(dest)
        remote_assert_empty(dest, args)

        remote = RemoteFolder.create(dest, args)
        for entry in remote.contents(args):
            entry.upload("/".join([remote.path, entry.name]), args)
        return remote

    def delete(self, args):
        """Delete this folder locally."""
        args.dryrun or shutil.rmtree(self.path)
        pdbox.info("Deleted %s/" % self.path, args)

    def sync(self, other, args):
        """
        Synchronize this folder to other.
        other is either a RemoteFolder or a string (in which case it is
        converted to a RemoteFolder).
        """
        pass
