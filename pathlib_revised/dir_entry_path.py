
"""
    pathlib revised
    ~~~~~~~~~~~~~~~

    :copyleft: 2016 by the pathlib_revised team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

# pathlib_revised
from pathlib_revised.pathlib import Path2


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

    def __init__(self, path, onerror=print):
        self.path_instance = Path2(path)
        self.path = str(self.path_instance)

        self.is_symlink = self.path_instance.is_symlink()
        self.is_file = self.path_instance.is_file()
        self.is_dir = self.path_instance.is_dir()
        self.stat = self.path_instance.stat()

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
            "path...........: %r" % self.path,
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
