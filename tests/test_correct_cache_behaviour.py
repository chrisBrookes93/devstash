from devstash import devstash_cache_call
from tests.conftest import CACHE_DIR


def dummy_func(x, y=1):
    return x + y


def test_devstash_cache_call_with_args():
    # First call with (1, 2)
    result1 = devstash_cache_call(dummy_func, 1, 2)
    assert result1 == 3
    files = list(CACHE_DIR.glob("*.pkl"))
    assert len(files) == 1
    cache_file = files[0]

    # Second call with same args - should reuse cache
    result2 = devstash_cache_call(dummy_func, 1, 2)
    assert result2 == 3
    assert cache_file.exists()

    # Different args - new file
    result3 = devstash_cache_call(dummy_func, 2, 3)
    assert result3 == 5
    files = list(CACHE_DIR.glob("*.pkl"))
    assert len(files) == 2


def test_devstash_cache_call_with_kwargs():
    # Call with kwargs
    result1 = devstash_cache_call(dummy_func, x=2, y=5)
    assert result1 == 7
    files = list(CACHE_DIR.glob("*.pkl"))
    assert len(files) == 1
    cache_file = files[0]

    # Repeat same kwargs - should hit cache
    result2 = devstash_cache_call(dummy_func, x=2, y=5)
    assert result2 == 7
    assert cache_file.exists()

    # Different kwargs - new file
    result3 = devstash_cache_call(dummy_func, x=3, y=5)
    assert result3 == 8
    files = list(CACHE_DIR.glob("*.pkl"))
    assert len(files) == 2
