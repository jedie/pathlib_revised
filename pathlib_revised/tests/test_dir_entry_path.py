
"""
    pathlib revised
    ~~~~~~~~~~~~~~~

    :copyleft: 2016 by the pathlib_revised team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

import os
import subprocess

import pytest

# pathlib_revised
from pathlib_revised import DirEntryPath, Path2

IS_NT = os.name == 'nt'


def test_normal_file(tmp_path):
    """
    Test DirEntryPath() on all platforms
    """
    f = Path2(tmp_path, "normal_file.txt")
    f.touch()
    assert f.is_file() is True

    p = Path2(tmp_path)
    dir_entries = tuple(p.scandir())
    print(dir_entries)
    assert len(dir_entries) == 1

    dir_entry = dir_entries[0]

    dir_entry_path = DirEntryPath(dir_entry)
    print(dir_entry_path.pformat())

    assert dir_entry_path.is_symlink is False
    assert dir_entry_path.different_path is False
    assert dir_entry_path.resolved_path == Path2(Path2(p, f).extended_path)
    assert dir_entry_path.resolve_error is None


@pytest.mark.skipif(not IS_NT, reason='test requires a Windows-compatible system')
class TestDirEntryPathWindows:
    # TODO: Make similar tests under Linux, too!

    def subprocess_run(self, *args, timeout=1, returncode=0, **kwargs):
        default_kwargs = {"shell": True}
        default_kwargs.update(kwargs)
        p = subprocess.Popen(args,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             **kwargs
                             )
        stderr_bytes = p.communicate(timeout=timeout)[0]

        # The following will not work:
        # encoding = sys.stdout.encoding or locale.getpreferredencoding()
        # In PyCharm:
        #   sys.stdout.encoding = None
        #   locale.getpreferredencoding() = "cp1252"
        # In SciTE:
        #   sys.stdout.encoding = "cp1252"
        #   locale.getpreferredencoding() = "cp1252"
        # under cmd.exe:
        #   sys.stdout.encoding = "cp850"
        txt = stderr_bytes.decode("cp850")
        self.assertEqual(p.returncode, returncode,
                         msg=(
                             "Command '%s' return code wrong!\n"
                             " *** command output: ***\n"
                             "%s"
                         ) % (" ".join(args), txt)
                         )
        return txt

    def test_subprocess_encoding(self):
        txt = self.subprocess_run("cmd.exe", "/c", 'echo "abcäöüß"')
        print(txt)
        self.assertIn("abcäöüß", txt)

    def mklink(self, *args, returncode=0):
        return self.subprocess_run(
            "cmd.exe", "/c", "mklink", *args,
            returncode=returncode
        )

    def test_mklink(self):
        txt = self.mklink("/?",
                          returncode=1  # Why in hell is the return code for the help page ==1 ?!?
                          )
        print(txt)
        self.assertIn("MKLINK [[/D] | [/H] | [/J]]", txt)

    def test_directory_junction(self, tmp_path):
        os.chdir(tmp_path)

        os.mkdir("dir1")
        dir1 = Path2("dir1").resolve()
        dir2 = Path2(self.temp_root_path, "dir2")
        print(dir1.path)
        print(dir2.path)

        # mklink /d /j <destination> <source>
        # Strange that first is destination and second is the source path !
        txt = self.mklink("/d", "/j", "dir2", "dir1")
        print(txt)
        self.assertIn("dir2 <<===>> dir1", txt)

        p = Path2(self.temp_root_path)
        dir_entries = list(p.scandir())
        dir_entries.sort(key=lambda x: x.name)
        print(dir_entries)
        self.assertEqual(repr(dir_entries), "[<DirEntry 'dir1'>, <DirEntry 'dir2'>]")

        dir_entry1, dir_entry2 = dir_entries
        self.assertEqual(dir_entry1.name, "dir1")
        self.assertEqual(dir_entry2.name, "dir2")

        dir_entry_path1 = DirEntryPath(dir_entry1)
        print(dir_entry_path1.pformat())
        self.assertEqual(dir_entry_path1.is_symlink, False)
        self.assertEqual(dir_entry_path1.different_path, False)
        self.assertEqual(
            dir_entry_path1.resolved_path,
            Path2(Path2(self.temp_root_path, "dir1").extended_path)
        )
        self.assertEqual(dir_entry_path1.resolve_error, None)

        dir_entry_path2 = DirEntryPath(dir_entry2)
        print(dir_entry_path2.pformat())
        self.assertEqual(dir_entry_path2.is_symlink, False)
        self.assertEqual(dir_entry_path2.different_path, True)  # <<--- because of junction
        self.assertEqual(  # pointed to dir1 !
            dir_entry_path2.resolved_path,
            Path2(Path2(self.temp_root_path, "dir1").extended_path)
        )
        self.assertEqual(dir_entry_path2.resolve_error, None)

        # remove junction source and try again
        # dir1.unlink() # Will not work: PermissionError: [WinError 5] Zugriff verweigert
        dir1.rename("new_name")  # Will also break the junction ;)

        # check again:
        dir_entry_path2 = DirEntryPath(
            dir_entry2,
            onerror=print  # will be called, because resolve can't be done.
        )
        print(dir_entry_path2.pformat())
        self.assertEqual(dir_entry_path2.is_symlink, False)
        self.assertEqual(dir_entry_path2.different_path, True)  # <<--- because of junction

        # can't be resole, because source was renamed:
        self.assertEqual(dir_entry_path2.resolved_path, None)
        self.assertIsInstance(dir_entry_path2.resolve_error, FileNotFoundError)


@pytest.mark.skipif(not IS_NT, reason='test requires a POSIX-compatible system')
class TestDirEntryPathPosix:
    def test_symlink(self, tmp_path):
        os.chdir(tmp_path)

        src_file = Path2("source_file.txt")
        src_file.touch()

        dst_file = Path2("destination.txt")
        dst_file.symlink_to(src_file)

        scan_result = list(Path2(".").scandir())
        scan_result.sort(key=lambda x: x.path)
        self.assertEqual([f.path for f in scan_result], ['./destination.txt', './source_file.txt'])

        for dir_entry in scan_result:
            dir_entry_path = DirEntryPath(dir_entry)
            info = dir_entry_path.pformat()
            # print(info)
            if dir_entry_path.path == "./source_file.txt":
                self.assertFalse(dir_entry_path.is_symlink)
                self.assertTrue(dir_entry_path.is_file)
            elif dir_entry_path.path == "./destination.txt":
                self.assertTrue(dir_entry_path.is_symlink)
                self.assertFalse(dir_entry_path.is_file)
            else:
                self.fail()

            self.assertEqual(
                dir_entry_path.resolved_path, Path2(
                    self.temp_root_path, "source_file.txt"))

        # Create a broken symlink, by deleting the source file:
        src_file.unlink()

        scan_result = list(Path2(".").scandir())
        self.assertEqual([f.path for f in scan_result], ['./destination.txt'])

        dir_entry_path = DirEntryPath(scan_result[0])
        info = dir_entry_path.pformat()
        print(info)
        self.assertEqual(dir_entry_path.path, "./destination.txt")
        self.assertEqual(dir_entry_path.resolved_path, None)  # <- broken, so can't be resolve
        self.assertIsInstance(
            dir_entry_path.resolve_error,
            FileNotFoundError)  # <- the error instance
        self.assertTrue(dir_entry_path.is_symlink)
        self.assertFalse(dir_entry_path.is_file)
