
"""
    pathlib revised
    ~~~~~~~~~~~~~~~

    :copyleft: 2016 by the pathlib_revised team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

from pathlib_revised import Path2


class DirEntryPath:
    """
    A Path2() instance from a os.DirEntry() instance that
    holds some more cached information.

    e.g.:

    * junction under windows:
        self.is_symlink = False
        self.different_path = True
        self.resolved_path = Path2() instance from junction destination

    * broken junction under windows:
        self.is_symlink = False
        self.different_path = True
        self.resolved_path = None
        self.resolve_error: contains the Error instance

    * symlink under linux:
        self.is_symlink = True
        self.different_path = True
        self.resolved_path = Path2() instance from symlink destination
        self.resolve_error = None

    * broken symlink under linux:
        self.is_symlink = True
        self.different_path = True
        self.resolved_path = None
        self.resolve_error: contains the Error instance
    """
    def __init__(self, dir_entry, onerror=print):
        """
        :param dir_entry: os.DirEntry() instance
        """
        self.dir_entry = dir_entry
        self.path = dir_entry.path

        self.is_symlink = dir_entry.is_symlink()
        self.is_file = dir_entry.is_file(follow_symlinks=False)
        self.is_dir = dir_entry.is_dir(follow_symlinks=False)
        self.stat = dir_entry.stat(follow_symlinks=False)

        self.path_instance = Path2(self.path)
        try:
            self.resolved_path = self.path_instance.resolve()
        except (PermissionError, FileNotFoundError) as err:
            onerror("Resolve %r error: %s" % (self.path, err))
            self.resolved_path = None
            self.resolve_error = err
        else:
            self.resolve_error = None

        if self.resolved_path is None:
            # e.g.: broken symlink under linux
            self.different_path = True
        else:
            # e.g.: a junction under windows
            # https://www.python-forum.de/viewtopic.php?f=1&t=37725&p=290429#p290428 (de)
            self.different_path = self.path_instance.path != self.resolved_path.path

    def pformat(self):
        return "\n".join((
            " *** %s :" % self,
            "path.......: %r" % self.path,
            "path instance..: %r" % self.path_instance,
            "resolved path..: %r" % self.resolved_path,
            "resolve error..: %r" % self.resolve_error,
            "different path.: %r" % self.different_path,
            "is symlink.....: %r" % self.is_symlink,
            "is file........: %r" % self.is_file,
            "is dir.........: %r" % self.is_dir,
            "stat.size......: %r" % self.stat.st_size,
        ))

    def __str__(self):
        return "<DirEntryPath %s>" % self.path_instance
