import pickle
import subprocess
import time

from tests.conftest import CACHE_DIR


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
