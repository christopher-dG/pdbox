class RemoteFile:
    """A file in Dropbox."""
    def __init__(self, path, args=None):
        pass

    def download(self, dest, args):
        """Download this file to dest locally."""
        pass

    def delete(self, args):
        """Delete this file inside Dropbox."""
        pass

    def copy(self, dest, args):
        """Copy this file to dest inside Dropbox."""
        pass

    def move(self, dest, args):
        """Move this file to dest inside Dropbox."""
        pass


class RemoteFolder:
    """A folder in Dropbox."""
    def __init__(self, path, args=None):
        pass

    def create(path, args):
        """Create a new folder in Dropbox."""
        pass

    def contents(self, args):
        """Get this folder's contents in Dropbox."""
        pass

    def download(self, dest, args):
        """Download this folder to dest locally."""
        pass

    def delete(self, args):
        """Delete this folder in Dropbox."""
        pass

    def copy(self, dest, args):
        """Copy this folder to dest in Dropbox."""
        pass

    def move(self, dest, args):
        """Move this folder to dest in Dropbox."""
        pass

    def sync(self, other, args):
        """
        Synchronize this folder to other.
        If dest is a LocalFolder or string, it is synchronized locally.
        If dest is a RemoteFolder, it is synchronized to that remote folder.
        """
        if isinstance(other, str):
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


class LocalFile:
    """A file on disk."""
    def __init__(self, path, args=None):
        pass

    def hash(self, args=None):
        """Get this file's hash according to Dropbox's algorithm."""
        pass

    def upload(self, dest, args):
        """Upload this file to dest in Dropbox."""
        pass

    def delete(self, args):
        """Delete this file locally."""
        pass


class LocalFolder:
    """A folder on disk."""
    def __init__(self, path, args=None):
        pass

    def create(path, args):
        """Create a new folder locally."""
        pass

    def contents(self, args):
        """Get this folder's contents locally."""
        pass

    def upload(self, dest, args):
        """Upload this folder to dest in Dropbox."""
        pass

    def delete(self, args):
        """Delete this folder locally."""
        pass

    def sync(self, other, args):
        """
        Synchronize this folder to other.
        other is either a RemoteFolder or a string (in which case it is
        converted to a RemoteFolder).
        """
        pass
