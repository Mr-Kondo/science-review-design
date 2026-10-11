#!/usr/bin/env python3
"""Remove unchanged science-review installations made by install.py."""

from __future__ import annotations

import shutil
import sys

from install import check_destination, destinations, parser


def main(argv: list[str] | None = None) -> int:
    args = parser("Uninstall science-review managed by install.py").parse_args(argv)
    try:
        paths = destinations(args)
        installed = [check_destination(path) for path in paths]
        for path, exists in zip(paths, installed):
            if exists and not args.dry_run:
                shutil.rmtree(path)
            action = "remove" if exists else "skip (not installed)"
            print(f"{'[dry-run] ' if args.dry_run else ''}{action}: {path}")
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
