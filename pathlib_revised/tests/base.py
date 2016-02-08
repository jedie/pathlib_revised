import shutil
import os
import tempfile
import unittest


class BaseTempTestCase(unittest.TestCase):
    """
    Test case with a temporary directory
    """
    def setUp(self):
        super(BaseTempTestCase, self).setUp()
        self.temp_root_path=tempfile.mkdtemp(prefix="%s_" % __name__)
        os.chdir(self.temp_root_path)

    def tearDown(self):
        super(BaseTempTestCase, self).tearDown()
        # FIXME: Under windows the root temp dir can't be deleted:
        # PermissionError: [WinError 32] The process cannot access the file because it is being used by another process
        def rmtree_error(function, path, excinfo):
            print("\nError remove temp: %r\n%s", path, excinfo[1])
        shutil.rmtree(self.temp_root_path, ignore_errors=True, onerror=rmtree_error)

