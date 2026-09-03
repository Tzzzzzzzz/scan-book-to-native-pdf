#!/usr/bin/env python3
"""Compute a deterministic revision hash over all runtime skill files."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def compute_revision(root: Path) -> tuple[str, list[dict[str, str]]]:
    package_path = root / "wikiskill.json"
    package = json.loads(package_path.read_text(encoding="utf-8"))
    relative_paths = package.get("access_policy", {}).get("inference", [])
    if not isinstance(relative_paths, list) or not relative_paths:
        raise ValueError("wikiskill.json has no inference access paths")

    normalized = sorted({Path(item).as_posix() for item in relative_paths})
    if len(normalized) != len(relative_paths):
        raise ValueError("inference access paths contain duplicates")

    digest = hashlib.sha256()
    digest.update(b"wikiskill-runtime-revision-v1\0")
    files: list[dict[str, str]] = []
    for relative in normalized:
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError(f"runtime path must stay inside the skill root: {relative}")
        if relative.startswith(("raw/", "wiki/")):
            raise ValueError(f"runtime revision cannot include evolution layer: {relative}")
        path = (root / relative_path).resolve()
        try:
            path.relative_to(root.resolve())
        except ValueError as exc:
            raise ValueError(f"runtime path escapes the skill root: {relative}") from exc
        if not path.is_file():
            raise ValueError(f"runtime file does not exist: {relative}")
        data = path.read_bytes()
        path_bytes = relative.encode("utf-8")
        digest.update(len(path_bytes).to_bytes(8, "big"))
        digest.update(path_bytes)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
        files.append(
            {
                "path": relative,
                "sha256": hashlib.sha256(data).hexdigest().upper(),
            }
        )
    return digest.hexdigest().upper(), files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="skill root (default: parent of scripts/)",
    )
    parser.add_argument("--json", action="store_true", help="include component file hashes")
    args = parser.parse_args()
    try:
        revision, files = compute_revision(args.root.resolve())
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"skill revision failed: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(
            json.dumps(
                {"root": str(args.root.resolve()), "skill_revision": revision, "files": files},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(revision)
    return 0


if __name__ == "__main__":
    sys.exit(main())
