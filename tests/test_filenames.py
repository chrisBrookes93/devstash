import re

from devstash._cache import MAX_FILENAME_LENGTH, safe_filename, sanitize_filename


def test_sanitize_filename_replaces_unsafe_characters():
    assert sanitize_filename("foo/bar:baz*?") == "foo_bar_baz__"
    assert sanitize_filename("Hello World!") == "Hello_World_"


def test_sanitize_filename_reserved_names_are_prefixed():
    assert sanitize_filename("CON") == "_CON"
    assert sanitize_filename("prn.txt") == "_prn.txt"
    assert sanitize_filename("COM1") == "_COM1"
    assert sanitize_filename("LPT9") == "_LPT9"


def test_safe_filename_truncates_and_hashes():
    long_name = "a" * (MAX_FILENAME_LENGTH + 50)
    result = safe_filename(long_name)
    assert len(result) <= MAX_FILENAME_LENGTH
    assert re.search(r"_[0-9a-f]{16}$", result)  # ends with hash


def test_safe_filename_short_names_unchanged():
    name = "short_file.pkl"
    assert safe_filename(name) == name
