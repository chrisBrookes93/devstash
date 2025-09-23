import ast
import re
import sys
from pathlib import Path

DEVSTASH_INLINE_RE = re.compile(r"#\s*@devstash")
DEVSTASH_STANDALONE_RE = re.compile(r"^\s*#\s*@devstash(\s+ttl\s*=\s*\S+)?\s*$")
DEVSTASH_TTL_RE = re.compile(r"ttl\s*=\s*([0-9]+[smhdw])")


def is_devstash_marker(line: str) -> bool:
    """True if line is *only* a '# @devstash' marker (whitespace tolerant)."""
    return bool(DEVSTASH_STANDALONE_RE.match(line))


def extract_ttl(line: str) -> str | None:
    """Extract ttl=... from a line, if present."""
    match = DEVSTASH_TTL_RE.search(line)
    return match.group(1) if match else None


class CacheNodeTransformer(ast.NodeTransformer):
    def __init__(self, lines):
        self.lines = lines

    def visit_Call(self, node):
        lineno = node.lineno - 1
        line = self.lines[lineno]

        ttl_value = None
        is_stash = False

        # Inline case
        if DEVSTASH_INLINE_RE.search(line):
            is_stash = True
            ttl_value = extract_ttl(line)

        # Standalone case (check previous line is only the marker)
        elif lineno > 0 and is_devstash_marker(self.lines[lineno - 1]):
            is_stash = True
            ttl_value = extract_ttl(self.lines[lineno - 1])

        if is_stash:
            keywords = node.keywords[:]
            if ttl_value:
                keywords.append(ast.keyword(arg="ttl", value=ast.Constant(value=ttl_value)))

            new_node = ast.Call(
                func=ast.Name(id="__devstash_cache_call", ctx=ast.Load()),
                args=[node.func] + node.args,
                keywords=keywords,
            )
            return ast.copy_location(new_node, node)

        return self.generic_visit(node)


def rewrite_and_run_main(main_file: Path, cache_func):
    src = main_file.read_text()
    lines = src.splitlines()

    tree = ast.parse(src, filename=str(main_file))
    tree = CacheNodeTransformer(lines).visit(tree)
    ast.fix_missing_locations(tree)

    code = compile(tree, filename=str(main_file), mode="exec")

    globs = {
        "__name__": "__main__",
        "__devstash_cache_call": cache_func,
    }

    exec(code, globs)
    sys.exit(0)
