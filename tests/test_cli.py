import os
import subprocess
import sys


def run_cli(*args, env=None):
    """Helper to run the devstash CLI as a subprocess."""
    return subprocess.run(
        [sys.executable, "-m", "devstash.cli", *args],
        text=True,
        capture_output=True,
        env=env or os.environ.copy(),
        check=True,
    )


def test_list_and_clear(tmp_path):
    # Redirect cache dir to temp folder
    cache_dir = tmp_path / ".devstash_cache"
    cache_dir.mkdir()

    # Create dummy cache files
    (cache_dir / "foo__bar__123.pkl").write_bytes(b"abc")
    (cache_dir / "baz__qux__456.pkl").write_bytes(b"xyz")

    env = os.environ.copy()
    env["DEVSTASH_CACHE_DIR"] = str(cache_dir)

    # Run "list" and check output contains filenames
    result = run_cli("list", env=env)
    assert "foo__bar__123.pkl" in result.stdout
    assert "baz__qux__456.pkl" in result.stdout

    # Run "clear" and ensure files are deleted
    run_cli("clear", env=env)
    assert not any(cache_dir.iterdir())


def test_list_empty_dir(tmp_path):
    cache_dir = tmp_path / ".devstash_cache"
    cache_dir.mkdir()

    env = os.environ.copy()
    env["DEVSTASH_CACHE_DIR"] = str(cache_dir)

    result = run_cli("list", env=env)
    assert "No cache entries found." in result.stdout
