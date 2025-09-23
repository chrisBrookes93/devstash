from devstash._ast_rewrite import (
    DEVSTASH_INLINE_RE,
    DEVSTASH_STANDALONE_RE,
    DEVSTASH_TTL_RE,
    extract_ttl,
    is_devstash_marker,
)


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
