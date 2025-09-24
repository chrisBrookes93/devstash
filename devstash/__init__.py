import logging
import os
import sys
from pathlib import Path

from devstash._ast_rewrite import rewrite_and_run_main
from devstash._cache import devstash_cache_call

logger = logging.getLogger("devstash")


def activate():
    """
    Activate devstash AST rewriting on the current entrypoint.

    Call this once at the top of your main script. Example:

        import devstash
        devstash.activate()

    Then any lines annotated with `# @devstash` will be cached.
    """
    if os.environ.get("DEVSTASH_ACTIVE") == "1":
        # Already rewritten, no-op
        return
    main_file = Path(sys.argv[0])

    skip = os.environ.get("DEVSTASH_SKIP_REWRITE", "").strip().lower() in ("1", "true", "yes")
    if main_file.exists() and not skip:
        os.environ["DEVSTASH_ACTIVE"] = "1"
        warning_banner = """
==================================================================
 WARNING: devstash is active!
 This tool is for DEVELOPMENT ONLY — do not use in production.
==================================================================
        """
        print(warning_banner, file=sys.stderr)
        rewrite_and_run_main(main_file, devstash_cache_call)


__all__ = ["activate"]
