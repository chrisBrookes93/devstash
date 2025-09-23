import argparse
import shutil
import time

from ._cache import CACHE_DIR, parse_ttl


def human_readable_duration(seconds: float) -> str:
    """Convert seconds into human-friendly string like '1d 2h 3m 4s'."""
    seconds = int(seconds)
    parts = []
    units = [
        ("w", 7 * 24 * 3600),
        ("d", 24 * 3600),
        ("h", 3600),
        ("m", 60),
        ("s", 1),
    ]
    for name, count in units:
        value, seconds = divmod(seconds, count)
        if value > 0:
            parts.append(f"{value}{name}")
    return " ".join(parts) if parts else "0s"


def list_cache(ttl: str | None = None):
    """List all cache files with age and TTL status."""
    if not CACHE_DIR.exists():
        print("No cache directory found.")
        return

    files = list(CACHE_DIR.glob("*.pkl"))
    if not files:
        print("No cache entries found.")
        return

    now = time.time()
    print(f"{'Cache File':60} {'Age':>12} {'TTL Status':>20}")
    print("-" * 100)

    for f in files:
        try:
            mtime = f.stat().st_mtime
            age_seconds = now - mtime
            age_str = human_readable_duration(age_seconds)

            status = "valid"
            if ttl:
                try:
                    td = parse_ttl(ttl)
                    if age_seconds > td.total_seconds():
                        status = f"expired (>{ttl})"
                    else:
                        status = f"valid (<={ttl})"
                except Exception as e:
                    status = f"invalid TTL ({e})"

            print(f"{f.name:60} {age_str:>12} {status:>20}")
        except Exception as e:
            print(f"{f.name:60} ERROR: {e}")


def clear_cache(all_files: bool = False, pattern: str | None = None):
    """Clear cache files by pattern or all at once."""
    if not CACHE_DIR.exists():
        print("No cache directory found.")
        return

    if all_files:
        shutil.rmtree(CACHE_DIR)
        print("✅ Cleared all cached entries.")
        return

    files = list(CACHE_DIR.glob("*.pkl"))
    if not files:
        print("No cache entries found.")
        return

    removed = 0
    for f in files:
        if pattern is None or pattern in f.name:
            f.unlink()
            removed += 1

    if removed:
        print(f"✅ Removed {removed} cache file(s).")
    else:
        print("No matching cache files found.")


def main():
    parser = argparse.ArgumentParser(prog="devstash")
    subparsers = parser.add_subparsers(dest="command")

    # list command
    list_parser = subparsers.add_parser("list", help="List cached entries")
    list_parser.add_argument("--ttl", help="Optional TTL filter, e.g. 1d, 2h")

    # clear command
    clear_parser = subparsers.add_parser("clear", help="Clear cached entries")
    clear_parser.add_argument("--all", action="store_true", help="Remove all cache files")
    clear_parser.add_argument(
        "--pattern",
        type=str,
        help="Remove only cache files containing this pattern in the filename",
    )

    args = parser.parse_args()

    if args.command == "list":
        list_cache(ttl=args.ttl)
    elif args.command == "clear":
        clear_cache(all_files=args.all, pattern=args.pattern)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
