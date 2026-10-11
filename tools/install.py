#!/usr/bin/env python3
"""Install or update science-review using only the Python standard library."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import stat
import sys
import tempfile


SOURCE = Path(__file__).resolve().parents[1] / ".claude/skills/science-review"
NAME = "science-review"
MARKER = ".science-review-install.json"
VERSION = "2.0.0"
EVAL_FILES = (
    "README.md", "cases.json", "trigger-cases.json", "input-preservation.json",
    "model-results.json", "extended-results.json", "verification-results.md",
)


def parser(description: str) -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=description)
    result.add_argument("--scope", choices=("user", "project"), default="user")
    result.add_argument("--target", choices=("codex", "claude", "all"), default="all")
    result.add_argument("--project-dir", type=Path, help="Required with --scope project")
    result.add_argument("--dry-run", action="store_true", help="Check and show without changing files")
    return result


def destinations(args: argparse.Namespace) -> list[Path]:
    if args.scope == "project":
        if args.project_dir is None or not args.project_dir.is_dir():
            raise ValueError("--scope project requires an existing --project-dir directory")
        base = args.project_dir.resolve()
    else:
        if args.project_dir is not None:
            raise ValueError("--project-dir is only valid with --scope project")
        base = Path.home().resolve()
    targets = ("codex", "claude") if args.target == "all" else (args.target,)
    return [base / (".agents" if target == "codex" else ".claude") / "skills" / NAME
            for target in targets]


def reject_links(path: Path) -> None:
    for entry in (path, *path.parents):
        try:
            attributes = getattr(entry.lstat(), "st_file_attributes", 0)
        except FileNotFoundError:
            continue
        if entry.is_symlink() or attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError(f"Refusing a symlink or junction: {entry}")


def inventory(directory: Path) -> dict[str, str | None]:
    result = {}
    for entry in sorted(directory.rglob("*")):
        reject_links(entry)
        key = entry.relative_to(directory).as_posix()
        if key == MARKER:
            continue
        if entry.name == "__pycache__" and entry.is_dir():
            continue
        if "__pycache__" in entry.relative_to(directory).parts and entry.suffix == ".pyc" and entry.is_file():
            continue
        if entry.is_dir():
            result[key + "/"] = None
        elif entry.is_file():
            result[key] = hashlib.sha256(entry.read_bytes()).hexdigest()
        else:
            raise ValueError(f"Not a regular file or directory: {entry}")
    return result


def check_destination(path: Path) -> bool:
    reject_links(path)
    if not path.exists():
        return False
    if path.resolve() == SOURCE.resolve() or not path.is_dir():
        raise ValueError(f"Refusing the source directory or a non-directory: {path}")
    marker = path / MARKER
    reject_links(marker)
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"Not an installation managed by this script: {path}") from exc
    if not isinstance(data, dict) or data.get("name") != NAME or data.get("schema") != 1:
        raise ValueError(f"Invalid installation marker: {path}")
    current = inventory(path)
    if not current.get("SKILL.md") or data.get("files") != current:
        raise ValueError(f"Changed, missing, or added files in {path}; back them up and move the directory first")
    return True


def package_files() -> list[Path]:
    files = [SOURCE / "SKILL.md", *(SOURCE / "evals" / name for name in EVAL_FILES)]
    for group in ("references", "assets", "scripts", "tests", "evals/fixtures"):
        for entry in sorted((SOURCE / group).rglob("*")):
            reject_links(entry)
            if "__pycache__" not in entry.parts and entry.suffix in (".md", ".py", ".json") and entry.is_file():
                files.append(entry)
    for entry in files:
        reject_links(entry)
        if not entry.is_file():
            raise ValueError(f"Missing package file: {entry}")
    for group in ("references", "assets", "scripts", "tests", "evals/fixtures"):
        if not any(entry.is_relative_to(SOURCE / group) for entry in files):
            raise ValueError(f"Missing package directory: {SOURCE / group}")
    return files


def install_one(destination: Path, files: list[Path]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".science-review-", dir=destination.parent))
    previous = temporary / "previous"
    try:
        staging = temporary / "new"
        staging.mkdir()
        for source in files:
            target = staging / source.relative_to(SOURCE)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        (staging / MARKER).write_text(json.dumps({
            "name": NAME, "schema": 1, "version": VERSION, "files": inventory(staging),
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if check_destination(destination):
            destination.rename(previous)
        try:
            staging.rename(destination)
        except OSError:
            if previous.exists():
                previous.rename(destination)
            raise
    finally:
        if previous.exists() and not destination.exists():
            print(f"Original installation preserved at: {previous}", file=sys.stderr)
        else:
            shutil.rmtree(temporary)


def main(argv: list[str] | None = None) -> int:
    args = parser("Install or update science-review for Codex and Claude Code").parse_args(argv)
    try:
        paths = destinations(args)
        files = package_files()
        installed = [check_destination(path) for path in paths]
        for path, exists in zip(paths, installed):
            action = "update" if exists else "install"
            if not args.dry_run:
                install_one(path, files)
            print(f"{'[dry-run] ' if args.dry_run else ''}{action}: {path}")
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    sys.exit(main())
