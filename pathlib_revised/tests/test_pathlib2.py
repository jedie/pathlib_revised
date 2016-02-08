
"""
    pathlib revised
    ~~~~~~~~~~~~~~~

    :copyleft: 2016 by the pathlib_revised team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

import logging
import os
import shutil
import unittest
import subprocess

from pathlib_revised import Path2
from pathlib_revised.pathlib import WindowsPath2, PosixPath2
from pathlib_revised.tests.base import BaseTempTestCase

IS_NT = os.name == 'nt'


class TestPath2(BaseTempTestCase):
    def test_callable(self):
        self.assertTrue(callable(Path2(".").makedirs))


class TestDeepPathBase(BaseTempTestCase):
    def setUp(self):
        super(TestDeepPathBase, self).setUp()
        self.deep_path = Path2(self.temp_root_path, "A"*255, "B"*255)
        self.deep_path.makedirs()

    def tearDown(self):
        def rmtree_error(function, path, excinfo):
            print("\nError remove temp: %r\n%s", path, excinfo[1])
        shutil.rmtree(self.deep_path.extended_path, ignore_errors=False, onerror=rmtree_error)
        shutil.rmtree(Path2(self.temp_root_path).extended_path, ignore_errors=False, onerror=rmtree_error)
        super(TestDeepPathBase, self).tearDown()


class TestDeepPath(TestDeepPathBase):
    def test_exists(self):
        self.assertTrue(self.deep_path.is_dir())
        self.assertEqual(self.deep_path.listdir(), [])

    def test_resolve(self):
        resolved_path = self.deep_path.resolve()
        self.assertEqual(self.deep_path.path, resolved_path.path)

    def test_utime(self):
        self.deep_path.utime()
        mtime = 111111111 # UTC: 1973-07-10 00:11:51
        atime = 222222222 # UTC: 1977-01-16 01:23:42
        self.deep_path.utime(times=(atime, mtime))
        stat = self.deep_path.stat()
        self.assertEqual(stat.st_atime, atime)
        self.assertEqual(stat.st_mtime, mtime)

    def test_touch(self):
        file_path = Path2(self.deep_path, "file.txt")
        self.assertFalse(file_path.is_file())
        file_path.touch()
        self.assertTrue(file_path.is_file())

    def test_open_file(self):
        file_path = Path2(self.deep_path, "file.txt")
        with file_path.open("w") as f:
            f.write("unittests!")

        self.assertTrue(file_path.is_file())
        with file_path.open("r") as f:
            self.assertEqual(f.read(), "unittests!")

    def test_listdir(self):
        Path2(self.deep_path, "a file.txt").touch()
        self.assertEqual(self.deep_path.listdir(), ["a file.txt"])

    def test_chmod(self):
        file_path = Path2(self.deep_path, "file.txt")
        file_path.touch()
        file_path.chmod(0o777)
        if not IS_NT:
            self.assertEqual(file_path.stat().st_mode, 33279)
        file_path.chmod(0o666)
        if not IS_NT:
            self.assertEqual(file_path.stat().st_mode, 33206)

    def test_rename(self):
        old_file = Path2(self.deep_path, "old_file.txt")
        old_file.touch()

        new_file = Path2(self.deep_path, "new_file.txt")
        self.assertFalse(new_file.is_file())
        old_file.rename(new_file)
        self.assertFalse(old_file.is_file())
        self.assertTrue(new_file.is_file())

    def test_unlink(self):
        file_path = Path2(self.deep_path, "file.txt")
        file_path.touch()
        file_path.unlink()
        self.assertFalse(file_path.is_file())


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

