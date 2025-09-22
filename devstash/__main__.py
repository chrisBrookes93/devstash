"""
Allow `python -m devstash` to act as a small debug utility.
This is not required for normal use but is helpful for testing.
"""

import sys
from pathlib import Path

from devstash._ast_rewrite import rewrite_and_run_main
from devstash._cache import devstash_cache_call


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m devstash <script.py> [args...]")
        sys.exit(1)

    script = Path(sys.argv[1])
    if not script.exists():
        print(f"Script not found: {script}")
        sys.exit(1)

    # Shift args so the target script sees correct sys.argv
    sys.argv = sys.argv[1:]
    rewrite_and_run_main(script, devstash_cache_call)


if __name__ == "__main__":
    main()
