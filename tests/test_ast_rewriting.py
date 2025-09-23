import ast

from devstash._ast_rewrite import CacheNodeTransformer


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
