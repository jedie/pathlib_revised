
"""
    pathlib revised
    ~~~~~~~~~~~~~~~

    :copyleft: 2016 by the pathlib_revised team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

import os
import unittest

# pathlib_revised
from pathlib_revised import Path2
from pathlib_revised.pathlib import PosixPath2, WindowsPath2

IS_NT = os.name == 'nt'


def test_makedirs_is_callable():
    assert callable(Path2(".").makedirs)


def test_exists(deep_path):
    assert deep_path.is_dir() is True
    assert deep_path.listdir() == []


def test_resolve(deep_path):
    resolved_path = deep_path.resolve()
    assert deep_path.path == resolved_path.path


def test_utime(deep_path):
    deep_path.utime()
    mtime = 111111111  # UTC: 1973-07-10 00:11:51
    atime = 222222222  # UTC: 1977-01-16 01:23:42
    deep_path.utime(times=(atime, mtime))
    stat = deep_path.stat()
    assert stat.st_atime == atime
    assert stat.st_mtime == mtime


def test_touch(deep_path):
    file_path = Path2(deep_path, "file.txt")
    assert file_path.is_file() is False
    file_path.touch()
    assert file_path.is_file() is True


def test_open_file(deep_path):
    file_path = Path2(deep_path, "file.txt")
    with file_path.open("w") as f:
        f.write("unittests!")

    assert file_path.is_file() is True
    with file_path.open("r") as f:
        assert f.read() == "unittests!"


def test_listdir(deep_path):
    Path2(deep_path, "a file.txt").touch()
    assert deep_path.listdir() == ["a file.txt"]


def test_chmod(deep_path):
    file_path = Path2(deep_path, "file.txt")
    file_path.touch()
    file_path.chmod(0o777)
    if not IS_NT:
        assert file_path.stat().st_mode == 33279
    file_path.chmod(0o666)
    if not IS_NT:
        assert file_path.stat().st_mode == 33206


def test_rename(deep_path):
    old_file = Path2(deep_path, "old_file.txt")
    old_file.touch()

    new_file = Path2(deep_path, "new_file.txt")
    assert new_file.is_file() is False

    old_file.rename(new_file)
    assert old_file.is_file() is False
    assert new_file.is_file() is True


def test_link(deep_path):
    old_file = Path2(deep_path, "old_file.txt")
    with old_file.open("w") as f:
        f.write("unittests!")

    new_file = Path2(deep_path, "new_file.txt")
    assert new_file.is_file() is False
    old_file.link(new_file)
    assert old_file.is_file() is True
    assert new_file.is_file() is True
    with new_file.open("r+") as f:
        assert f.read() == "unittests!"
        f.seek(0)
        f.write("new content!")
    with old_file.open("r") as f:
        assert f.read() == "new content!"


def test_unlink(deep_path):
    file_path = Path2(deep_path, "file.txt")
    file_path.touch()
    file_path.unlink()
    assert file_path.is_file() is False


def test_copyfile(deep_path):
    old_file = Path2(deep_path, "old_file.txt")
    with old_file.open("w") as f:
        f.write("unittests!")

    new_file = Path2(deep_path, "new_file.txt")
    assert new_file.is_file() is False
    old_file.copyfile(new_file)
    assert old_file.is_file() is True
    assert new_file.is_file() is True
    with new_file.open("r") as f:
        assert f.read() == "unittests!"


def test_rglob(deep_path):
    file_path = Path2(deep_path, "a test file.txt")
    file_path.touch()

    files = tuple(deep_path.rglob("*"))
    assert len(files) == 1

    f = files[0]
    assert f.is_file() is True
    assert f.extended_path == file_path.extended_path


@unittest.skipUnless(IS_NT, 'test requires a Windows-compatible system')
class TestWindowsPath2(unittest.TestCase):
    def test_instances(self):
        self.assertIsInstance(Path2(), WindowsPath2)
        self.assertIsInstance(Path2("."), WindowsPath2)
        self.assertIsInstance(Path2(".").resolve(), WindowsPath2)
        self.assertIsInstance(Path2.home(), WindowsPath2)

    def test_callable(self):
        self.assertTrue(callable(WindowsPath2(".").link))

    def test_extended_path_hack(self):
        abs_path = Path2("c:/foo/bar/")
        self.assertEqual(str(abs_path), "c:\\foo\\bar")
        self.assertEqual(abs_path.path, "c:\\foo\\bar")
        self.assertEqual(abs_path.extended_path, "\\\\?\\c:\\foo\\bar")

        rel_path = Path2("../foo/bar/")
        self.assertEqual(str(rel_path), "..\\foo\\bar")
        self.assertEqual(rel_path.extended_path, "..\\foo\\bar")

        with self.assertRaises(FileNotFoundError) as err:
            abs_path.resolve()
        self.assertEqual(err.exception.filename, "\\\\?\\c:\\foo\\bar")
        # self.assertEqual(err.exception.filename, "c:\\foo\\bar")

        path = Path2("~").expanduser()
        path = path.resolve()
        self.assertNotIn("\\\\?\\", str(path))

    def test_already_extended(self):
        existing_path = Path2("~").expanduser()
        extended_path = existing_path.extended_path
        self.assertTrue(extended_path.startswith("\\\\?\\"))

        # A already extended path should not added \\?\ two times:
        extended_path2 = Path2(extended_path).extended_path
        self.assertEqual(extended_path2, "\\\\?\\%s" % existing_path)
        self.assertEqual(extended_path2.count("\\\\?\\"), 1)

    def test_home(self):
        self.assertEqual(
            Path2("~/foo").expanduser().path,
            os.path.expanduser("~\\foo")
        )

        self.assertEqual(
            Path2("~/foo").expanduser().extended_path,
            "\\\\?\\%s" % os.path.expanduser("~\\foo")
        )

        existing_path = Path2("~").expanduser()
        ref_path = os.path.expanduser("~")
        self.assertEqual(str(existing_path), "%s" % ref_path)
        self.assertEqual(existing_path.extended_path, "\\\\?\\%s" % ref_path)
        self.assertTrue(existing_path.is_dir())
        self.assertTrue(existing_path.exists())

        self.assertEqual(str(existing_path), str(existing_path.resolve()))

    def test_relative_to(self):
        path1 = Path2("C:\\foo")
        path2 = Path2("C:\\foo\\bar")
        self.assertEqual(path2.relative_to(path1).path, "bar")

        path1 = Path2("\\\\?\\C:\\foo")
        path2 = Path2("\\\\?\\C:\\foo\\bar")
        self.assertEqual(path2.relative_to(path1).path, "bar")

        path1 = Path2("C:\\foo")
        path2 = Path2("\\\\?\\C:\\foo\\bar")
        self.assertEqual(path2.relative_to(path1).path, "bar")

        path1 = Path2("\\\\?\\C:\\foo")
        path2 = Path2("C:\\foo\\bar")
        self.assertEqual(path2.relative_to(path1).path, "bar")


@unittest.skipIf(IS_NT, 'test requires a POSIX-compatible system')
class TestPosixPath2(unittest.TestCase):

    def test_instances(self):
        self.assertIsInstance(Path2(), PosixPath2)
        self.assertIsInstance(Path2("."), PosixPath2)
        self.assertIsInstance(Path2.home(), PosixPath2)
        self.assertIsInstance(Path2.home().resolve(), PosixPath2)

    def test_callable(self):
        self.assertTrue(callable(PosixPath2(".").utime))

    def test_extended_path(self):
        # extended_path exists just for same API
        self.assertEqual(PosixPath2("foo/bar").path, "foo/bar")
        self.assertEqual(PosixPath2("foo/bar").extended_path, "foo/bar")

    def test_home(self):
        self.assertEqual(
            str(Path2("~").expanduser()),
            os.path.expanduser("~")
        )
        self.assertEqual(
            Path2("~/foo").expanduser().path,
            os.path.expanduser("~/foo")
        )
