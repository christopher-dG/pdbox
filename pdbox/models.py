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
    """
    if meta:  # Don't look up the path, just use what's provided.
        if isinstance(meta, dropbox.files.FileMetadata):
            return RemoteFile(None, meta=meta)
        if isinstance(meta, dropbox.files.FolderMetadata):
            return RemoteFolder(None, meta=meta)

    path = normpath(path)
    if path == "/":  # get_metadata on the root is not supported.
        return RemoteFolder(path)
    try:
        meta = execute(args, pdbox.dbx.files_get_metadata, path)
    except DropboxError:
        raise ValueError("%s could not be found" % dbx_uri(path))
    if isinstance(meta, dropbox.files.DeletedMetadata):
        pdbox.debug("%s was recently deleted" % dbx_uri(path), args)
        raise ValueError("%s could not be found" % dbx_uri(path))
    if isinstance(meta, dropbox.files.FolderMetadata):
        return RemoteFolder(None, args, meta=meta)
    else:
        # This doesn't account for types other than FileMetadata but I don't
        # think that they can be returned here.
        return RemoteFile(None, args, meta=meta)


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
    except ValueError:  # Nothing exists at path, nothing to worry about.
        return
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
        - DropboxError
        """
        dest = normpath(dest)
        try:
            remote = get_remote(dest, args)
        except ValueError:  # Nothing exists at dest, nothing to worry about.
            remote = None
        else:  # Something exists here.
            if not overwrite:
                raise ValueError("Something exists at %s" % remote.uri)
            try:
                if self.hash == remote.hash:  # Nothing to update.
                    pdbox.info(
                        "%s and %s are identical" % (self.uri, remote.uri),
                        args,
                    )
                    return
            except AttributeError:  # RemoteFolder doesn't have a hash.
                pass

        if not args.dryrun:
            if overwrite and remote:
                # There's no way to copy and overwrite at the same time,
                # so delete the existing file first.
                remote.delete(args)

            result = execute(args, pdbox.dbx.files_copy_v2, self.path, dest)
            pdbox.debug("Metadata respones: %s" % result.metadata)

        pdbox.info("Copied %s to %s" % (self.uri, dbx_uri(dest)), args)
        if not args.dryrun:  # Return the newly created object.
            return get_remote(None, args, meta=result.metadata)

    def move(self, dest, args, overwrite=False):
        """
        Move a file or folder to dest inside Dropbox.
        Note that this is essentially "rename", and will not move the source
        into a folder. Instead, it will delete that folder if overwrite is set.
        Raises:
        - ValueError
        - DropboxError
        """
        dest = normpath(dest)
        try:
            remote = get_remote(dest, args)
        except ValueError:  # Nothing exists at dest, nothing to worry about.
            pass
        else:  # Something exists here.
            if not overwrite:
                raise ValueError("Something exists at %s" % remote.uri)
            # There's no way to copy and overwrite at the same time,
            # so delete the existing file first.
            # Note that this can delete folders too.
            remote.delete(args)

        if not args.dryrun:
            result = execute(args, pdbox.dbx.files_move_v2, self.path, dest)
            pdbox.debug("Metadata response: %s" % result.metadata)

        pdbox.info("Moved %s to %s" % (self.path, dbx_uri(dest)), args)
        if not args.dryrun:  # Return the newly created object.
            return get_remote(None, args, meta=result.metadata)


class RemoteFile(RemoteObject):
    """A file in Dropbox."""
    def __init__(self, path, args=None, meta=None):
        """Raises: ValueError"""
        if not meta:  # Look for a file at path.
            path = normpath(path)
            if path == "/":  # get_metadata on the root is not supported.
                raise ValueError("The root folder is not a file")
            try:
                meta = execute(args, pdbox.dbx.files_get_metadata, path)
            except DropboxError:
                raise ValueError("%s could not be found" % dbx_uri(path))
            if isinstance(meta, dropbox.files.FolderMetadata):
                raise ValueError("%s is a folder" % dbx_uri(meta.path_display))
            if isinstance(meta, dropbox.files.DeletedMetadata):
                pdbox.debug("%s was recently deleted" % dbx_uri(path), args)
                raise ValueError("%s could not be found" % dbx_uri(path))

        self.id = meta.id  # File ID, not sure how this can be used.
        self.size = meta.size  # Size in bytes.
        self.path = meta.path_display  # Path, including the name.
        self.name = meta.name  # File name with extension.
        self.modified = meta.server_modified  # Last modified time.
        self.rev = meta.rev  # Revision, not sure how this can be used.
        self.hash = meta.content_hash  # Hash for comparing the contents.
        self.uri = dbx_uri(self.path)  # Convenience field for display.

    def download(self, dest, args, overwrite=False):
        """
        Download this file to dest locally.
        Raises:
        - ValueError
        - DropboxError
        - Exception
        """
        dest = os.path.abspath(dest)
        try:
            local = get_local(dest, args)
        except ValueError:  # Nothing exists at dest, nothing to worry about.
            local = None
        else:  # Something exists here.
            if local.hash(args) == self.hash:  # Nothing to update.
                pdbox.info(
                    "%s and %s are identical" % (self.uri, local.path),
                    args,
                )
                return
            if not overwrite:
                raise ValueError("%s already exists" % local.path)

        # To avoid any weird overwriting behaviour in the case of errors, we'll
        # download to a different location first, then move to dest afterwards.
        tmp_dest = os.path.join(
            pdbox.TMP_DOWNLOAD_DIR,
            os.path.basename(dest),
        )
        while os.path.exists(tmp_dest):  # Make sure the temp name is unique.
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
            # Create the parent directories of dest.
            os.makedirs(os.path.dirname(dest))

        # os.rename overwrites files just fine, but not directories.
        if local and not args.dryrun and isinstance(local, LocalFolder):
            shutil.rmtree(local.path)
        # Move the file from the temp location to dest.
        os.rename(tmp_dest, dest)

        pdbox.info("Downloaded %s to %s" % (self.uri, dest), args)
        return LocalFile(dest)  # Return the newly created file.


class RemoteFolder(RemoteObject):
    """A folder in Dropbox."""
    def __init__(self, path, args=None, meta=None):
        """Raises: ValueError"""
        if not meta:  # Look for a folder at path.
            path = normpath(path)
            if path == "/":
                # get_metadata on the root folder is not supported.
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

    def create(path, args, overwrite=False):
        """
        Create a new folder in Dropbox.
        Raises:
        - ValueError
        - DropboxError
        """
        path = normpath(path)
        try:
            remote = get_remote(path, args)
        except ValueError:  # Nothing exists at path, nothing to worry about.
            pass
        else:
            if isinstance(remote, RemoteFolder):
                pdbox.info("%s already exists" % remote.uri, args)
                return remote
            elif not overwrite:
                raise ValueError("%s already exists" % remote.uri)

        if not args.dryrun:
            result = execute(args, pdbox.dbx.files_create_folder_v2, path)
            pdbox.debug("Metadata response: %s" % result.metadata, args)

        pdbox.info("Created new folder %s" % dbx_uri(path), args)

        if not args.dryrun:  # Return the newly created folder.
            return RemoteFolder(None, args, meta=result.metadata)

    def contents(self, args):
        """Get this folder's contents in Dropbox."""
        # list_folder on "/" isn't supported for some reason.
        path = "" if self.path == "/" else self.path
        result = execute(args, pdbox.dbx.files_list_folder, path)
        entries = [get_remote(None, args, meta=e) for e in result.entries]

        # TODO: Verify that this works.
        while result.has_more:
            # As long as there are more pages to look through,
            # add their contents to the list of entries.
            more = execute(
                args,
                pdbox.dbx.files_list_folder_continue,
                result.cursor,
            )
            entries.extend(get_remote(None, args, meta=e) for e in more)

        return entries

    def download(self, dest, args, overwrite=False):
        """
        Download this folder to dest locally.
        Raises:
        - ValueError
        - DropboxError
        """
        dest = os.path.abspath(dest)
        try:
            local = get_local(dest, args)
        except ValueError:  # Nothing exists at dest, nothing to worry about.
            local = None
        else:
            if not overwrite:
                raise ValueError("%s already exists" % local.path)

        # To avoid any weird overwriting behaviour in the case of errors, we'll
        # download to a different location first, then move to dest afterwards.
        tmp_dest = os.path.join(
            pdbox.TMP_DOWNLOAD_DIR,
            os.path.basename(dest),
        )
        while os.path.exists(tmp_dest):
            dest += "_"  # Make sure the temp name is unique.

        LocalFolder.create(tmp_dest, overwrite=overwrite)

        for entry in self.contents(args):
            try:
                entry.download(
                    os.path.join(tmp_dest, entry.name),
                    args,
                )
            except:
                pdbox.error("%s could not be downloaded" % self.uri, args)

        if not args.dryrun:
            # os.rename overwrites files just fine, but not directories.
            if local and isinstance(local, LocalFolder):
                shutil.rmtree(local.path)
            # Move the folder from the temp location to dest.
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
        pass  # TODO

    def sync_remote(self, other, args):
        """
        Synchronize this folder to other inside Dropbox.
        dest is a RemoteFolder.
        """
        pass  # TODO


class LocalFile(object):
    """A file on disk."""
    def __init__(self, path, args=None):
        path = os.path.abspath(path)
        if not os.path.exists(path):
            raise ValueError("%s could not be found" % path)
        if not os.path.isfile(path):
            raise ValueError("%s is a folder" % path)

        self.path = path  # Path the the file, including name.
        self.name = os.path.basename(self.path)  # File name with extension.
        self.islink = os.path.islink(self.path)  # If the file is a symlink.
        self.size = os.path.getsize(self.path)  # Size in bytes.

    def hash(self, args=None):
        """
        Get this file's hash according to Dropbox's algorithm.
        https://www.dropbox.com/developers/reference/content-hash
        """
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
        except ValueError:  # Nothing exists at dest, nothing to worry about.
            pass
        else:  # Something exists here.
            if isinstance(remote, RemoteFile):
                if self.hash(args) == remote.hash:  # Nothing to update.
                    pdbox.info(
                        "%s and %s are identical" % (self.path, remote.uri),
                        args,
                    )
                    return
            if not overwrite:
                raise ValueError("%s exists" % remote.uri)

        # Uploading can either happen all at once (with a 150 MB limit),
        # or in chunks. If the file is smaller than the selected chunk size,
        # then try to upload in one go.
        args.chunksize = min(args.chunksize, 149.0)
        pdbox.debug("Chunk size: %.2f MB" % args.chunksize, args)
        if args.dryrun:
            pdbox.info("Uploaded %s to %s" % (self.path, dbx_uri(dest)), args)
            return None

        # Set the write mode.
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
            # Initiate the upload with just the first byte.
            start = execute(args, pdbox.dbx.files_upload_session_start, f[0])
            cursor = dropbox.files.UploadSessionCursor(start.session_id, 1)

            # Now just add each chunk.
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

            # Upload the remaining to finish the transaction.
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

    def create(path, args, overwrite=False):
        """
        Create a new folder locally.
        Raises: ValueError
        """
        path = os.path.abspath(path)
        if os.path.isfile(path):
            if overwrite:
                args.dryrun or os.remove(path)
            else:
                raise ValueError("%s is a file" % path)
        if os.path.isdir(path):
            if overwrite:
                args.dryrun or shutil.rmtree(path)
            else:
                raise ValueError("%s already exists" % path)

        args.dryrun or os.makedirs(path)

        pdbox.info("Created new folder %s" % path, args)
        return None if args.dryrun else LocalFolder(path)

    def contents(self, args):
        """Get this folder's contents locally."""
        entries = []
        walk = next(os.walk(self.path))
        entries.extend(  # Folders.
            LocalFolder(os.path.join(walk[0], f), args) for f in walk[1],
        )
        entries.extend(  # Files.
            LocalFile(os.path.join(walk[0], f), args) for f in walk[2],
        )
        return entries

    def upload(self, dest, args, overwrite=False):
        """
        Upload this folder to dest in Dropbox.
        Raises:
        - ValueError
        - DropboxError
        TODO: Parallel batch upload.
        https://www.dropbox.com/developers/reference/data-ingress-guide
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
        pass  # TODO
