import ast
import pickle
import subprocess
import time
from pathlib import Path

from devstash import devstash_cache_call
from devstash._ast_rewrite import (
    DEVSTASH_INLINE_RE,
    DEVSTASH_STANDALONE_RE,
    DEVSTASH_TTL_RE,
    CacheNodeTransformer,
    extract_ttl,
    is_devstash_marker,
)

CACHE_DIR = Path("./.devstash_cache")


def run_script(tmp_path, script):
    """Helper: run a script with `python` and return stdout."""
    script_file = tmp_path / "script.py"
    script_file.write_text(script)
    result = subprocess.run(["python", str(script_file)], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def test_function_caching(tmp_path):
    script = """
import devstash

devstash.activate()

def slow_function(x):
    print("running slow_function")
    return x * 2

val = slow_function(5)  # @devstash
print(val)
"""
    out1 = run_script(tmp_path, script)
    out2 = run_script(tmp_path, script)

    # First run prints slow_function + result, second run only result
    assert "running slow_function" in out1
    assert "running slow_function" not in out2
    assert out2.endswith("10")


def test_ttl_expiry(tmp_path):
    script = """
import devstash
import time

devstash.activate()

def now():
    print("executing now()")
    return int(time.time())

val = now()  # @devstash ttl=1s
print(val)
"""
    out1 = run_script(tmp_path, script)
    out2 = run_script(tmp_path, script)
    assert "executing now()" in out1
    assert "executing now()" not in out2  # still cached

    # Wait >1s to expire TTL
    time.sleep(1.5)
    out3 = run_script(tmp_path, script)
    assert "executing now()" in out3


def test_cache_file_written(tmp_path):
    script = """
import devstash

devstash.activate()

def f():
    return 42

val = f()  # @devstash
print(val)
"""
    run_script(tmp_path, script)
    files = list(map(str, CACHE_DIR.glob("*.pkl")))
    assert len(files) == 1
    expected_filename = ".devstash_cache/__main____f"
    assert expected_filename in files[0], "Expected a cache file to be written"
    with open(files[0], "rb") as f:
        val = pickle.load(f)
    assert val == 42


# -----------------------------
# Regex + helper function tests
# -----------------------------
def test_inline_regex_matches_variants():
    assert DEVSTASH_INLINE_RE.search("x = foo()  # @devstash")
    assert DEVSTASH_INLINE_RE.search("y = bar()  #    @devstash   ")
    assert not DEVSTASH_INLINE_RE.search("z = 1  # not @devstash")


def test_standalone_regex_matches_clean_marker():
    assert DEVSTASH_STANDALONE_RE.match("# @devstash")
    assert DEVSTASH_STANDALONE_RE.match("   #   @devstash   ")
    assert DEVSTASH_STANDALONE_RE.match("# @devstash ttl=5m")
    assert DEVSTASH_STANDALONE_RE.match("   # @devstash   ttl=10s  ")
    assert not DEVSTASH_STANDALONE_RE.match("# @devstash extra stuff")
    assert not DEVSTASH_STANDALONE_RE.match("x = 1  # @devstash")


def test_ttl_regex_extracts_value():
    assert DEVSTASH_TTL_RE.search("# @devstash ttl=10s").group(1) == "10s"
    assert DEVSTASH_TTL_RE.search("bar()  # @devstash ttl=5m").group(1) == "5m"
    assert DEVSTASH_TTL_RE.search("# @devstash ttl=2h").group(1) == "2h"
    assert DEVSTASH_TTL_RE.search("# @devstash").group(1) if DEVSTASH_TTL_RE.search("# @devstash") else None is None


def test_is_devstash_marker():
    assert is_devstash_marker("# @devstash")
    assert is_devstash_marker("   # @devstash   ttl=1d  ")
    assert not is_devstash_marker("print('hi')  # @devstash")
    assert not is_devstash_marker("# @devstash extra")


def test_extract_ttl_function():
    assert extract_ttl("# @devstash ttl=10s") == "10s"
    assert extract_ttl("foo()  # @devstash ttl=3h") == "3h"
    assert extract_ttl("# @devstash") is None


# -----------------------------
# Transformer tests
# -----------------------------
def _transform_and_get_code(src: str):
    """Helper: run CacheNodeTransformer and return transformed code as string."""
    lines = src.splitlines()
    tree = ast.parse(src)
    new_tree = CacheNodeTransformer(lines).visit(tree)
    ast.fix_missing_locations(new_tree)
    return compile(new_tree, "<test>", "exec")


def test_inline_marker_wraps_call():
    src = "foo()  # @devstash ttl=5s"
    tree = ast.parse(src)
    new_tree = CacheNodeTransformer(src.splitlines()).visit(tree)
    ast.fix_missing_locations(new_tree)

    result = ast.unparse(new_tree)
    assert result == "__devstash_cache_call(foo, ttl='5s')"


def test_standalone_marker_wraps_next_call():
    src = "# @devstash ttl=10m\nbar()"
    tree = ast.parse(src)
    new_tree = CacheNodeTransformer(src.splitlines()).visit(tree)
    ast.fix_missing_locations(new_tree)

    result = ast.unparse(new_tree)
    assert result == "__devstash_cache_call(bar, ttl='10m')"


def test_no_marker_does_not_wrap():
    src = "baz()"
    tree = ast.parse(src)
    new_tree = CacheNodeTransformer(src.splitlines()).visit(tree)
    ast.fix_missing_locations(new_tree)

    result = ast.unparse(new_tree)
    assert result == src


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
