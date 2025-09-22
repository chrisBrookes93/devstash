import shutil
from pathlib import Path

import pytest

CACHE_DIR = Path("./.devstash_cache")


@pytest.fixture(autouse=True)
def clean_cache_dir():
    """Ensure .devstash_cache/ is removed before each test."""
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
    yield
    # Cleanup again after test just in case
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
