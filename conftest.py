import os

import pytest

# pathlib_revised
from pathlib_revised import Path2


@pytest.fixture(scope="function")
def deep_path(tmp_path):
    os.chdir(tmp_path)

    deep_path = Path2(tmp_path, "A" * 255, "B" * 255)
    deep_path.makedirs()

    return deep_path
